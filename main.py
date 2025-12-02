from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
import user, methodology, benefit, analysis
from db import create_tables
import reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables(app)
    yield


app = FastAPI(lifespan=lifespan, title="Social Impact API")

app.include_router(user.router, prefix="/users")
app.include_router(methodology.router, prefix="/methodologies")
app.include_router(benefit.router, prefix="/benefits")
app.include_router(analysis.router, prefix="/analyses")
app.include_router(reports.router, prefix="/reports", tags=["reports"])

templates = Jinja2Templates(directory="templates")

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