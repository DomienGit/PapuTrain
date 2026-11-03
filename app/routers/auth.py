"""Logowanie — jedyny publiczny endpoint API obok /hello.

POST /api/auth/login — sprawdza login i hasło, zwraca token JWT.
GET  /api/auth/me    — chroniony: pozwala frontendowi sprawdzić, czy
                       zapisany token nadal jest ważny.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.auth import CurrentUser, create_access_token, verify_password
from app.database import SessionDep
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: SessionDep) -> TokenResponse:
    user = session.exec(select(User)).first()
    # Jeden komunikat niezależnie od tego, co się nie zgadza (login czy hasło):
    # nie zdradzamy napastnikowi, który składnik był błędny.
    if (
        user is None
        or user.username != data.username
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Nieprawidłowy login lub hasło"
        )
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me")
def me(username: CurrentUser) -> dict[str, str]:
    return {"username": username}
