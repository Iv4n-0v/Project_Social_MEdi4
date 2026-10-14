"""Logica de negocio del servicio de usuarios.

Responsabilidades (principio S): reglas de negocio, validacion de imagen,
auditoria y coordinar repositorio + almacenamiento. No conoce HTTP (no lanza
HTTPException) ni SQL.
"""
from typing import Optional

from models import User
from repository import UserRepository
from schemas import UserResponse, UserUpdate
from storage import ImageStorage

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


class UserNotFound(Exception):
    pass


class InvalidImage(Exception):
    """Base de los errores de validacion de imagen."""


class UnsupportedImageType(InvalidImage):
    pass


class EmptyImage(InvalidImage):
    pass


class ImageTooLarge(InvalidImage):
    pass


class UserService:
    def __init__(self, repo: UserRepository, storage: ImageStorage) -> None:
        self.repo = repo
        self.storage = storage

    # ---- helpers ----
    def _get_or_raise(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise UserNotFound("User not found")
        return user

    def _to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            name=user.name,
            is_active=user.is_active,
            img=user.img,
            methodology_ids=self.repo.methodology_ids(user.id),
        )

    @staticmethod
    def _validate_image(content: bytes, content_type: Optional[str]) -> None:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise UnsupportedImageType(
                "Formato de imagen no permitido (JPG, PNG, WEBP o GIF)"
            )
        if not content:
            raise EmptyImage("El archivo de imagen esta vacio")
        if len(content) > MAX_IMAGE_BYTES:
            raise ImageTooLarge("La imagen supera los 5 MB")

    async def _upload_image(
        self, content: bytes, filename: str, content_type: Optional[str]
    ) -> str:
        self._validate_image(content, content_type)
        return await self.storage.upload(content, filename, content_type, "users")

    def _set_active(self, user_id: int, active: bool, action: str) -> UserResponse:
        user = self._get_or_raise(user_id)
        user.is_active = active
        self.repo.add_audit(user.id, action)
        self.repo.commit()
        self.repo.refresh(user)
        return self._to_response(user)

    # ---- casos de uso ----
    def list_users(self, is_active: Optional[bool] = None) -> list[UserResponse]:
        return [self._to_response(u) for u in self.repo.find_all(is_active)]

    def get_user(self, user_id: int) -> UserResponse:
        return self._to_response(self._get_or_raise(user_id))

    async def create_user(
        self,
        name: str,
        is_active: bool,
        methodology_ids: list[int],
        image: Optional[tuple[bytes, str, Optional[str]]] = None,
    ) -> UserResponse:
        """`image` es (contenido, nombre_de_archivo, content_type) o None."""
        img_url = None
        if image is not None:
            img_url = await self._upload_image(*image)

        user = self.repo.add(User(name=name.strip(), is_active=is_active, img=img_url))
        self.repo.set_methodologies(user.id, methodology_ids)
        self.repo.add_audit(user.id, "CREATE")
        self.repo.commit()
        self.repo.refresh(user)
        return self._to_response(user)

    def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = self._get_or_raise(user_id)
        if data.name is not None:
            user.name = data.name
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.methodology_ids is not None:
            self.repo.set_methodologies(user.id, data.methodology_ids)
        self.repo.add_audit(user.id, "UPDATE")
        self.repo.commit()
        self.repo.refresh(user)
        return self._to_response(user)

    async def update_image(
        self, user_id: int, content: bytes, filename: str, content_type: Optional[str]
    ) -> UserResponse:
        user = self._get_or_raise(user_id)
        user.img = await self._upload_image(content, filename, content_type)
        self.repo.add_audit(user.id, "UPDATE_IMAGE")
        self.repo.commit()
        self.repo.refresh(user)
        return self._to_response(user)

    def delete_user(self, user_id: int) -> UserResponse:
        """Borrado logico: el registro no se destruye, queda is_active=False."""
        return self._set_active(user_id, False, "DELETE")

    def restore_user(self, user_id: int) -> UserResponse:
        return self._set_active(user_id, True, "RESTORE")

    def audits(self, user_id: int):
        self._get_or_raise(user_id)
        return self.repo.audits(user_id)
