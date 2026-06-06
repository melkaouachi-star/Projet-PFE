"""In-process pub/sub broker for dashboard WebSocket and SSE clients."""
from __future__ import annotations

import asyncio
import json
from collections import deque
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator


class EventBroker:
    def __init__(self, replay_size: int = 250):
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._recent: deque[dict[str, Any]] = deque(maxlen=replay_size)

    async def publish(self, event: dict[str, Any]) -> None:
        self._recent.appendleft(event)
        dead: list[asyncio.Queue[dict[str, Any]]] = []
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)
        for queue in dead:
            self._subscribers.discard(queue)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._recent)[:limit]

    @asynccontextmanager
    async def subscribe(self, replay: int = 25) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        for event in reversed(self.recent(replay)):
            await queue.put(event)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)


def sse_pack(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


_BROKER = EventBroker()


def get_broker() -> EventBroker:
    return _BROKER

