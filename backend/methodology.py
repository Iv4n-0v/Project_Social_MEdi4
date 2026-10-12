from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from backend.db import SessionDep
from backend.models import Methodology, MethodologyBase
from backend.services import methodology_service

router = APIRouter(tags=["methodologies"])


@router.post("/", response_model=Methodology)
def create_methodology(new_methodology: MethodologyBase, session: SessionDep):
    return methodology_service.create_methodology(session, new_methodology)


@router.put("/assign", summary="Assign Methodology to User")
def assign_methodology(user_id: int, methodology_id: int, session: SessionDep):
    result = methodology_service.assign_methodology(session, user_id, methodology_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User or Methodology not found")
    user, methodology = result
    return {"message": f"User {user.name} assigned to methodology {methodology.name}"}


@router.get("/all", response_model=list[Methodology])
def get_all_methodologies(session: SessionDep):
    return methodology_service.get_all_methodologies(session)


@router.get("/by_name/{name}", summary="Get methodology by name with assigned users")
def get_users_by_methodology(name: str, session: SessionDep):
    result = methodology_service.get_methodology_with_users(session, name)
    if result is None:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return result


@router.get("", response_class=HTMLResponse)
def show_methodologies(request: Request, session: SessionDep):
    methodologies = methodology_service.get_all_methodologies(session)
    return request.app.state.templates.TemplateResponse(
        "methodologies_list.html",
        {"request": request, "methodologies": methodologies}
    )


@router.get("/new", response_class=HTMLResponse)
def new_methodology_form(request: Request, session: SessionDep):
    benefits = methodology_service.get_all_benefits(session)
    return request.app.state.templates.TemplateResponse(
        "new_methodology.html",
        {"request": request, "benefits": benefits}
    )


@router.post("/new")
def create_methodology_web(
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(None),
    benefit_ids: list[int] = Form(default=[])
):
    methodology_service.create_methodology_web(session, name, description, benefit_ids)
    return RedirectResponse(url="/methodologies", status_code=303)


@router.get("/edit/{methodology_id}", response_class=HTMLResponse)
def edit_methodology_form(methodology_id: int, request: Request, session: SessionDep):
    methodology = methodology_service.get_methodology_by_id(session, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")

    benefits = methodology_service.get_all_benefits(session)

    return request.app.state.templates.TemplateResponse(
        "methodology_edit.html",
        {"request": request, "methodology": methodology, "benefits": benefits}
    )


@router.post("/edit/{methodology_id}")
def update_methodology(
    methodology_id: int,
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(None),
    benefit_ids: list[int] = Form(default=[])
):
    methodology = methodology_service.update_methodology(session, methodology_id, name, description, benefit_ids)
    if methodology is None:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return RedirectResponse(url="/methodologies", status_code=303)