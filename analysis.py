from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import Analysis, AnalysisBase, User

router = APIRouter(tags=["analyses"])


@router.post("/", response_model=Analysis)
def create_analysis(new_analysis: AnalysisBase, user_id: int, session: SessionDep):
    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    analysis = Analysis.model_validate(new_analysis, update={"user_id": user_id})
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


@router.get("/all", response_model=list[Analysis])
def get_all_analyses(session: SessionDep):
    return session.query(Analysis).all()


@router.get("/{analysis_id}", response_model=Analysis)
def get_one_analysis(analysis_id: int, session: SessionDep):
    analysis_db = session.get(Analysis, analysis_id)
    if not analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_db