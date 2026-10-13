import os
import uuid

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile

load_dotenv()

BUCKET = os.getenv("SUPABASE_BUCKET", "bucket")
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

_client = None


def _get_client():
    """Crea el cliente solo al primer uso, así el servicio arranca sin Supabase."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise HTTPException(503, "Almacenamiento de imagenes no configurado")
        from supabase import create_client
        _client = create_client(url, key)
    return _client


async def upload_to_bucket(file: UploadFile, folder: str = "users") -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Formato de imagen no permitido (JPG, PNG, WEBP o GIF)")

    content = await file.read()
    if not content:
        raise HTTPException(400, "El archivo de imagen esta vacio")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "La imagen supera los 5 MB")

    extension = os.path.splitext(file.filename or "")[1].lower()
    path = f"{folder}/{uuid.uuid4()}{extension}"
    try:
        _get_client().storage.from_(BUCKET).upload(
            path,
            content,
            # los headers deben ser texto: "false", no False
            {"content-type": file.content_type, "cache-control": "no-cache", "upsert": "false"},
        )
    except Exception:
        raise HTTPException(502, "No se pudo subir la imagen al almacenamiento")

    return f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{BUCKET}/{path}"