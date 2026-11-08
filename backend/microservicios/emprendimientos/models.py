"""Modelo de datos del servicio de emprendimientos (la "M" de MVC).

- Un emprendimiento por cuenta (owner_account_id es unico). La cuenta vive en
  el servicio auth: aqui solo se guarda su id, sin llave foranea.
- Borrado logico: is_active=False. Cada cambio queda en venture_audit.
- Publico vs privado: el catalogo solo lee emprendimientos con
  is_published=True e is_active=True, y nunca expone owner_account_id.
"""
import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    is_active: bool = True


class Venture(SQLModel, table=True):
    __tablename__ = "ventures"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_account_id: int = Field(unique=True, index=True)  # referencia logica a auth
    name: str
    entrepreneur_name: Optional[str] = None
    show_entrepreneur_name: bool = False  # el nombre del emprendedor solo se muestra si lo autoriza
    description: Optional[str] = None
    location: Optional[str] = None
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    profile_image_url: Optional[str] = None  # la subida de imagen llega en la Fase 6
    is_published: bool = False  # nace como borrador
    is_active: bool = True
    created_at: datetime.datetime = Field(default_factory=utcnow)
    updated_at: datetime.datetime = Field(default_factory=utcnow)


class SocialLink(SQLModel, table=True):
    """Una red del NEGOCIO (independiente del inicio de sesion con Google/Facebook)."""

    __tablename__ = "social_links"
    __table_args__ = (UniqueConstraint("venture_id", "platform"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    venture_id: int = Field(foreign_key="ventures.id", index=True)
    platform: str
    url: str
    is_active: bool = True


class FollowerStat(SQLModel, table=True):
    """Historial de seguidores. source: 'manual' (declarado) o 'api' (obtenido de la red)."""

    __tablename__ = "follower_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    social_link_id: int = Field(foreign_key="social_links.id", index=True)
    followers: int
    source: str = "manual"
    updated_at: datetime.datetime = Field(default_factory=utcnow)


class Favorite(SQLModel, table=True):
    """Favoritos: privados, ligados a la cuenta autenticada."""

    __tablename__ = "favorites"

    account_id: int = Field(primary_key=True)  # referencia logica a auth
    venture_id: int = Field(foreign_key="ventures.id", primary_key=True)
    created_at: datetime.datetime = Field(default_factory=utcnow)


class VentureAudit(SQLModel, table=True):
    __tablename__ = "venture_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    venture_id: int = Field(foreign_key="ventures.id", index=True)
    action: str
    timestamp: datetime.datetime = Field(default_factory=utcnow)
