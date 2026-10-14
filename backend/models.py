from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import datetime

# Tabla intermedia usuario <-> metodologia.
# La metodologia vive en OTRO servicio: aqui solo se guarda su ID (sin llave foranea).
class UserMethodologyLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    methodology_id: int = Field(primary_key=True)

# Esquemas de entrada de las rutas (ya NO son tablas: los datos viven en los micros)
class MethodologyBase(SQLModel):
    name: str
    description: Optional[str] = None

class BenefitBase(SQLModel):
    name: str
    description: Optional[str] = None

# User
class UserBase(SQLModel):
    name: str
    is_active: bool = True

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    analyses: List["Analysis"] = Relationship(back_populates="user")
    audits: List["UserAudit"] = Relationship(back_populates="user")
    img: Optional[str] = Field(default=None, nullable=True)

# Analysis
class AnalysisBase(SQLModel):
    sector: str
    reach: int
    time_in_social_media: float
    

class Analysis(AnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="analyses")
    

# UserAudit
class UserAudit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user: User = Relationship(back_populates="audits")