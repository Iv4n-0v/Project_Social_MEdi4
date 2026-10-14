"""Esquemas de entrada/salida del servicio de analisis.

Son la "vista" de la API (la V de MVC para un servicio JSON): definen
exactamente que se recibe y que se expone, sin filtrar los modelos de la BD.
"""
import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


def _clean_sector(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("El sector no puede estar vacio")
    return value


class AnalysisCreate(SQLModel):
    sector: str = Field(max_length=100)
    reach: int = Field(ge=0)
    time_in_social_media: float = Field(ge=0)
    user_id: int = Field(gt=0)

    @field_validator("sector")
    @classmethod
    def _validate_sector(cls, v):
        return _clean_sector(v)


class AnalysisUpdate(SQLModel):
    """Actualizacion parcial: solo se modifica lo que venga informado.

    user_id no se puede cambiar: un analisis pertenece a quien lo creo.
    """

    sector: Optional[str] = Field(default=None, max_length=100)
    reach: Optional[int] = Field(default=None, ge=0)
    time_in_social_media: Optional[float] = Field(default=None, ge=0)

    @field_validator("sector")
    @classmethod
    def _validate_sector(cls, v):
        return _clean_sector(v)


class AnalysisResponse(SQLModel):
    id: int
    sector: str
    reach: int
    time_in_social_media: float
    user_id: int
    date: datetime.datetime
    is_active: bool


class AuditResponse(SQLModel):
    id: int
    analysis_id: int
    action: str
    timestamp: datetime.datetime
