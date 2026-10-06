from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Request, Form
from backend.db import SessionDep
from backend.models import Analysis, AnalysisBase
from backend.services import analysis_service

router = APIRouter(tags=["analyses"])


@router.post("/", response_model=Analysis)
def create_analysis_api(new_analysis: AnalysisBase, user_id: int, session: SessionDep):
    analysis = analysis_service.create_analysis(session, new_analysis, user_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="User not found")
    return analysis


@router.get("/all", response_model=list[Analysis])
def get_all_analyses(session: SessionDep):
    return analysis_service.get_all_analyses(session)


@router.get("/new", response_class=HTMLResponse)
def new_analysis_form(request: Request, session: SessionDep):
    users = analysis_service.get_all_users(session)
    return request.app.state.templates.TemplateResponse(
        "new_analysis.html",
        {"request": request, "users": users}
    )


@router.get("", response_class=HTMLResponse)
def show_analyses(request: Request, session: SessionDep):
    analysis = analysis_service.get_all_analyses(session)
    return request.app.state.templates.TemplateResponse(
        "analysis_list.html",
        {"request": request, "analyses": analysis}
    )


@router.post("/create")
def create_analysis_web(
    session: SessionDep,
    user_id: int = Form(...),
    sector: str = Form(...),
    reach: int = Form(...),
    time_in_social_media: float = Form(...)
):
    analysis_service.create_analysis_web(session, user_id, sector, reach, time_in_social_media)
    return RedirectResponse("/analysis", status_code=303)


@router.get("/{analysis_id}", response_model=Analysis)
def get_one_analysis(analysis_id: int, session: SessionDep):
    analysis_db = analysis_service.get_analysis_by_id(session, analysis_id)
    if not analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_db