"""Redis client helper with fakeredis fallback for testing."""

from __future__ import annotations

import logging
from typing import Optional

from redis import RedisError
from redis.asyncio import Redis

try:  # pragma: no cover - optional dependency
    import fakeredis.aioredis as fakeredis  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback
    fakeredis = None


class InMemoryRedis:
    """Minimal async-compatible Redis substitute used for tests when fakeredis is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, list[str]] = {}
        self._kv: dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def rpush(self, key: str, value: str) -> None:
        self._store.setdefault(key, []).append(value)

    async def expire(self, key: str, _ttl: int) -> None:  # noqa: D401
        return

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        values = self._store.get(key, [])
        if end == -1:
            end = len(values)
        else:
            end = min(len(values), end + 1)
        return values[start:end]

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._kv[key] = value

    async def get(self, key: str) -> str | None:
        return self._kv.get(key)

from app.config import settings

logger = logging.getLogger(__name__)


def _create_client(url: str) -> Optional[Redis]:
    try:
        if url.startswith("fakeredis://"):
            logger.debug("Using fakeredis/in-memory client")
            if fakeredis is not None:
                return fakeredis.FakeRedis(decode_responses=True)
            return InMemoryRedis()
        return Redis.from_url(url, decode_responses=True)
    except RedisError as exc:  # pragma: no cover - defensive
        logger.warning("Failed to create Redis client: %s", exc)
        return None


redis = _create_client(settings.redis_url)


async def ping() -> bool:
    """Check if Redis client is available."""

    if redis is None:
        return False
    try:
        await redis.ping()
    except RedisError:
        return False
    except AttributeError:  # pragma: no cover - InMemory client
        return True
    return True
