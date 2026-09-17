import httpx
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from sqlmodel import select
from backend.db import SessionDep
from backend.models import Benefit, BenefitBase, Methodology, MethodologyBenefitLink

router = APIRouter(tags=["benefits"])

BENEFITS_SERVICE_URL = "http://127.0.0.1:8001/benefits"


@router.post("/", response_model=Benefit)
def create_benefit(new_benefit: BenefitBase):
    response = httpx.post(BENEFITS_SERVICE_URL, json=new_benefit.model_dump())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al crear el beneficio")
    return response.json()


@router.get("/all", response_model=list[Benefit])
def get_all_benefits():
    response = httpx.get(BENEFITS_SERVICE_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener beneficios")
    return response.json()


@router.post("/link", summary="Link Benefit to Methodology")
def link_methodology_benefit(methodology_id: int, benefit_id: int, session: SessionDep):
    methodology = session.get(Methodology, methodology_id)
    benefit = session.get(Benefit, benefit_id)
    if not methodology or not benefit:
        raise HTTPException(status_code=404, detail="Methodology or Benefit not found")
    link = MethodologyBenefitLink(methodology_id=methodology_id, benefit_id=benefit_id)
    session.add(link)
    session.commit()
    return {"message": "Link created successfully"}


@router.get("/methodologies_with_benefits")
def get_methodologies_with_benefits(session: SessionDep):
    result = []

    metodologias = session.exec(select(Methodology)).all()
    for met in metodologias:
        links = session.exec(
            select(MethodologyBenefitLink).where(MethodologyBenefitLink.methodology_id == met.id)
        ).all()

        beneficios = []
        for link in links:
            benefit = session.get(Benefit, link.benefit_id)
            if benefit:
                beneficios.append({"id": benefit.id, "name": benefit.name, "description": benefit.description})

        result.append({
            "methodology": {"id": met.id, "name": met.name, "description": met.description},
            "benefits": beneficios
        })

    return result


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
    new_benefit = Benefit(
        name=name,
        description=description
    )

    session.add(new_benefit)
    session.commit()
    session.refresh(new_benefit)

    return RedirectResponse(url="/benefits", status_code=303)


@router.get("", response_class=HTMLResponse)
def show_benefits(request: Request, session: SessionDep):
    benefits = session.exec(select(Benefit)).all()

    return request.app.state.templates.TemplateResponse(
        "benefits_list.html",
        {
            "request": request,
            "benefits": benefits
        }
    )