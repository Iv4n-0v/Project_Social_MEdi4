"""Capa HTTP del servicio de analisis (parte del "controlador").

Solo traduce HTTP <-> casos de uso del servicio. Sin reglas de negocio ni SQL.
Los errores de dominio (AnalysisNotFound) se convierten en HTTP en main.py.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from database import SessionDep
from repository import AnalysisRepository
from schemas import AnalysisCreate, AnalysisResponse, AnalysisUpdate, AuditResponse
from service import AnalysisService

router = APIRouter(tags=["analysis"])


def get_service(session: SessionDep) -> AnalysisService:
    return AnalysisService(AnalysisRepository(session))


ServiceDep = Annotated[AnalysisService, Depends(get_service)]


@router.get("/", response_model=list[AnalysisResponse])
def get_all_analyses(
    service: ServiceDep,
    is_active: Optional[bool] = None,
    user_id: Optional[int] = None,
):
    """?is_active=true -> activos | false -> eliminados | ?user_id=3 -> de ese usuario"""
    return service.list_analyses(is_active, user_id)


@router.post("/", response_model=AnalysisResponse, status_code=201)
def create_analysis(data: AnalysisCreate, service: ServiceDep):
    return service.create_analysis(data)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int, service: ServiceDep):
    return service.get_analysis(analysis_id)


@router.put("/{analysis_id}", response_model=AnalysisResponse)
def update_analysis(analysis_id: int, data: AnalysisUpdate, service: ServiceDep):
    """Actualizacion parcial: un campo omitido no cambia."""
    return service.update_analysis(analysis_id, data)


@router.delete("/{analysis_id}", response_model=AnalysisResponse)
def delete_analysis(analysis_id: int, service: ServiceDep):
    """Borrado logico (is_active=False). Se puede deshacer con /restore."""
    return service.delete_analysis(analysis_id)


@router.post("/{analysis_id}/restore", response_model=AnalysisResponse)
def restore_analysis(analysis_id: int, service: ServiceDep):
    return service.restore_analysis(analysis_id)


@router.get("/{analysis_id}/audits", response_model=list[AuditResponse])
def get_analysis_audits(analysis_id: int, service: ServiceDep):
    return service.audits(analysis_id)
