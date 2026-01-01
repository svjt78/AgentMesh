"""
SSE Broadcaster - Real-time event streaming for workflow execution.

Demonstrates scalability patterns:
- Non-blocking event streaming
- Client connection management
- Event buffering for reconnections
- Clean resource cleanup
- Graceful disconnection handling
"""

import asyncio
import json
import logging
from typing import Dict, List, AsyncGenerator, Optional
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """
    Server-Sent Events broadcaster for real-time workflow updates.

    Manages multiple client connections per session and broadcasts events
    to all connected clients.

    Scalability patterns:
    - Event buffering (max 100 events per session)
    - Multiple concurrent client connections
    - Reconnection support via last_event_id
    - Automatic cleanup on completion
    """

    def __init__(self, max_buffer_size: int = 100):
        """
        Initialize SSE broadcaster.

        Args:
            max_buffer_size: Maximum events to buffer per session
        """
        self.max_buffer_size = max_buffer_size

        # Session-level event queues
        # Structure: {session_id: deque of events}
        self._session_buffers: Dict[str, deque] = {}

        # Active client queues
        # Structure: {session_id: [asyncio.Queue, ...]}
        self._client_queues: Dict[str, List[asyncio.Queue]] = {}

        # Session completion flags
        self._completed_sessions: Dict[str, bool] = {}

        logger.info("SSE Broadcaster initialized")

    async def subscribe(
        self,
        session_id: str,
        last_event_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to session events.

        Args:
            session_id: Session to subscribe to
            last_event_id: Last received event ID (for reconnection)

        Yields:
            SSE-formatted event strings

        Demonstrates: Client-specific async generator for streaming
        """
        logger.info(f"New SSE subscription: session_id={session_id}")

        # Create client queue
        client_queue: asyncio.Queue = asyncio.Queue()

        # Register client
        if session_id not in self._client_queues:
            self._client_queues[session_id] = []
        self._client_queues[session_id].append(client_queue)

        try:
            # Send buffered events if reconnecting
            if last_event_id and session_id in self._session_buffers:
                for buffered_event in self._session_buffers[session_id]:
                    if buffered_event.get("id", "") > last_event_id:
                        yield self._format_sse_event(buffered_event)

            # Stream new events
            while True:
                # Wait for next event
                event = await client_queue.get()

                # Check for completion signal
                if event is None:
                    logger.info(f"Stream complete for session {session_id}")
                    break

                # Send event
                yield self._format_sse_event(event)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        finally:
            # Unregister client
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
        event_id: Optional[str] = None
    ) -> None:
        """
        Broadcast event to all subscribers of a session.

        Args:
            session_id: Target session
            event_type: Event type
            event_data: Event data
            event_id: Optional event ID

        Demonstrates: Fan-out pattern for multiple clients
        """
        # Create event
        event = {
            "id": event_id or self._generate_event_id(),
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Buffer event
        if session_id not in self._session_buffers:
            self._session_buffers[session_id] = deque(maxlen=self.max_buffer_size)
        self._session_buffers[session_id].append(event)

        # Broadcast to all connected clients
        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(event)
                except Exception as e:
                    logger.error(f"Failed to send event to client: {e}")

    async def complete_session(self, session_id: str) -> None:
        """
        Signal session completion to all clients.

        Args:
            session_id: Session that completed

        Demonstrates: Graceful stream termination
        """
        logger.info(f"Completing session {session_id}")

        # Mark as completed
        self._completed_sessions[session_id] = True

        # Send completion signal (None) to all clients
        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(None)
                except Exception as e:
                    logger.error(f"Failed to send completion signal: {e}")

    def _format_sse_event(self, event: Dict) -> str:
        """
        Format event as SSE string.

        SSE format:
        id: <event_id>
        event: <event_type>
        data: <json_data>

        (blank line signals end of event)
        """
        lines = []

        if "id" in event:
            lines.append(f"id: {event['id']}")

        if "event" in event:
            lines.append(f"event: {event['event']}")

        if "data" in event:
            data_json = json.dumps(event["data"])
            lines.append(f"data: {data_json}")

        lines.append("")  # Empty line signals end of event

        return "\n".join(lines) + "\n"

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}"

    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up session resources.

        Call this after sufficient time has passed to allow clients to reconnect.

        Demonstrates: Resource management
        """
        if session_id in self._session_buffers:
            del self._session_buffers[session_id]

        if session_id in self._completed_sessions:
            del self._completed_sessions[session_id]

        logger.info(f"Cleaned up session {session_id}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get broadcaster statistics for observability.

        Returns:
            Dict with current stats
        """
        return {
            "active_sessions": len(self._session_buffers),
            "active_clients": sum(len(queues) for queues in self._client_queues.values()),
            "completed_sessions": len(self._completed_sessions)
        }


# Global broadcaster instance
_broadcaster: Optional[SSEBroadcaster] = None


def get_broadcaster() -> SSEBroadcaster:
    """Get singleton SSE broadcaster."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = SSEBroadcaster()
    return _broadcaster


def reset_broadcaster() -> None:
    """Reset broadcaster (for testing)."""
    global _broadcaster
    _broadcaster = None
