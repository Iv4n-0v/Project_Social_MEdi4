from fastapi import APIRouter, HTTPException
from sqlmodel import select
from database import SessionDep
from models import Benefit, BenefitBase

router = APIRouter(tags=["benefits"])

@router.post("/", response_model=Benefit)
def create_benefit(new_benefit: BenefitBase, session: SessionDep):
    benefit = Benefit.model_validate(new_benefit)
    session.add(benefit)
    session.commit()
    session.refresh(benefit)
    return benefit

@router.get("/", response_model=list[Benefit])
def get_all_benefits(session: SessionDep):
    return session.exec(select(Benefit)).all()

@router.get("/{benefit_id}", response_model=Benefit)
def get_benefit(benefit_id: int, session: SessionDep):
    benefit = session.get(Benefit, benefit_id)
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found")
    return benefit

@router.put("/{benefit_id}", response_model=Benefit)
def update_benefit(benefit_id: int, benefit_data: BenefitBase, session: SessionDep):
    benefit = session.get(Benefit, benefit_id)
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found") 
    benefit.name = benefit_data.name
    benefit.description = benefit_data.description
    session.add(benefit)
    session.commit()
    session.refresh(benefit)
    return benefit

