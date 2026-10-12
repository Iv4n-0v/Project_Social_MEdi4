from sqlmodel import SQLModel, Field
from typing import Optional

class BenefitBase(SQLModel):
    name: str
    description: Optional[str] = None

class Benefit(BenefitBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)