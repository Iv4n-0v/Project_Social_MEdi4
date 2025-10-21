from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import Benefit, BenefitBase, Methodology, MethodologyBenefitLink

router = APIRouter()


@router.post("/", response_model=Benefit)
def create_benefit(new_benefit: BenefitBase, session: SessionDep):
    benefit = Benefit.model_validate(new_benefit)
    session.add(benefit)
    session.commit()
    session.refresh(benefit)
    return benefit


@router.get("/", response_model=list[Benefit])
def get_all_benefits(session: SessionDep):
    return session.query(Benefit).all()


@router.post("/link", summary="Asociar metodología y beneficio")
def link_methodology_benefit(methodology_id: int, benefit_id: int, session: SessionDep):
    methodology = session.get(Methodology, methodology_id)
    benefit = session.get(Benefit, benefit_id)

    if not methodology or not benefit:
        raise HTTPException(status_code=404, detail="Methodology or Benefit not found")

    link = MethodologyBenefitLink(methodology_id=methodology_id, benefit_id=benefit_id)
    session.add(link)
    session.commit()
    return {"message": "Link created successfully"}