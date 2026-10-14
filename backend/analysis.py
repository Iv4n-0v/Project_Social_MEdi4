from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.clients.analysis_client import AnalysisClient, AnalysisDTO, get_analysis_client
from backend.db import SessionDep
from backend.models import AnalysisBase
from backend.services import analysis_service

router = APIRouter(tags=["analyses"])

ClientDep = Annotated[AnalysisClient, Depends(get_analysis_client)]


@router.post("/", response_model=AnalysisDTO)
def create_analysis_api(
    new_analysis: AnalysisBase, user_id: int, session: SessionDep, client: ClientDep
):
    analysis = analysis_service.create_analysis(client, session, user_id, new_analysis)
    if not analysis:
        raise HTTPException(status_code=404, detail="User not found")
    return analysis


@router.get("/all", response_model=list[AnalysisDTO])
def get_all_analyses(client: ClientDep):
    return analysis_service.get_all_analyses(client)


@router.get("/new", response_class=HTMLResponse)
def new_analysis_form(request: Request, session: SessionDep):
    users = analysis_service.get_all_users(session)
    return request.app.state.templates.TemplateResponse(
        "new_analysis.html",
        {"request": request, "users": users}
    )


@router.get("", response_class=HTMLResponse)
def show_analyses(request: Request, session: SessionDep, client: ClientDep):
    analyses = analysis_service.get_all_analyses_with_user_name(client, session)
    return request.app.state.templates.TemplateResponse(
        "analysis_list.html",
        {"request": request, "analyses": analyses}
    )


@router.post("/create")
def create_analysis_web(
    session: SessionDep,
    client: ClientDep,
    user_id: int = Form(...),
    sector: str = Form(...),
    reach: int = Form(...),
    time_in_social_media: float = Form(...)
):
    created = analysis_service.create_analysis_web(
        client, session, user_id, sector, reach, time_in_social_media
    )
    if created is None:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse("/analysis", status_code=303)


@router.get("/{analysis_id}", response_model=AnalysisDTO)
def get_one_analysis(analysis_id: int, client: ClientDep):
    return analysis_service.get_analysis_by_id(client, analysis_id)
