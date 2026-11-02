from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import catalog, equipment, profile


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Przy starcie serwera: stwórz tabele i zasil katalog (tylko za pierwszym razem)."""
    init_db()
    yield


app = FastAPI(title="PapuTrain API", lifespan=lifespan)

app.include_router(profile.router)
app.include_router(equipment.router)
app.include_router(catalog.router)


@app.get("/hello")
def hello():
    return {"message": "Cześć, PapuTrain działa!"}
