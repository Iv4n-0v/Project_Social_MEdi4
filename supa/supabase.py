import os
import uuid
from supabase import create_client
from fastapi import UploadFile

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def upload_to_bucket(file: UploadFile, folder: str = "users"):

    bucket = "bucket"
    content = await file.read()
    extension = os.path.splitext(file.filename)[1].lower()

    unique_name = f"{uuid.uuid4()}{extension}"

    file_path = f"{folder}/{unique_name}"

    supabase.storage.from_(bucket).upload(
        file_path,
        content,
        {
            "content-type": file.content_type,
            "cache-control": "no-cache",
            "upsert": False
        }
    )

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"
    public_url = f"{public_url}?v={uuid.uuid4()}"

    return public_url