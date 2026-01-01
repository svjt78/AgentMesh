"""
Checkpoint Manager

Thread-safe in-memory state management for active checkpoints.
Handles creation, resolution, timeout checking, and role-based filtering.
"""

import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from app.models.checkpoint_models import (
    CheckpointInstance,
    CheckpointConfig,
    CheckpointResolution,
    CheckpointStatus,
    CheckpointType
)
from app.services.checkpoint_store import get_checkpoint_store

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Thread-safe checkpoint state manager.

    Manages active checkpoint instances in memory with background timeout checking.
    """

    def __init__(self):
        """Initialize checkpoint manager"""
        self._checkpoints: Dict[str, CheckpointInstance] = {}
        self._lock = threading.Lock()
        self._session_checkpoints: Dict[str, List[str]] = {}  # session_id -> checkpoint_instance_ids

        # Checkpoint store for persistence
        self.checkpoint_store = get_checkpoint_store()

        # Load existing pending checkpoints from disk into memory
        self._load_pending_checkpoints_from_disk()

        # Start background timeout checker
        self._timeout_thread = threading.Thread(
            target=self._timeout_checker_loop,
            daemon=True
        )
        self._timeout_thread.start()

        logger.info("CheckpointManager initialized with background timeout checker")

    def _load_pending_checkpoints_from_disk(self) -> None:
        """Load all pending checkpoints from disk into memory on initialization."""
        try:
            pending_checkpoints = self.checkpoint_store.list_pending_checkpoints()
            for checkpoint in pending_checkpoints:
                self._checkpoints[checkpoint.checkpoint_instance_id] = checkpoint

                # Update session checkpoint index
                if checkpoint.session_id not in self._session_checkpoints:
                    self._session_checkpoints[checkpoint.session_id] = []
                self._session_checkpoints[checkpoint.session_id].append(checkpoint.checkpoint_instance_id)

            if pending_checkpoints:
                logger.info(f"Loaded {len(pending_checkpoints)} pending checkpoints from disk")
        except Exception as e:
            logger.error(f"Error loading pending checkpoints from disk: {e}", exc_info=True)

    def create_checkpoint(
        self,
        session_id: str,
        workflow_id: str,
        checkpoint_config: CheckpointConfig,
        context_data: Dict[str, Any]
    ) -> CheckpointInstance:
        """
        Create new checkpoint instance.

        Args:
            session_id: Workflow session ID
            workflow_id: Workflow type
            checkpoint_config: Checkpoint configuration from registry
            context_data: Context data for UI display

        Returns:
            Created checkpoint instance
        """
        # Generate unique instance ID
        checkpoint_instance_id = f"cp_{uuid.uuid4().hex[:12]}"

        # Calculate timeout timestamp
        timeout_at = None
        if checkpoint_config.timeout_config.enabled and checkpoint_config.timeout_config.timeout_seconds:
            timeout_at = (
                datetime.utcnow() +
                timedelta(seconds=checkpoint_config.timeout_config.timeout_seconds)
            ).isoformat() + "Z"

        # Create checkpoint instance
        checkpoint = CheckpointInstance(
            checkpoint_instance_id=checkpoint_instance_id,
            session_id=session_id,
            workflow_id=workflow_id,
            checkpoint_id=checkpoint_config.checkpoint_id,
            checkpoint_type=checkpoint_config.checkpoint_type,
            checkpoint_name=checkpoint_config.checkpoint_name,
            description=checkpoint_config.description,
            status=CheckpointStatus.PENDING,
            created_at=datetime.utcnow().isoformat() + "Z",
            timeout_at=timeout_at,
            resolved_at=None,
            resolution=None,
            context_data=context_data,
            required_role=checkpoint_config.required_role,
            on_timeout=checkpoint_config.timeout_config.on_timeout if checkpoint_config.timeout_config.enabled else None,
            ui_schema=checkpoint_config.ui_schema
        )

        # Store in memory
        with self._lock:
            self._checkpoints[checkpoint_instance_id] = checkpoint

            # Track session checkpoints
            if session_id not in self._session_checkpoints:
                self._session_checkpoints[session_id] = []
            self._session_checkpoints[session_id].append(checkpoint_instance_id)

        # Persist to disk
        self.checkpoint_store.save_checkpoint(checkpoint)

        logger.info(
            f"Created checkpoint: {checkpoint_instance_id} "
            f"(session={session_id}, checkpoint_id={checkpoint_config.checkpoint_id})"
        )

        return checkpoint

    def resolve_checkpoint(
        self,
        checkpoint_instance_id: str,
        resolution: CheckpointResolution
    ) -> bool:
        """
        Resolve checkpoint with human decision.

        Args:
            checkpoint_instance_id: Checkpoint instance ID
            resolution: Human decision/input

        Returns:
            True if resolved successfully, False if not found or already resolved
        """
        with self._lock:
            checkpoint = self._checkpoints.get(checkpoint_instance_id)

            if not checkpoint:
                logger.warning(f"Checkpoint not found: {checkpoint_instance_id}")
                return False

            if checkpoint.status != CheckpointStatus.PENDING:
                logger.warning(
                    f"Checkpoint {checkpoint_instance_id} already resolved/cancelled "
                    f"(status={checkpoint.status})"
                )
                return False

            # Update checkpoint
            checkpoint.status = CheckpointStatus.RESOLVED
            checkpoint.resolution = resolution
            checkpoint.resolved_at = resolution.resolved_at

            logger.info(
                f"Resolved checkpoint: {checkpoint_instance_id} "
                f"(action={resolution.action}, user={resolution.user_id})"
            )

        # Persist to disk
        self.checkpoint_store.save_checkpoint(checkpoint)

        return True

    def get_checkpoint(self, checkpoint_instance_id: str) -> Optional[CheckpointInstance]:
        """
        Get checkpoint by ID.

        Args:
            checkpoint_instance_id: Checkpoint instance ID

        Returns:
            CheckpointInstance if found, None otherwise
        """
        with self._lock:
            checkpoint = self._checkpoints.get(checkpoint_instance_id)

        # If not in memory, try loading from disk
        if not checkpoint:
            checkpoint = self.checkpoint_store.load_checkpoint(checkpoint_instance_id)
            if checkpoint:
                # Add to memory cache
                with self._lock:
                    self._checkpoints[checkpoint_instance_id] = checkpoint

        return checkpoint

    def get_pending_checkpoints(
        self,
        user_role: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> List[CheckpointInstance]:
        """
        Get all pending checkpoints (filterable by role/workflow).

        Args:
            user_role: Filter by required role (optional)
            workflow_id: Filter by workflow type (optional)

        Returns:
            List of pending checkpoint instances
        """
        with self._lock:
            pending = [
                cp for cp in self._checkpoints.values()
                if cp.status == CheckpointStatus.PENDING
            ]

        # Apply filters
        if user_role:
            pending = [cp for cp in pending if cp.required_role == user_role or user_role == "admin"]

        if workflow_id:
            pending = [cp for cp in pending if cp.workflow_id == workflow_id]

        # Sort by created_at (oldest first)
        pending.sort(key=lambda cp: cp.created_at)

        return pending

    def get_session_checkpoints(self, session_id: str) -> List[CheckpointInstance]:
        """
        Get all checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint instances for session
        """
        with self._lock:
            checkpoint_ids = self._session_checkpoints.get(session_id, [])
            checkpoints = [
                self._checkpoints[cp_id]
                for cp_id in checkpoint_ids
                if cp_id in self._checkpoints
            ]

        # If none in memory, try loading from disk
        if not checkpoints:
            checkpoints = self.checkpoint_store.list_session_checkpoints(session_id)
            # Add to memory cache
            with self._lock:
                for cp in checkpoints:
                    self._checkpoints[cp.checkpoint_instance_id] = cp

        return checkpoints

    def check_timeout(self, checkpoint_instance_id: str) -> Optional[str]:
        """
        Check if checkpoint has timed out.

        Args:
            checkpoint_instance_id: Checkpoint instance ID

        Returns:
            Timeout action if timed out, None otherwise
        """
        checkpoint = self.get_checkpoint(checkpoint_instance_id)

        if not checkpoint or checkpoint.status != CheckpointStatus.PENDING:
            return None

        if not checkpoint.timeout_at:
            return None  # No timeout configured

        # Check if timeout threshold reached
        now = datetime.utcnow()
        timeout_time = datetime.fromisoformat(checkpoint.timeout_at.replace('Z', '+00:00').replace('+00:00', ''))

        if now >= timeout_time:
            return checkpoint.on_timeout or "auto_approve"

        return None

    def cancel_checkpoint(self, checkpoint_instance_id: str) -> bool:
        """
        Cancel checkpoint (admin only).

        Args:
            checkpoint_instance_id: Checkpoint instance ID

        Returns:
            True if cancelled, False if not found or already resolved
        """
        with self._lock:
            checkpoint = self._checkpoints.get(checkpoint_instance_id)

            if not checkpoint:
                return False

            if checkpoint.status != CheckpointStatus.PENDING:
                return False

            # Update checkpoint
            checkpoint.status = CheckpointStatus.CANCELLED
            checkpoint.resolved_at = datetime.utcnow().isoformat() + "Z"

            logger.info(f"Cancelled checkpoint: {checkpoint_instance_id}")

        # Persist to disk
        self.checkpoint_store.save_checkpoint(checkpoint)

        return True

    def cancel_session_checkpoints(self, session_id: str) -> None:
        """
        Cancel all checkpoints for a session.

        Args:
            session_id: Session ID
        """
        checkpoints = self.get_session_checkpoints(session_id)

        for checkpoint in checkpoints:
            if checkpoint.status == CheckpointStatus.PENDING:
                self.cancel_checkpoint(checkpoint.checkpoint_instance_id)

        logger.info(f"Cancelled all checkpoints for session: {session_id}")

    def _timeout_checker_loop(self) -> None:
        """
        Background thread to check for expired checkpoints.

        Runs every 30 seconds and processes any checkpoints that have timed out.
        """
        logger.info("Checkpoint timeout checker started")

        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                self._process_expired_checkpoints()
            except Exception as e:
                logger.error(f"Error in timeout checker: {e}")

    def _process_expired_checkpoints(self) -> None:
        """
        Find and resolve expired checkpoints.

        Applies configured timeout action (auto_approve, auto_reject, etc).
        """
        now = datetime.utcnow()

        with self._lock:
            pending_checkpoints = [
                cp for cp in self._checkpoints.values()
                if cp.status == CheckpointStatus.PENDING and cp.timeout_at
            ]

        for checkpoint in pending_checkpoints:
            try:
                timeout_time = datetime.fromisoformat(
                    checkpoint.timeout_at.replace('Z', '+00:00').replace('+00:00', '')
                )

                if now >= timeout_time:
                    self._apply_timeout_action(checkpoint)
            except Exception as e:
                logger.error(
                    f"Error processing timeout for checkpoint {checkpoint.checkpoint_instance_id}: {e}"
                )

    def _apply_timeout_action(self, checkpoint: CheckpointInstance) -> None:
        """
        Apply configured timeout action to checkpoint.

        Args:
            checkpoint: Checkpoint instance that has timed out
        """
        action = checkpoint.on_timeout or "auto_approve"

        logger.warning(
            f"Checkpoint {checkpoint.checkpoint_instance_id} timed out, "
            f"applying action: {action}"
        )

        # Create system resolution
        resolution = CheckpointResolution(
            action=action,
            user_id="system",
            user_role="system",
            comments=f"Checkpoint timed out - automatic action: {action}",
            resolved_at=datetime.utcnow().isoformat() + "Z"
        )

        # Update checkpoint
        with self._lock:
            checkpoint.status = CheckpointStatus.TIMEOUT
            checkpoint.resolution = resolution
            checkpoint.resolved_at = resolution.resolved_at

        # Persist to disk
        self.checkpoint_store.save_checkpoint(checkpoint)


# Singleton instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """
    Get singleton checkpoint manager instance.

    Returns:
        CheckpointManager instance
    """
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
