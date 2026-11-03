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


class EquipmentUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    owned: bool | None = None


class CatalogExerciseCreate(SQLModel):
    """Własne ćwiczenie dopisywane przez użytkownika (source: "custom")."""

    name: str = Field(min_length=1, max_length=150)
    required_equipment: list[str] = Field(default_factory=list)


class CatalogExerciseUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    chosen: bool | None = None
    preference_rating: int | None = Field(default=None, ge=1, le=5)


class LoginRequest(SQLModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
