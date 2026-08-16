from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from sqlmodel import select
from backend.db import SessionDep
from backend.models import Methodology, MethodologyBase, User, Benefit

router = APIRouter(tags=["methodologies"])

@router.post("/", response_model=Methodology)
def create_methodology(new_methodology: MethodologyBase, session: SessionDep):
    methodology = Methodology.model_validate(new_methodology)
    session.add(methodology)
    session.commit()
    session.refresh(methodology)
    return methodology

@router.put("/assign", summary="Assign Methodology to User")
def assign_methodology(user_id: int, methodology_id: int, session: SessionDep):
    user = session.get(User, user_id)
    methodology = session.get(Methodology, methodology_id)
    if not user or not methodology:
        raise HTTPException(status_code=404, detail="User or Methodology not found")
    user.methodology_id = methodology_id
    session.add(user)
    session.commit()
    return {"message": f"User {user.name} assigned to methodology {methodology.name}"}

@router.get("/all", response_model=list[Methodology])
def get_all_methodologies(session: SessionDep):
    return session.query(Methodology).all()

@router.get("/by_name/{name}", summary="Get methodology by name with assigned users")
def get_users_by_methodology(name: str, session: SessionDep):
    methodology = session.exec(select(Methodology).where(Methodology.name == name)).first()
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")
    users = session.exec(select(User).where(User.methodology_id == methodology.id)).all()
    return {
        "methodology": {"id": methodology.id, "name": methodology.name, "description": methodology.description},
        "users": [{"id": u.id, "name": u.name, "type": u.type} for u in users]
    }

@router.get("", response_class=HTMLResponse)
def show_methodologies(request: Request, session: SessionDep):
    methodologies = session.exec(select(Methodology)).all()

    return request.app.state.templates.TemplateResponse(
        "methodologies_list.html",
        {
            "request": request,
            "methodologies": methodologies
        }
    )


@router.get("/new", response_class=HTMLResponse)
def new_methodology_form(request: Request, session: SessionDep):
    benefits = session.exec(select(Benefit)).all()
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
    new_methodology = Methodology(
        name=name,
        description=description
    )

    session.add(new_methodology)
    session.commit()
    session.refresh(new_methodology)

    # Asociar beneficios existentes
    for b_id in benefit_ids:
        benefit = session.get(Benefit, b_id)
        if benefit:
            new_methodology.benefits.append(benefit)

    session.commit()

    return RedirectResponse(url="/methodologies", status_code=303)

@router.get("/edit/{methodology_id}", response_class=HTMLResponse)
def edit_methodology_form(methodology_id: int, request: Request, session: SessionDep):
    methodology = session.get(Methodology, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")

    benefits = session.exec(select(Benefit)).all()

    return request.app.state.templates.TemplateResponse(
        "methodology_edit.html",
        {
            "request": request,
            "methodology": methodology,
            "benefits": benefits
        }
    )

@router.post("/edit/{methodology_id}")
def update_methodology(
    methodology_id: int,
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(None),
    benefit_ids: list[int] = Form(default=[])
):
    methodology = session.get(Methodology, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")

    methodology.name = name
    methodology.description = description

    methodology.benefits.clear()

    for b_id in benefit_ids:
        benefit = session.get(Benefit, b_id)
        if benefit:
            methodology.benefits.append(benefit)

    session.commit()

    return RedirectResponse(url="/methodologies", status_code=303)