"""Logica de negocio del servicio de analisis.

Responsabilidades (principio S): reglas de negocio y auditoria, coordinando
el repositorio. No conoce HTTP (no lanza HTTPException) ni SQL.
"""
from typing import Optional

from models import Analysis
from repository import AnalysisRepository
from schemas import AnalysisCreate, AnalysisResponse, AnalysisUpdate


class AnalysisNotFound(Exception):
    pass


class AnalysisService:
    def __init__(self, repo: AnalysisRepository) -> None:
        self.repo = repo

    # ---- helpers ----
    def _get_or_raise(self, analysis_id: int) -> Analysis:
        analysis = self.repo.get(analysis_id)
        if analysis is None:
            raise AnalysisNotFound("Analysis not found")
        return analysis

    @staticmethod
    def _to_response(a: Analysis) -> AnalysisResponse:
        return AnalysisResponse(
            id=a.id,
            sector=a.sector,
            reach=a.reach,
            time_in_social_media=a.time_in_social_media,
            user_id=a.user_id,
            date=a.date,
            is_active=a.is_active,
        )

    def _set_active(self, analysis_id: int, active: bool, action: str) -> AnalysisResponse:
        analysis = self._get_or_raise(analysis_id)
        analysis.is_active = active
        self.repo.add_audit(analysis.id, action)
        self.repo.commit()
        self.repo.refresh(analysis)
        return self._to_response(analysis)

    # ---- casos de uso ----
    def list_analyses(
        self, is_active: Optional[bool] = None, user_id: Optional[int] = None
    ) -> list[AnalysisResponse]:
        return [self._to_response(a) for a in self.repo.find_all(is_active, user_id)]

    def get_analysis(self, analysis_id: int) -> AnalysisResponse:
        return self._to_response(self._get_or_raise(analysis_id))

    def create_analysis(self, data: AnalysisCreate) -> AnalysisResponse:
        analysis = self.repo.add(
            Analysis(
                sector=data.sector,
                reach=data.reach,
                time_in_social_media=data.time_in_social_media,
                user_id=data.user_id,
            )
        )
        self.repo.add_audit(analysis.id, "CREATE")
        self.repo.commit()
        self.repo.refresh(analysis)
        return self._to_response(analysis)

    def update_analysis(self, analysis_id: int, data: AnalysisUpdate) -> AnalysisResponse:
        analysis = self._get_or_raise(analysis_id)
        if data.sector is not None:
            analysis.sector = data.sector
        if data.reach is not None:
            analysis.reach = data.reach
        if data.time_in_social_media is not None:
            analysis.time_in_social_media = data.time_in_social_media
        self.repo.add_audit(analysis.id, "UPDATE")
        self.repo.commit()
        self.repo.refresh(analysis)
        return self._to_response(analysis)

    def delete_analysis(self, analysis_id: int) -> AnalysisResponse:
        """Borrado logico: el registro no se destruye, queda is_active=False."""
        return self._set_active(analysis_id, False, "DELETE")

    def restore_analysis(self, analysis_id: int) -> AnalysisResponse:
        return self._set_active(analysis_id, True, "RESTORE")

    def audits(self, analysis_id: int):
        self._get_or_raise(analysis_id)
        return self.repo.audits(analysis_id)
