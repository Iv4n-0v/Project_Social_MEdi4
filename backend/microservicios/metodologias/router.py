"""Capa HTTP del servicio de metodologias (parte del "controlador").

Solo traduce HTTP <-> casos de uso del servicio. Sin reglas de negocio ni SQL.
Los errores de dominio (MethodologyNotFound) se convierten en HTTP en main.py.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from database import SessionDep
from repository import MethodologyRepository
from schemas import (
    AuditResponse,
    MethodologyCreate,
    MethodologyResponse,
    MethodologyUpdate,
)
from service import MethodologyService

router = APIRouter(tags=["methodologies"])


def get_service(session: SessionDep) -> MethodologyService:
    return MethodologyService(MethodologyRepository(session))


ServiceDep = Annotated[MethodologyService, Depends(get_service)]


@router.get("/", response_model=list[MethodologyResponse])
def get_all_methodologies(service: ServiceDep, is_active: Optional[bool] = None):
    """?is_active=true -> activas | ?is_active=false -> eliminadas | sin filtro -> todas"""
    return service.list_methodologies(is_active)


@router.post("/", response_model=MethodologyResponse, status_code=201)
def create_methodology(data: MethodologyCreate, service: ServiceDep):
    return service.create_methodology(data)


@router.get("/{methodology_id}", response_model=MethodologyResponse)
def get_methodology(methodology_id: int, service: ServiceDep):
    return service.get_methodology(methodology_id)


@router.put("/{methodology_id}", response_model=MethodologyResponse)
def update_methodology(
    methodology_id: int, data: MethodologyUpdate, service: ServiceDep
):
    return service.update_methodology(methodology_id, data)


@router.delete("/{methodology_id}", response_model=MethodologyResponse)
def delete_methodology(methodology_id: int, service: ServiceDep):
    """Borrado logico (is_active=False). Se puede deshacer con /restore."""
    return service.delete_methodology(methodology_id)


@router.post("/{methodology_id}/restore", response_model=MethodologyResponse)
def restore_methodology(methodology_id: int, service: ServiceDep):
    return service.restore_methodology(methodology_id)


@router.get("/{methodology_id}/audits", response_model=list[AuditResponse])
def get_methodology_audits(methodology_id: int, service: ServiceDep):
    return service.audits(methodology_id)
