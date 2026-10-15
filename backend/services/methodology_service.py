"""Servicio de metodologias del monolito (parte del Controlador).

Las metodologias viven en el microservicio de metodologias. Lo unico local es
la relacion usuario <-> metodologia (solo IDs), hasta migrar el modulo de usuarios.
"""
from backend.clients.base import ServiceError, or_none
from backend.clients.benefit_client import BenefitClient
from backend.clients.methodology_client import MethodologyClient
from backend.clients.users_client import UsersClient
from backend.models import MethodologyBase


def create_methodology(client: MethodologyClient, new_methodology: MethodologyBase):
    return client.create(new_methodology.name, new_methodology.description)


def get_all_methodologies(client: MethodologyClient):
    return client.find_all()


def get_all_benefits(benefit_client: BenefitClient):
    return benefit_client.find_all()


def get_methodology_by_id(client: MethodologyClient, methodology_id: int):
    try:
        return client.get(methodology_id)
    except ServiceError as e:
        if e.status_code == 404:
            return None
        raise


def create_methodology_web(
    client: MethodologyClient, name: str, description: str | None, benefit_ids: list[int]
):
    return client.create(name, description, benefit_ids)


def update_methodology(
    client: MethodologyClient, methodology_id: int, name: str,
    description: str | None, benefit_ids: list[int],
):
    try:
        return client.update(methodology_id, name, description, benefit_ids)
    except ServiceError as e:
        if e.status_code == 404:
            return None
        raise


def assign_methodology(
    users_client: UsersClient, client: MethodologyClient, user_id: int, methodology_id: int
):
    """Agrega la metodologia a las del usuario. None si alguno no existe."""
    user = or_none(users_client.get, user_id)
    methodology = get_methodology_by_id(client, methodology_id)
    if not user or not methodology:
        return None
    ids = sorted(set(user.methodology_ids) | {methodology_id})
    users_client.update(user_id, methodology_ids=ids)
    return user, methodology


def get_methodology_with_users(users_client: UsersClient, client: MethodologyClient, name: str):
    methodology = next((m for m in client.find_all() if m.name == name), None)
    if methodology is None:
        return None
    users = [u for u in users_client.find_all() if methodology.id in u.methodology_ids]
    return {
        "methodology": {"id": methodology.id, "name": methodology.name,
                        "description": methodology.description},
        "users": [{"id": u.id, "name": u.name} for u in users],
    }
