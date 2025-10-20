"""Endpoints for document upload and registration."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import DocumentUploadResponse
from app.services import documents

router = APIRouter()


@router.post("", summary="Upload a requirement document", response_model=DocumentUploadResponse)
async def upload_document(
    file: Annotated[UploadFile, File(description="Requirement document file")],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentUploadResponse:
    """Persist the uploaded document and return metadata."""

    result = await documents.handle_upload(db_session, file=file)
    return DocumentUploadResponse(document=result["document"], is_duplicate=result["is_duplicate"])

