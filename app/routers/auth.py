"""Logowanie — jedyne publiczne endpointy API obok /hello.

POST /api/auth/login         — sprawdza login i hasło, zwraca token JWT.
                               Konto utworzone BEZ hasła dostaje zamiast tego
                               {"setup_required": true} (req 27) — frontend
                               pokazuje wtedy ekran ustawiania hasła.
POST /api/auth/set-password  — ustawia pierwsze hasło takiego konta i od razu
                               loguje (zwraca token). Działa tylko dla kont
                               z pustym hasłem.
GET  /api/auth/me            — chroniony: pozwala frontendowi sprawdzić, czy
                               zapisany token nadal jest ważny.
"""

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth import CurrentUser, create_access_token, hash_password, verify_password
from app.database import SessionDep
from app.limiter import limiter
from app.models import User
from app.schemas import LoginRequest, SetPasswordRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Fałszywy hash bcrypt — do spalania czasu, gdy login nie istnieje
# (wygenerowany raz przy starcie, żeby nie liczyć go przy każdym żądaniu).
_DUMMY_HASH = hash_password("x")

# Jeden komunikat niezależnie od tego, co się nie zgadza (login czy hasło):
# nie zdradzamy napastnikowi, który składnik był błędny.
_GENERIC_401 = "Nieprawidłowy login lub hasło"


@router.post("/login")
@limiter.limit("5/minute")  # ochrona przed brute force (review 2026-11-04, pkt 1)
def login(request: Request, data: LoginRequest, session: SessionDep) -> dict:
    user = session.exec(select(User).where(User.username == data.username)).first()
    if user is not None and user.password_hash == "":
        # Konto bez hasła (req 27): nie da się "zalogować" — front przechodzi
        # do ekranu ustawiania hasła.
        return {"setup_required": True}
    if user is None or not verify_password(data.password, user.password_hash):
        # Celowe hashowanie na fałszywym hashu: wyrównuje czas odpowiedzi
        # do ścieżki z prawdziwym bcryptem — inaczej "login nie istnieje"
        # odpowiadałoby w ~1 ms, a "złe hasło" w ~250 ms, co zdradzałoby,
        # które loginy istnieją (review 2026-11-04, pkt 4).
        verify_password(data.password, _DUMMY_HASH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _GENERIC_401)
    return TokenResponse(access_token=create_access_token(user.username)).model_dump()


@router.post("/set-password", response_model=TokenResponse)
@limiter.limit("5/minute")
def set_password(
    request: Request, data: SetPasswordRequest, session: SessionDep
) -> TokenResponse:
    """Pierwsze logowanie konta utworzonego bez hasła (req 27)."""
    user = session.exec(select(User).where(User.username == data.username)).first()
    if user is None or user.password_hash != "":
        # Ten sam generyczny błąd co w loginie: endpoint działa TYLKO dla kont
        # z pustym hasłem, a komunikat nie zdradza, dlaczego odrzucono.
        verify_password(data.password, _DUMMY_HASH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _GENERIC_401)
    user.password_hash = hash_password(data.password)
    session.add(user)
    session.commit()
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me")
def me(username: CurrentUser) -> dict[str, str]:
    return {"username": username}
