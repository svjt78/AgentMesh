"""
Storage service for JSONL event streams and JSON artifacts.

Provides thread-safe append-only JSONL logging for session events
and JSON artifact storage for Evidence Maps and other outputs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import fcntl


class SessionWriter:
    """Thread-safe JSONL writer for session event streams."""

    def __init__(self, storage_path: str = "/storage"):
        self.storage_path = Path(storage_path)
        self.sessions_path = self.storage_path / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self._locks = {}
        self._locks_lock = threading.Lock()

    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session JSONL file."""
        return self.sessions_path / f"{session_id}.jsonl"

    def _get_lock(self, session_id: str) -> threading.Lock:
        """Get or create lock for session file."""
        with self._locks_lock:
            if session_id not in self._locks:
                self._locks[session_id] = threading.Lock()
            return self._locks[session_id]

    def write_event(self, session_id: str, event: Dict[str, Any]) -> None:
        """
        Append event to session JSONL file (thread-safe).

        Args:
            session_id: Session identifier
            event: Event dictionary (will be serialized to JSON line)
        """
        lock = self._get_lock(session_id)
        session_file = self._get_session_file(session_id)

        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add session_id to event
        event["session_id"] = session_id

        with lock:
            # Use file locking for additional safety across processes
            with open(session_file, "a") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(event) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def read_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Read all events from a session JSONL file.

        Args:
            session_id: Session identifier

        Returns:
            List of event dictionaries in chronological order
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return []

        events = []
        with open(session_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        # Log error but continue reading
                        print(f"Error parsing JSONL line: {e}")
                        continue

        return events

    def session_exists(self, session_id: str) -> bool:
        """Check if session file exists."""
        return self._get_session_file(session_id).exists()

    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        return [f.stem for f in self.sessions_path.glob("*.jsonl")]


class ArtifactStore:
    """Store and retrieve JSON artifacts (Evidence Maps, etc.)."""

    def __init__(self, storage_path: str = "/storage"):
        self.storage_path = Path(storage_path)
        self.artifacts_path = self.storage_path / "artifacts"
        self.artifacts_path.mkdir(parents=True, exist_ok=True)

    def save_artifact(self, artifact_id: str, data: Dict[str, Any]) -> str:
        """
        Save artifact as JSON file.

        Args:
            artifact_id: Unique artifact identifier
            data: Artifact data (will be serialized to JSON)

        Returns:
            Path to saved artifact file
        """
        artifact_file = self.artifacts_path / f"{artifact_id}.json"

        # Add metadata
        artifact_data = {
            "artifact_id": artifact_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        with open(artifact_file, "w") as f:
            json.dump(artifact_data, f, indent=2)

        return str(artifact_file)

    def load_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Load artifact from JSON file.

        Args:
            artifact_id: Unique artifact identifier

        Returns:
            Artifact data dict or None if not found
        """
        artifact_file = self.artifacts_path / f"{artifact_id}.json"

        if not artifact_file.exists():
            return None

        with open(artifact_file, "r") as f:
            artifact_data = json.load(f)

        return artifact_data.get("data")

    def artifact_exists(self, artifact_id: str) -> bool:
        """Check if artifact exists."""
        return (self.artifacts_path / f"{artifact_id}.json").exists()

    def list_artifacts(self) -> List[str]:
        """List all artifact IDs."""
        return [f.stem for f in self.artifacts_path.glob("*.json")]


# Singleton instances (initialized in main app)
_session_writer: Optional[SessionWriter] = None
_artifact_store: Optional[ArtifactStore] = None


def init_storage(storage_path: str = "/storage"):
    """Initialize storage services."""
    global _session_writer, _artifact_store
    _session_writer = SessionWriter(storage_path)
    _artifact_store = ArtifactStore(storage_path)


def get_session_writer() -> SessionWriter:
    """Get singleton SessionWriter instance."""
    if _session_writer is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _session_writer


def get_artifact_store() -> ArtifactStore:
    """Get singleton ArtifactStore instance."""
    if _artifact_store is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _artifact_store
