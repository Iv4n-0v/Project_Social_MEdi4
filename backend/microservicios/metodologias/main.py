from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import create_tables
from router import router
from service import MethodologyNotFound


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Metodologias")

app.include_router(router, prefix="/methodologies")


# ---- errores de dominio -> codigos HTTP ----
@app.exception_handler(MethodologyNotFound)
async def methodology_not_found_handler(request, exc: MethodologyNotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"servicio": "metodologias", "status": "ok"}


@app.get("/health")
def health():
    """Para el healthcheck de Docker / KrakenD."""
    return {"status": "ok"}
