from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import oauth
import tokens
from database import create_tables
from router import get_keys, router, well_known
from service import (
    AccountDisabled,
    AccountNotFound,
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidInput,
    InvalidRefreshToken,
    InvalidResetToken,
    OAuthEmailConflict,
    ProviderNotConfigured,
    ProviderNotFound,
    TooManyAttempts,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    get_keys()  # carga (o crea) la llave de firma al arrancar
    yield


app = FastAPI(lifespan=lifespan, title="Servicio de Autenticacion")

app.include_router(router)
app.include_router(well_known)


# ---- errores de dominio -> codigos HTTP ----
# Es el UNICO lugar que conoce los numeros HTTP.
ERROR_STATUS = {
    InvalidInput: 422,
    EmailAlreadyRegistered: 409,
    OAuthEmailConflict: 409,
    InvalidCredentials: 401,
    InvalidRefreshToken: 401,
    tokens.InvalidToken: 401,
    InvalidResetToken: 400,
    AccountDisabled: 403,
    AccountNotFound: 404,
    ProviderNotFound: 404,
    TooManyAttempts: 429,
    ProviderNotConfigured: 503,
    oauth.OAuthFailed: 502,
}


def _make_handler(status_code: int):
    async def handler(request, exc):
        headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
        return JSONResponse(
            status_code=status_code, content={"detail": str(exc)}, headers=headers
        )

    return handler


for _exc_class, _status in ERROR_STATUS.items():
    app.add_exception_handler(_exc_class, _make_handler(_status))


@app.middleware("http")
async def no_store(request, call_next):
    """Las respuestas de autenticacion nunca deben quedar en cache."""
    response = await call_next(request)
    if request.url.path.startswith("/auth"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def root():
    return {"servicio": "auth", "status": "ok"}


@app.get("/health")
def health():
    """Para el healthcheck de Docker / KrakenD."""
    return {"status": "ok"}
