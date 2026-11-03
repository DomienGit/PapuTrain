"""Sprzęt użytkownika — CRUD.

Nazwa zgodna z listą predefiniowaną => type="predefined", inaczej "custom".
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep, predefined_equipment_names
from app.models import Equipment
from app.schemas import EquipmentCreate, EquipmentUpdate

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


def _get_or_404(session: SessionDep, equipment_id: int) -> Equipment:
    equipment = session.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprzęt o tym id nie istnieje")
    return equipment


def _assert_name_free(session: SessionDep, name: str, ignore_id: int | None = None) -> None:
    for row in session.exec(select(Equipment)).all():
        if row.name.casefold() == name.casefold() and row.id != ignore_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Taki sprzęt już jest na liście")


@router.get("", response_model=list[Equipment])
def list_equipment(session: SessionDep, owned: bool | None = None) -> list[Equipment]:
    rows = session.exec(select(Equipment)).all()
    if owned is not None:
        rows = [r for r in rows if r.owned == owned]
    return list(rows)


@router.post("", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(data: EquipmentCreate, session: SessionDep) -> Equipment:
    name = data.name.strip()
    _assert_name_free(session, name)
    equipment = Equipment(
        name=name,
        type="predefined" if name.casefold() in predefined_equipment_names() else "custom",
        owned=data.owned,
        details=data.details,
    )
    session.add(equipment)
    session.commit()
    session.refresh(equipment)
    return equipment


@router.put("/{equipment_id}", response_model=Equipment)
def update_equipment(
    equipment_id: int, data: EquipmentUpdate, session: SessionDep
) -> Equipment:
    equipment = _get_or_404(session, equipment_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        name = updates["name"].strip()
        _assert_name_free(session, name, ignore_id=equipment_id)
        updates["name"] = name
        updates["type"] = (
            "predefined" if name.casefold() in predefined_equipment_names() else "custom"
        )
    for key, value in updates.items():
        setattr(equipment, key, value)
    session.add(equipment)
    session.commit()
    session.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, session: SessionDep) -> None:
    equipment = _get_or_404(session, equipment_id)
    session.delete(equipment)
    session.commit()
