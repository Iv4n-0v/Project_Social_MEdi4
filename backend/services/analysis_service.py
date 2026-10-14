"""Servicio de analisis del monolito (parte del Controlador).

Los analisis YA NO se guardan aqui: viven en el microservicio de analisis y se
piden por el gateway con AnalysisClient. Lo unico local, por ahora, son los
usuarios (hasta migrar el modulo de usuarios).
"""
from sqlmodel import Session, select

from backend.clients.analysis_client import AnalysisClient, AnalysisDTO
from backend.models import User


def get_all_users(session: Session):
    # TODO: cuando usuarios migre, reemplazar por UsersClient.list()
    return session.exec(select(User)).all()


def create_analysis(client: AnalysisClient, session: Session, user_id: int, data):
    """Devuelve None si el usuario no existe (el micro no lo valida)."""
    if session.get(User, user_id) is None:  # TODO: UsersClient.get(user_id)
        return None
    return client.create(user_id, data.sector, data.reach, data.time_in_social_media)


def create_analysis_web(
    client: AnalysisClient, session: Session, user_id: int,
    sector: str, reach: int, time_in_social_media: float,
):
    if session.get(User, user_id) is None:
        return None
    return client.create(user_id, sector, reach, time_in_social_media)


def get_all_analyses(client: AnalysisClient) -> list[AnalysisDTO]:
    return client.find_all()


def get_all_analyses_with_user_name(client: AnalysisClient, session: Session) -> list[dict]:
    """Composicion en el monolito: analisis (micro) + nombre del usuario (local)."""
    names = {u.id: u.name for u in get_all_users(session)}
    return [
        {**a.model_dump(), "user_name": names.get(a.user_id, f"Usuario {a.user_id}")}
        for a in client.find_all()
    ]


def get_analyses_by_user(client: AnalysisClient) -> dict[int, list[AnalysisDTO]]:
    """Agrupa por usuario, para las paginas de usuarios."""
    grouped: dict[int, list[AnalysisDTO]] = {}
    for a in client.find_all():
        grouped.setdefault(a.user_id, []).append(a)
    return grouped


def get_analysis_by_id(client: AnalysisClient, analysis_id: int) -> AnalysisDTO:
    return client.get(analysis_id)
