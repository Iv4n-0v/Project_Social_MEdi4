from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select, Session
from typing import Optional
from db import SessionDep
from models import User, UserBase, UserAudit
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
def show_create(request: Request):
    return request.app.state.templates.TemplateResponse(
        "new_user.html",
        {"request": request}
    )

@router.post("/new")
async def create_user_web(
    request: Request,
    session: SessionDep,
    name: str = Form(...),
    type: str = Form(...),
    is_active: str = Form("true"),       
    img: Optional[UploadFile] = File(None)
):
    is_active_bool = True if is_active in ("true", "True", "1", True) else False

    img_url = None
    if img:
        try:
            img_url = await upload_to_bucket(img, 'users')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error subiendo imagen: {e}")

    try:
        new_user = User(
            name=name,
            type=type,
            is_active=is_active_bool,
            img=img_url
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR creando usuario:", tb)
        raise HTTPException(status_code=500, detail="Error interno al crear usuario")

    return RedirectResponse(url="/users", status_code=303)

@router.get("/users/active")
def get_active_users():
    response = supabase.table("users").select("*").eq("active", True).execute()
    return response.data

@router.put("/users/{user_id}/deactivate")
def deactivate_user(user_id: str):
    response = supabase.table("users").update({"active": False}).eq("id", user_id).execute()
    return {"message": "Usuario desactivado"}

@router.post("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep, request: Request):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active:
        return request.app.state.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "El usuario ya está activo"}
        )

    user.is_active = True
    session.add(user)

    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)

    session.commit()

    return RedirectResponse(url="/users_elist", status_code=303)

@router.post("/{user_id}/delete")
def delete_user(user_id: int, session: SessionDep, request: Request):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        return request.app.state.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "El usuario ya está inactivo"}
        )

    user.is_active = False
    session.add(user)

    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)

    session.commit()

    return RedirectResponse(url="/users", status_code=303)

@router.get("/elist", response_class=HTMLResponse)
def list_inactive_users(request: Request, session: SessionDep):
    users = session.exec(select(User).where(User.is_active == False)).all()
    return request.app.state.templates.TemplateResponse(
        "user_elist.html",
        {"request": request, "users": users}
    )

@router.get("/active", response_model=list[User])
def get_active_users(session: SessionDep):
    return session.query(User).filter(User.is_active==True).all()


@router.get("/api/all", response_model=list[User])
def get_all_users_api(session: SessionDep):
    return session.query(User).all()


@router.post("/", response_model=User)
async def create_user(
    request: Request,
    session: SessionDep,
    name: str = Form(...),
    type: str = Form(...),
    is_active: bool = Form(True),
    img: Optional[UploadFile] = File(None)
):
    img_url = None

    if img:
        try:
            img_url = await upload_to_bucket(img)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    new_user = User(
        name=name,
        type=type,
        is_active=is_active,
        img=img_url
    )

    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RedirectResponse(url="/users", status_code=303)


@router.get("/{user_id}", response_class=HTMLResponse)
def get_user(request: Request, user_id: int, session: SessionDep):
    user_db = session.get(User, user_id)

    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    return request.app.state.templates.TemplateResponse(
        "user_detail.html",
        {"request": request, "user": user_db}
    )



@router.put("/{user_id}/update", response_model=User)
def update_user(user_id: int, updated_user: UserBase, session: SessionDep):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = updated_user.name
    user.type = updated_user.type

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.post("/{user_id}/delete")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    session.add(user)

    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)

    session.commit()

    return RedirectResponse(url=f"/users/{user_id}", status_code=303)

@router.post("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    session.add(user)

    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)

    session.commit()

    return RedirectResponse(url=f"/users/{user_id}", status_code=303)



@router.get("/audit/logs", response_model=list[UserAudit])
def get_audit_logs(session: SessionDep):
    return session.exec(select(UserAudit)).all()
