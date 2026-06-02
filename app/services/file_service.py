"""
File upload service — validates type/size and persists to disk.
"""

import uuid
from pathlib import Path
from fastapi import UploadFile

from app.config import settings


async def save_upload_file(file: UploadFile, user_id: str) -> dict:
    original_name = file.filename or "uploaded_file"
    ext = (
        original_name.rsplit(".", 1)[-1].lower()
        if "." in original_name
        else ""
    )

    if ext not in settings.allowed_file_types:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Allowed: {sorted(settings.allowed_file_types)}"
        )

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File exceeds max size of {settings.max_file_size_mb} MB"
        )

    user_dir = Path(settings.upload_dir) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4()}_{original_name}"
    path = user_dir / safe_name
    path.write_bytes(content)

    return {
        "file_path": str(path),
        "file_name": original_name,
        "file_type": ext,
    }
