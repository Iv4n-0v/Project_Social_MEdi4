from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from typing import Optional
from db import SessionDep
from models import User, UserBase, UserAudit,Methodology
from supa.supabase import upload_to_bucket
import traceback
import supabase

router = APIRouter(tags=["users"])


@router.get("", response_class=HTMLResponse)
def get_active_users(request: Request, session: SessionDep):
    users = session.exec(select(User).where(User.is_active == True)).all()
    return request.app.state.templates.TemplateResponse(
        "user_list.html",
        {"request": request, "users": users}
    )

@router.get("/new", response_class=HTMLResponse)
def show_create(request: Request, session: SessionDep):
    methodologies = session.exec(select(Methodology)).all()
    return request.app.state.templates.TemplateResponse(
        "new_user.html",
        {"request": request, "methodologies": methodologies}
    )

@router.post("/new")
async def create_user_web(
    request: Request,
    session: SessionDep,
    name: str = Form(...),
    methodology_ids: list[int] = Form([]),
    is_active: str = Form("true"),
    img: Optional[UploadFile] = File(None)
):
    is_active_bool = is_active.lower() == "true"
    img_url = None
    if img:
        img_url = await upload_to_bucket(img, "users")
    new_user = User(name=name,is_active=is_active_bool,img=img_url,)
    session.add(new_user)
    session.commit()

    for mid in methodology_ids:
        methodology = session.get(Methodology, mid)
        if methodology:
            new_user.methodologies.append(methodology)

    session.commit()
    session.refresh(new_user)

    return RedirectResponse(url="/users", status_code=303)


@router.get("/deleted", response_class=HTMLResponse)
def list_inactive_users(request: Request, session: SessionDep):
    users = session.exec(select(User).where(User.is_active == False)).all()
    return request.app.state.templates.TemplateResponse(
        "user_elist.html",
        {"request": request, "users": users}
    )


@router.get("/active")
def get_active_users_supabase():
    response = supabase.table("users").select("*").eq("active", True).execute()
    return response.data

@router.put("/{user_id}/deactivate")
def deactivate_user_supabase(user_id: str):
    response = supabase.table("users").update({"active": False}).eq("id", user_id).execute()
    return {"message": "Usuario desactivado"}


@router.get("/api/active", response_model=list[User])
def get_active_users_local(session: SessionDep):
    return session.exec(select(User).where(User.is_active == True)).all()

@router.get("/api/all", response_model=list[User])
def get_all_users_api(session: SessionDep):
    return session.exec(select(User)).all()


@router.post("/", response_model=User)
async def create_user_api(
    session: SessionDep,
    name: str = Form(...),
    is_active: bool = Form(True),
    img: Optional[UploadFile] = File(None)
):
    img_url = None
    if img:
        img_url = await upload_to_bucket(img, "users")

    new_user = User(
        name=name,
        is_active=is_active,
        img=img_url
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@router.get("/detail/{user_id}", response_class=HTMLResponse)
def get_user_detail(request: Request, user_id: int, session: SessionDep):
    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    return request.app.state.templates.TemplateResponse(
        "user_detail.html",
        {"request": request, "user": user_db}
    )


@router.post("/api/update/{user_id}")
def update_user(
    user_id: int,
    session: SessionDep,
    name: str = Form(...),
    methodology_ids: list[int] = Form([])
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name

    user.methodologies.clear()

    for mid in methodology_ids:
        methodology = session.get(Methodology, mid)
        if methodology:
            user.methodologies.append(methodology)
    session.commit()
    return {"message": "ok"}


@router.post("/{user_id}/delete")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    session.add(user)
    session.commit()

    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)
    session.commit()

    return RedirectResponse(url="/users", status_code=303)


@router.post("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    session.commit()

    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)
    session.commit()

    return RedirectResponse(url="/users/deleted", status_code=303)


@router.get("/edit/{user_id}", response_class=HTMLResponse)
def edit_user_page(request: Request, user_id: int, session: SessionDep):

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    methodologies = session.exec(select(Methodology)).all()

    return request.app.state.templates.TemplateResponse(
        "user_edit.html",
        {
            "request": request,
            "user": user,
            "methodologies": methodologies  
        }
    )

@router.post("/{user_id}/update")
def update_user_web(
    user_id: int,
    session: SessionDep,
    name: str = Form(...),
    methodology_ids: list[int] = Form([])
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name

    # Limpiar metodologías actuales
    user.methodologies.clear()
    session.commit()

    # Agregar nuevas
    for mid in methodology_ids:
        methodology = session.get(Methodology, mid)
        if methodology:
            user.methodologies.append(methodology)

    session.commit()

    return RedirectResponse(url="/users", status_code=303)