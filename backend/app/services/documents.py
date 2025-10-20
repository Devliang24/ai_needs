"""Domain services for document handling."""

import hashlib
from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import document_repository


async def _write_upload_to_disk(file: UploadFile) -> Tuple[Path, str, int]:
    """Persist the uploaded file to disk and return (path, checksum, size)."""

    upload_dir = settings.resolved_upload_dir
    hasher = hashlib.sha256()
    size = 0
    safe_name = Path(file.filename or "upload").name
    temp_path = upload_dir / f"{safe_name}.{uuid4().hex}.part"

    try:
        with temp_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds maximum allowed size",
                    )
                hasher.update(chunk)
                buffer.write(chunk)

        checksum = hasher.hexdigest()
        final_path = upload_dir / checksum

        if final_path.exists():
            temp_path.unlink(missing_ok=True)
        else:
            temp_path.rename(final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return final_path, checksum, size


async def save_upload_file(file: UploadFile) -> Path:
    """Save uploaded file to disk and return the path."""
    path, _, _ = await _write_upload_to_disk(file)
    return path


async def handle_upload(
    db_session: AsyncSession,
    *,
    file: UploadFile,
) -> dict:
    """Store an uploaded file and persist the document metadata."""

    storage_path, checksum, size = await _write_upload_to_disk(file)

    existing = await document_repository.get_by_checksum(db_session, checksum)
    if existing:
        return {
            "document": existing,
            "is_duplicate": True,
        }

    document = await document_repository.create_document(
        db_session,
        original_name=file.filename,
        storage_path=storage_path,
        checksum=checksum,
        size=size,
    )
    return {
        "document": document,
        "is_duplicate": False,
    }
