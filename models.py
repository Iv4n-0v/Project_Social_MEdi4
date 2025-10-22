from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import datetime

# Tablas intermedias
class UserMethodologyLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    methodology_id: Optional[int] = Field(default=None, foreign_key="methodology.id", primary_key=True)

class MethodologyBenefitLink(SQLModel, table=True):
    methodology_id: Optional[int] = Field(default=None, foreign_key="methodology.id", primary_key=True)
    benefit_id: Optional[int] = Field(default=None, foreign_key="benefit.id", primary_key=True)

# Methodology
class MethodologyBase(SQLModel):
    name: str
    description: Optional[str] = None

class Methodology(MethodologyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(back_populates="methodology")
    benefits: List["Benefit"] = Relationship(back_populates="methodologies", link_model=MethodologyBenefitLink)

# Benefit
class BenefitBase(SQLModel):
    name: str
    description: Optional[str] = None

class Benefit(BenefitBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    methodologies: List[Methodology] = Relationship(back_populates="benefits", link_model=MethodologyBenefitLink)

# User
class UserBase(SQLModel):
    name: str
    type: str
    is_active: bool = True

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    methodology_id: Optional[int] = Field(default=None, foreign_key="methodology.id")
    methodology: Optional[Methodology] = Relationship(back_populates="users")
    analyses: List["Analysis"] = Relationship(back_populates="user")
    audits: List["UserAudit"] = Relationship(back_populates="user")

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