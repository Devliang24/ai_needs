"""Pydantic schemas for document resources."""

from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    original_name: str
    storage_path: str
    checksum: str
    size: int
    status: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    is_duplicate: bool = False

