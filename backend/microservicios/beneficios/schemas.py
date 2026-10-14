"""Esquemas de entrada/salida del servicio de beneficios.

Son la "vista" de la API (la V de MVC para un servicio JSON): definen
exactamente que se recibe y que se expone, sin filtrar los modelos de la BD.
"""
import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


def _clean_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("El nombre no puede estar vacio")
    return value


class BenefitCreate(SQLModel):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        return _clean_name(v)


class BenefitUpdate(SQLModel):
    """Actualizacion parcial: solo se modifica lo que venga informado."""

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        return _clean_name(v)


class BenefitResponse(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool


class AuditResponse(SQLModel):
    id: int
    benefit_id: int
    action: str
    timestamp: datetime.datetime
