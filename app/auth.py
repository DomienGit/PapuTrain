"""Logika logowania: hashowanie haseł (bcrypt) i tokeny JWT.

bcrypt — bezpieczne haszowanie haseł: z hasła robi się "odcisk" (hash),
z którego NIE da się odtworzyć hasła, ale da się sprawdzić poprawność.
JWT — podpisany token: serwer tworzy go przy logowaniu, przeglądarka
odsyła w nagłówku Authorization przy każdym zapytaniu, a serwer sprawdza podpis.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# auto_error=False => brak nagłówka dostaje nasz własny 401, nie domyślny 403
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(username: str) -> str:
    """Tworzy token ważny token_expire_days dni od teraz."""
    payload = {
        "sub": username,  # "sub" = subject: czyj to token (standard JWT)
        "exp": datetime.now(UTC) + timedelta(days=settings.token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Zależność FastAPI chroniąca endpointy: waliduje token, zwraca login."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Brak tokena — zaloguj się")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        # obejmuje też wygasły token (ExpiredSignatureError)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token nieprawidłowy lub wygasł — zaloguj się"
        )
    return str(payload["sub"])


CurrentUser = Annotated[str, Depends(get_current_user)]
