"""Domain services for session lifecycle."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session_repository
from app.models.session import AgentStage, Session, SessionStatus


async def create_session(
    db_session: AsyncSession,
    *,
    document_ids: list[str],
    config: dict[str, Any],
    created_by: str | None,
) -> Session:
    if not document_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one document is required")

    session = await session_repository.create_session(
        db_session,
        document_ids=document_ids,
        config=config,
        created_by=created_by,
    )

    if len(session.documents) != len(document_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more documents not found")

    return session


async def get_session(db_session: AsyncSession, session_id: str) -> Session:
    session = await session_repository.get_session(db_session, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


async def list_sessions(
    db_session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> tuple[list[Session], int]:
    status_value = None
    if status_filter:
        try:
            status_value = SessionStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status filter") from exc
    sessions, total = await session_repository.list_sessions(
        db_session,
        page=page,
        page_size=page_size,
        status=status_value,
    )
    return sessions, total


async def advance_session(
    db_session: AsyncSession,
    *,
    session_id: str,
    decision: str,
    comment: str | None,
) -> Session:
    session = await session_repository.get_session(db_session, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    if session.status != SessionStatus.awaiting_confirmation:
        raise HTTPException(status.HTTP_409_CONFLICT, "Session not awaiting confirmation")

    next_stage = AgentStage.test_generation
    await session_repository.update_session_status(
        db_session,
        session_id=session_id,
        from_status=SessionStatus.awaiting_confirmation,
        to_status=SessionStatus.processing,
        stage=next_stage,
        progress=0.5,
    )

    confirmations = list(session.config.get("confirmations", []))
    confirmations.append({"decision": decision, "comment": comment})
    session.config["confirmations"] = confirmations
    await db_session.flush()
    return session
