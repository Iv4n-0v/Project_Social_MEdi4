from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from sqlmodel import select
from backend.db import SessionDep
from backend.models import Analysis, AnalysisBase, User

router = APIRouter(tags=["analyses"])


@router.post("/", response_model=Analysis)
def create_analysis_api(new_analysis: AnalysisBase, user_id: int, session: SessionDep):
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


@router.get("/new", response_class=HTMLResponse)
def new_analysis_form(request: Request, session: SessionDep):

    users = session.exec(select(User)).all()

    return request.app.state.templates.TemplateResponse(
        "new_analysis.html",
        {"request": request, "users": users}
    )

@router.get("", response_class=HTMLResponse)
def show_analyses(request: Request, session: SessionDep):
    analysis = session.exec(select(Analysis)).all()

    return request.app.state.templates.TemplateResponse(
        "analysis_list.html",
        {
            "request": request,
            "analyses": analysis
        }
    )

@router.post("/create")
def create_analysis_web(
    session: SessionDep,
    user_id: int = Form(...),
    sector: str = Form(...),
    reach: int = Form(...),
    time_in_social_media: float = Form(...)
):
    analysis = Analysis(
        user_id=user_id,
        sector=sector,
        reach=reach,
        time_in_social_media=time_in_social_media
    )

    session.add(analysis)
    session.commit()
    session.refresh(analysis) 

    return RedirectResponse("/analysis", status_code=303)


@router.get("/{analysis_id}", response_model=Analysis)
def get_one_analysis(analysis_id: int, session: SessionDep):
    analysis_db = session.get(Analysis, analysis_id)
    if not analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_db