from sqlmodel import select, Session
from backend.models import Benefit, Methodology, MethodologyBenefitLink


def link_methodology_benefit(session: Session, methodology_id: int, benefit_id: int):
    methodology = session.get(Methodology, methodology_id)
    benefit = session.get(Benefit, benefit_id)
    if not methodology or not benefit:
        return None

    link = MethodologyBenefitLink(methodology_id=methodology_id, benefit_id=benefit_id)
    session.add(link)
    session.commit()
    return link


def get_methodologies_with_benefits(session: Session):
    result = []
    metodologias = session.exec(select(Methodology)).all()

    for met in metodologias:
        links = session.exec(
            select(MethodologyBenefitLink).where(MethodologyBenefitLink.methodology_id == met.id)
        ).all()

        beneficios = []
        for link in links:
            benefit = session.get(Benefit, link.benefit_id)
            if benefit:
                beneficios.append({"id": benefit.id, "name": benefit.name, "description": benefit.description})

        result.append({
            "methodology": {"id": met.id, "name": met.name, "description": met.description},
            "benefits": beneficios
        })

    return result


def create_benefit_local(session: Session, name: str, description: str | None):
    new_benefit = Benefit(name=name, description=description)
    session.add(new_benefit)
    session.commit()
    session.refresh(new_benefit)
    return new_benefit


def get_all_benefits_local(session: Session):
    return session.exec(select(Benefit)).all()