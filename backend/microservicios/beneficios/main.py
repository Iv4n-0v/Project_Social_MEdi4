from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import create_tables
from router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Servicio de Beneficios")

app.include_router(router, prefix="/benefits")

@app.get("/")
def root():
    return {"servicio": "beneficios", "status": "ok"}