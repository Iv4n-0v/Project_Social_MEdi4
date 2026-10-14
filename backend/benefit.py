import httpx
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from backend.db import SessionDep
from backend.models import Benefit, BenefitBase
from backend.services import benefit_service

router = APIRouter(tags=["benefits"])

BENEFITS_SERVICE_URL = "http://127.0.0.1:8001/benefits/"


@router.post("/", response_model=Benefit)
def create_benefit(new_benefit: BenefitBase):
    try:
        response = httpx.post(BENEFITS_SERVICE_URL, json=new_benefit.model_dump(), timeout=5)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de beneficios no disponible")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al crear el beneficio")
    return response.json()


@router.get("/all", response_model=list[Benefit])
def get_all_benefits():
    try:
        response = httpx.get(BENEFITS_SERVICE_URL, timeout=5)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de beneficios no disponible")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener beneficios")
    return response.json()


@router.post("/link", summary="Link Benefit to Methodology")
def link_methodology_benefit(methodology_id: int, benefit_id: int, session: SessionDep):
    link = benefit_service.link_methodology_benefit(session, methodology_id, benefit_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Methodology or Benefit not found")
    return {"message": "Link created successfully"}


@router.get("/methodologies_with_benefits")
def get_methodologies_with_benefits(session: SessionDep):
    return benefit_service.get_methodologies_with_benefits(session)


@router.get("/new", response_class=HTMLResponse)
def new_benefit_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        "new_benefit.html",
        {"request": request}
    )


@router.post("/new")
def create_benefit_web(
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(None)
):
    benefit_service.create_benefit_local(session, name, description)
    return RedirectResponse(url="/benefits", status_code=303)


@router.get("", response_class=HTMLResponse)
def show_benefits(request: Request, session: SessionDep):
    benefits = benefit_service.get_all_benefits_local(session)
    return request.app.state.templates.TemplateResponse(
        "benefits_list.html",
        {
            "request": request,
            "benefits": benefits
        }
    )