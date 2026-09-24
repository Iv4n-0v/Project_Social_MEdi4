from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select

from database import SessionDep
from models import Analysis, AnalysisBase, AnalysisUpdate

router = APIRouter(tags=["analyses"])

@router.post("/", response_model=Analysis, status_code=status.HTTP_201_CREATED)
def create_analysis(analysis_data: AnalysisBase,session: SessionDep):
    analysis = Analysis.model_validate(analysis_data)
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


@router.get("/", response_model=list[Analysis])
def get_all_analyses(session: SessionDep):
    return session.exec(select(Analysis)).all()


@router.get("/{analysis_id}", response_model=Analysis)
def get_analysis(analysis_id: int, session: SessionDep):
    analysis = session.get(Analysis, analysis_id)

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Analysis not found")
    return analysis


@router.put("/{analysis_id}", response_model=Analysis)
def update_analysis(analysis_id: int, analysis_data: AnalysisBase, session: SessionDep):
    analysis = session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    analysis.sector = analysis_data.sector
    analysis.reach = analysis_data.reach
    analysis.time_in_social_media = analysis_data.time_in_social_media
    analysis.user_id = analysis_data.user_id
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


@router.patch("/{analysis_id}", response_model=Analysis)
def partially_update_analysis(analysis_id: int, analysis_data: AnalysisUpdate, session: SessionDep):
    analysis = session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    changes = analysis_data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(analysis, field, value)
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, session: SessionDep):
    analysis = session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Analysis not found")
    session.delete(analysis)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)