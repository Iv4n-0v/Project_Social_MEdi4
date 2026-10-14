from typing import Optional
from fastapi import UploadFile
from sqlmodel import select, Session
from backend.models import User, Methodology, UserAudit
from backend.supa.supabase import upload_to_bucket, supabase as supabase_client


def get_active_users(session: Session):
    return session.exec(select(User).where(User.is_active == True)).all()


def get_inactive_users(session: Session):
    return session.exec(select(User).where(User.is_active == False)).all()


def get_all_users(session: Session):
    return session.exec(select(User)).all()


def get_all_methodologies(session: Session):
    return session.exec(select(Methodology)).all()


def get_user_by_id(session: Session, user_id: int):
    return session.get(User, user_id)


async def create_user(session: Session, name: str, is_active: bool, img: Optional[UploadFile], methodology_ids: list[int] | None = None):
    img_url = None
    if img:
        img_url = await upload_to_bucket(img, "users")

    new_user = User(name=name, is_active=is_active, img=img_url)
    session.add(new_user)
    session.commit()

    if methodology_ids:
        for mid in methodology_ids:
            methodology = session.get(Methodology, mid)
            if methodology:
                new_user.methodologies.append(methodology)
        session.commit()

    session.refresh(new_user)
    return new_user


def update_user(session: Session, user_id: int, name: str, methodology_ids: list[int]):
    user = session.get(User, user_id)
    if not user:
        return None

    user.name = name
    user.methodologies.clear()
    session.commit()
    session.refresh(user)

    for mid in methodology_ids:
        methodology = session.get(Methodology, mid)
        if methodology:
            user.methodologies.append(methodology)

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