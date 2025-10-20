"""Session lifecycle endpoints."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import (
    PaginationMeta,
    SessionConfirmationRequest,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetail,
    SessionListResponse,
    SessionResultsResponse,
    SessionSummary,
)
from app.services import sessions as session_service
from app.orchestrator import workflow

router = APIRouter()


def _to_session_summary(db_obj) -> SessionSummary:
    return SessionSummary.model_validate(db_obj)


def _to_session_detail(db_obj) -> SessionDetail:
    data = SessionDetail.model_validate(db_obj)
    return data


@router.post("", summary="Create an analysis session", response_model=SessionCreateResponse)
async def create_session(
    payload: SessionCreateRequest,
    db_session: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> SessionCreateResponse:
    session = await session_service.create_session(
        db_session,
        document_ids=payload.document_ids,
        config=payload.config,
        created_by=payload.created_by,
    )
    await workflow.launch(session.id)
    return SessionCreateResponse(
        session_id=session.id,
        status=session.status.value,
        expires_at=session.expires_at,
    )


@router.get("", summary="List sessions", response_model=SessionListResponse)
async def list_sessions(
    db_session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
) -> SessionListResponse:
    items, total = await session_service.list_sessions(
        db_session,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )

    summaries = [_to_session_summary(item) for item in items]
    pagination = PaginationMeta(page=page, page_size=page_size, total=total)
    return SessionListResponse(items=summaries, pagination=pagination)


@router.get("/{session_id}", summary="Get session detail", response_model=SessionDetail)
async def get_session_detail(
    session_id: str,
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionDetail:
    session = await session_service.get_session(db_session, session_id)
    return _to_session_detail(session)


@router.post(
    "/{session_id}/confirm",
    summary="Submit human confirmation to advance workflow",
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_session(
    session_id: str,
    payload: SessionConfirmationRequest,
    db_session: Annotated[AsyncSession, Depends(get_db)],
):
    session = await session_service.advance_session(
        db_session,
        session_id=session_id,
        decision=payload.decision,
        comment=payload.comment,
    )
    return {
        "status": session.status.value,
        "next_stage": session.current_stage.value if session.current_stage else None,
    }


@router.get(
    "/{session_id}/results",
    summary="Fetch latest session results",
    response_model=SessionResultsResponse,
)
async def get_session_results(
    session_id: str,
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResultsResponse:
    session = await session_service.get_session(db_session, session_id)
    if not session.results:
        return SessionResultsResponse(
            analysis={},
            test_cases={},
            statistics={},
            version=0,
            generated_at=session.created_at,
        )
    latest = max(session.results, key=lambda res: res.version)
    return SessionResultsResponse(
        analysis=latest.summary,
        test_cases=latest.test_cases,
        statistics=latest.metrics,
        version=latest.version,
        generated_at=latest.created_at,
    )
