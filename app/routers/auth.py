"""Logowanie — jedyny publiczny endpoint API obok /hello.

POST /api/auth/login — sprawdza login i hasło, zwraca token JWT.
GET  /api/auth/me    — chroniony: pozwala frontendowi sprawdzić, czy
                       zapisany token nadal jest ważny.
"""

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth import CurrentUser, create_access_token, hash_password, verify_password
from app.database import SessionDep
from app.limiter import limiter
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Fałszywy hash bcrypt — do spalania czasu, gdy login nie istnieje
# (wygenerowany raz przy starcie, żeby nie liczyć go przy każdym żądaniu).
_DUMMY_HASH = hash_password("x")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # ochrona przed brute force (review 2026-11-04, pkt 1)
def login(request: Request, data: LoginRequest, session: SessionDep) -> TokenResponse:
    user = session.exec(select(User)).first()
    # Jeden komunikat niezależnie od tego, co się nie zgadza (login czy hasło):
    # nie zdradzamy napastnikowi, który składnik był błędny.
    if user is None or user.username != data.username:
        # Celowe hashowanie na fałszywym hashu: wyrównuje czas odpowiedzi
        # do ścieżki z prawdziwym bcryptem — inaczej "login nie istnieje"
        # odpowiadałoby w ~1 ms, a "złe hasło" w ~250 ms, co zdradzałoby,
        # które loginy istnieją (review 2026-11-04, pkt 4).
        verify_password(data.password, _DUMMY_HASH)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Nieprawidłowy login lub hasło"
        )
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Nieprawidłowy login lub hasło"
        )
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me")
def me(username: CurrentUser) -> dict[str, str]:
    return {"username": username}
