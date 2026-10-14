"""Acceso a datos del servicio de beneficios (patron Repository).

Es la unica capa que conoce SQL/SQLModel. El servicio pide "dame los
beneficios activos" y no sabe como se consulta.
"""
from typing import Optional

from sqlmodel import Session, select

from models import Benefit, BenefitAudit


class BenefitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- beneficios ----
    def find_all(
        self, is_active: Optional[bool] = None, ids: Optional[list[int]] = None
    ) -> list[Benefit]:
        stmt = select(Benefit)
        if is_active is not None:
            stmt = stmt.where(Benefit.is_active == is_active)
        if ids is not None:
            stmt = stmt.where(Benefit.id.in_(ids))
        return list(self.session.exec(stmt.order_by(Benefit.id)).all())

    def get(self, benefit_id: int) -> Optional[Benefit]:
        return self.session.get(Benefit, benefit_id)

    def add(self, benefit: Benefit) -> Benefit:
        self.session.add(benefit)
        self.session.flush()  # asigna benefit.id sin cerrar la transaccion
        return benefit

    # ---- auditoria ----
    def add_audit(self, benefit_id: int, action: str) -> None:
        self.session.add(BenefitAudit(benefit_id=benefit_id, action=action))

    def audits(self, benefit_id: int) -> list[BenefitAudit]:
        return list(
            self.session.exec(
                select(BenefitAudit)
                .where(BenefitAudit.benefit_id == benefit_id)
                .order_by(BenefitAudit.id)
            ).all()
        )

    # ---- transaccion ----
    def commit(self) -> None:
        self.session.commit()

    def refresh(self, benefit: Benefit) -> None:
        self.session.refresh(benefit)
