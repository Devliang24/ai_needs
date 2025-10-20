"""Utilities for database initialisation at application startup."""

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base, engine


async def init_models(db_engine: AsyncEngine | None = None) -> None:
    """Create database tables if they do not exist."""

    engine_to_use = db_engine or engine
    async with engine_to_use.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

