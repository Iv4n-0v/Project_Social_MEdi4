import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class UserResponse(SQLModel):
    id: int
    name: str
    is_active: bool
    img: Optional[str] = None
    methodology_ids: list[int] = Field(default_factory=list)


class UserUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
    methodology_ids: Optional[list[int]] = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacio")
        return v


class AuditResponse(SQLModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime.datetime