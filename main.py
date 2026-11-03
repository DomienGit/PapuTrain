from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.auth import get_current_user
from app.database import init_db
from app.routers import auth, catalog, equipment, plans, profile


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Przy starcie serwera: stwórz tabele i zasil katalog (tylko za pierwszym razem)."""
    init_db()
    yield


app = FastAPI(title="PapuTrain API", lifespan=lifespan)

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
