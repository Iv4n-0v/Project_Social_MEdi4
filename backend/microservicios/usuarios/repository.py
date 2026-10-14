"""Acceso a datos del servicio de usuarios (patron Repository).

Es la unica capa que conoce SQL/SQLModel. El servicio le pide "dame los
usuarios activos" y no sabe como se consulta. Si cambia la BD o la consulta,
solo se toca este archivo.
"""
from typing import Optional

from sqlmodel import Session, select

from models import User, UserAudit, UserMethodologyLink


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- usuarios ----
    def find_all(self, is_active: Optional[bool] = None) -> list[User]:
        stmt = select(User)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        return list(self.session.exec(stmt.order_by(User.id)).all())

    def get(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()  # asigna user.id sin cerrar la transaccion
        return user

    # ---- metodologias del usuario (solo IDs, viven en otro servicio) ----
    def methodology_ids(self, user_id: int) -> list[int]:
        rows = self.session.exec(
            select(UserMethodologyLink.methodology_id)
            .where(UserMethodologyLink.user_id == user_id)
            .order_by(UserMethodologyLink.methodology_id)
        ).all()
        return list(rows)

    def set_methodologies(self, user_id: int, ids: list[int]) -> None:
        old = self.session.exec(
            select(UserMethodologyLink).where(UserMethodologyLink.user_id == user_id)
        ).all()
        for link in old:
            self.session.delete(link)
        self.session.flush()
        for mid in sorted(set(ids)):
            self.session.add(UserMethodologyLink(user_id=user_id, methodology_id=mid))

    # ---- auditoria ----
    def add_audit(self, user_id: int, action: str) -> None:
        self.session.add(UserAudit(user_id=user_id, action=action))

    def audits(self, user_id: int) -> list[UserAudit]:
        return list(
            self.session.exec(
                select(UserAudit)
                .where(UserAudit.user_id == user_id)
                .order_by(UserAudit.id)
            ).all()
        )

    # ---- transaccion ----
    def commit(self) -> None:
        self.session.commit()

    def refresh(self, user: User) -> None:
        self.session.refresh(user)
