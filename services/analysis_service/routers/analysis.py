from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from services.analysis_service.database import get_session
from services.analysis_service.models import Analysis
from services.analysis_service.schemas import (
    AnalysisCreate,
    AnalysisResponse
)

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)


@router.post(
    "/",
    response_model=AnalysisResponse
)
def create_analysis(
    data: AnalysisCreate,
    session: Session = Depends(get_session)
):
    analysis = Analysis(
        sector=data.sector,
        reach=data.reach,
        time_in_social_media=data.time_in_social_media,
        user_id=data.user_id
    )

    session.add(analysis)
    session.commit()
    session.refresh(analysis)

    return analysis


@router.get(
    "/",
    response_model=list[AnalysisResponse]
)
def get_all_analyses(
    session: Session = Depends(get_session)
):
    return session.exec(
        select(Analysis)
    ).all()


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse
)
def get_analysis(
    analysis_id: int,
    session: Session = Depends(get_session)
):
    analysis = session.get(
        Analysis,
        analysis_id
    )

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    return analysis