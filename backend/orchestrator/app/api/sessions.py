"""
Sessions API - Endpoints for session replay and evidence maps.

Demonstrates:
- Session retrieval
- Event filtering
- Artifact access
- Pagination
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import logging

from .models import SessionSummary, SessionDetails, EvidenceMapResponse
from ..services.storage import get_session_writer, get_artifact_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionSummary])
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    List recent sessions.

    Returns paginated list of session summaries.

    Demonstrates:
    - Pagination pattern
    - Filesystem-based querying
    - Error resilience
    """
    reader = get_session_writer()

    # Get all session files
    storage_path = Path("/storage/sessions")
    if not storage_path.exists():
        return []

    session_files = sorted(
        storage_path.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    # Apply pagination
    session_files = session_files[offset:offset + limit]

    # Build summaries
    summaries = []
    for session_file in session_files:
        session_id = session_file.stem

        try:
            events = reader.read_session(session_id)

            if not events:
                continue

            # Extract summary info
            first_event = events[0]
            last_event = events[-1]

            # Get agents executed
            agents_executed = []
            for event in events:
                if event.get("event_type") == "agent_invocation_completed":
                    agent_id = event.get("event_data", {}).get("agent_id")
                    if agent_id and agent_id not in agents_executed:
                        agents_executed.append(agent_id)

            # Calculate duration if completed
            duration_seconds = None
            if first_event.get("timestamp") and last_event.get("timestamp"):
                try:
                    start_time = datetime.fromisoformat(first_event["timestamp"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(last_event["timestamp"].replace("Z", "+00:00"))
                    duration_seconds = (end_time - start_time).total_seconds()
                except Exception:
                    pass

            summary = SessionSummary(
                session_id=session_id,
                workflow_id=first_event.get("event_data", {}).get("workflow_id", "unknown"),
                status=last_event.get("event_type", "unknown"),
                created_at=first_event.get("timestamp", ""),
                completed_at=last_event.get("timestamp"),
                duration_seconds=duration_seconds,
                event_count=len(events),
                agents_executed=agents_executed
            )

            summaries.append(summary)

        except Exception as e:
            logger.error(f"Failed to read session {session_id}: {e}")
            continue

    return summaries


@router.get("/{session_id}", response_model=SessionDetails)
async def get_session(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter events by type")
):
    """
    Get complete session details with events.

    Args:
        session_id: Session ID
        event_type: Optional event type filter

    Demonstrates:
    - Detailed session retrieval
    - Event filtering
    - Metadata extraction
    """
    reader = get_session_writer()

    try:
        # Read events
        if event_type:
            events = reader.filter_events(session_id, event_type)
            # Need to read all events for metadata
            all_events = reader.read_session(session_id)
        else:
            events = reader.read_session(session_id)
            all_events = events

        if not all_events:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        # Extract session metadata
        first_event = all_events[0]
        last_event = all_events[-1]

        # Extract input/output
        input_data = {}
        output_data = None

        for event in all_events:
            event_type_name = event.get("event_type", "")
            if event_type_name == "orchestrator_started":
                # Input might be in event_data
                input_data = event.get("event_data", {}).get("input_data", {})
            elif event_type_name == "workflow_completed":
                output_data = event.get("event_data", {})

        # Get agents executed
        agents_executed = []
        for event in all_events:
            if event.get("event_type") == "agent_invocation_completed":
                agent_id = event.get("event_data", {}).get("agent_id")
                if agent_id and agent_id not in agents_executed:
                    agents_executed.append(agent_id)

        # Count iterations
        total_iterations = len([
            e for e in all_events
            if "iteration" in e.get("event_type", "")
        ])

        # Calculate duration
        duration_seconds = None
        if first_event.get("timestamp") and last_event.get("timestamp"):
            try:
                start_time = datetime.fromisoformat(first_event["timestamp"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(last_event["timestamp"].replace("Z", "+00:00"))
                duration_seconds = (end_time - start_time).total_seconds()
            except Exception:
                pass

        # Extract warnings and errors
        warnings = []
        errors = []
        for event in all_events:
            event_type_name = event.get("event_type", "")
            if "warning" in event_type_name.lower():
                warnings.append(event.get("event_data", {}).get("message", str(event)))
            elif "error" in event_type_name.lower():
                errors.append(event.get("event_data", {}).get("error", str(event)))

        # Build details
        details = SessionDetails(
            session_id=session_id,
            workflow_id=first_event.get("event_data", {}).get("workflow_id", "unknown"),
            status=last_event.get("event_type", "unknown"),
            created_at=first_event.get("timestamp", ""),
            completed_at=last_event.get("timestamp"),
            duration_seconds=duration_seconds,
            input_data=input_data,
            output_data=output_data,
            agents_executed=agents_executed,
            total_iterations=max(total_iterations, 1),
            total_agent_invocations=len(agents_executed),
            events=events,  # Return filtered events
            warnings=warnings,
            errors=errors
        )

        return details

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.get("/{session_id}/evidence", response_model=EvidenceMapResponse)
async def get_evidence_map(session_id: str):
    """
    Get evidence map for session.

    Returns final evidence map artifact.

    Demonstrates:
    - Artifact retrieval
    - Error handling
    """
    artifact_reader = get_artifact_store()
    artifact_id = f"{session_id}_evidence_map"

    try:
        artifact = artifact_reader.read_artifact(artifact_id)

        return EvidenceMapResponse(
            session_id=session_id,
            evidence_map=artifact["data"],
            generated_at=artifact["created_at"]
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Evidence map not found for session '{session_id}'"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve evidence map for {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence map: {str(e)}"
        )


@router.get("/{session_id}/events/{event_type}")
async def get_events_by_type(
    session_id: str,
    event_type: str
):
    """
    Get events of specific type for session.

    Args:
        session_id: Session ID
        event_type: Event type to filter

    Returns:
        Filtered events

    Demonstrates:
    - Event filtering
    - Specialized queries
    """
    reader = get_session_writer()

    try:
        events = reader.filter_events(session_id, event_type)

        return {
            "session_id": session_id,
            "event_type": event_type,
            "event_count": len(events),
            "events": events
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to filter events for {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to filter events: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its artifacts.

    Args:
        session_id: Session to delete

    Returns:
        Deletion confirmation

    Demonstrates:
    - Resource cleanup
    - Cascading deletion
    """
    try:
        # Delete session file
        session_path = Path(f"/storage/sessions/{session_id}.jsonl")
        if session_path.exists():
            session_path.unlink()

        # Delete evidence map artifact
        artifact_path = Path(f"/storage/artifacts/{session_id}_evidence_map.json")
        if artifact_path.exists():
            artifact_path.unlink()

        logger.info(f"Deleted session: {session_id}")

        return {
            "session_id": session_id,
            "status": "deleted",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )
