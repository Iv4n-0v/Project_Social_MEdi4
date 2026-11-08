"""Capa HTTP del servicio de emprendimientos.

La identidad llega SOLO en la cabecera X-User-Id, que el gateway (KrakenD) pone
despues de validar el JWT. Los servicios no deben ser alcanzables sin pasar por el.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from database import SessionDep
from repository import VentureRepository
from schemas import (
    AuditResponse,
    CategoryResponse,
    FavoriteIds,
    OwnVenture,
    PublicVenture,
    PublicVentureList,
    SocialSave,
    VentureSave,
)
from service import VentureService

router = APIRouter(tags=["emprendimientos"])


def get_service(session: SessionDep) -> VentureService:
    return VentureService(VentureRepository(session))


ServiceDep = Annotated[VentureService, Depends(get_service)]


def current_account(x_user_id: Annotated[Optional[str], Header()] = None) -> int:
    try:
        return int(x_user_id or "")
    except ValueError:
        raise HTTPException(status_code=401, detail="No autenticado")


AccountDep = Annotated[int, Depends(current_account)]


# ---- publico ----
@router.get("/categories", response_model=list[CategoryResponse])
def categories(svc: ServiceDep):
    return svc.list_categories()


@router.get("/ventures", response_model=PublicVentureList)
def search(
    svc: ServiceDep,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    return svc.search(q, category_id, limit, offset)


@router.get("/ventures/{venture_id}", response_model=PublicVenture)
def public_venture(venture_id: int, svc: ServiceDep):
    return svc.get_public(venture_id)


# ---- mi emprendimiento (rol entrepreneur, lo exige el gateway) ----
@router.get("/me/venture", response_model=OwnVenture)
def my_venture(account: AccountDep, svc: ServiceDep):
    return svc.get_mine(account)


@router.put("/me/venture", response_model=OwnVenture)
def save_my_venture(data: VentureSave, account: AccountDep, svc: ServiceDep, response: Response):
    venture, created = svc.save_mine(account, data)
    response.status_code = 201 if created else 200
    return venture


@router.delete("/me/venture", response_model=OwnVenture)
def delete_my_venture(account: AccountDep, svc: ServiceDep):
    return svc.delete_mine(account)


@router.post("/me/venture/restore", response_model=OwnVenture)
def restore_my_venture(account: AccountDep, svc: ServiceDep):
    return svc.restore_mine(account)


@router.post("/me/venture/publish", response_model=OwnVenture)
def publish(account: AccountDep, svc: ServiceDep):
    return svc.publish(account)


@router.post("/me/venture/unpublish", response_model=OwnVenture)
def unpublish(account: AccountDep, svc: ServiceDep):
    return svc.unpublish(account)


@router.get("/me/venture/audits", response_model=list[AuditResponse])
def audits(account: AccountDep, svc: ServiceDep):
    return svc.audits_mine(account)


@router.put("/me/venture/social/{platform}", response_model=OwnVenture)
def set_social(platform: str, data: SocialSave, account: AccountDep, svc: ServiceDep):
    return svc.set_social(account, platform, data.url, data.followers)


@router.delete("/me/venture/social/{platform}", response_model=OwnVenture)
def remove_social(platform: str, account: AccountDep, svc: ServiceDep):
    return svc.remove_social(account, platform)


# ---- favoritos (cualquier cuenta con sesion) ----
@router.get("/me/favorites", response_model=list[PublicVenture])
def favorites(account: AccountDep, svc: ServiceDep):
    return svc.list_favorites(account)


@router.get("/me/favorite-ids", response_model=FavoriteIds)
def favorite_ids(account: AccountDep, svc: ServiceDep):
    return FavoriteIds(ids=svc.favorite_ids(account))


@router.put("/me/favorites/{venture_id}", status_code=204)
def add_favorite(venture_id: int, account: AccountDep, svc: ServiceDep):
    svc.add_favorite(account, venture_id)
    return Response(status_code=204)


@router.delete("/me/favorites/{venture_id}", status_code=204)
def remove_favorite(venture_id: int, account: AccountDep, svc: ServiceDep):
    svc.remove_favorite(account, venture_id)
    return Response(status_code=204)
