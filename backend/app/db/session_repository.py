"""Repository helpers for analysis sessions."""

from datetime import datetime, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.document import Document
from app.models.session import AgentStage, Session, SessionResult, SessionStatus


async def create_session(
    session: AsyncSession,
    *,
    document_ids: list[str],
    config: dict,
    created_by: str | None = None,
) -> Session:
    """Create a session and attach documents."""

    expires_at = datetime.utcnow() + timedelta(seconds=settings.session_ttl_seconds)
    result = await session.execute(
        select(Document).where(Document.id.in_(document_ids))
    )
    documents = list(result.scalars().unique())

    analysis_session = Session(
        status=SessionStatus.created,
        config=config,
        created_by=created_by,
        expires_at=expires_at,
        last_activity_at=datetime.utcnow(),
        current_stage=AgentStage.requirement_analysis,
        documents=documents,
    )
    session.add(analysis_session)
    await session.flush()
    return analysis_session


async def get_session(session: AsyncSession, session_id: str) -> Session | None:
    """Fetch a session by identifier with related documents and latest result."""

    stmt: Select[tuple[Session]] = (
        select(Session)
        .options(
            selectinload(Session.documents),
            selectinload(Session.results),
        )
        .where(Session.id == session_id)
    )
    result = await session.execute(stmt)
    session_obj = result.scalar_one_or_none()
    if session_obj and session_obj.results:
        session_obj.results.sort(key=lambda res: res.version, reverse=True)
    return session_obj


async def list_sessions(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: SessionStatus | None = None,
) -> tuple[list[Session], int]:
    """Return paginated sessions with optional status filter."""

    stmt: Select[tuple[Session]] = select(Session).order_by(Session.created_at.desc())
    count_stmt = select(func.count(Session.id))

    if status:
        stmt = stmt.where(Session.status == status)
        count_stmt = count_stmt.where(Session.status == status)

    total = (await session.execute(count_stmt)).scalar_one()
    offset = max(page - 1, 0) * page_size
    result = await session.execute(stmt.offset(offset).limit(page_size))
    return list(result.scalars().unique()), total


async def add_session_result(
    session: AsyncSession,
    *,
    session_id: str,
    summary: dict,
    payload: dict,
    metrics: dict,
    stage: AgentStage | None = None,
    progress: float | None = None,
) -> SessionResult:
    """Persist a session result snapshot."""

    db_session = await get_session(session, session_id)
    if db_session is None:
        raise ValueError("Session not found")

    next_version = 1
    if db_session.results:
        next_version = max(result.version for result in db_session.results) + 1

    result_record = SessionResult(
        session=db_session,
        version=next_version,
        summary=summary,
        test_cases=payload,
        metrics=metrics,
    )
    session.add(result_record)
    db_session.status = SessionStatus.completed
    if stage is not None:
        db_session.current_stage = stage
    if progress is not None:
        db_session.progress = progress
    db_session.last_activity_at = datetime.utcnow()
    await session.flush()
    return result_record


async def update_session_status(
    session: AsyncSession,
    *,
    session_id: str,
    from_status: SessionStatus | None,
    to_status: SessionStatus,
    stage: AgentStage | None = None,
    progress: float | None = None,
) -> Session | None:
    """Transition a session to a new status when preconditions pass."""

    db_session = await get_session(session, session_id)
    if db_session is None:
        return None
    if from_status and db_session.status != from_status:
        return None

    db_session.status = to_status
    if stage is not None:
        db_session.current_stage = stage
    if progress is not None:
        db_session.progress = progress
    db_session.last_activity_at = datetime.utcnow()
    await session.flush()
    return db_session
