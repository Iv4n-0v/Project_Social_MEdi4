from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from frontend.clients.benefit_client import BenefitClient, BenefitDTO, get_benefit_client
from frontend.clients.methodology_client import MethodologyClient, get_methodology_client
from frontend.models import BenefitBase
from frontend.services import benefit_service

router = APIRouter(tags=["benefits"])

BenefitClientDep = Annotated[BenefitClient, Depends(get_benefit_client)]
MethodologyClientDep = Annotated[MethodologyClient, Depends(get_methodology_client)]


@router.post("/", response_model=BenefitDTO)
def create_benefit(new_benefit: BenefitBase, client: BenefitClientDep):
    return benefit_service.create_benefit(client, new_benefit.name, new_benefit.description)


@router.get("/all", response_model=list[BenefitDTO])
def get_all_benefits(client: BenefitClientDep):
    return benefit_service.get_all_benefits(client)


@router.post("/link", summary="Link Benefit to Methodology")
def link_methodology_benefit(
    methodology_id: int, benefit_id: int,
    methodology_client: MethodologyClientDep, benefit_client: BenefitClientDep,
):
    link = benefit_service.link_methodology_benefit(
        methodology_client, benefit_client, methodology_id, benefit_id
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Methodology or Benefit not found")
    return {"message": "Link created successfully"}


@router.get("/methodologies_with_benefits")
def get_methodologies_with_benefits(
    methodology_client: MethodologyClientDep, benefit_client: BenefitClientDep
):
    return benefit_service.get_methodologies_with_benefits(methodology_client, benefit_client)


@router.get("/new", response_class=HTMLResponse)
def new_benefit_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        "new_benefit.html",
        {"request": request}
    )


@router.post("/new")
def create_benefit_web(
    client: BenefitClientDep,
    name: str = Form(...),
    description: str = Form(None)
):
    benefit_service.create_benefit(client, name, description)
    return RedirectResponse(url="/benefits", status_code=303)


@router.get("", response_class=HTMLResponse)
def show_benefits(
    request: Request, benefit_client: BenefitClientDep, methodology_client: MethodologyClientDep
):
    benefits = benefit_service.get_benefits_with_methodologies(benefit_client, methodology_client)
    return request.app.state.templates.TemplateResponse(
        "benefits_list.html",
        {"request": request, "benefits": benefits}
    )
