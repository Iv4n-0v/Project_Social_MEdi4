from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import Methodology, MethodologyBase, User

router = APIRouter(tags=["methodologies"])

@router.post("/", response_model=Methodology)
def create_methodology(new_methodology: MethodologyBase, session: SessionDep):
    data = new_methodology.model_dump()
    user_id = data.get("user_id")

    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    methodology = Methodology.model_validate(data)
    session.add(methodology)
    session.commit()
    session.refresh(methodology)
    return methodology


@router.get("/", response_model=list[Methodology])
def get_all_methodologies(session: SessionDep):
    return session.query(Methodology).all()


@router.get("/{methodology_id}", response_model=Methodology)
def get_one_methodology(methodology_id: int, session: SessionDep):
    methodology_db = session.get(Methodology, methodology_id)
    if not methodology_db:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return methodology_db