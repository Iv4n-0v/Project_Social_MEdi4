"""Almacenamiento de imagenes del emprendimiento (objetos, no la base de datos).

Solo sabe guardar y borrar un archivo; la validacion la hace service.py y los
codigos HTTP, main.py. Mismo contrato que el del servicio de usuarios.
"""
import os
import uuid
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()


class StorageUnavailable(Exception):
    """El almacenamiento no esta configurado (faltan credenciales)."""


class StorageError(Exception):
    """El almacenamiento esta configurado pero la operacion fallo."""


class ImageStorage(Protocol):
    def is_configured(self) -> bool: ...

    async def upload(self, content: bytes, extension: str, content_type: str, folder: str) -> str:
        """Guarda la imagen y devuelve su URL publica."""
        ...

    async def delete(self, url: str) -> None:
        """Borra la imagen si se puede; nunca lanza (es limpieza, no parte del flujo)."""
        ...


class SupabaseStorage:
    def __init__(self) -> None:
        self._client = None

    def _bucket(self) -> str:
        return os.getenv("SUPABASE_BUCKET", "bucket")

    def is_configured(self) -> bool:
        return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))

    def _get_client(self):
        """Cliente creado en el primer uso: el servicio arranca sin Supabase."""
        if self._client is None:
            if not self.is_configured():
                raise StorageUnavailable("Almacenamiento de imagenes no configurado")
            from supabase import create_client

            self._client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        return self._client

    def _public_prefix(self) -> str:
        return f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{self._bucket()}/"

    async def upload(self, content: bytes, extension: str, content_type: str, folder: str) -> str:
        client = self._get_client()
        path = f"{folder}/{uuid.uuid4()}{extension}"
        try:
            client.storage.from_(self._bucket()).upload(
                path,
                content,
                {"content-type": content_type, "cache-control": "no-cache", "upsert": "false"},
            )
        except Exception as exc:
            raise StorageError("No se pudo subir la imagen al almacenamiento") from exc
        return self._public_prefix() + path

    async def delete(self, url: str) -> None:
        try:
            prefix = self._public_prefix()
            if url and url.startswith(prefix):
                self._get_client().storage.from_(self._bucket()).remove([url[len(prefix):]])
        except Exception:
            pass  # la foto nueva ya esta guardada; un archivo huerfano no debe romper nada


_storage: ImageStorage = SupabaseStorage()


def get_storage() -> ImageStorage:
    """Dependencia de FastAPI. En pruebas se reemplaza con dependency_overrides."""
    return _storage
