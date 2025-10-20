"""Helpers for storing and retrieving session events in Redis."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from redis import RedisError

from app.cache.redis_client import redis
from app.config import settings


def _events_key(session_id: str) -> str:
    return f"session:{session_id}:events"


def _status_key(session_id: str) -> str:
    return f"session:{session_id}:status"


def _confirmation_key(session_id: str) -> str:
    return f"session:{session_id}:confirmation"


_memory_events: dict[str, list[Dict[str, Any]]] = {}
_memory_status: dict[str, Dict[str, Any]] = {}
_memory_confirmations: dict[str, Dict[str, Any]] = {}


async def append_event(session_id: str, event: Dict[str, Any]) -> None:
    if redis is None:
        _memory_events.setdefault(session_id, []).append(event)
        return
    try:
        payload = json.dumps(event)
        await redis.rpush(_events_key(session_id), payload)
        await redis.expire(_events_key(session_id), settings.session_ttl_seconds * 2)
    except RedisError:  # pragma: no cover - ignore cache errors
        _memory_events.setdefault(session_id, []).append(event)
        return


async def fetch_events(session_id: str) -> List[Dict[str, Any]]:
    if redis is None:
        return _memory_events.get(session_id, [])
    try:
        raw_events = await redis.lrange(_events_key(session_id), 0, -1)
        return [json.loads(item) for item in raw_events]
    except RedisError:
        return _memory_events.get(session_id, [])


async def set_status(session_id: str, status: Dict[str, Any]) -> None:
    if redis is None:
        _memory_status[session_id] = status
        return
    try:
        await redis.set(_status_key(session_id), json.dumps(status), ex=settings.session_ttl_seconds * 2)
    except RedisError:
        _memory_status[session_id] = status
        return


async def get_status(session_id: str) -> Dict[str, Any] | None:
    if redis is None:
        return _memory_status.get(session_id)
    try:
        raw = await redis.get(_status_key(session_id))
        return json.loads(raw) if raw else None
    except RedisError:
        return _memory_status.get(session_id)


async def set_confirmation(session_id: str, confirmation: Dict[str, Any]) -> None:
    """Store confirmation data from user."""
    if redis is None:
        _memory_confirmations[session_id] = confirmation
        return
    try:
        await redis.set(_confirmation_key(session_id), json.dumps(confirmation), ex=settings.session_ttl_seconds)
    except RedisError:
        _memory_confirmations[session_id] = confirmation
        return


async def get_confirmation(session_id: str) -> Dict[str, Any] | None:
    """Retrieve confirmation data."""
    if redis is None:
        return _memory_confirmations.get(session_id)
    try:
        raw = await redis.get(_confirmation_key(session_id))
        return json.loads(raw) if raw else None
    except RedisError:
        return _memory_confirmations.get(session_id)


async def clear_confirmation(session_id: str) -> None:
    """Clear confirmation data after processing."""
    if redis is None:
        _memory_confirmations.pop(session_id, None)
        return
    try:
        await redis.delete(_confirmation_key(session_id))
    except RedisError:
        _memory_confirmations.pop(session_id, None)
        return
