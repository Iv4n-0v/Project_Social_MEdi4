"""Servicio de beneficios del monolito (parte del Controlador).

Los beneficios y sus relaciones con metodologias viven en los microservicios.
Aqui solo se COMPONE: pedir a un micro y a otro, y unir el resultado para la vista.
"""
from frontend.clients.base import ServiceError
from frontend.clients.benefit_client import BenefitClient
from frontend.clients.methodology_client import MethodologyClient


def create_benefit(client: BenefitClient, name: str, description: str | None):
    return client.create(name, description)


def get_all_benefits(client: BenefitClient):
    return client.find_all()


def get_benefits_with_methodologies(
    benefit_client: BenefitClient, methodology_client: MethodologyClient
) -> list[dict]:
    """Para /benefits: cada beneficio con los nombres de sus metodologias."""
    methodologies = methodology_client.find_all()
    result = []
    for b in benefit_client.find_all():
        result.append({
            **b.model_dump(),
            "methodologies": [m for m in methodologies if b.id in m.benefit_ids],
        })
    return result


def get_methodologies_with_benefits(
    methodology_client: MethodologyClient, benefit_client: BenefitClient
) -> list[dict]:
    """Composicion: metodologias (micro) + datos de sus beneficios (otro micro).

    Una sola llamada a beneficios con ?ids=1,2,3 (no una por metodologia).
    """
    methodologies = methodology_client.find_all()
    all_ids = sorted({i for m in methodologies for i in m.benefit_ids})
    benefits = {b.id: b for b in benefit_client.find_all(all_ids)}
    return [
        {
            **m.model_dump(),
            "benefits": [benefits[i] for i in m.benefit_ids if i in benefits],
        }
        for m in methodologies
    ]


def link_methodology_benefit(
    methodology_client: MethodologyClient, benefit_client: BenefitClient,
    methodology_id: int, benefit_id: int,
):
    """Agrega un beneficio a una metodologia. None si alguno no existe."""
    try:
        methodology = methodology_client.get(methodology_id)
        benefit_client.get(benefit_id)
    except ServiceError as e:
        if e.status_code == 404:
            return None
        raise
    ids = sorted(set(methodology.benefit_ids) | {benefit_id})
    return methodology_client.update(methodology_id, benefit_ids=ids)
