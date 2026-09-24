import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str
    is_active: bool = True


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    img: Optional[str] = Field(default=None, nullable=True)


class UserMethodologyLink(SQLModel, table=True):
    """
    Que metodologias tiene cada usuario.
    methodology_id NO es ForeignKey: esa tabla vive en el servicio de
    metodologias, aqui solo guardamos el ID (igual que analysis_service
    guarda user_id sin FK).
    """
    __tablename__ = "user_methodology"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    methodology_id: int = Field(primary_key=True)


class UserAudit(SQLModel, table=True):
    __tablename__ = "user_audit"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    action: str
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )