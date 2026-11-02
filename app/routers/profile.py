"""Profil treningowy — jeden rekord: odczyt (GET) i zapis/aktualizacja (PUT).

PUT działa jako "upsert": aktualizuje istniejący profil albo tworzy pierwszy.
"""

from sqlmodel import select

from fastapi import APIRouter

from app.database import SessionDep
from app.models import Profile
from app.schemas import ProfileUpsert

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=Profile | None)
def get_profile(session: SessionDep) -> Profile | None:
    return session.exec(select(Profile)).first()


@router.put("", response_model=Profile)
def save_profile(data: ProfileUpsert, session: SessionDep) -> Profile:
    profile = session.exec(select(Profile)).first()
    if profile is None:
        profile = Profile.model_validate(data)
    else:
        for key, value in data.model_dump().items():
            setattr(profile, key, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
