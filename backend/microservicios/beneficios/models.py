"""Modelo de datos del servicio de beneficios (la "M" de MVC).

Borrado logico: un beneficio eliminado no se destruye, queda is_active=False.
Cada cambio queda registrado en benefit_audit.
"""
import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Benefit(SQLModel, table=True):
    __tablename__ = "benefits"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    is_active: bool = True


class BenefitAudit(SQLModel, table=True):
    __tablename__ = "benefit_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    benefit_id: int = Field(foreign_key="benefits.id")
    action: str
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
