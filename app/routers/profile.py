"""Profil treningowy — jeden rekord na konto (req 27): odczyt i zapis/aktualizacja.

PUT działa jako "upsert": aktualizuje profil zalogowanego użytkownika albo tworzy
pierwszy (wtedy onboarding się kończy).
"""

from sqlmodel import select

from fastapi import APIRouter

from app.auth import CurrentUserObj
from app.database import SessionDep
from app.models import Profile
from app.schemas import ProfileUpsert

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=Profile | None)
def get_profile(user: CurrentUserObj, session: SessionDep) -> Profile | None:
    return session.exec(select(Profile).where(Profile.user_id == user.id)).first()


@router.put("", response_model=Profile)
def save_profile(
    data: ProfileUpsert, user: CurrentUserObj, session: SessionDep
) -> Profile:
    profile = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    if profile is None:
        profile = Profile.model_validate(data)
        profile.user_id = user.id
    else:
        for key, value in data.model_dump().items():
            setattr(profile, key, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
