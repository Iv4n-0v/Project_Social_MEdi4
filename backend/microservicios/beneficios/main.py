from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import create_tables
from router import router
from service import BenefitNotFound


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Beneficios")

app.include_router(router, prefix="/benefits")


# ---- errores de dominio -> codigos HTTP ----
@app.exception_handler(BenefitNotFound)
async def benefit_not_found_handler(request, exc: BenefitNotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"servicio": "beneficios", "status": "ok"}


@app.get("/health")
def health():
    """Para el healthcheck de Docker / KrakenD."""
    return {"status": "ok"}
