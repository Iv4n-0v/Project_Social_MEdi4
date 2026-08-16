from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse 
from fastapi import FastAPI, Request, HTTPException

from backend import user, methodology, benefit, analysis, reports
from backend.db import create_tables

# Ruta de la carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpeta donde están los templates
TEMPLATES_DIR = BASE_DIR / "templates"

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables(app)
    yield


app = FastAPI(lifespan=lifespan, title="Social Impact API")

app.include_router(user.router, prefix="/users")
app.include_router(methodology.router, prefix="/methodologies")
app.include_router(benefit.router, prefix="/benefits")
app.include_router(analysis.router, prefix="/analysis")
app.include_router(reports.router, prefix="/reports", tags=["reports"])

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.state.templates = templates

@app.get("/", response_class=HTMLResponse, tags=["Vistas HTML"])
def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "texto": "Bienvenido a la página de tu taller de confianza",
            "titulo_pagina": "Taller de Carros - Inicio"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request, 
            "status_code": exc.status_code, 
            "detail": exc.detail
        },
        status_code=exc.status_code,
    )