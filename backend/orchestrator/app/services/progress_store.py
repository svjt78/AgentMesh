"""
ProgressStore - Thread-safe in-memory event buffer for real-time SSE streaming.

Pattern: ClaimSense AI polling-based approach

Demonstrates:
- Thread-safe concurrent access from sync orchestrator and async SSE
- Delta streaming (send only new events)
- Memory-bounded storage (auto-trim old events)
- Session lifecycle management
"""

from threading import Lock
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class SessionProgress(BaseModel):
    """Progress tracking for a workflow session"""
    session_id: str
    workflow_id: str
    status: str  # "running", "completed", "error"
    created_at: str
    updated_at: str
    events: List[Dict] = []  # All logged events
    current_agent: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ProgressStore:
    """
    Thread-safe in-memory store for session progress.

    Provides real-time event streaming via polling pattern:
    - Orchestrator writes events synchronously
    - SSE endpoint polls for new events asynchronously
    - No callbacks or async bridge needed
    """

    def __init__(self, max_events_per_session: int = 200):
        """
        Initialize progress store.

        Args:
            max_events_per_session: Maximum events to keep per session (auto-trim oldest)
        """
        self._sessions: Dict[str, SessionProgress] = {}
        self._lock = Lock()  # Thread-safe access
        self.max_events = max_events_per_session

    def create_session(self, session_id: str, workflow_id: str) -> None:
        """
        Initialize session progress tracking.

        Args:
            session_id: Unique session identifier
            workflow_id: Workflow being executed
        """
        with self._lock:
            self._sessions[session_id] = SessionProgress(
                session_id=session_id,
                workflow_id=workflow_id,
                status="running",
                created_at=datetime.utcnow().isoformat() + "Z",
                updated_at=datetime.utcnow().isoformat() + "Z",
                events=[]
            )

    def add_event(self, session_id: str, event: Dict) -> None:
        """
        Add event to session (called by orchestrator/agents).

        Args:
            event: Event dictionary with event_type, timestamp, etc.

        Thread-safe: Can be called from sync orchestrator running in thread pool
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.events.append(event)
                session.updated_at = datetime.utcnow().isoformat() + "Z"

                # Extract current agent from event if present
                if event.get("event_type") == "agent_invocation_started":
                    session.current_agent = event.get("agent_id")
                elif event.get("event_type") in ["agent_invocation_completed", "agent_invocation_error", "agent_invocation_incomplete"]:
                    session.current_agent = None

                # Trim if exceeds max (keep most recent events)
                if len(session.events) > self.max_events:
                    session.events = session.events[-self.max_events:]

    def update_status(self, session_id: str, status: str) -> None:
        """
        Update session status.

        Args:
            session_id: Session to update
            status: New status ("running", "completed", "error")
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = status
                self._sessions[session_id].updated_at = datetime.utcnow().isoformat() + "Z"

    def get_session_progress(self, session_id: str) -> Optional[SessionProgress]:
        """
        Get session progress (called by SSE endpoint).

        Args:
            session_id: Session to retrieve

        Returns:
            SessionProgress if exists, None otherwise

        Thread-safe: Can be called from async SSE endpoint while orchestrator writes
        """
        with self._lock:
            session = self._sessions.get(session_id)
            # Return a copy to avoid external mutations
            if session:
                return SessionProgress(**session.dict())
            return None

    def cleanup_session(self, session_id: str) -> None:
        """
        Remove session from memory (after SSE disconnect + delay).

        Args:
            session_id: Session to cleanup
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def get_stats(self) -> Dict:
        """
        Get store statistics for observability.

        Returns:
            Dict with active_sessions, total_events
        """
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "total_events": sum(len(s.events) for s in self._sessions.values())
            }


# Singleton instance
_progress_store: Optional[ProgressStore] = None


def get_progress_store() -> ProgressStore:
    """Get singleton progress store instance."""
    global _progress_store
    if _progress_store is None:
        _progress_store = ProgressStore()
    return _progress_store


def reset_progress_store() -> None:
    """Reset progress store (for testing)."""
    global _progress_store
    _progress_store = None
