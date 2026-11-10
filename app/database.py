"""Konfiguracja bazy SQLite: połączenie, sesja, tworzenie tabel i seed katalogu.

Plik bazy (app.db) leży w katalogu projektu, ale jest zgitignore'owany.
W Dockerze (Etap 10) ścieżkę nadpisuje zmienna PAPUTRAIN_DB — baza leży
wtedy w volume ./data, żeby przetrwała przebudowanie kontenera.
"""

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401 — import rejestruje tabele w SQLModel

DB_PATH = Path(os.environ.get("PAPUTRAIN_DB", Path(__file__).resolve().parent.parent / "app.db"))
CATALOG_JSON = Path(__file__).resolve().parent / "data" / "exercise_catalog.json"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def get_session() -> Iterator[Session]:
    """Zależność FastAPI: jedna sesja bazy na jedno zapytanie HTTP."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def load_catalog_json() -> dict:
    return json.loads(CATALOG_JSON.read_text(encoding="utf-8"))


def predefined_equipment_names() -> set[str]:
    """Nazwy sprzętu predefiniowanego (małymi literami) — do rozpoznawania typu."""
    return {name.casefold() for name in load_catalog_json()["equipment"]}


def init_db() -> None:
    """Tworzy tabele (jeśli brak) i dogania schemat istniejącej bazy.

    Seed sprzętu/katalogu NIE odbywa się tu — od req 27 każde konto dostaje
    własną kopię przy tworzeniu (seed_user_data, woła ją app/create_user.py).
    """
    SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    """Drobne zmiany schematu dla istniejącej bazy (create_all nie dodaje kolumn)."""
    _add_column("equipment", "details", "TEXT NOT NULL DEFAULT ''")
    _add_column("plans", "week_title", "TEXT NOT NULL DEFAULT ''")
    _add_column("plans", "coach_note", "TEXT NOT NULL DEFAULT ''")
    _add_column("exercises", "performed", "TEXT NOT NULL DEFAULT ''")  # req 21: "zrobiłem"
    _add_column("exercises", "muscle_group", "TEXT NOT NULL DEFAULT ''")  # req 22: partia
    _add_column("profile", "muscle_preferences", "TEXT NOT NULL DEFAULT '{}'")  # req 23
    _add_column("exercise_catalog", "last_rating", "INTEGER")  # req 24: pamięć gwiazdek

    # req 27: multi-user. Tabele equipment i exercise_catalog wymagają przebudowy
    # (SQLite nie umie usunąć UNIQUE z kolumny przez ALTER TABLE), reszta dostaje
    # kolumnę user_id zwykłym ALTER-em. Po przypisaniu user_id dane starego
    # jedynego konta (MIN(id) z users) zostają jego własnością.
    _rebuild_table_with_user_id("equipment")
    _rebuild_table_with_user_id("exercise_catalog")
    _add_column("profile", "user_id", "INTEGER")
    _add_column("plans", "user_id", "INTEGER")
    _backfill_user_id("profile")
    _backfill_user_id("plans")


def _table_columns(table: str) -> set[str]:
    """Nazwy kolumn tabeli (PRAGMA table_info) — do sprawdzania stanu schematu."""
    with Session(engine) as session:
        rows = session.execute(text(f"PRAGMA table_info({table})")).all()
    return {row[1] for row in rows}


def _add_column(table: str, column: str, definition: str) -> None:
    """ALTER TABLE dla SQLite; ignoruje błąd, gdy kolumna już istnieje."""
    try:
        with Session(engine) as session:
            session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            session.commit()
    except OperationalError:
        pass  # kolumna już jest — nic do zrobienia


def _backfill_user_id(table: str) -> None:
    """Niezapisane wiersze przypisuje pierwszemu kontu (stare dane jedynego usera).
    Idempotentne: po pierwszym uruchomieniu NULL-i już nie występują."""
    with Session(engine) as session:
        session.execute(
            text(
                f"UPDATE {table} SET user_id = (SELECT MIN(id) FROM users) "
                f"WHERE user_id IS NULL"
            )
        )
        session.commit()


# Schemat docelowy tabel przebudowywanych przy migracji req 27. Kluczowe różnice
# wobec starych tabel: kolumna user_id oraz BRAK UNIQUE na name (różne konta mają
# własne kopie wierszy o tej samej nazwie).
_REBUILD_SCHEMAS: dict[str, str] = {
    "equipment": """
        CREATE TABLE {new} (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL DEFAULT 'custom',
            owned BOOLEAN NOT NULL DEFAULT 0,
            details VARCHAR NOT NULL DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """,
    "exercise_catalog": """
        CREATE TABLE {new} (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER,
            name VARCHAR NOT NULL,
            required_equipment JSON NOT NULL,
            chosen BOOLEAN NOT NULL DEFAULT 0,
            preference_rating INTEGER,
            last_rating INTEGER,
            source VARCHAR NOT NULL DEFAULT 'builtin',
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """,
}

# Indeksy odtwarzane PO przebudowie (stare indeksy zawierają UNIQUE i znikają
# razem ze starą tabelą).
_REBUILD_INDEXES: dict[str, list[str]] = {
    "equipment": ["CREATE INDEX ix_equipment_name ON equipment (name)",
                  "CREATE INDEX ix_equipment_user_id ON equipment (user_id)"],
    "exercise_catalog": ["CREATE INDEX ix_exercise_catalog_name ON exercise_catalog (name)",
                         "CREATE INDEX ix_exercise_catalog_user_id ON exercise_catalog (user_id)"],
}


def _rebuild_table_with_user_id(table: str) -> None:
    """Przebudowa tabeli na schemat z user_id i bez UNIQUE na name (req 27).

    Potrzebna tylko dla starych baz (bez kolumny user_id). Kolejność jest
    wymuszona przez SQLite: najpierw nowa tabela i kopiowanie danych, potem
    drop starej (usuwają się też jej indeksy, zwalniając ich nazwy), rename
    i odtworzenie indeksów.
    """
    if "user_id" in _table_columns(table):
        return  # już po migracji
    new_name = f"{table}_new"
    create_sql = _REBUILD_SCHEMAS[table].format(new=new_name)
    columns = ", ".join(sorted(_table_columns(table)))
    with Session(engine) as session:
        session.execute(text(create_sql))
        # MIN(id) = id starego, jedynego konta — jego dane zostają jego własnością.
        session.execute(
            text(
                f"INSERT INTO {new_name} (id, user_id, {columns}) "
                f"SELECT id, (SELECT MIN(id) FROM users), {columns} FROM {table}"
            )
        )
        session.execute(text(f"DROP TABLE {table}"))
        session.execute(text(f"ALTER TABLE {new_name} RENAME TO {table}"))
        for index_sql in _REBUILD_INDEXES[table]:
            session.execute(text(index_sql))
        session.commit()


def seed_user_data(session: Session, user_id: int) -> None:
    """Wyposaża NOWE konto: 14 predefiniowanych sprzętów + katalog wbudowany (req 27).
    Wołane z app/create_user.py przy tworzeniu konta."""
    data = load_catalog_json()
    for name in data["equipment"]:
        session.add(models.Equipment(user_id=user_id, name=name, type="predefined", owned=False))
    for item in data["exercises"]:
        session.add(
            models.CatalogExercise(
                user_id=user_id,
                name=item["name"],
                required_equipment=item["equipment"],
                source="builtin",
            )
        )
    session.commit()
