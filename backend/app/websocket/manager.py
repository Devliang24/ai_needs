"""Manage active WebSocket connections per session."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[session_id].add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            websockets = self._connections.get(session_id)
            if websockets and websocket in websockets:
                websockets.remove(websocket)
            if websockets and not websockets:
                self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, message: dict) -> None:
        async with self._lock:
            targets = list(self._connections.get(session_id, set()))

        disconnected: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_json(message)
            except RuntimeError:
                disconnected.append(websocket)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                for websocket in disconnected:
                    self._connections.get(session_id, set()).discard(websocket)


manager = ConnectionManager()

