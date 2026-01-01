"""
Runs API - Endpoints for workflow execution and streaming.

Demonstrates:
- Async API endpoints
- SSE streaming
- Background task management
- Error handling
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import logging
import json
import asyncio

from .models import RunWorkflowRequest, RunWorkflowResponse
from ..services.workflow_executor import get_workflow_executor
from ..services.sse_broadcaster import get_broadcaster
from ..services.progress_store import get_progress_store
from ..services.registry_manager import get_registry_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunWorkflowResponse)
async def create_run(request: RunWorkflowRequest):
    """
    Create new workflow run.

    Starts workflow execution in background and returns session info with stream URL.

    Demonstrates:
    - Async request handling
    - Validation before execution
    - Background task creation
    """
    logger.info(f"Creating workflow run: workflow_id={request.workflow_id}")

    # Validate workflow exists
    registry = get_registry_manager()
    workflow = registry.get_workflow(request.workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request.workflow_id}' not found"
        )

    try:
        # Execute workflow in background
        executor = get_workflow_executor()
        session_id = await executor.execute_workflow(
            workflow_id=request.workflow_id,
            input_data=request.input_data,
            session_id=request.session_id
        )

        # Return response with URLs
        return RunWorkflowResponse(
            session_id=session_id,
            workflow_id=request.workflow_id,
            status="running",
            created_at=datetime.utcnow().isoformat() + "Z",
            stream_url=f"/runs/{session_id}/stream",
            session_url=f"/sessions/{session_id}"
        )

    except Exception as e:
        logger.error(f"Failed to create run: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/{session_id}/stream")
async def stream_run(
    session_id: str,
    request: Request,
    last_event_id: Optional[str] = None
):
    """
    Stream workflow execution events via Server-Sent Events.

    Uses polling pattern (ClaimSense AI approach):
    - Polls progress_store every 100ms
    - Sends delta events (only new events since last poll)
    - Thread-safe, no async bridge needed

    Args:
        session_id: Session to stream
        last_event_id: Last received event ID (for reconnection, currently unused)

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"Starting SSE stream: session_id={session_id}")

    progress_store = get_progress_store()

    async def event_generator():
        """Poll progress store and stream new events."""
        last_sent_index = 0

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: session_id={session_id}")
                    break

                # Get current progress
                progress = progress_store.get_session_progress(session_id)

                if not progress:
                    # Session not found yet, wait and retry
                    await asyncio.sleep(0.1)
                    continue

                # Send new events (delta streaming)
                if last_sent_index < len(progress.events):
                    for event in progress.events[last_sent_index:]:
                        # Send event directly (useSSE hook will wrap it)
                        yield f"data: {json.dumps(event)}\n\n"

                    last_sent_index = len(progress.events)

                # Check if workflow completed
                if progress.status in ["completed", "error"]:
                    # Send final status event
                    final_event = {
                        "event_type": f"workflow_{progress.status}",
                        "status": progress.status,
                        "timestamp": progress.updated_at
                    }
                    yield f"event: workflow_{progress.status}\ndata: {json.dumps(final_event)}\n\n"

                    logger.info(f"Workflow {progress.status}: session_id={session_id}")
                    break

                # Poll interval: 100ms (same as ClaimSense AI)
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/{session_id}/status")
async def get_run_status(session_id: str):
    """
    Get current status of a workflow run.

    Returns quick status without full session details.

    Demonstrates:
    - Lightweight status check
    - Running/completed detection
    """
    executor = get_workflow_executor()

    is_running = executor.is_running(session_id)

    # Determine status
    if is_running:
        status = "running"
    else:
        # Check if session file exists (completed)
        from ..services.storage import get_session_writer
        try:
            writer = get_session_writer()
            events = writer.read_session(session_id)
            status = "completed" if events else "not_found"
        except FileNotFoundError:
            status = "not_found"

    return {
        "session_id": session_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/{session_id}/cancel")
async def cancel_run(session_id: str):
    """
    Cancel a running workflow.

    Args:
        session_id: Session to cancel

    Returns:
        Cancellation confirmation

    Demonstrates:
    - Graceful cancellation
    - Error handling for non-existent sessions
    """
    logger.info(f"Cancelling workflow: session_id={session_id}")

    executor = get_workflow_executor()

    success = await executor.cancel_workflow(session_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found or not running"
        )

    return {
        "session_id": session_id,
        "status": "cancelled",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("")
async def list_runs():
    """
    List currently running workflows.

    Returns:
        List of running session IDs with stats

    Demonstrates:
    - Observability endpoint
    - System health monitoring
    """
    executor = get_workflow_executor()
    broadcaster = get_broadcaster()

    return {
        "running_sessions": executor.get_running_sessions(),
        "executor_stats": executor.get_stats(),
        "broadcaster_stats": broadcaster.get_stats(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
