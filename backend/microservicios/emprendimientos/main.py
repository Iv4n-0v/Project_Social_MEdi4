from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlmodel import Session

from database import create_tables, engine
from repository import VentureRepository
from router import router
from storage import StorageError, StorageUnavailable
from service import (
    InvalidInput,
    NotPublishable,
    VentureInactive,
    VentureNotFound,
    seed_categories,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    with Session(engine) as session:
        seed_categories(VentureRepository(session))
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Emprendimientos")
app.include_router(router)

# Unico lugar que conoce los numeros HTTP
ERROR_STATUS = {
    InvalidInput: 422,
    VentureNotFound: 404,
    VentureInactive: 409,
    NotPublishable: 422,
    StorageUnavailable: 503,
    StorageError: 502,
}


def _make_handler(status_code: int):
    async def handler(request, exc):
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


for _cls, _status in ERROR_STATUS.items():
    app.add_exception_handler(_cls, _make_handler(_status))


@app.get("/")
def root():
    return {"servicio": "emprendimientos", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
