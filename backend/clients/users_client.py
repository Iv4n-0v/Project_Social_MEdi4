"""Cliente del microservicio de usuarios (via KrakenD)."""
from typing import Optional

from sqlmodel import SQLModel

from backend.clients.base import BaseClient

# (nombre_de_archivo, contenido, content_type)
Image = tuple[str, bytes, Optional[str]]


class UserDTO(SQLModel):
    id: int
    name: str
    is_active: bool = True
    img: Optional[str] = None
    methodology_ids: list[int] = []


class UsersClient(BaseClient):
    resource = "users"

    def find_all(self, is_active: Optional[bool] = None) -> list[UserDTO]:
        params = {} if is_active is None else {"is_active": str(is_active).lower()}
        return [UserDTO(**u) for u in self._request("GET", params=params)]

    def get(self, user_id: int) -> UserDTO:
        return UserDTO(**self._request("GET", f"/{user_id}"))

    def create(
        self, name: str, is_active: bool = True,
        methodology_ids: Optional[list[int]] = None, image: Optional[Image] = None,
    ) -> UserDTO:
        """El micro recibe formulario (multipart si hay imagen)."""
        data = {
            "name": name,
            "is_active": "true" if is_active else "false",
            "methodology_ids": [str(i) for i in (methodology_ids or [])],
        }
        files = {"img": image} if image else None
        return UserDTO(**self._request("POST", data=data, files=files))

    def update(
        self, user_id: int, name: Optional[str] = None,
        is_active: Optional[bool] = None, methodology_ids: Optional[list[int]] = None,
    ) -> UserDTO:
        """PUT parcial: lo que sea None no se envia y no cambia."""
        body = {
            k: v for k, v in
            {"name": name, "is_active": is_active, "methodology_ids": methodology_ids}.items()
            if v is not None
        }
        return UserDTO(**self._request("PUT", f"/{user_id}", json=body))

    def update_image(self, user_id: int, image: Image) -> UserDTO:
        return UserDTO(**self._request("PUT", f"/{user_id}/image", files={"img": image}))

    def delete(self, user_id: int) -> UserDTO:
        """Borrado logico: el usuario queda inactivo y se puede restaurar."""
        return UserDTO(**self._request("DELETE", f"/{user_id}"))

    def restore(self, user_id: int) -> UserDTO:
        return UserDTO(**self._request("POST", f"/{user_id}/restore"))


def get_users_client() -> UsersClient:
    return UsersClient()
