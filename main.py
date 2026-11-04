from contextlib import asynccontextmanager

import logging

from fastapi import Depends, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth import get_current_user
from app.database import init_db
from app.limiter import limiter
from app.routers import auth, catalog, equipment, plans, profile

# Logi aplikacyjne (np. który model Gemini odpowiedział) idą na stderr razem z logami uvicorn.
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Przy starcie serwera: stwórz tabele i zasil katalog (tylko za pierwszym razem)."""
    init_db()
    yield


# Dokumentacja API (/docs, /openapi.json) wyłączona — nie wystawiamy
# mapy endpointów bez logowania (review 2026-11-04, pkt 5).
app = FastAPI(
    title="PapuTrain API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Rate limiting (slowapi): rejestracja limitera + obsługa błędu 429
# "zbyt wiele żądań" (review 2026-11-04, pkt 1).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Każdy nowy router z danymi rejestruj z dependencies=auth_deps (Etap 2: ochrona API).
auth_deps = [Depends(get_current_user)]

app.include_router(profile.router, dependencies=auth_deps)
app.include_router(equipment.router, dependencies=auth_deps)
app.include_router(catalog.router, dependencies=auth_deps)
app.include_router(plans.router, dependencies=auth_deps)
app.include_router(auth.router)  # publiczny — sam endpoint logowania


@app.get("/hello")
def hello():
    return {"message": "Cześć, PapuTrain działa!"}
