from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from backend.db import SessionDep
from backend.models import User
from backend.services import user_service

router = APIRouter(tags=["users"])


@router.get("", response_class=HTMLResponse)
def get_active_users(request: Request, session: SessionDep):
    users = user_service.get_active_users(session)
    return request.app.state.templates.TemplateResponse(
        "user_list.html",
        {"request": request, "users": users}
    )


@router.get("/new", response_class=HTMLResponse)
def show_create(request: Request, session: SessionDep):
    methodologies = user_service.get_all_methodologies(session)
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
    await user_service.create_user(session, name, is_active_bool, img, methodology_ids)
    return RedirectResponse(url="/users", status_code=303)


@router.get("/deleted", response_class=HTMLResponse)
def list_inactive_users(request: Request, session: SessionDep):
    users = user_service.get_inactive_users(session)
    return request.app.state.templates.TemplateResponse(
        "user_elist.html",
        {"request": request, "users": users}
    )


@router.get("/active")
def get_active_users_supabase():
    return user_service.get_active_users_supabase()


@router.put("/{user_id}/deactivate")
def deactivate_user_supabase(user_id: str):
    user_service.deactivate_user_supabase(user_id)
    return {"message": "Usuario desactivado"}


@router.get("/api/active", response_model=list[User])
def get_active_users_local(session: SessionDep):
    return user_service.get_active_users(session)


@router.get("/api/all", response_model=list[User])
def get_all_users_api(session: SessionDep):
    return user_service.get_all_users(session)


@router.post("/", response_model=User)
async def create_user_api(
    session: SessionDep,
    name: str = Form(...),
    is_active: bool = Form(True),
    img: Optional[UploadFile] = File(None)
):
    return await user_service.create_user(session, name, is_active, img)


@router.get("/detail/{user_id}", response_class=HTMLResponse)
def get_user_detail(request: Request, user_id: int, session: SessionDep):
    user_db = user_service.get_user_by_id(session, user_id)
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
    user = user_service.update_user(session, user_id, name, methodology_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "ok"}


@router.post("/{user_id}/delete")
def delete_user(user_id: int, session: SessionDep):
    user = user_service.soft_delete_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users", status_code=303)


@router.post("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep):
    user = user_service.restore_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users/deleted", status_code=303)


@router.get("/edit/{user_id}", response_class=HTMLResponse)
def edit_user_page(request: Request, user_id: int, session: SessionDep):
    user = user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    methodologies = user_service.get_all_methodologies(session)

    return request.app.state.templates.TemplateResponse(
        "user_edit.html",
        {"request": request, "user": user, "methodologies": methodologies}
    )


@router.post("/{user_id}/update")
def update_user_web(
    user_id: int,
    session: SessionDep,
    name: str = Form(...),
    methodology_ids: list[int] = Form([])
):
    user = user_service.update_user(session, user_id, name, methodology_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users", status_code=303)