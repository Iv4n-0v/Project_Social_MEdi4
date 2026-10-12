from sqlmodel import select, Session
from backend.models import Methodology, MethodologyBenefitLink, Benefit, User


def get_methodologies_full_report(session: Session):
    metodologias = session.exec(select(Methodology)).all()
    if not metodologias:
        return None

    report = []
    for met in metodologias:
        links = session.exec(
            select(MethodologyBenefitLink).where(MethodologyBenefitLink.methodology_id == met.id)
        ).all()
        benefits = [session.get(Benefit, link.benefit_id) for link in links]
        benefits = [b for b in benefits if b]

        users = session.exec(select(User).where(User.methodology_id == met.id)).all()

        report.append({
            "methodology": met,
            "benefits": benefits,
            "users": users,
        })

    return report