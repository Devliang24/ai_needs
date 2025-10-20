"""Repository helpers for Document persistence."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document, DocumentStatus


async def get_by_checksum(session: AsyncSession, checksum: str) -> Document | None:
    """Fetch a document record matching the checksum."""

    result = await session.execute(select(Document).where(Document.checksum == checksum))
    return result.scalar_one_or_none()


async def create_document(
    session: AsyncSession,
    *,
    original_name: str,
    storage_path: Path,
    checksum: str,
    size: int,
) -> Document:
    """Persist a new document record."""

    expires_at = datetime.utcnow() + timedelta(seconds=settings.session_ttl_seconds)
    document = Document(
        original_name=original_name,
        storage_path=str(storage_path),
        checksum=checksum,
        size=size,
        status=DocumentStatus.uploaded,
        expires_at=expires_at,
    )
    session.add(document)
    await session.flush()
    return document


async def mark_documents_expired(session: AsyncSession, document_ids: Iterable[str]) -> None:
    """Mark documents as expired. Used during cleanup flows."""

    if not document_ids:
        return
    stmt = (
        select(Document)
        .where(Document.id.in_(list(document_ids)))
    )
    result = await session.execute(stmt)
    for document in result.scalars():
        document.status = DocumentStatus.expired

