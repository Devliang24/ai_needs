"""Export endpoints for session results."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.exporters import generate_excel_bytes, generate_xmind_bytes
from app.schemas import ExportRequest
from app.services import sessions as session_service

router = APIRouter()


def _select_result(session, version: int | None):
    if not session.results:
        raise HTTPException(status.HTTP_409_CONFLICT, "No generated results to export")
    if version is None:
        return max(session.results, key=lambda item: item.version)
    for item in session.results:
        if item.version == version:
            return item
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Result version not found")


@router.post("/{session_id}/exports/xmind", summary="Export session results to XMind")
async def export_xmind(
    session_id: str,
    payload: ExportRequest,
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    session = await session_service.get_session(db_session, session_id)
    result = _select_result(session, payload.result_version)
    file_bytes = generate_xmind_bytes(session_id, result.test_cases)
    filename = f"session-{session_id}.xmind"
    return StreamingResponse(
        iter([file_bytes]),
        media_type="application/vnd.xmind.workbook",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{session_id}/exports/excel", summary="Export session results to Excel")
async def export_excel(
    session_id: str,
    payload: ExportRequest,
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    session = await session_service.get_session(db_session, session_id)
    result = _select_result(session, payload.result_version)
    file_bytes = generate_excel_bytes(result.test_cases)
    filename = f"session-{session_id}.xlsx"
    return StreamingResponse(
        iter([file_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

