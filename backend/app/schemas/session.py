"""Pydantic schemas for session management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.document import DocumentOut


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class SessionCreateRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class SessionConfirmationRequest(BaseModel):
    stage: str
    decision: str
    comment: str | None = None


class SessionSummary(BaseModel):
    id: str
    status: str
    current_stage: str | None
    progress: float
    created_at: datetime
    expires_at: datetime | None
    last_activity_at: datetime

    model_config = {"from_attributes": True}


class SessionDetail(SessionSummary):
    config: dict[str, Any]
    documents: list[DocumentOut]

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    items: list[SessionSummary]
    pagination: PaginationMeta


class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    expires_at: datetime | None


class SessionResultsResponse(BaseModel):
    analysis: dict[str, Any] | str
    test_cases: dict[str, Any]
    statistics: dict[str, Any]
    version: int
    generated_at: datetime


class ExportRequest(BaseModel):
    result_version: int | None = None
