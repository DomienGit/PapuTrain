"""Schematy (kształty danych) przyjmowane przez API.

To modele "tylko do walidacji" — nie są tabelami w bazie. Pydantic sprawdza
tu np. zakresy (ocena 1-5), zanim dane dotkną bazy.
"""

from sqlmodel import Field, SQLModel


class ProfileUpsert(SQLModel):
    goal: str = Field(min_length=1, max_length=200)
    level: str = Field(min_length=1, max_length=50)
    workouts_per_week: int = Field(ge=1, le=7)
    workout_duration_min: int = Field(ge=10, le=240)
    weight_kg: float | None = Field(default=None, gt=0, lt=400)
    height_cm: float | None = Field(default=None, gt=0, lt=260)
    limitations: str = Field(default="", max_length=2000)


class EquipmentCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    owned: bool = True  # domyślnie: dodaję, bo mam
    details: str = Field(default="", max_length=500)


class EquipmentUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    owned: bool | None = None
    details: str | None = Field(default=None, max_length=500)


class CatalogExerciseCreate(SQLModel):
    """Własne ćwiczenie dopisywane przez użytkownika (source: "custom")."""

    name: str = Field(min_length=1, max_length=150)
    required_equipment: list[str] = Field(default_factory=list)


class CatalogExerciseUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    chosen: bool | None = None
    preference_rating: int | None = Field(default=None, ge=1, le=5)


class AiExercise(SQLModel):
    """Ćwiczenie w odpowiedzi AI — walidacja zanim dane trafią do bazy."""

    name: str = Field(min_length=1, max_length=150)
    sets: int = Field(ge=1, le=20)
    reps: str = Field(min_length=1, max_length=100)
    rest_between_sets: int = Field(ge=0, le=600)  # sekundy
    notes: str = Field(default="", max_length=500)


class AiWorkout(SQLModel):
    workout_name: str = Field(min_length=1, max_length=150)
    rest_between_exercises: int = Field(ge=0, le=600)  # sekundy
    exercises: list[AiExercise] = Field(min_length=1, max_length=20)


class AiPlan(SQLModel):
    """Cała odpowiedź AI: tytuł tygodnia, treningi i notatka trenera."""

    week_title: str = Field(min_length=1, max_length=100)
    workouts: list[AiWorkout] = Field(min_length=1, max_length=7)
    coach_note: str = Field(default="", max_length=1000)


class LoginRequest(SQLModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
