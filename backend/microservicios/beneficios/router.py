"""Capa HTTP del servicio de beneficios (parte del "controlador").

Solo traduce HTTP <-> casos de uso del servicio. Sin reglas de negocio ni SQL.
Los errores de dominio (BenefitNotFound) se convierten en HTTP en main.py.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from database import SessionDep
from repository import BenefitRepository
from schemas import AuditResponse, BenefitCreate, BenefitResponse, BenefitUpdate
from service import BenefitService

router = APIRouter(tags=["benefits"])


def get_service(session: SessionDep) -> BenefitService:
    return BenefitService(BenefitRepository(session))


ServiceDep = Annotated[BenefitService, Depends(get_service)]


def _parse_ids(ids: Optional[str]) -> Optional[list[int]]:
    """'1,2,3' -> [1, 2, 3]. None si no se envia el parametro."""
    if ids is None:
        return None
    try:
        return [int(part) for part in ids.split(",") if part.strip()]
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="ids debe ser una lista de enteros separados por coma, ej. 1,2,3",
        )


@router.get("/", response_model=list[BenefitResponse])
def get_all_benefits(
    service: ServiceDep,
    is_active: Optional[bool] = None,
    ids: Optional[str] = Query(
        None, description="Filtrar por IDs separados por coma, ej. 1,2,3"
    ),
):
    """?is_active=true -> activos | ?is_active=false -> eliminados | sin filtro -> todos"""
    return service.list_benefits(is_active, _parse_ids(ids))


@router.post("/", response_model=BenefitResponse, status_code=201)
def create_benefit(data: BenefitCreate, service: ServiceDep):
    return service.create_benefit(data)


@router.get("/{benefit_id}", response_model=BenefitResponse)
def get_benefit(benefit_id: int, service: ServiceDep):
    return service.get_benefit(benefit_id)


@router.put("/{benefit_id}", response_model=BenefitResponse)
def update_benefit(benefit_id: int, data: BenefitUpdate, service: ServiceDep):
    return service.update_benefit(benefit_id, data)


@router.delete("/{benefit_id}", response_model=BenefitResponse)
def delete_benefit(benefit_id: int, service: ServiceDep):
    """Borrado logico (is_active=False). Se puede deshacer con /restore."""
    return service.delete_benefit(benefit_id)


@router.post("/{benefit_id}/restore", response_model=BenefitResponse)
def restore_benefit(benefit_id: int, service: ServiceDep):
    return service.restore_benefit(benefit_id)


@router.get("/{benefit_id}/audits", response_model=list[AuditResponse])
def get_benefit_audits(benefit_id: int, service: ServiceDep):
    return service.audits(benefit_id)
