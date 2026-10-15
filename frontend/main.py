from pathlib import Path

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse 
from fastapi import FastAPI, Request, HTTPException

from frontend.clients.base import ServiceError, ServiceUnavailable
from frontend import user, methodology, benefit, analysis, reports

# Ruta de la carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent  # carpeta frontend/

# Carpeta donde están los templates
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Social Impact API")

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
            "texto": "Bienvenido a la página del manejo y registro de metodologias de tu pagina web",
            "titulo_pagina": "Social Media - Inicio"
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


def _error_page(request: Request, status_code: int, detail: str):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": status_code, "detail": detail},
        status_code=status_code,
    )


@app.exception_handler(ServiceUnavailable)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailable):
    return _error_page(request, 503, str(exc))


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return _error_page(request, exc.status_code, exc.detail)
