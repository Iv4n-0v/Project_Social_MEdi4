"""Datos del reporte PDF: compone 3 servicios (metodologias, beneficios, usuarios)."""
from frontend.clients.benefit_client import BenefitClient
from frontend.clients.methodology_client import MethodologyClient
from frontend.clients.users_client import UsersClient


def get_methodologies_full_report(
    users_client: UsersClient, methodology_client: MethodologyClient,
    benefit_client: BenefitClient,
):
    methodologies = methodology_client.find_all()
    if not methodologies:
        return None

    all_ids = sorted({i for m in methodologies for i in m.benefit_ids})
    benefits = {b.id: b for b in benefit_client.find_all(all_ids)}
    users = users_client.find_all(True)

    return [
        {
            "methodology": met,
            "benefits": [benefits[i] for i in met.benefit_ids if i in benefits],
            "users": [u for u in users if met.id in u.methodology_ids],
        }
        for met in methodologies
    ]
