"""Konfiguracja bazy SQLite: połączenie, sesja, tworzenie tabel i seed katalogu.

Plik bazy (app.db) leży w katalogu projektu, ale jest zgitignore'owany.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine, select

from app import models  # noqa: F401 — import rejestruje tabele w SQLModel

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"
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
    """Drobne zmiany schematu dla istniejącej bazy (create_all nie dodaje kolumn).

    SQLite wymaga ALTER TABLE; jeśli kolumna już istnieje, po prostu ignorujemy błąd.
    """
    try:
        with Session(engine) as session:
            session.execute(
                text("ALTER TABLE equipment ADD COLUMN details TEXT NOT NULL DEFAULT ''")
            )
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
