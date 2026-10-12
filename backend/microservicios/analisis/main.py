from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import create_tables
from router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Servicio de Análisis")

app.include_router(router, prefix="/analysis")

@app.get("/")
def root():
    return {"servicio": "analysis", "status": "ok"}