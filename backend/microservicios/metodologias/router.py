from fastapi import APIRouter, HTTPException
from sqlmodel import select
from database import SessionDep
from models import Methodology, MethodologyBase

router = APIRouter(tags=["methodologies"])

@router.post("/", response_model=Methodology)
def create_methodology(new_methodology: MethodologyBase, session: SessionDep):
    methodology = Methodology.model_validate(new_methodology)
    session.add(methodology)
    session.commit()
    session.refresh(methodology)
    return methodology

@router.get("/", response_model=list[Methodology])
def get_all_methodologies(session: SessionDep):
    return session.exec(select(Methodology)).all()

@router.get("/{methodology_id}", response_model=Methodology)
def get_methodology(methodology_id: int, session: SessionDep):
    methodology = session.get(Methodology, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")
    return methodology

@router.put("/{methodology_id}", response_model=Methodology)
def update_methodology(methodology_id: int, methodology_data: MethodologyBase, session: SessionDep):
    methodology = session.get(Methodology, methodology_id)
    if not methodology:
        raise HTTPException(status_code=404, detail="Methodology not found")
    methodology.name = methodology_data.name
    methodology.description = methodology_data.description
    session.add(methodology)
    session.commit()
    session.refresh(methodology)
    return methodology