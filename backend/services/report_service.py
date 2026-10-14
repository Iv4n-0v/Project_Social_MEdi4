"""Datos del reporte PDF: compone 3 fuentes (metodologias, beneficios, usuarios)."""
from sqlmodel import Session, select

from backend.clients.benefit_client import BenefitClient
from backend.clients.methodology_client import MethodologyClient
from backend.models import User, UserMethodologyLink


def get_methodologies_full_report(
    session: Session, methodology_client: MethodologyClient, benefit_client: BenefitClient
):
    methodologies = methodology_client.find_all()
    if not methodologies:
        return None

    all_ids = sorted({i for m in methodologies for i in m.benefit_ids})
    benefits = {b.id: b for b in benefit_client.find_all(all_ids)}
    users = {u.id: u for u in session.exec(select(User)).all()}
    links = session.exec(select(UserMethodologyLink)).all()

    report = []
    for met in methodologies:
        report.append({
            "methodology": met,
            "benefits": [benefits[i] for i in met.benefit_ids if i in benefits],
            "users": [users[l.user_id] for l in links
                      if l.methodology_id == met.id and l.user_id in users],
        })
    return report
