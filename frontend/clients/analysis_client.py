"""Cliente del microservicio de analisis (via KrakenD)."""
import datetime
from typing import Optional

from sqlmodel import SQLModel

from frontend.clients.base import BaseClient


class AnalysisDTO(SQLModel):
    """Lo que devuelve el microservicio (no es una tabla del monolito)."""

    id: int
    sector: str
    reach: int
    time_in_social_media: float
    user_id: int
    date: datetime.datetime
    is_active: bool = True


class AnalysisClient(BaseClient):
    resource = "analysis"

    def find_all(self, user_id: Optional[int] = None) -> list[AnalysisDTO]:
        params = {"is_active": "true"}
        if user_id is not None:
            params["user_id"] = user_id
        return [AnalysisDTO(**a) for a in self._request("GET", params=params)]

    def get(self, analysis_id: int) -> AnalysisDTO:
        return AnalysisDTO(**self._request("GET", f"/{analysis_id}"))

    def create(
        self, user_id: int, sector: str, reach: int, time_in_social_media: float
    ) -> AnalysisDTO:
        body = {
            "user_id": user_id,
            "sector": sector,
            "reach": reach,
            "time_in_social_media": time_in_social_media,
        }
        return AnalysisDTO(**self._request("POST", json=body))


def get_analysis_client() -> AnalysisClient:
    return AnalysisClient()
