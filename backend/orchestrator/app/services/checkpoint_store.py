"""
Checkpoint Store

Disk persistence for checkpoint instances.
Follows same JSONL pattern as SessionWriter for consistency.
"""

import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from app.models.checkpoint_models import CheckpointInstance, CheckpointStatus
from app.config import get_config


class CheckpointStore:
    """
    Persistent storage for checkpoint instances.

    Uses JSON files for individual checkpoints and JSONL indexes for fast lookups.
    """

    def __init__(self, storage_path: str = "storage"):
        """
        Initialize checkpoint store.

        Args:
            storage_path: Base storage directory
        """
        self.base_path = Path(storage_path)
        self.checkpoints_path = self.base_path / "checkpoints"
        self.index_path = self.checkpoints_path / "index"

        # Create directories
        self.checkpoints_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: CheckpointInstance) -> None:
        """
        Save checkpoint to disk.

        Args:
            checkpoint: Checkpoint instance to save
        """
        # Save individual checkpoint file
        checkpoint_file = self.checkpoints_path / f"{checkpoint.checkpoint_instance_id}.json"

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint.model_dump(), f, indent=2)

        # Update indexes
        self._update_pending_index(checkpoint)
        self._update_session_index(checkpoint)

    def load_checkpoint(self, checkpoint_instance_id: str) -> Optional[CheckpointInstance]:
        """
        Load checkpoint from disk.

        Args:
            checkpoint_instance_id: Checkpoint instance ID

        Returns:
            CheckpointInstance if found, None otherwise
        """
        checkpoint_file = self.checkpoints_path / f"{checkpoint_instance_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
                return CheckpointInstance(**data)
        except Exception as e:
            print(f"Error loading checkpoint {checkpoint_instance_id}: {e}")
            return None

    def list_pending_checkpoints(self) -> List[CheckpointInstance]:
        """
        List all pending checkpoints.

        Returns:
            List of pending checkpoint instances
        """
        pending_index_file = self.index_path / "pending.jsonl"

        if not pending_index_file.exists():
            return []

        checkpoints = []

        try:
            with open(pending_index_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            checkpoint_id = json.loads(line.strip())["checkpoint_instance_id"]
                            checkpoint = self.load_checkpoint(checkpoint_id)
                            if checkpoint and checkpoint.status == CheckpointStatus.PENDING:
                                checkpoints.append(checkpoint)
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error reading pending index: {e}")

        return checkpoints

    def list_session_checkpoints(self, session_id: str) -> List[CheckpointInstance]:
        """
        List all checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint instances for session
        """
        session_index_file = self.index_path / f"by_session_{session_id}.jsonl"

        if not session_index_file.exists():
            return []

        checkpoints = []

        try:
            with open(session_index_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            checkpoint_id = json.loads(line.strip())["checkpoint_instance_id"]
                            checkpoint = self.load_checkpoint(checkpoint_id)
                            if checkpoint:
                                checkpoints.append(checkpoint)
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error reading session index for {session_id}: {e}")

        return checkpoints

    def delete_checkpoint(self, checkpoint_instance_id: str) -> bool:
        """
        Delete checkpoint from disk.

        Args:
            checkpoint_instance_id: Checkpoint instance ID

        Returns:
            True if deleted, False if not found
        """
        checkpoint_file = self.checkpoints_path / f"{checkpoint_instance_id}.json"

        if checkpoint_file.exists():
            os.remove(checkpoint_file)
            return True

        return False

    def _update_pending_index(self, checkpoint: CheckpointInstance) -> None:
        """
        Update pending checkpoints index.

        Args:
            checkpoint: Checkpoint instance
        """
        pending_index_file = self.index_path / "pending.jsonl"

        # If checkpoint is pending, add to index
        if checkpoint.status == CheckpointStatus.PENDING:
            with open(pending_index_file, 'a') as f:
                index_entry = {
                    "checkpoint_instance_id": checkpoint.checkpoint_instance_id,
                    "session_id": checkpoint.session_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "required_role": checkpoint.required_role,
                    "created_at": checkpoint.created_at
                }
                f.write(json.dumps(index_entry) + '\n')
        else:
            # If resolved/timeout/cancelled, rebuild index without this checkpoint
            self._rebuild_pending_index()

    def _update_session_index(self, checkpoint: CheckpointInstance) -> None:
        """
        Update session checkpoints index.

        Args:
            checkpoint: Checkpoint instance
        """
        session_index_file = self.index_path / f"by_session_{checkpoint.session_id}.jsonl"

        # Append to session index (we keep all checkpoints, regardless of status)
        with open(session_index_file, 'a') as f:
            index_entry = {
                "checkpoint_instance_id": checkpoint.checkpoint_instance_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "status": checkpoint.status.value,
                "created_at": checkpoint.created_at
            }
            f.write(json.dumps(index_entry) + '\n')

    def _rebuild_pending_index(self) -> None:
        """
        Rebuild pending checkpoints index.

        Scans all checkpoint files and rebuilds index with only pending checkpoints.
        """
        pending_index_file = self.index_path / "pending.jsonl"

        # Remove existing index
        if pending_index_file.exists():
            os.remove(pending_index_file)

        # Scan all checkpoint files
        for checkpoint_file in self.checkpoints_path.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    if data.get("status") == "pending":
                        with open(pending_index_file, 'a') as idx_f:
                            index_entry = {
                                "checkpoint_instance_id": data["checkpoint_instance_id"],
                                "session_id": data["session_id"],
                                "checkpoint_id": data["checkpoint_id"],
                                "required_role": data["required_role"],
                                "created_at": data["created_at"]
                            }
                            idx_f.write(json.dumps(index_entry) + '\n')
            except Exception:
                continue


# Singleton instance
_checkpoint_store: Optional[CheckpointStore] = None


def get_checkpoint_store(storage_path: Optional[str] = None) -> CheckpointStore:
    """
    Get singleton checkpoint store instance.

    Args:
        storage_path: Base storage directory (defaults to config value)

    Returns:
        CheckpointStore instance
    """
    global _checkpoint_store
    if _checkpoint_store is None:
        if storage_path is None:
            config = get_config()
            storage_path = config.storage_path
        _checkpoint_store = CheckpointStore(storage_path)
    return _checkpoint_store
