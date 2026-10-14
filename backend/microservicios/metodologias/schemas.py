"""Esquemas de entrada/salida del servicio de metodologias.

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


def _check_ids(value: Optional[list[int]]) -> Optional[list[int]]:
    if value is not None and any(i <= 0 for i in value):
        raise ValueError("Los IDs deben ser enteros positivos")
    return value


class MethodologyCreate(SQLModel):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    # Solo IDs: la tabla de beneficios vive en otro servicio.
    benefit_ids: list[int] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        return _clean_name(v)

    @field_validator("benefit_ids")
    @classmethod
    def _validate_benefit_ids(cls, v):
        return _check_ids(v)


class MethodologyUpdate(SQLModel):
    """Actualizacion parcial: solo se modifica lo que venga informado."""

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None
    benefit_ids: Optional[list[int]] = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        return _clean_name(v)

    @field_validator("benefit_ids")
    @classmethod
    def _validate_benefit_ids(cls, v):
        return _check_ids(v)


class MethodologyResponse(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    benefit_ids: list[int] = Field(default_factory=list)


class AuditResponse(SQLModel):
    id: int
    methodology_id: int
    action: str
    timestamp: datetime.datetime
