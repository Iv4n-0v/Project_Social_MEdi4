from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import create_tables
from router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Servicio de Metodologias")

app.include_router(router, prefix="/methodologies")

@app.get("/")
def root():
    return {"servicio": "metodologias", "status": "ok"}