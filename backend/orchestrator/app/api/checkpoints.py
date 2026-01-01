"""
Checkpoint API Endpoints

REST API for Human-in-the-Loop (HITL) checkpoint operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from app.models.checkpoint_models import (
    CheckpointInstance,
    CheckpointListResponse,
    ResolveCheckpointRequest,
    ResolveCheckpointResponse,
    CheckpointResolution
)
from app.services.checkpoint_manager import get_checkpoint_manager
from app.services.governance_enforcer import create_governance_enforcer
from app.services.storage import get_session_writer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])


@router.get("/pending", response_model=CheckpointListResponse)
async def get_pending_checkpoints(
    user_role: Optional[str] = Query(None, description="Filter by required role"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow type")
):
    """
    Get all pending checkpoints.

    Query parameters:
    - user_role: Filter by required role (e.g., 'reviewer', 'fraud_investigator')
    - workflow_id: Filter by workflow type (e.g., 'claims_triage')

    Returns list of pending checkpoints matching filters.
    """
    try:
        checkpoint_manager = get_checkpoint_manager()
        checkpoints = checkpoint_manager.get_pending_checkpoints(
            user_role=user_role,
            workflow_id=workflow_id
        )

        logger.info(
            f"Fetched {len(checkpoints)} pending checkpoints "
            f"(role={user_role}, workflow={workflow_id})"
        )

        return CheckpointListResponse(
            checkpoints=checkpoints,
            total_count=len(checkpoints)
        )

    except Exception as e:
        logger.error(f"Error fetching pending checkpoints: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching checkpoints: {str(e)}")


@router.get("/{checkpoint_instance_id}", response_model=CheckpointInstance)
async def get_checkpoint(checkpoint_instance_id: str):
    """
    Get specific checkpoint details.

    Args:
        checkpoint_instance_id: Unique checkpoint instance ID

    Returns checkpoint instance with full details.
    """
    try:
        checkpoint_manager = get_checkpoint_manager()
        checkpoint = checkpoint_manager.get_checkpoint(checkpoint_instance_id)

        if not checkpoint:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint not found: {checkpoint_instance_id}"
            )

        logger.info(f"Fetched checkpoint: {checkpoint_instance_id}")

        return checkpoint

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching checkpoint {checkpoint_instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching checkpoint: {str(e)}")


@router.post("/{checkpoint_instance_id}/resolve", response_model=ResolveCheckpointResponse)
async def resolve_checkpoint(
    checkpoint_instance_id: str,
    request: ResolveCheckpointRequest
):
    """
    Resolve checkpoint with human decision.

    Args:
        checkpoint_instance_id: Unique checkpoint instance ID
        request: Resolution details (action, user_id, user_role, comments, data_updates)

    Returns success confirmation.

    Validates user role has permission before resolving.
    """
    try:
        checkpoint_manager = get_checkpoint_manager()
        storage = get_session_writer()

        # Get checkpoint
        checkpoint = checkpoint_manager.get_checkpoint(checkpoint_instance_id)

        if not checkpoint:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint not found: {checkpoint_instance_id}"
            )

        # Validate role authorization
        governance = create_governance_enforcer(None)
        if not governance.check_hitl_access(request.user_role, checkpoint.required_role):
            logger.warning(
                f"Unauthorized checkpoint resolution attempt: "
                f"user_role={request.user_role}, required_role={checkpoint.required_role}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Role '{request.user_role}' does not have permission to resolve this checkpoint. "
                       f"Required role: '{checkpoint.required_role}'"
            )

        # Create resolution
        resolution = CheckpointResolution(
            action=request.action,
            user_id=request.user_id,
            user_role=request.user_role,
            comments=request.comments,
            data_updates=request.data_updates,
            resolved_at=datetime.utcnow().isoformat() + "Z"
        )

        # Resolve checkpoint
        success = checkpoint_manager.resolve_checkpoint(checkpoint_instance_id, resolution)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to resolve checkpoint (may already be resolved)"
            )

        # Log to session JSONL
        storage.write_event(checkpoint.session_id, {
            "event_type": "checkpoint_resolved",
            "checkpoint_id": checkpoint.checkpoint_id,
            "checkpoint_instance_id": checkpoint_instance_id,
            "checkpoint_name": checkpoint.checkpoint_name,
            "resolution": resolution.model_dump()
        })

        logger.info(
            f"Resolved checkpoint: {checkpoint_instance_id} "
            f"(action={request.action}, user={request.user_id})"
        )

        return ResolveCheckpointResponse(
            success=True,
            message="Checkpoint resolved successfully",
            checkpoint_instance_id=checkpoint_instance_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving checkpoint {checkpoint_instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving checkpoint: {str(e)}")


@router.post("/{checkpoint_instance_id}/cancel", response_model=ResolveCheckpointResponse)
async def cancel_checkpoint(
    checkpoint_instance_id: str,
    user_role: str = Query(..., description="User role (must be admin)")
):
    """
    Cancel checkpoint (admin only).

    Args:
        checkpoint_instance_id: Unique checkpoint instance ID
        user_role: User role (must be 'admin')

    Returns success confirmation.
    """
    try:
        # Only admins can cancel checkpoints
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can cancel checkpoints"
            )

        checkpoint_manager = get_checkpoint_manager()
        storage = get_session_writer()

        # Get checkpoint
        checkpoint = checkpoint_manager.get_checkpoint(checkpoint_instance_id)

        if not checkpoint:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint not found: {checkpoint_instance_id}"
            )

        # Cancel checkpoint
        success = checkpoint_manager.cancel_checkpoint(checkpoint_instance_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to cancel checkpoint (may already be resolved/cancelled)"
            )

        # Log to session JSONL
        storage.write_event(checkpoint.session_id, {
            "event_type": "checkpoint_cancelled",
            "checkpoint_id": checkpoint.checkpoint_id,
            "checkpoint_instance_id": checkpoint_instance_id,
            "cancelled_by": user_role
        })

        logger.info(f"Cancelled checkpoint: {checkpoint_instance_id}")

        return ResolveCheckpointResponse(
            success=True,
            message="Checkpoint cancelled successfully",
            checkpoint_instance_id=checkpoint_instance_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling checkpoint {checkpoint_instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling checkpoint: {str(e)}")


@router.get("/session/{session_id}", response_model=CheckpointListResponse)
async def get_session_checkpoints(session_id: str):
    """
    Get all checkpoints for a session.

    Args:
        session_id: Workflow session ID

    Returns list of all checkpoints (pending and resolved) for the session.
    """
    try:
        checkpoint_manager = get_checkpoint_manager()
        checkpoints = checkpoint_manager.get_session_checkpoints(session_id)

        logger.info(f"Fetched {len(checkpoints)} checkpoints for session: {session_id}")

        return CheckpointListResponse(
            checkpoints=checkpoints,
            total_count=len(checkpoints)
        )

    except Exception as e:
        logger.error(f"Error fetching session checkpoints for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching session checkpoints: {str(e)}")
