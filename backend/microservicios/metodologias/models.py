from sqlmodel import SQLModel, Field
from typing import Optional

class MethodologyBase(SQLModel):
    name: str
    description: Optional[str] = None

class Methodology(MethodologyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)