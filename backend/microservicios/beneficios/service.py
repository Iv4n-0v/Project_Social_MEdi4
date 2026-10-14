"""Logica de negocio del servicio de beneficios.

Responsabilidades (principio S): reglas de negocio y auditoria, coordinando
el repositorio. No conoce HTTP (no lanza HTTPException) ni SQL.
"""
from typing import Optional

from models import Benefit
from repository import BenefitRepository
from schemas import BenefitCreate, BenefitResponse, BenefitUpdate


class BenefitNotFound(Exception):
    pass


class BenefitService:
    def __init__(self, repo: BenefitRepository) -> None:
        self.repo = repo

    # ---- helpers ----
    def _get_or_raise(self, benefit_id: int) -> Benefit:
        benefit = self.repo.get(benefit_id)
        if benefit is None:
            raise BenefitNotFound("Benefit not found")
        return benefit

    @staticmethod
    def _to_response(benefit: Benefit) -> BenefitResponse:
        return BenefitResponse(
            id=benefit.id,
            name=benefit.name,
            description=benefit.description,
            is_active=benefit.is_active,
        )

    def _set_active(self, benefit_id: int, active: bool, action: str) -> BenefitResponse:
        benefit = self._get_or_raise(benefit_id)
        benefit.is_active = active
        self.repo.add_audit(benefit.id, action)
        self.repo.commit()
        self.repo.refresh(benefit)
        return self._to_response(benefit)

    # ---- casos de uso ----
    def list_benefits(
        self, is_active: Optional[bool] = None, ids: Optional[list[int]] = None
    ) -> list[BenefitResponse]:
        return [self._to_response(b) for b in self.repo.find_all(is_active, ids)]

    def get_benefit(self, benefit_id: int) -> BenefitResponse:
        return self._to_response(self._get_or_raise(benefit_id))

    def create_benefit(self, data: BenefitCreate) -> BenefitResponse:
        benefit = self.repo.add(
            Benefit(name=data.name, description=data.description)
        )
        self.repo.add_audit(benefit.id, "CREATE")
        self.repo.commit()
        self.repo.refresh(benefit)
        return self._to_response(benefit)

    def update_benefit(self, benefit_id: int, data: BenefitUpdate) -> BenefitResponse:
        benefit = self._get_or_raise(benefit_id)
        if data.name is not None:
            benefit.name = data.name
        if data.description is not None:
            benefit.description = data.description
        if data.is_active is not None:
            benefit.is_active = data.is_active
        self.repo.add_audit(benefit.id, "UPDATE")
        self.repo.commit()
        self.repo.refresh(benefit)
        return self._to_response(benefit)

    def delete_benefit(self, benefit_id: int) -> BenefitResponse:
        """Borrado logico: el registro no se destruye, queda is_active=False."""
        return self._set_active(benefit_id, False, "DELETE")

    def restore_benefit(self, benefit_id: int) -> BenefitResponse:
        return self._set_active(benefit_id, True, "RESTORE")

    def audits(self, benefit_id: int):
        self._get_or_raise(benefit_id)
        return self.repo.audits(benefit_id)
