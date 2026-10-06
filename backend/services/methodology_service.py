from sqlmodel import select, Session
from backend.models import Methodology, MethodologyBase, User, Benefit


def create_methodology(session: Session, new_methodology: MethodologyBase) -> Methodology:
    methodology = Methodology.model_validate(new_methodology)
    session.add(methodology)
    session.commit()
    session.refresh(methodology)
    return methodology


def assign_methodology(session: Session, user_id: int, methodology_id: int):
    user = session.get(User, user_id)
    methodology = session.get(Methodology, methodology_id)
    if not user or not methodology:
        return None
    user.methodology_id = methodology_id
    session.add(user)
    session.commit()
    return user, methodology


def get_all_methodologies(session: Session):
    return session.exec(select(Methodology)).all()


def get_methodology_with_users(session: Session, name: str):
    methodology = session.exec(select(Methodology).where(Methodology.name == name)).first()
    if not methodology:
        return None
    users = session.exec(select(User).where(User.methodology_id == methodology.id)).all()
    return {
        "methodology": {"id": methodology.id, "name": methodology.name, "description": methodology.description},
        "users": [{"id": u.id, "name": u.name, "type": u.type} for u in users]
    }


def get_all_benefits(session: Session):
    return session.exec(select(Benefit)).all()


def create_methodology_web(session: Session, name: str, description: str | None, benefit_ids: list[int]):
    new_methodology = Methodology(name=name, description=description)
    session.add(new_methodology)
    session.commit()
    session.refresh(new_methodology)

    for b_id in benefit_ids:
        benefit = session.get(Benefit, b_id)
        if benefit:
            new_methodology.benefits.append(benefit)

    session.commit()
    return new_methodology


def get_methodology_by_id(session: Session, methodology_id: int):
    return session.get(Methodology, methodology_id)


def update_methodology(session: Session, methodology_id: int, name: str, description: str | None, benefit_ids: list[int]):
    methodology = session.get(Methodology, methodology_id)
    if not methodology:
        return None

    methodology.name = name
    methodology.description = description
    methodology.benefits.clear()

    for b_id in benefit_ids:
        benefit = session.get(Benefit, b_id)
        if benefit:
            methodology.benefits.append(benefit)

    session.commit()
    return methodology