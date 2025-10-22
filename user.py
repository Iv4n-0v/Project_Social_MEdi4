from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import User, UserBase, UserAudit
import traceback

router = APIRouter(tags=["users"])

@router.post("/", response_model=User)
def create_user(new_user: UserBase, session: SessionDep):
    try:
        user = User(**new_user.model_dump())
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/active", response_model=list[User])
def get_active_users(session: SessionDep):
    return session.query(User).filter(User.is_active==True).all()

@router.get("/all", response_model=list[User])
def get_all_users(session: SessionDep):
    return session.query(User).all()

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

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