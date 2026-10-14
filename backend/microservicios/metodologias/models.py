"""Modelo de datos del servicio de metodologias (la "M" de MVC).

Borrado logico: una metodologia eliminada no se destruye, queda is_active=False.
Cada cambio queda registrado en methodology_audit.
"""
import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Methodology(SQLModel, table=True):
    __tablename__ = "methodologies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    is_active: bool = True


class MethodologyBenefit(SQLModel, table=True):
    """
    Que beneficios tiene cada metodologia.
    benefit_id NO es ForeignKey: la tabla de beneficios vive en el servicio de
    beneficios (otra base de datos). Aqui solo guardamos el ID, igual que el
    servicio de usuarios guarda methodology_id.
    """

    __tablename__ = "methodology_benefit"

    methodology_id: int = Field(foreign_key="methodologies.id", primary_key=True)
    benefit_id: int = Field(primary_key=True)


class MethodologyAudit(SQLModel, table=True):
    __tablename__ = "methodology_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    methodology_id: int = Field(foreign_key="methodologies.id")
    action: str
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
