"""Acceso a datos del servicio de analisis (patron Repository).

Es la unica capa que conoce SQL/SQLModel. El servicio pide "dame los
analisis activos de este usuario" y no sabe como se consulta.
"""
from typing import Optional

from sqlmodel import Session, select

from models import Analysis, AnalysisAudit


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- analisis ----
    def find_all(
        self, is_active: Optional[bool] = None, user_id: Optional[int] = None
    ) -> list[Analysis]:
        stmt = select(Analysis)
        if is_active is not None:
            stmt = stmt.where(Analysis.is_active == is_active)
        if user_id is not None:
            stmt = stmt.where(Analysis.user_id == user_id)
        return list(self.session.exec(stmt.order_by(Analysis.id)).all())

    def get(self, analysis_id: int) -> Optional[Analysis]:
        return self.session.get(Analysis, analysis_id)

    def add(self, analysis: Analysis) -> Analysis:
        self.session.add(analysis)
        self.session.flush()  # asigna analysis.id sin cerrar la transaccion
        return analysis

    # ---- auditoria ----
    def add_audit(self, analysis_id: int, action: str) -> None:
        self.session.add(AnalysisAudit(analysis_id=analysis_id, action=action))

    def audits(self, analysis_id: int) -> list[AnalysisAudit]:
        return list(
            self.session.exec(
                select(AnalysisAudit)
                .where(AnalysisAudit.analysis_id == analysis_id)
                .order_by(AnalysisAudit.id)
            ).all()
        )

    # ---- transaccion ----
    def commit(self) -> None:
        self.session.commit()

    def refresh(self, analysis: Analysis) -> None:
        self.session.refresh(analysis)
