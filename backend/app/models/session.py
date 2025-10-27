"""Session and related ORM models."""

import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict

from app.db.base import Base
from app.models.document import Document


class SessionStatus(str, enum.Enum):
    """Processing status for an analysis session."""

    created = "created"
    processing = "processing"
    awaiting_confirmation = "awaiting_confirmation"
    awaiting_review = "awaiting_review"
    completed = "completed"
    failed = "failed"
    archived = "archived"
    expired = "expired"


session_documents = Table(
    "session_documents",
    Base.metadata,
    Column("session_id", String(36), ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)


class AgentStage(str, enum.Enum):
    """Stages executed by the agent workflow."""

    requirement_analysis = "requirement_analysis"
    confirmation = "confirmation"
    test_generation = "test_generation"
    test_completion = "test_completion"
    review = "review"
    completed = "completed"


class Session(Base):
    """Persisted analysis session."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), default=SessionStatus.created
    )
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )

    documents: Mapped[list[Document]] = relationship(
        "Document",
        secondary=session_documents,
        lazy="selectin",
    )
    runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    results: Mapped[list["SessionResult"]] = relationship(
        "SessionResult",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    current_stage: Mapped[Optional[AgentStage]] = mapped_column(
        Enum(AgentStage, name="agent_stage"), nullable=True
    )
    progress: Mapped[float] = mapped_column(default=0.0)


class AgentRun(Base):
    """Audit trail of individual agent executions."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), index=True
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    stage: Mapped[AgentStage] = mapped_column(Enum(AgentStage, name="agent_stage_enum"))
    payload: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))
    error: Mapped[Optional[str]] = mapped_column(Text)

    session: Mapped[Session] = relationship("Session", back_populates="runs", lazy="joined")


class SessionResult(Base):
    """Persisted snapshots of agent output to support exports/history."""

    __tablename__ = "session_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), index=True
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(default=1)
    summary: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    test_cases: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    metrics: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )

    session: Mapped[Session] = relationship("Session", back_populates="results", lazy="joined")
