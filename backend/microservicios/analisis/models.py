from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class AnalysisBase(SQLModel):
    sector: str = Field(min_length=1, max_length=100)
    reach: int = Field(ge=0)
    time_in_social_media: float = Field(ge=0)
    user_id: int = Field(gt=0)


class Analysis(AnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AnalysisUpdate(SQLModel):
    sector: Optional[str] = Field(default=None, min_length=1, max_length=100)
    reach: Optional[int] = Field(default=None, ge=0)
    time_in_social_media: Optional[float] = Field(default=None, ge=0)
    user_id: Optional[int] = Field(default=None, gt=0)