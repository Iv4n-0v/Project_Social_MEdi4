from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import create_tables
from router import router
from service import EmptyImage, ImageTooLarge, UnsupportedImageType, UserNotFound
from storage import StorageError, StorageUnavailable


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Usuarios")

app.include_router(router, prefix="/users")


# ---- errores de dominio -> codigos HTTP ----
# Es el UNICO lugar que conoce los numeros HTTP: servicio y almacenamiento
# solo lanzan errores con nombre propio.
ERROR_STATUS = {
    UserNotFound: 404,
    UnsupportedImageType: 415,
    EmptyImage: 400,
    ImageTooLarge: 413,
    StorageError: 502,
    StorageUnavailable: 503,
}


def _make_handler(status_code: int):
    async def handler(request, exc):
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


for _exc_class, _status in ERROR_STATUS.items():
    app.add_exception_handler(_exc_class, _make_handler(_status))


@app.get("/")
def root():
    return {"servicio": "usuarios", "status": "ok"}


@app.get("/health")
def health():
    """Para el healthcheck de Docker / KrakenD."""
    return {"status": "ok"}
