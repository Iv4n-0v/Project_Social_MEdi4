"""Servicio de usuarios del monolito (parte del Controlador).

Los usuarios, sus imagenes (Supabase) y sus metodologias viven en el
microservicio de usuarios. Aqui solo se coordina: validar contra el servicio
de metodologias y llamar al cliente.
"""
from typing import Optional

from fastapi import UploadFile

from backend.clients.base import or_none
from backend.clients.methodology_client import MethodologyClient
from backend.clients.users_client import UserDTO, UsersClient


def get_active_users(client: UsersClient) -> list[UserDTO]:
    return client.find_all(True)


def get_inactive_users(client: UsersClient) -> list[UserDTO]:
    return client.find_all(False)


def get_all_users(client: UsersClient) -> list[UserDTO]:
    return client.find_all()


def get_all_methodologies(client: MethodologyClient):
    return client.find_all()


def get_user_by_id(client: UsersClient, user_id: int) -> Optional[UserDTO]:
    return or_none(client.get, user_id)


def _valid_methodology_ids(
    methodology_client: MethodologyClient, ids: Optional[list[int]]
) -> list[int]:
    """Solo deja los IDs que existen en el servicio de metodologias."""
    if not ids:
        return []
    valid = {m.id for m in methodology_client.find_all()}
    return sorted(set(ids) & valid)


async def create_user(
    client: UsersClient, methodology_client: MethodologyClient,
    name: str, is_active: bool, img: Optional[UploadFile],
    methodology_ids: Optional[list[int]] = None,
) -> UserDTO:
    image = None
    if img and img.filename:  # un campo de archivo vacio llega con filename ""
        image = (img.filename, await img.read(), img.content_type)
    ids = _valid_methodology_ids(methodology_client, methodology_ids)
    return client.create(name, is_active, ids, image)


def update_user(
    client: UsersClient, methodology_client: MethodologyClient,
    user_id: int, name: str, methodology_ids: list[int],
) -> Optional[UserDTO]:
    ids = _valid_methodology_ids(methodology_client, methodology_ids)
    return or_none(client.update, user_id, name=name, methodology_ids=ids)


def soft_delete_user(client: UsersClient, user_id: int) -> Optional[UserDTO]:
    return or_none(client.delete, user_id)


def restore_user(client: UsersClient, user_id: int) -> Optional[UserDTO]:
    return or_none(client.restore, user_id)
