"""Katalog ćwiczeń — CRUD + oznaczanie preferencji (czy_wybrane, ocena 1-5).

POST służy do dopisywania własnych ćwiczeń (source="custom").
Ćwiczenia od AI dopisze później Etap 5 (source="ai").
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import CatalogExercise
from app.schemas import CatalogExerciseCreate, CatalogExerciseUpdate

router = APIRouter(prefix="/api/exercises", tags=["exercise catalog"])


def _get_or_404(session: SessionDep, exercise_id: int) -> CatalogExercise:
    exercise = session.get(CatalogExercise, exercise_id)
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ćwiczenie o tym id nie istnieje")
    return exercise


def _assert_name_free(session: SessionDep, name: str, ignore_id: int | None = None) -> None:
    for row in session.exec(select(CatalogExercise)).all():
        if row.name.casefold() == name.casefold() and row.id != ignore_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Takie ćwiczenie już jest w katalogu")


@router.get("", response_model=list[CatalogExercise])
def list_exercises(
    session: SessionDep, equipment: str | None = None
) -> list[CatalogExercise]:
    rows = session.exec(select(CatalogExercise)).all()
    if equipment is not None:
        needle = equipment.casefold()
        rows = [r for r in rows if needle in (name.casefold() for name in r.required_equipment)]
    return list(rows)


@router.post("", response_model=CatalogExercise, status_code=status.HTTP_201_CREATED)
def create_exercise(data: CatalogExerciseCreate, session: SessionDep) -> CatalogExercise:
    name = data.name.strip()
    _assert_name_free(session, name)
    exercise = CatalogExercise(
        name=name,
        required_equipment=[eq.strip() for eq in data.required_equipment if eq.strip()],
        source="custom",
    )
    session.add(exercise)
    session.commit()
    session.refresh(exercise)
    return exercise


@router.put("/{exercise_id}", response_model=CatalogExercise)
def update_exercise(
    exercise_id: int, data: CatalogExerciseUpdate, session: SessionDep
) -> CatalogExercise:
    exercise = _get_or_404(session, exercise_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        name = updates["name"].strip()
        _assert_name_free(session, name, ignore_id=exercise_id)
        updates["name"] = name
    for key, value in updates.items():
        setattr(exercise, key, value)
    session.add(exercise)
    session.commit()
    session.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, session: SessionDep) -> None:
    exercise = _get_or_404(session, exercise_id)
    session.delete(exercise)
    session.commit()
