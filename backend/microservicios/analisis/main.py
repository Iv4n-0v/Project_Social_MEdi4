from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import create_tables
from router import router
from service import AnalysisNotFound


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Analisis")

app.include_router(router, prefix="/analysis")


# ---- errores de dominio -> codigos HTTP ----
@app.exception_handler(AnalysisNotFound)
async def analysis_not_found_handler(request, exc: AnalysisNotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"servicio": "analisis", "status": "ok"}


@app.get("/health")
def health():
    """Para el healthcheck de Docker / KrakenD."""
    return {"status": "ok"}
