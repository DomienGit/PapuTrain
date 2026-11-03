"""Modele tabel bazy danych (SQLModel).

Nazwy pól po angielsku (konwencja), znaczenie zgodne z PLAN.md:
profile, equipment, exercise_catalog, plans, workouts, exercises.
"""

from datetime import date

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Jedno konto logowania — aplikacja jest jednoosobowa."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str  # hash bcrypt — czystego hasła NIGDY nie zapisujemy


class Profile(SQLModel, table=True):
    """Jeden rekord — profil treningowy Dominika."""

    __tablename__ = "profile"

    id: int | None = Field(default=None, primary_key=True)
    goal: str  # cel, np. "siła", "redukcja tłuszczu"
    level: str  # poziom: "początkujący" / "średni" / "zaawansowany"
    workouts_per_week: int  # N treningów w tygodniu
    workout_duration_min: int  # czas jednego treningu w minutach
    weight_kg: float | None = None
    height_cm: float | None = None
    limitations: str = ""  # ograniczenia zdrowotne (puste = brak)


class Equipment(SQLModel, table=True):
    """Sprzęt użytkownika. type: "predefined" (znany z katalogu) / "custom" (własny wpis)."""

    __tablename__ = "equipment"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    type: str = "custom"
    owned: bool = False  # czy_posiadany
    details: str = ""  # np. "4×2,5 kg + 2×10 kg" (krążki dla "Obciążenie")


class CatalogExercise(SQLModel, table=True):
    """Katalog ćwiczeń (wbudowany + dopisywany przez AI i użytkownika).

    source: "builtin" / "ai" / "custom"
    preference_rating: ocena preferencji 1-5 (None = nieocenione).
    """

    __tablename__ = "exercise_catalog"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    required_equipment: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    chosen: bool = False  # "pasuje mi" — preferencja, nie zamknięta pula
    preference_rating: int | None = None
    source: str = "builtin"


class Plan(SQLModel, table=True):
    """Plan tygodnia. status: "draft" / "active" / "archived"."""

    __tablename__ = "plans"

    id: int | None = Field(default=None, primary_key=True)
    week_start_date: date | None = None
    status: str = Field(default="draft")
    week_number: int = 1
    week_title: str = ""  # tytuł z odpowiedzi AI, np. "Tydzień 3"
    coach_note: str = ""  # notatka trenera z odpowiedzi AI
    user_notes: str = ""


class Workout(SQLModel, table=True):
    """Trening w planie — ponumerowany, BEZ przypisania do dnia tygodnia."""

    __tablename__ = "workouts"

    id: int | None = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plans.id", index=True)
    number: int  # 1, 2, 3...
    name: str  # np. "Trening A — góra ciała"
    rest_between_exercises_s: int | None = None  # przerwa między ćwiczeniami (sekundy)
    done: bool = False
    completed_date: date | None = None  # data wykonania (realny rytm dla AI)


class Exercise(SQLModel, table=True):
    """Ćwiczenie w treningu. rating to ocena WYKONANIA (1-5), nie preferencji."""

    __tablename__ = "exercises"

    id: int | None = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workouts.id", index=True)
    name: str
    sets: int = 1
    reps: str = ""  # np. "8-12" albo "40 s"
    rest_between_sets_s: int | None = None
    load: str = ""  # obciążenie / opis
    rating: int | None = None
    note: str = ""  # uwaga, np. "boli kolano przy przysiadzie"
