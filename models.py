from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import datetime

# 🔹 Tabla intermedia para relación N:M entre Metodología y Beneficio
class MethodologyBenefitLink(SQLModel, table=True):
    methodology_id: Optional[int] = Field(default=None, foreign_key="methodology.id", primary_key=True)
    benefit_id: Optional[int] = Field(default=None, foreign_key="benefit.id", primary_key=True)

# 🔹 Usuario (Emprendedor o Vendedor)
class UserBase(SQLModel):
    name: str
    type: str  # "Emprendedor" o "Vendedor"

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    methodologies: List["Methodology"] = Relationship(back_populates="user")
    analyses: List["Analysis"] = Relationship(back_populates="user")
    audits: List["UserAudit"] = Relationship(back_populates="user")

# 🔹 Metodología (E-commerce, Publicidad, etc.)
class MethodologyBase(SQLModel):
    name: str
    description: Optional[str] = None
    user_id: int

class Methodology(MethodologyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="methodologies")
    benefits: List["Benefit"] = Relationship(back_populates="methodologies", link_model=MethodologyBenefitLink)

# 🔹 Beneficio Económico
class BenefitBase(SQLModel):
    name: str
    description: Optional[str] = None

class Benefit(BenefitBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    methodologies: List[Methodology] = Relationship(back_populates="benefits", link_model=MethodologyBenefitLink)

# 🔹 Análisis General (relación M:1 con Usuario)
class AnalysisBase(SQLModel):
    sector: str
    reach: int
    time_in_social_media: float

class Analysis(AnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="analyses")

# 🔹 Auditoría de Usuario
class UserAudit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str  # "DELETE" o "RESTORE"
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user: User = Relationship(back_populates="audits")