from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.clients.analysis_client import AnalysisClient, get_analysis_client
from backend.clients.base import ServiceUnavailable
from backend.clients.methodology_client import MethodologyClient, get_methodology_client
from backend.clients.users_client import UserDTO, UsersClient, get_users_client
from backend.services import analysis_service, user_service

router = APIRouter(tags=["users"])


def _methodology_names_by_user(users: list[UserDTO], client: MethodologyClient) -> dict:
    """{user_id: [nombres]}. Si el servicio de metodologias cae, la pagina igual carga."""
    try:
        names = {m.id: m.name for m in client.find_all()}
    except ServiceUnavailable:
        names = {}
    return {
        u.id: [names.get(mid, f"Metodologia {mid}") for mid in u.methodology_ids]
        for u in users
    }


def _analyses_by_user(client: AnalysisClient) -> dict:
    """Analisis agrupados por usuario. Si el servicio cae, la pagina igual carga."""
    try:
        return analysis_service.get_analyses_by_user(client)
    except ServiceUnavailable:
        return {}


@router.get("", response_class=HTMLResponse)
def get_active_users(
    request: Request,
    users_client: UsersClient = Depends(get_users_client),
    analysis_client: AnalysisClient = Depends(get_analysis_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    users = user_service.get_active_users(users_client)
    return request.app.state.templates.TemplateResponse(
        "user_list.html",
        {"request": request, "users": users,
         "analyses_by_user": _analyses_by_user(analysis_client),
         "methodologies_by_user": _methodology_names_by_user(users, methodology_client)}
    )


@router.get("/new", response_class=HTMLResponse)
def show_create(
    request: Request,
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    methodologies = user_service.get_all_methodologies(methodology_client)
    return request.app.state.templates.TemplateResponse(
        "new_user.html",
        {"request": request, "methodologies": methodologies}
    )


@router.post("/new")
async def create_user_web(
    name: str = Form(...),
    methodology_ids: list[int] = Form([]),
    is_active: str = Form("true"),
    img: Optional[UploadFile] = File(None),
    users_client: UsersClient = Depends(get_users_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    await user_service.create_user(
        users_client, methodology_client, name, is_active.lower() == "true", img, methodology_ids
    )
    return RedirectResponse(url="/users", status_code=303)


@router.get("/deleted", response_class=HTMLResponse)
def list_inactive_users(
    request: Request,
    users_client: UsersClient = Depends(get_users_client),
    analysis_client: AnalysisClient = Depends(get_analysis_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    users = user_service.get_inactive_users(users_client)
    return request.app.state.templates.TemplateResponse(
        "user_elist.html",
        {"request": request, "users": users,
         "analyses_by_user": _analyses_by_user(analysis_client),
         "methodologies_by_user": _methodology_names_by_user(users, methodology_client)}
    )


@router.get("/api/active", response_model=list[UserDTO])
def get_active_users_api(users_client: UsersClient = Depends(get_users_client)):
    return user_service.get_active_users(users_client)


@router.get("/api/all", response_model=list[UserDTO])
def get_all_users_api(users_client: UsersClient = Depends(get_users_client)):
    return user_service.get_all_users(users_client)


@router.post("/", response_model=UserDTO)
async def create_user_api(
    name: str = Form(...),
    is_active: bool = Form(True),
    img: Optional[UploadFile] = File(None),
    users_client: UsersClient = Depends(get_users_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    return await user_service.create_user(
        users_client, methodology_client, name, is_active, img
    )


@router.post("/api/update/{user_id}")
def update_user(
    user_id: int,
    name: str = Form(...),
    methodology_ids: list[int] = Form([]),
    users_client: UsersClient = Depends(get_users_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    user = user_service.update_user(users_client, methodology_client, user_id, name, methodology_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "ok"}


@router.post("/{user_id}/delete")
def delete_user(user_id: int, users_client: UsersClient = Depends(get_users_client)):
    user = user_service.soft_delete_user(users_client, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users", status_code=303)


@router.post("/{user_id}/restore")
def restore_user(user_id: int, users_client: UsersClient = Depends(get_users_client)):
    user = user_service.restore_user(users_client, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users/deleted", status_code=303)


@router.get("/edit/{user_id}", response_class=HTMLResponse)
def edit_user_page(
    request: Request, user_id: int,
    users_client: UsersClient = Depends(get_users_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    user = user_service.get_user_by_id(users_client, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return request.app.state.templates.TemplateResponse(
        "user_edit.html",
        {"request": request, "user": user,
         "methodologies": user_service.get_all_methodologies(methodology_client),
         "selected_ids": user.methodology_ids}
    )


@router.post("/{user_id}/update")
def update_user_web(
    user_id: int,
    name: str = Form(...),
    methodology_ids: list[int] = Form([]),
    users_client: UsersClient = Depends(get_users_client),
    methodology_client: MethodologyClient = Depends(get_methodology_client),
):
    user = user_service.update_user(users_client, methodology_client, user_id, name, methodology_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/users", status_code=303)
