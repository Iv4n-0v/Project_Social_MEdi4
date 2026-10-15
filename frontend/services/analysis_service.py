"""Servicio de analisis del monolito (parte del Controlador).

Los analisis viven en el microservicio de analisis y los usuarios en el de
usuarios. Aqui solo se compone: validar el usuario y unir nombres para la vista.
"""
from frontend.clients.analysis_client import AnalysisClient, AnalysisDTO
from frontend.clients.base import or_none
from frontend.clients.users_client import UsersClient, UserDTO


def get_all_users(users_client: UsersClient) -> list[UserDTO]:
    return users_client.find_all(True)  # para el desplegable del formulario


def create_analysis(client: AnalysisClient, users_client: UsersClient, user_id: int, data):
    """Devuelve None si el usuario no existe (el micro de analisis no lo valida)."""
    if or_none(users_client.get, user_id) is None:
        return None
    return client.create(user_id, data.sector, data.reach, data.time_in_social_media)


def create_analysis_web(
    client: AnalysisClient, users_client: UsersClient, user_id: int,
    sector: str, reach: int, time_in_social_media: float,
):
    if or_none(users_client.get, user_id) is None:
        return None
    return client.create(user_id, sector, reach, time_in_social_media)


def get_all_analyses(client: AnalysisClient) -> list[AnalysisDTO]:
    return client.find_all()


def get_all_analyses_with_user_name(client: AnalysisClient, users_client: UsersClient) -> list[dict]:
    """Composicion en el monolito: analisis (micro) + nombre del usuario (otro micro)."""
    names = {u.id: u.name for u in users_client.find_all()}
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
