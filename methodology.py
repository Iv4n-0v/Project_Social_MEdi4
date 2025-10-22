from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import Methodology, MethodologyBase, User

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