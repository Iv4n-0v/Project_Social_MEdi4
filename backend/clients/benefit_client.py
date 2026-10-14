"""Cliente del microservicio de beneficios (via KrakenD)."""
from typing import Optional

from sqlmodel import SQLModel

from backend.clients.base import BaseClient


class BenefitDTO(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True


class BenefitClient(BaseClient):
    resource = "benefits"

    def find_all(self, ids: Optional[list[int]] = None) -> list[BenefitDTO]:
        params = {"is_active": "true"}
        if ids is not None:
            if not ids:  # lista vacia: no hay nada que pedir
                return []
            params["ids"] = ",".join(str(i) for i in ids)
        return [BenefitDTO(**b) for b in self._request("GET", params=params)]

    def get(self, benefit_id: int) -> BenefitDTO:
        return BenefitDTO(**self._request("GET", f"/{benefit_id}"))

    def create(self, name: str, description: Optional[str] = None) -> BenefitDTO:
        body = {"name": name, "description": description}
        return BenefitDTO(**self._request("POST", json=body))


def get_benefit_client() -> BenefitClient:
    return BenefitClient()
