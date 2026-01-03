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
    from ..config import get_config

    storage_path = Path(get_config().storage_path) / "sessions"
    if not storage_path.exists():
        return []

    session_files = sorted(
        [f for f in storage_path.glob("*.jsonl") if not f.stem.endswith("_context_lineage")],
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


@router.post("/{session_id}/trigger-compaction")
async def trigger_compaction(
    session_id: str,
    method: Optional[str] = Query(None, description="Compaction method: rule_based or llm_based")
):
    """
    Manually trigger context compaction for a session.

    Args:
        session_id: Session to compact
        method: Compaction method (rule_based/llm_based), defaults to config

    Returns:
        Compaction result

    Demonstrates:
    - Manual compaction triggering
    - Context engineering API
    - Session event management
    """
    try:
        from ..services.compaction_manager import CompactionManager

        # Get session events
        reader = get_session_writer()
        events = reader.read_session(session_id)

        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        # Initialize compaction manager
        compaction_manager = CompactionManager(session_id)

        # Trigger compaction
        result = compaction_manager.compact_events(events, method)

        # Write compaction events
        compaction_manager.write_compaction_event(result)

        logger.info(
            f"Manual compaction triggered for session={session_id}, "
            f"method={result.method}, "
            f"{result.events_before_count} → {result.events_after_count} events"
        )

        return {
            "compaction_id": result.compaction_id,
            "session_id": result.session_id,
            "method": result.method,
            "events_before": result.events_before_count,
            "events_after": result.events_after_count,
            "tokens_before": result.tokens_before,
            "tokens_after": result.tokens_after,
            "compression_ratio": result.compression_ratio,
            "summary": result.summary_text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to trigger compaction for session {session_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger compaction: {str(e)}"
        )


@router.get("/{session_id}/context-lineage")
async def get_context_lineage(
    session_id: str,
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """
    Get context compilation lineage for a session.

    Returns detailed information about all context compilations
    including processor executions, token metrics, and modifications.

    Args:
        session_id: Session identifier
        agent_id: Optional filter by agent ID
        limit: Maximum compilations to return
        offset: Number of compilations to skip

    Returns:
        List of context compilations with detailed metrics
    """
    try:
        from ..services.context_lineage_tracker import get_context_lineage_tracker

        lineage_tracker = get_context_lineage_tracker(session_id)
        compilations = lineage_tracker.list_compilations(
            agent_id=agent_id,
            limit=limit,
            offset=offset
        )

        return {
            "session_id": session_id,
            "compilations": [c.model_dump() for c in compilations],
            "total_count": len(compilations),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(
            f"Failed to get context lineage for session {session_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context lineage: {str(e)}"
        )


@router.get("/{session_id}/context-lineage/{compilation_id}")
async def get_compilation_details(
    session_id: str,
    compilation_id: str
):
    """
    Get details for a specific context compilation.

    Args:
        session_id: Session identifier
        compilation_id: Compilation identifier

    Returns:
        Detailed compilation information
    """
    try:
        from ..services.context_lineage_tracker import get_context_lineage_tracker

        lineage_tracker = get_context_lineage_tracker(session_id)
        compilation = lineage_tracker.get_compilation(compilation_id)

        if not compilation:
            raise HTTPException(
                status_code=404,
                detail=f"Compilation '{compilation_id}' not found"
            )

        return compilation.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get compilation {compilation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compilation: {str(e)}"
        )


@router.get("/{session_id}/context-stats")
async def get_context_stats(session_id: str):
    """
    Get context compilation statistics for a session.

    Returns aggregate statistics about context compilations:
    - Total compilations
    - Agents involved
    - Average token counts
    - Truncations/compactions applied
    - Memories/artifacts loaded

    Args:
        session_id: Session identifier

    Returns:
        Context compilation statistics
    """
    try:
        from ..services.context_lineage_tracker import get_context_lineage_tracker

        lineage_tracker = get_context_lineage_tracker(session_id)
        stats = lineage_tracker.get_compilation_stats()

        return {
            "session_id": session_id,
            **stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(
            f"Failed to get context stats for session {session_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context stats: {str(e)}"
        )


@router.get("/{session_id}/token-budget-timeline")
async def get_token_budget_timeline(session_id: str):
    """
    Get token budget timeline for visualization.

    Returns a timeline of token counts before/after compilation,
    useful for visualizing token usage over time.

    Args:
        session_id: Session identifier

    Returns:
        Timeline data for visualization
    """
    try:
        from ..services.context_lineage_tracker import get_context_lineage_tracker

        lineage_tracker = get_context_lineage_tracker(session_id)
        timeline = lineage_tracker.get_token_budget_timeline()

        return {
            "session_id": session_id,
            "timeline": timeline,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(
            f"Failed to get token budget timeline for session {session_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get token budget timeline: {str(e)}"
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
        from ..config import get_config

        storage_root = Path(get_config().storage_path)
        sessions_root = storage_root / "sessions"
        artifacts_root = storage_root / "artifacts"
        compactions_root = storage_root / "compactions"

        # Delete session file
        session_path = sessions_root / f"{session_id}.jsonl"
        if session_path.exists():
            session_path.unlink()

        # Delete context lineage file
        lineage_path = sessions_root / f"{session_id}_context_lineage.jsonl"
        if lineage_path.exists():
            lineage_path.unlink()

        # Delete evidence map artifact
        artifact_path = artifacts_root / f"{session_id}_evidence_map.json"
        if artifact_path.exists():
            artifact_path.unlink()

        # Delete compaction archives for this session
        if compactions_root.exists():
            for archive_path in compactions_root.glob(f"{session_id}_compaction_*.json"):
                archive_path.unlink()

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
