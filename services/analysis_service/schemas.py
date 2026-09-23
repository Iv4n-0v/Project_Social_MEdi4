from pydantic import BaseModel
from datetime import datetime


class AnalysisCreate(BaseModel):
    sector: str
    reach: int
    time_in_social_media: float
    user_id: int


class AnalysisResponse(BaseModel):
    id: int
    sector: str
    reach: int
    time_in_social_media: float
    date: datetime
    user_id: int