import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator

from publisher_support.models.events import AuditEvent, ClientMessage


class EventBroadcaster:
    """In-memory pub/sub for SSE per case_id."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, case_id: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._queues[case_id].append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                if queue in self._queues[case_id]:
                    self._queues[case_id].remove(queue)

    async def publish(self, case_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._queues.get(case_id, []))
        for queue in queues:
            await queue.put(payload)

    async def emit_audit(self, case_id: str, event: AuditEvent) -> None:
        await self.publish(case_id, event.to_sse())

    async def emit_client_message(self, case_id: str, message: ClientMessage) -> None:
        await self.publish(
            case_id,
            {"event": "client_message", "data": message.model_dump(mode="json")},
        )


broadcaster = EventBroadcaster()
