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
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine, select

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
    """Tworzy tabele (jeśli brak), dodaje nowe kolumny i zasila katalog."""
    SQLModel.metadata.create_all(engine)
    _migrate()
    _seed_equipment()
    _seed_catalog()


def _migrate() -> None:
    """Drobne zmiany schematu dla istniejącej bazy (create_all nie dodaje kolumn)."""
    _add_column("equipment", "details", "TEXT NOT NULL DEFAULT ''")
    _add_column("plans", "week_title", "TEXT NOT NULL DEFAULT ''")
    _add_column("plans", "coach_note", "TEXT NOT NULL DEFAULT ''")
    _add_column("exercises", "performed", "TEXT NOT NULL DEFAULT ''")  # req 21: "zrobiłem"
    _add_column("exercises", "muscle_group", "TEXT NOT NULL DEFAULT ''")  # req 22: partia


def _add_column(table: str, column: str, definition: str) -> None:
    """ALTER TABLE dla SQLite; ignoruje błąd, gdy kolumna już istnieje."""
    try:
        with Session(engine) as session:
            session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            session.commit()
    except OperationalError:
        pass  # kolumna już jest — nic do zrobienia


def _seed_equipment() -> None:
    with Session(engine) as session:
        existing = {e.name.casefold() for e in session.exec(select(models.Equipment)).all()}
        for name in load_catalog_json()["equipment"]:
            if name.casefold() not in existing:
                session.add(models.Equipment(name=name, type="predefined", owned=False))
        session.commit()


def _seed_catalog() -> None:
    with Session(engine) as session:
        count = session.exec(
            select(func.count()).select_from(models.CatalogExercise)
        ).one()
        if count > 0:
            return
        for item in load_catalog_json()["exercises"]:
            session.add(
                models.CatalogExercise(
                    name=item["name"],
                    required_equipment=item["equipment"],
                    source="builtin",
                )
            )
        session.commit()
