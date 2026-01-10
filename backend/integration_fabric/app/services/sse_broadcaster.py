import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    def __init__(self, max_buffer_size: int = 100) -> None:
        self.max_buffer_size = max_buffer_size
        self._session_buffers: Dict[str, deque] = {}
        self._client_queues: Dict[str, List[asyncio.Queue]] = {}
        self._completed_sessions: Dict[str, bool] = {}

    async def subscribe(
        self,
        session_id: str,
        last_event_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        client_queue: asyncio.Queue = asyncio.Queue()
        if session_id not in self._client_queues:
            self._client_queues[session_id] = []
        self._client_queues[session_id].append(client_queue)

        try:
            if session_id in self._session_buffers:
                for buffered_event in self._session_buffers[session_id]:
                    if last_event_id:
                        if buffered_event.get("id", "") > last_event_id:
                            yield self._format_sse_event(buffered_event)
                    else:
                        yield self._format_sse_event(buffered_event)

            if self._completed_sessions.get(session_id):
                return

            while True:
                event = await client_queue.get()
                if event is None:
                    break
                yield self._format_sse_event(event)
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled for run %s", session_id)
        finally:
            if session_id in self._client_queues:
                try:
                    self._client_queues[session_id].remove(client_queue)
                    if not self._client_queues[session_id]:
                        del self._client_queues[session_id]
                except ValueError:
                    pass

    async def broadcast_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict,
        event_id: Optional[str] = None,
    ) -> None:
        event = {
            "id": event_id or self._generate_event_id(),
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if session_id not in self._session_buffers:
            self._session_buffers[session_id] = deque(maxlen=self.max_buffer_size)
        self._session_buffers[session_id].append(event)

        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(event)
                except Exception as exc:
                    logger.error("Failed to send event: %s", exc)

    async def complete_session(self, session_id: str) -> None:
        self._completed_sessions[session_id] = True
        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(None)
                except Exception as exc:
                    logger.error("Failed to complete stream: %s", exc)

    def cleanup_session(self, session_id: str) -> None:
        if session_id in self._session_buffers:
            del self._session_buffers[session_id]
        if session_id in self._completed_sessions:
            del self._completed_sessions[session_id]

    def _format_sse_event(self, event: Dict) -> str:
        lines = []
        if "id" in event:
            lines.append(f"id: {event['id']}")
        if "event" in event:
            lines.append(f"event: {event['event']}")
        if "data" in event:
            lines.append(f"data: {json.dumps(event['data'])}")
        lines.append("")
        return "\n".join(lines) + "\n"

    def _generate_event_id(self) -> str:
        import uuid

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}"


_broadcaster: Optional[SSEBroadcaster] = None


def get_broadcaster() -> SSEBroadcaster:
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = SSEBroadcaster()
    return _broadcaster
