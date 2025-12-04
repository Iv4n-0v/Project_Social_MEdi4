import os
import uuid
from supabase import create_client
from fastapi import UploadFile

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def upload_to_bucket(file: UploadFile, folder: str = "users", bucket: str = "bucket"):
    try:
        content = await file.read()
        extension = os.path.splitext(file.filename)[1].lower()
        unique_name = f"{uuid.uuid4()}{extension}"
        file_path = f"{folder}/{unique_name}"
        response = supabase.storage.from_(bucket).upload(
            file_path,
            content,
            {
                "content-type": file.content_type,
                "cache-control": "3600",
                "upsert": False
            }
        )
        if hasattr(response, "error") and response.error is not None:
            raise Exception(response.error.message)
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"

        return public_url

    except Exception as e:
        print("Upload error:", str(e))
        return None