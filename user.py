from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select, Session
from typing import Optional
from db import SessionDep
from models import User, UserBase, UserAudit
import traceback
from supa.supabase import upload_to_bucket
from starlette.status import HTTP_303_SEE_OTHER

router = APIRouter(tags=["users"])

@router.get("/", response_class=HTMLResponse)
def get_all_users_html(request: Request, session: Session = Depends(SessionDep)):
    users = session.exec(select(User).where(User.active == True)).all()
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

    return RedirectResponse(url=f"/users/{new_user.id}", status_code=303)



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

@router.delete("/{user_id}/delete")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    session.add(user)
    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)
    session.commit()
    return {"message": "User deactivated successfully"}

@router.patch("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    session.add(user)
    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)
    session.commit()
    return {"message": "User activated successfully"}

@router.get("/audit/logs", response_model=list[UserAudit])
def get_audit_logs(session: SessionDep):
    return session.query(UserAudit).all()