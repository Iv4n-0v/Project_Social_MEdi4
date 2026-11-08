"""Contratos de entrada y salida.

PublicVenture es lo UNICO que ve un visitante: no incluye el id de la cuenta
duena ni ningun dato de integracion.
"""
import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str


class SocialPublic(BaseModel):
    platform: str
    url: str
    followers: Optional[int] = None
    # 'manual' = declarado por el emprendedor; 'api' = obtenido de la red
    followers_source: Optional[str] = None
    followers_updated_at: Optional[datetime.datetime] = None


class PublicVenture(BaseModel):
    id: int
    name: str
    entrepreneur_name: Optional[str] = None  # solo si el emprendedor lo publica
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[CategoryResponse] = None
    profile_image_url: Optional[str] = None
    social: list[SocialPublic] = []


class PublicVentureList(BaseModel):
    items: list[PublicVenture]
    total: int
    limit: int
    offset: int


class OwnVenture(PublicVenture):
    """Vista del dueno: agrega lo que el visitante no ve."""

    entrepreneur_name: Optional[str] = None  # el dueno siempre lo ve
    show_entrepreneur_name: bool
    is_published: bool
    is_active: bool
    category_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class VentureSave(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"\S")
    entrepreneur_name: Optional[str] = Field(default=None, max_length=100)
    show_entrepreneur_name: bool = False
    description: Optional[str] = Field(default=None, max_length=1000)
    location: Optional[str] = Field(default=None, max_length=120)
    category_id: Optional[int] = None


class SocialSave(BaseModel):
    url: str = Field(max_length=300)
    # Opcional: seguidores declarados a mano. Si se omite, no se toca el ultimo valor.
    followers: Optional[int] = Field(default=None, ge=0, le=2_000_000_000)


class FavoriteIds(BaseModel):
    ids: list[int]


class AuditResponse(BaseModel):
    id: int
    action: str
    timestamp: datetime.datetime
