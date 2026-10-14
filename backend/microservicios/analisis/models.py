"""Modelo de datos del servicio de analisis (la "M" de MVC).

Borrado logico: un analisis eliminado no se destruye, queda is_active=False.
Cada cambio queda registrado en analysis_audit.

user_id es solo un numero: el usuario vive en OTRO servicio (con su propia BD),
por eso no hay llave foranea hacia el.
"""
import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Analysis(SQLModel, table=True):
    __tablename__ = "analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    sector: str
    reach: int
    time_in_social_media: float
    user_id: int  # referencia logica al servicio de usuarios (sin FK)
    date: datetime.datetime = Field(default_factory=_utcnow)
    is_active: bool = True


class AnalysisAudit(SQLModel, table=True):
    __tablename__ = "analysis_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analysis.id")
    action: str
    timestamp: datetime.datetime = Field(default_factory=_utcnow)
