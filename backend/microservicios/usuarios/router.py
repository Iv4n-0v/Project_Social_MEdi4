from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import select

from database import SessionDep
from models import User, UserAudit, UserMethodologyLink
from schemas import AuditResponse, UserResponse, UserUpdate
from storage import upload_to_bucket

router = APIRouter(tags=["users"])


# ---------- helpers ----------
def _get_user_or_404(session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _methodology_ids(session, user_id: int) -> list[int]:
    return list(
        session.exec(
            select(UserMethodologyLink.methodology_id).where(
                UserMethodologyLink.user_id == user_id
            )
        ).all()
    )


def _set_methodologies(session, user_id: int, ids: list[int]) -> None:
    old = session.exec(
        select(UserMethodologyLink).where(UserMethodologyLink.user_id == user_id)
    ).all()
    for link in old:
        session.delete(link)
    session.flush()
    for mid in set(ids):
        session.add(UserMethodologyLink(user_id=user_id, methodology_id=mid))


def _audit(session, user_id: int, action: str) -> None:
    session.add(UserAudit(user_id=user_id, action=action))


def _to_response(session, user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        is_active=user.is_active,
        img=user.img,
        methodology_ids=_methodology_ids(session, user.id),
    )


# ---------- endpoints ----------
@router.get("/", response_model=list[UserResponse])
def get_all_users(session: SessionDep, is_active: Optional[bool] = None):
    """?is_active=true -> activos | ?is_active=false -> eliminados | sin filtro -> todos"""
    stmt = select(User)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return [_to_response(session, u) for u in session.exec(stmt).all()]


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    session: SessionDep,
    name: str = Form(...),
    is_active: bool = Form(True),
    methodology_ids: list[int] = Form([]),
    img: Optional[UploadFile] = File(None),
):
    img_url = None
    if img and img.filename:
        img_url = await upload_to_bucket(img, "users")

    user = User(name=name, is_active=is_active, img=img_url)
    session.add(user)
    session.flush()  # obtiene user.id
    _set_methodologies(session, user.id, methodology_ids)
    _audit(session, user.id, "CREATE")
    session.commit()
    session.refresh(user)
    return _to_response(session, user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: SessionDep):
    return _to_response(session, _get_user_or_404(session, user_id))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, session: SessionDep):
    user = _get_user_or_404(session, user_id)
    if data.name is not None:
        user.name = data.name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.methodology_ids is not None:
        _set_methodologies(session, user.id, data.methodology_ids)
    session.add(user)
    _audit(session, user.id, "UPDATE")
    session.commit()
    session.refresh(user)
    return _to_response(session, user)


@router.put("/{user_id}/image", response_model=UserResponse)
async def update_user_image(
    user_id: int, session: SessionDep, img: UploadFile = File(...)
):
    user = _get_user_or_404(session, user_id)
    user.img = await upload_to_bucket(img, "users")
    session.add(user)
    _audit(session, user.id, "UPDATE_IMAGE")
    session.commit()
    session.refresh(user)
    return _to_response(session, user)


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, session: SessionDep):
    """Borrado logico (como en el backend original): is_active=False."""
    user = _get_user_or_404(session, user_id)
    user.is_active = False
    session.add(user)
    _audit(session, user.id, "DELETE")
    session.commit()
    session.refresh(user)
    return _to_response(session, user)


@router.post("/{user_id}/restore", response_model=UserResponse)
def restore_user(user_id: int, session: SessionDep):
    user = _get_user_or_404(session, user_id)
    user.is_active = True
    session.add(user)
    _audit(session, user.id, "RESTORE")
    session.commit()
    session.refresh(user)
    return _to_response(session, user)


@router.get("/{user_id}/audits", response_model=list[AuditResponse])
def get_user_audits(user_id: int, session: SessionDep):
    _get_user_or_404(session, user_id)
    return session.exec(
        select(UserAudit).where(UserAudit.user_id == user_id).order_by(UserAudit.id)
    ).all()