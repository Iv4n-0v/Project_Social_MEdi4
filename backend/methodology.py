from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.clients.benefit_client import BenefitClient, get_benefit_client
from backend.clients.methodology_client import (
    MethodologyClient, MethodologyDTO, get_methodology_client,
)
from backend.db import SessionDep
from backend.models import MethodologyBase
from backend.services import benefit_service, methodology_service

router = APIRouter(tags=["methodologies"])

ClientDep = Annotated[MethodologyClient, Depends(get_methodology_client)]
BenefitClientDep = Annotated[BenefitClient, Depends(get_benefit_client)]


@router.post("/", response_model=MethodologyDTO)
def create_methodology(new_methodology: MethodologyBase, client: ClientDep):
    return methodology_service.create_methodology(client, new_methodology)


@router.put("/assign", summary="Assign Methodology to User")
def assign_methodology(user_id: int, methodology_id: int, session: SessionDep, client: ClientDep):
    result = methodology_service.assign_methodology(session, client, user_id, methodology_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User or Methodology not found")
    user, methodology = result
    return {"message": f"User {user.name} assigned to methodology {methodology.name}"}


@router.get("/all", response_model=list[MethodologyDTO])
def get_all_methodologies(client: ClientDep):
    return methodology_service.get_all_methodologies(client)


@router.get("/by_name/{name}", summary="Get methodology by name with assigned users")
def get_users_by_methodology(name: str, session: SessionDep, client: ClientDep):
    result = methodology_service.get_methodology_with_users(session, client, name)
    if result is None:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return result


@router.get("", response_class=HTMLResponse)
def show_methodologies(request: Request, client: ClientDep, benefit_client: BenefitClientDep):
    methodologies = benefit_service.get_methodologies_with_benefits(client, benefit_client)
    return request.app.state.templates.TemplateResponse(
        "methodologies_list.html",
        {"request": request, "methodologies": methodologies}
    )


@router.get("/new", response_class=HTMLResponse)
def new_methodology_form(request: Request, benefit_client: BenefitClientDep):
    benefits = methodology_service.get_all_benefits(benefit_client)
    return request.app.state.templates.TemplateResponse(
        "new_methodology.html",
        {"request": request, "benefits": benefits}
    )


@router.post("/new")
def create_methodology_web(
    client: ClientDep,
    name: str = Form(...),
    description: str = Form(None),
    benefit_ids: list[int] = Form(default=[])
):
    methodology_service.create_methodology_web(client, name, description, benefit_ids)
    return RedirectResponse(url="/methodologies", status_code=303)


@router.get("/edit/{methodology_id}", response_class=HTMLResponse)
def edit_methodology_form(
    methodology_id: int, request: Request, client: ClientDep, benefit_client: BenefitClientDep
):
    methodology = methodology_service.get_methodology_by_id(client, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")

    benefits = methodology_service.get_all_benefits(benefit_client)

    return request.app.state.templates.TemplateResponse(
        "methodology_edit.html",
        {"request": request, "methodology": methodology, "benefits": benefits}
    )


@router.post("/edit/{methodology_id}")
def update_methodology(
    methodology_id: int,
    client: ClientDep,
    name: str = Form(...),
    description: str = Form(None),
    benefit_ids: list[int] = Form(default=[])
):
    methodology = methodology_service.update_methodology(
        client, methodology_id, name, description, benefit_ids
    )
    if methodology is None:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return RedirectResponse(url="/methodologies", status_code=303)
