from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import create_tables
from router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Usuarios")

app.include_router(router, prefix="/users")


@app.get("/")
def root():
    return {"servicio": "usuarios", "status": "ok"}