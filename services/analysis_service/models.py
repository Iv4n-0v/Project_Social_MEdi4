from sqlmodel import SQLModel, Field
from typing import Optional
import datetime


class AnalysisBase(SQLModel):
    sector: str
    reach: int
    time_in_social_media: float


class Analysis(AnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    date: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )

    user_id: int