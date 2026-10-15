"""Esquemas de entrada de las rutas del monolito.

El monolito YA NO tiene tablas ni base de datos: usuarios, metodologias,
beneficios y analisis viven en sus microservicios. Estos esquemas solo validan
lo que llega por las rutas (la parte "Vista/Controlador" del MVC).
"""
from sqlmodel import SQLModel
from typing import Optional


class MethodologyBase(SQLModel):
    name: str
    description: Optional[str] = None


class BenefitBase(SQLModel):
    name: str
    description: Optional[str] = None


class AnalysisBase(SQLModel):
    sector: str
    reach: int
    time_in_social_media: float
