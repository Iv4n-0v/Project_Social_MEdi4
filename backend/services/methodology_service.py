"""Servicio de metodologias del monolito (parte del Controlador).

Las metodologias viven en el microservicio de metodologias. Lo unico local es
la relacion usuario <-> metodologia (solo IDs), hasta migrar el modulo de usuarios.
"""
from sqlmodel import Session, select

from backend.clients.base import ServiceError
from backend.clients.benefit_client import BenefitClient
from backend.clients.methodology_client import MethodologyClient
from backend.models import MethodologyBase, User, UserMethodologyLink


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
    session: Session, client: MethodologyClient, user_id: int, methodology_id: int
):
    user = session.get(User, user_id)
    methodology = get_methodology_by_id(client, methodology_id)
    if not user or not methodology:
        return None
    exists = session.get(UserMethodologyLink, (user_id, methodology_id))
    if not exists:
        session.add(UserMethodologyLink(user_id=user_id, methodology_id=methodology_id))
        session.commit()
    return user, methodology


def get_methodology_with_users(session: Session, client: MethodologyClient, name: str):
    methodology = next((m for m in client.find_all() if m.name == name), None)
    if methodology is None:
        return None
    links = session.exec(
        select(UserMethodologyLink).where(UserMethodologyLink.methodology_id == methodology.id)
    ).all()
    users = [session.get(User, link.user_id) for link in links]
    return {
        "methodology": {"id": methodology.id, "name": methodology.name,
                        "description": methodology.description},
        "users": [{"id": u.id, "name": u.name} for u in users if u],
    }
