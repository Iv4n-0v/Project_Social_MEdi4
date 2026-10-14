"""Acceso a datos del servicio de metodologias (patron Repository).

Es la unica capa que conoce SQL/SQLModel. El servicio pide "dame las
metodologias activas" y no sabe como se consulta.

Nota: no se define ningun metodo llamado `list`, porque taparia el tipo `list`
de Python en las anotaciones de la clase. Por eso el metodo es `find_all`.
"""
from typing import Optional

from sqlmodel import Session, select

from models import Methodology, MethodologyAudit, MethodologyBenefit


class MethodologyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- metodologias ----
    def find_all(self, is_active: Optional[bool] = None) -> list[Methodology]:
        stmt = select(Methodology)
        if is_active is not None:
            stmt = stmt.where(Methodology.is_active == is_active)
        return list(self.session.exec(stmt.order_by(Methodology.id)).all())

    def get(self, methodology_id: int) -> Optional[Methodology]:
        return self.session.get(Methodology, methodology_id)

    def add(self, methodology: Methodology) -> Methodology:
        self.session.add(methodology)
        self.session.flush()  # asigna methodology.id sin cerrar la transaccion
        return methodology

    # ---- beneficios de la metodologia (solo IDs, viven en otro servicio) ----
    def benefit_ids(self, methodology_id: int) -> list[int]:
        rows = self.session.exec(
            select(MethodologyBenefit.benefit_id)
            .where(MethodologyBenefit.methodology_id == methodology_id)
            .order_by(MethodologyBenefit.benefit_id)
        ).all()
        return list(rows)

    def set_benefits(self, methodology_id: int, ids: list[int]) -> None:
        old = self.session.exec(
            select(MethodologyBenefit).where(
                MethodologyBenefit.methodology_id == methodology_id
            )
        ).all()
        for link in old:
            self.session.delete(link)
        self.session.flush()
        for benefit_id in sorted(set(ids)):
            self.session.add(
                MethodologyBenefit(methodology_id=methodology_id, benefit_id=benefit_id)
            )

    # ---- auditoria ----
    def add_audit(self, methodology_id: int, action: str) -> None:
        self.session.add(MethodologyAudit(methodology_id=methodology_id, action=action))

    def audits(self, methodology_id: int) -> list[MethodologyAudit]:
        return list(
            self.session.exec(
                select(MethodologyAudit)
                .where(MethodologyAudit.methodology_id == methodology_id)
                .order_by(MethodologyAudit.id)
            ).all()
        )

    # ---- transaccion ----
    def commit(self) -> None:
        self.session.commit()

    def refresh(self, methodology: Methodology) -> None:
        self.session.refresh(methodology)
