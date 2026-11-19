"""Modelo de datos del servicio de autenticacion.

Separacion de responsabilidades: aqui viven las CUENTAS (quien eres, como
entras y que roles tienes). El perfil publico del emprendimiento vive en otro
servicio y solo guarda el id de la cuenta (referencia logica, sin FK).

Roles: una misma cuenta puede tener 'visitor' y 'entrepreneur' a la vez.
Borrado logico: una cuenta desactivada queda is_active=False.
"""
import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

ROLE_VISITOR = "visitor"
ROLE_ENTREPRENEUR = "entrepreneur"
ROLES = (ROLE_VISITOR, ROLE_ENTREPRENEUR)


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)  # siempre en minusculas
    name: str
    # None cuando la cuenta se creo solo con Google/Facebook (sin contrasena)
    password_hash: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = True
    created_at: datetime.datetime = Field(default_factory=utcnow)


class AccountRole(SQLModel, table=True):
    """Que roles tiene cada cuenta (llave compuesta: no se repite el rol)."""

    __tablename__ = "account_roles"

    account_id: int = Field(foreign_key="accounts.id", primary_key=True)
    role: str = Field(primary_key=True)


class OAuthIdentity(SQLModel, table=True):
    """Identidad en un proveedor externo (Google/Facebook) ligada a una cuenta.

    Es SOLO para iniciar sesion. Vincular redes del negocio (Instagram, TikTok...)
    es otra funcionalidad, en otro servicio.
    """

    __tablename__ = "oauth_identities"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    provider: str = Field(index=True)
    provider_user_id: str = Field(index=True)
    created_at: datetime.datetime = Field(default_factory=utcnow)


class RefreshToken(SQLModel, table=True):
    """Sesiones. Se guarda solo el HASH del token, nunca el token."""

    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    expires_at: datetime.datetime
    revoked_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=utcnow)


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    expires_at: datetime.datetime
    used_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=utcnow)


class AccountAudit(SQLModel, table=True):
    """Auditoria de eventos de la cuenta (mismo patron de los otros servicios)."""

    __tablename__ = "account_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    action: str
    timestamp: datetime.datetime = Field(default_factory=utcnow)
