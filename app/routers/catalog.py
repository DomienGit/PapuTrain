"""Katalog ćwiczeń — CRUD + oznaczanie preferencji (czy_wybrane, ocena 1-5).

POST służy do dopisywania własnych ćwiczeń (source="custom"). Ćwiczenia od AI
dopisuje backend przy generowaniu planu (source="ai"). Od req 27 katalog jest
per konto (kopie — oceny i preferencje są osobiste), więc unikatowość nazwy
pilnujemy w obrębie konta.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.auth import CurrentUserObj
from app.database import SessionDep
from app.models import CatalogExercise, User
from app.schemas import CatalogExerciseCreate, CatalogExerciseUpdate

router = APIRouter(prefix="/api/exercises", tags=["exercise catalog"])


def _get_or_404(session: SessionDep, user: User, exercise_id: int) -> CatalogExercise:
    exercise = session.get(CatalogExercise, exercise_id)
    if exercise is None or exercise.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ćwiczenie o tym id nie istnieje")
    return exercise


def _assert_name_free(
    session: SessionDep, user: User, name: str, ignore_id: int | None = None
) -> None:
    rows = session.exec(
        select(CatalogExercise).where(CatalogExercise.user_id == user.id)
    ).all()
    for row in rows:
        if row.name.casefold() == name.casefold() and row.id != ignore_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Takie ćwiczenie już jest w katalogu")


@router.get("", response_model=list[CatalogExercise])
def list_exercises(
    user: CurrentUserObj, session: SessionDep, equipment: str | None = None
) -> list[CatalogExercise]:
    rows = session.exec(
        select(CatalogExercise).where(CatalogExercise.user_id == user.id)
    ).all()
    if equipment is not None:
        needle = equipment.casefold()
        rows = [r for r in rows if needle in (name.casefold() for name in r.required_equipment)]
    return list(rows)


@router.post("", response_model=CatalogExercise, status_code=status.HTTP_201_CREATED)
def create_exercise(
    data: CatalogExerciseCreate, user: CurrentUserObj, session: SessionDep
) -> CatalogExercise:
    name = data.name.strip()
    _assert_name_free(session, user, name)
    exercise = CatalogExercise(
        user_id=user.id,
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
    exercise_id: int, data: CatalogExerciseUpdate, user: CurrentUserObj, session: SessionDep
) -> CatalogExercise:
    exercise = _get_or_404(session, user, exercise_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        name = updates["name"].strip()
        _assert_name_free(session, user, name, ignore_id=exercise_id)
        updates["name"] = name
    for key, value in updates.items():
        setattr(exercise, key, value)
    session.add(exercise)
    session.commit()
    session.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int, user: CurrentUserObj, session: SessionDep
) -> None:
    exercise = _get_or_404(session, user, exercise_id)
    session.delete(exercise)
    session.commit()
