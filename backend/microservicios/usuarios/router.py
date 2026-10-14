"""Capa HTTP del servicio de usuarios (el "controlador").

Solo traduce HTTP <-> casos de uso del servicio. Sin reglas de negocio ni SQL.
Los errores de dominio (UserNotFound, InvalidImage, StorageUnavailable) se
convierten en respuestas HTTP en main.py.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from database import SessionDep
from repository import UserRepository
from schemas import AuditResponse, UserResponse, UserUpdate
from service import UserService
from storage import ImageStorage, get_storage

router = APIRouter(tags=["users"])


def get_service(
    session: SessionDep, storage: Annotated[ImageStorage, Depends(get_storage)]
) -> UserService:
    return UserService(UserRepository(session), storage)


ServiceDep = Annotated[UserService, Depends(get_service)]


async def _read(img: UploadFile) -> tuple[bytes, str, Optional[str]]:
    return await img.read(), img.filename or "upload", img.content_type


@router.get("/", response_model=list[UserResponse])
def get_all_users(service: ServiceDep, is_active: Optional[bool] = None):
    """?is_active=true -> activos | ?is_active=false -> eliminados | sin filtro -> todos"""
    return service.list_users(is_active)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    service: ServiceDep,
    name: str = Form(..., min_length=1, max_length=100, pattern=r"\S"),
    is_active: bool = Form(True),
    methodology_ids: list[int] = Form([]),
    img: Optional[UploadFile] = File(None),
):
    image = await _read(img) if img and img.filename else None
    return await service.create_user(name, is_active, methodology_ids, image)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, service: ServiceDep):
    return service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, service: ServiceDep):
    return service.update_user(user_id, data)


@router.put("/{user_id}/image", response_model=UserResponse)
async def update_user_image(
    user_id: int, service: ServiceDep, img: UploadFile = File(...)
):
    content, filename, content_type = await _read(img)
    return await service.update_image(user_id, content, filename, content_type)


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, service: ServiceDep):
    """Borrado logico (is_active=False). Se puede deshacer con /restore."""
    return service.delete_user(user_id)


@router.post("/{user_id}/restore", response_model=UserResponse)
def restore_user(user_id: int, service: ServiceDep):
    return service.restore_user(user_id)


@router.get("/{user_id}/audits", response_model=list[AuditResponse])
def get_user_audits(user_id: int, service: ServiceDep):
    return service.audits(user_id)
