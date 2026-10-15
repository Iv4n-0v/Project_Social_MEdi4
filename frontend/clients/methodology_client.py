"""Cliente del microservicio de metodologias (via KrakenD)."""
from typing import Optional

from sqlmodel import SQLModel

from frontend.clients.base import BaseClient


class MethodologyDTO(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    benefit_ids: list[int] = []
    is_active: bool = True


class MethodologyClient(BaseClient):
    resource = "methodologies"

    def find_all(self) -> list[MethodologyDTO]:
        return [MethodologyDTO(**m) for m in self._request("GET", params={"is_active": "true"})]

    def get(self, methodology_id: int) -> MethodologyDTO:
        return MethodologyDTO(**self._request("GET", f"/{methodology_id}"))

    def create(
        self, name: str, description: Optional[str] = None,
        benefit_ids: Optional[list[int]] = None,
    ) -> MethodologyDTO:
        body = {"name": name, "description": description, "benefit_ids": benefit_ids or []}
        return MethodologyDTO(**self._request("POST", json=body))

    def update(
        self, methodology_id: int, name: Optional[str] = None,
        description: Optional[str] = None, benefit_ids: Optional[list[int]] = None,
    ) -> MethodologyDTO:
        """PUT parcial: lo que sea None no se envia y no cambia."""
        body = {
            k: v for k, v in
            {"name": name, "description": description, "benefit_ids": benefit_ids}.items()
            if v is not None
        }
        return MethodologyDTO(**self._request("PUT", f"/{methodology_id}", json=body))


def get_methodology_client() -> MethodologyClient:
    return MethodologyClient()
