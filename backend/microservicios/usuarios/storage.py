"""Almacenamiento de imagenes detras de una interfaz.

Este archivo SOLO sabe guardar un archivo y devolver su URL. No valida la
imagen (eso lo hace service.py) y no conoce HTTP (los errores se traducen a
codigos en main.py).

Principios SOLID aplicados:
- D (inversion de dependencias): el servicio depende de `ImageStorage` (un
  contrato), no de Supabase.
- O (abierto/cerrado): para usar otro proveedor se agrega una clase nueva que
  cumpla `ImageStorage`; no se edita el codigo existente.
"""
import os
import uuid
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()


class StorageUnavailable(Exception):
    """El almacenamiento no esta configurado (faltan credenciales)."""


class StorageError(Exception):
    """El almacenamiento esta configurado pero la subida fallo."""


class ImageStorage(Protocol):
    """Contrato: cualquier clase con este metodo sirve como almacenamiento."""

    async def upload(
        self, content: bytes, filename: str, content_type: str, folder: str
    ) -> str:
        """Guarda la imagen y devuelve su URL publica."""
        ...


class SupabaseStorage:
    """Implementacion sobre Supabase Storage."""

    def __init__(self) -> None:
        self._client = None

    def _bucket(self) -> str:
        return os.getenv("SUPABASE_BUCKET", "bucket")

    def _get_client(self):
        """Crea el cliente solo al primer uso: el servicio arranca sin Supabase."""
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise StorageUnavailable("Almacenamiento de imagenes no configurado")
            from supabase import create_client

            self._client = create_client(url, key)
        return self._client

    async def upload(
        self, content: bytes, filename: str, content_type: str, folder: str
    ) -> str:
        client = self._get_client()
        extension = os.path.splitext(filename or "")[1].lower()
        path = f"{folder}/{uuid.uuid4()}{extension}"
        try:
            client.storage.from_(self._bucket()).upload(
                path,
                content,
                # los headers deben ser texto: "false", no False
                {
                    "content-type": content_type,
                    "cache-control": "no-cache",
                    "upsert": "false",
                },
            )
        except Exception as exc:
            raise StorageError(
                "No se pudo subir la imagen al almacenamiento"
            ) from exc
        return (
            f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/"
            f"{self._bucket()}/{path}"
        )


_storage: ImageStorage = SupabaseStorage()


def get_storage() -> ImageStorage:
    """Dependencia de FastAPI. En pruebas se reemplaza con dependency_overrides."""
    return _storage
