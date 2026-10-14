from typing import Optional
from fastapi import UploadFile
from sqlmodel import select, Session
from backend.clients.methodology_client import MethodologyClient
from backend.models import User, UserAudit, UserMethodologyLink
from backend.supa.supabase import upload_to_bucket, supabase as supabase_client


def get_active_users(session: Session):
    return session.exec(select(User).where(User.is_active == True)).all()


def get_inactive_users(session: Session):
    return session.exec(select(User).where(User.is_active == False)).all()


def get_all_users(session: Session):
    return session.exec(select(User)).all()


def get_all_methodologies(client: MethodologyClient):
    return client.find_all()


def get_methodology_ids(session: Session, user_id: int) -> list[int]:
    links = session.exec(
        select(UserMethodologyLink).where(UserMethodologyLink.user_id == user_id)
    ).all()
    return sorted(link.methodology_id for link in links)


def get_methodology_ids_by_user(session: Session) -> dict[int, list[int]]:
    grouped: dict[int, list[int]] = {}
    for link in session.exec(select(UserMethodologyLink)).all():
        grouped.setdefault(link.user_id, []).append(link.methodology_id)
    return grouped


def _set_methodologies(session: Session, user_id: int, methodology_ids: list[int],
                       client: MethodologyClient) -> None:
    """Reemplaza las metodologias del usuario (solo IDs que existan en el micro)."""
    valid = {m.id for m in client.find_all()}
    for link in session.exec(
        select(UserMethodologyLink).where(UserMethodologyLink.user_id == user_id)
    ).all():
        session.delete(link)
    session.flush()
    for mid in sorted(set(methodology_ids) & valid):
        session.add(UserMethodologyLink(user_id=user_id, methodology_id=mid))


def get_user_by_id(session: Session, user_id: int):
    return session.get(User, user_id)


async def create_user(session: Session, name: str, is_active: bool, img: Optional[UploadFile],
                      methodology_ids: list[int] | None = None,
                      methodology_client: MethodologyClient | None = None):
    img_url = None
    if img and img.filename:
        img_url = await upload_to_bucket(img, "users")

    new_user = User(name=name, is_active=is_active, img=img_url)
    session.add(new_user)
    session.commit()

    if methodology_ids and methodology_client is not None:
        _set_methodologies(session, new_user.id, methodology_ids, methodology_client)
        session.commit()

    session.refresh(new_user)
    return new_user


def update_user(session: Session, user_id: int, name: str, methodology_ids: list[int],
                methodology_client: MethodologyClient):
    user = session.get(User, user_id)
    if not user:
        return None

    user.name = name
    _set_methodologies(session, user_id, methodology_ids, methodology_client)
    session.commit()
    session.refresh(user)
    return user


def soft_delete_user(session: Session, user_id: int):
    user = session.get(User, user_id)
    if not user:
        return None

    user.is_active = False
    session.add(user)
    session.commit()

    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)
    session.commit()
    return user


def restore_user(session: Session, user_id: int):
    user = session.get(User, user_id)
    if not user:
        return None

    user.is_active = True
    session.commit()

    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)
    session.commit()
    return user


def get_active_users_supabase():
    response = supabase_client.table("users").select("*").eq("active", True).execute()
    return response.data


def deactivate_user_supabase(user_id: str):
    supabase_client.table("users").update({"active": False}).eq("id", user_id).execute()