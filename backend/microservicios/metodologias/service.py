"""Logica de negocio del servicio de metodologias.

Responsabilidades (principio S): reglas de negocio y auditoria, coordinando
el repositorio. No conoce HTTP (no lanza HTTPException) ni SQL.
"""
from typing import Optional

from models import Methodology
from repository import MethodologyRepository
from schemas import MethodologyCreate, MethodologyResponse, MethodologyUpdate


class MethodologyNotFound(Exception):
    pass


class MethodologyService:
    def __init__(self, repo: MethodologyRepository) -> None:
        self.repo = repo

    # ---- helpers ----
    def _get_or_raise(self, methodology_id: int) -> Methodology:
        methodology = self.repo.get(methodology_id)
        if methodology is None:
            raise MethodologyNotFound("Methodology not found")
        return methodology

    def _to_response(self, methodology: Methodology) -> MethodologyResponse:
        return MethodologyResponse(
            id=methodology.id,
            name=methodology.name,
            description=methodology.description,
            is_active=methodology.is_active,
            benefit_ids=self.repo.benefit_ids(methodology.id),
        )

    def _set_active(
        self, methodology_id: int, active: bool, action: str
    ) -> MethodologyResponse:
        methodology = self._get_or_raise(methodology_id)
        methodology.is_active = active
        self.repo.add_audit(methodology.id, action)
        self.repo.commit()
        self.repo.refresh(methodology)
        return self._to_response(methodology)

    # ---- casos de uso ----
    def list_methodologies(
        self, is_active: Optional[bool] = None
    ) -> list[MethodologyResponse]:
        return [self._to_response(m) for m in self.repo.find_all(is_active)]

    def get_methodology(self, methodology_id: int) -> MethodologyResponse:
        return self._to_response(self._get_or_raise(methodology_id))

    def create_methodology(self, data: MethodologyCreate) -> MethodologyResponse:
        methodology = self.repo.add(
            Methodology(name=data.name, description=data.description)
        )
        self.repo.set_benefits(methodology.id, data.benefit_ids)
        self.repo.add_audit(methodology.id, "CREATE")
        self.repo.commit()
        self.repo.refresh(methodology)
        return self._to_response(methodology)

    def update_methodology(
        self, methodology_id: int, data: MethodologyUpdate
    ) -> MethodologyResponse:
        methodology = self._get_or_raise(methodology_id)
        if data.name is not None:
            methodology.name = data.name
        if data.description is not None:
            methodology.description = data.description
        if data.is_active is not None:
            methodology.is_active = data.is_active
        if data.benefit_ids is not None:
            self.repo.set_benefits(methodology.id, data.benefit_ids)
        self.repo.add_audit(methodology.id, "UPDATE")
        self.repo.commit()
        self.repo.refresh(methodology)
        return self._to_response(methodology)

    def delete_methodology(self, methodology_id: int) -> MethodologyResponse:
        """Borrado logico: el registro no se destruye, queda is_active=False."""
        return self._set_active(methodology_id, False, "DELETE")

    def restore_methodology(self, methodology_id: int) -> MethodologyResponse:
        return self._set_active(methodology_id, True, "RESTORE")

    def audits(self, methodology_id: int):
        self._get_or_raise(methodology_id)
        return self.repo.audits(methodology_id)
