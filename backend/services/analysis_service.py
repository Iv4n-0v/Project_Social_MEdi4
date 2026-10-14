from sqlmodel import select, Session
from backend.models import Analysis, AnalysisBase, User


def create_analysis(session: Session, new_analysis: AnalysisBase, user_id: int):
    user_db = session.get(User, user_id)
    if not user_db:
        return None

    analysis = Analysis.model_validate(new_analysis, update={"user_id": user_id})
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


def get_all_analyses(session: Session):
    return session.exec(select(Analysis)).all()


def get_all_users(session: Session):
    return session.exec(select(User)).all()


def create_analysis_web(session: Session, user_id: int, sector: str, reach: int, time_in_social_media: float):
    analysis = Analysis(
        user_id=user_id,
        sector=sector,
        reach=reach,
        time_in_social_media=time_in_social_media
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


def get_analysis_by_id(session: Session, analysis_id: int):
    return session.get(Analysis, analysis_id)