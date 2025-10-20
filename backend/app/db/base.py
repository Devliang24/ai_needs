"""Database session and base declarative configuration."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy models."""


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a unit of work."""

    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:  # noqa: BLE001
        await session.rollback()
        raise
    else:
        await session.commit()
    finally:
        await session.close()
