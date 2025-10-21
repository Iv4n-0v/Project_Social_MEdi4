from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import User, UserBase

router = APIRouter()

@router.post("/", response_model=User)
def create_user(new_user: UserBase, session: SessionDep):
    user = User.model_validate(new_user)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.get("/", response_model=list[User])
def get_users(session: SessionDep):
    return session.query(User).all()



