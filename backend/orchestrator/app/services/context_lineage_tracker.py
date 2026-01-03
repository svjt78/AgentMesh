"""
ContextLineageTracker - Service for tracking context compilation lineage.

Demonstrates:
- Context compilation tracking
- Processor execution metrics
- Token budget analysis
- Debugging and observability
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import logging
from pydantic import BaseModel
import uuid

logger = logging.getLogger(__name__)


# ============= Data Models =============

class ProcessorExecution(BaseModel):
    """Metadata for a single processor execution."""
    processor_id: str
    execution_time_ms: float
    success: bool
    modifications_made: Dict[str, Any]
    error: Optional[str] = None


class ContextCompilation(BaseModel):
    """Complete record of a context compilation."""
    compilation_id: str
    session_id: str
    agent_id: str
    timestamp: str

    # Input metrics
    tokens_before: int
    components_before: Dict[str, int]  # e.g., {"original_input": 100, "prior_outputs": 500}

    # Processor execution
    processors_executed: List[ProcessorExecution]
    total_execution_time_ms: float

    # Output metrics
    tokens_after: int
    components_after: Dict[str, int]

    # Modifications applied
    truncation_applied: bool
    truncation_details: Optional[Dict[str, Any]] = None
    compaction_applied: bool
    compaction_details: Optional[Dict[str, Any]] = None
    memories_retrieved: int
    memory_ids: List[str] = []
    artifacts_resolved: int
    artifact_handles: List[str] = []

    # Budget analysis
    budget_allocation: Dict[str, int]  # e.g., {"original_input": 30, "prior_outputs": 50, "observations": 20}
    max_tokens: Optional[int] = None
    budget_exceeded: bool
    budget_utilization_percent: float


# ============= ContextLineageTracker Service =============

class ContextLineageTracker:
    """
    Tracks context compilation lineage for debugging and observability.

    Storage structure:
    - storage/sessions/{session_id}_context_lineage.jsonl (append-only)
    """

    def __init__(self, session_id: str, storage_path: str = "storage/sessions"):
        """
        Initialize context lineage tracker.

        Args:
            session_id: Session identifier
            storage_path: Base path for storage
        """
        self.session_id = session_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.lineage_file = self.storage_path / f"{session_id}_context_lineage.jsonl"

        logger.info(f"ContextLineageTracker initialized for session {session_id}")

    def record_compilation(
        self,
        agent_id: str,
        tokens_before: int,
        tokens_after: int,
        components_before: Dict[str, int],
        components_after: Dict[str, int],
        processors_executed: List[ProcessorExecution],
        budget_allocation: Dict[str, int],
        max_tokens: int,
        truncation_applied: bool = False,
        truncation_details: Optional[Dict[str, Any]] = None,
        compaction_applied: bool = False,
        compaction_details: Optional[Dict[str, Any]] = None,
        memories_retrieved: int = 0,
        memory_ids: Optional[List[str]] = None,
        artifacts_resolved: int = 0,
        artifact_handles: Optional[List[str]] = None,
    ) -> str:
        """
        Record a context compilation.

        Args:
            agent_id: Agent identifier
            tokens_before: Token count before compilation
            tokens_after: Token count after compilation
            components_before: Component token counts before
            components_after: Component token counts after
            processors_executed: List of processor executions
            budget_allocation: Budget allocation percentages
            max_tokens: Maximum token budget
            truncation_applied: Whether truncation was applied
            truncation_details: Details of truncation
            compaction_applied: Whether compaction was applied
            compaction_details: Details of compaction
            memories_retrieved: Number of memories retrieved
            memory_ids: List of memory IDs retrieved
            artifacts_resolved: Number of artifacts resolved
            artifact_handles: List of artifact handles resolved

        Returns:
            Compilation ID
        """
        try:
            # Generate compilation ID
            compilation_id = f"ctx_compile_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Calculate total execution time
            total_execution_time = sum(p.execution_time_ms for p in processors_executed)

            # Calculate budget metrics
            budget_exceeded = tokens_after > max_tokens
            budget_utilization = (tokens_after / max_tokens * 100) if max_tokens > 0 else 0

            # Create compilation record
            compilation = ContextCompilation(
                compilation_id=compilation_id,
                session_id=self.session_id,
                agent_id=agent_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                tokens_before=tokens_before,
                components_before=components_before,
                processors_executed=processors_executed,
                total_execution_time_ms=total_execution_time,
                tokens_after=tokens_after,
                components_after=components_after,
                truncation_applied=truncation_applied,
                truncation_details=truncation_details,
                compaction_applied=compaction_applied,
                compaction_details=compaction_details,
                memories_retrieved=memories_retrieved,
                memory_ids=memory_ids or [],
                artifacts_resolved=artifacts_resolved,
                artifact_handles=artifact_handles or [],
                budget_allocation=budget_allocation,
                max_tokens=max_tokens,
                budget_exceeded=budget_exceeded,
                budget_utilization_percent=budget_utilization,
            )

            # Write to lineage file (append-only JSONL)
            with open(self.lineage_file, 'a') as f:
                f.write(json.dumps(compilation.model_dump()) + '\n')

            logger.info(
                f"Context compilation recorded: {compilation_id}, "
                f"agent={agent_id}, tokens={tokens_before}->{tokens_after}, "
                f"processors={len(processors_executed)}"
            )

            return compilation_id

        except Exception as e:
            logger.error(f"Failed to record compilation: {e}", exc_info=True)
            raise

    def get_compilation(self, compilation_id: str) -> Optional[ContextCompilation]:
        """
        Retrieve a specific compilation by ID.

        Args:
            compilation_id: Compilation identifier

        Returns:
            ContextCompilation or None if not found
        """
        try:
            if not self.lineage_file.exists():
                return None

            with open(self.lineage_file, 'r') as f:
                for line in f:
                    compilation_data = json.loads(line.strip())
                    if compilation_data.get('compilation_id') == compilation_id:
                        return ContextCompilation(**compilation_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get compilation {compilation_id}: {e}")
            return None

    def list_compilations(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContextCompilation]:
        """
        List all compilations for this session.

        Args:
            agent_id: Filter by agent ID (optional)
            limit: Maximum compilations to return
            offset: Number of compilations to skip

        Returns:
            List of ContextCompilation objects
        """
        try:
            if not self.lineage_file.exists():
                return []

            compilations = []

            with open(self.lineage_file, 'r') as f:
                for line in f:
                    compilation_data = json.loads(line.strip())

                    # Filter by agent_id if specified
                    if agent_id and compilation_data.get('agent_id') != agent_id:
                        continue

                    compilations.append(ContextCompilation(**compilation_data))

            # Apply offset and limit
            return compilations[offset:offset + limit]

        except Exception as e:
            logger.error(f"Failed to list compilations: {e}")
            return []

    def get_compilation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about compilations for this session.

        Returns:
            Dictionary with compilation statistics
        """
        try:
            if not self.lineage_file.exists():
                return {
                    "total_compilations": 0,
                    "agents": [],
                    "total_processors_executed": 0,
                    "total_execution_time_ms": 0,
                    "avg_tokens_before": 0,
                    "avg_tokens_after": 0,
                    "truncations": 0,
                    "compactions": 0,
                    "memories_retrieved": 0,
                    "artifacts_resolved": 0,
                }

            compilations = self.list_compilations(limit=10000)

            if not compilations:
                return {
                    "total_compilations": 0,
                    "agents": [],
                    "total_processors_executed": 0,
                    "total_execution_time_ms": 0,
                    "avg_tokens_before": 0,
                    "avg_tokens_after": 0,
                    "truncations": 0,
                    "compactions": 0,
                    "memories_retrieved": 0,
                    "artifacts_resolved": 0,
                }

            agents = list(set(c.agent_id for c in compilations))
            total_processors = sum(len(c.processors_executed) for c in compilations)
            total_time = sum(c.total_execution_time_ms for c in compilations)
            avg_tokens_before = sum(c.tokens_before for c in compilations) / len(compilations)
            avg_tokens_after = sum(c.tokens_after for c in compilations) / len(compilations)
            truncations = sum(1 for c in compilations if c.truncation_applied)
            compactions = sum(1 for c in compilations if c.compaction_applied)
            total_memories = sum(c.memories_retrieved for c in compilations)
            total_artifacts = sum(c.artifacts_resolved for c in compilations)

            return {
                "total_compilations": len(compilations),
                "agents": agents,
                "total_processors_executed": total_processors,
                "total_execution_time_ms": total_time,
                "avg_tokens_before": avg_tokens_before,
                "avg_tokens_after": avg_tokens_after,
                "truncations": truncations,
                "compactions": compactions,
                "memories_retrieved": total_memories,
                "artifacts_resolved": total_artifacts,
            }

        except Exception as e:
            logger.error(f"Failed to get compilation stats: {e}")
            return {}

    def get_token_budget_timeline(self) -> List[Dict[str, Any]]:
        """
        Get token budget timeline for visualization.

        Returns:
            List of timeline points with token counts
        """
        try:
            compilations = self.list_compilations(limit=10000)

            timeline = []
            for compilation in compilations:
                timeline.append({
                    "compilation_id": compilation.compilation_id,
                    "agent_id": compilation.agent_id,
                    "timestamp": compilation.timestamp,
                    "tokens_before": compilation.tokens_before,
                    "tokens_after": compilation.tokens_after,
                    "max_tokens": compilation.max_tokens,
                    "budget_exceeded": compilation.budget_exceeded,
                    "truncation_applied": compilation.truncation_applied,
                    "compaction_applied": compilation.compaction_applied,
                })

            return timeline

        except Exception as e:
            logger.error(f"Failed to get token budget timeline: {e}")
            return []


# ============= Singleton Access =============

_context_lineage_trackers: Dict[str, ContextLineageTracker] = {}


def get_context_lineage_tracker(session_id: str) -> ContextLineageTracker:
    """
    Get or create ContextLineageTracker for a session.

    Args:
        session_id: Session identifier

    Returns:
        ContextLineageTracker instance
    """
    global _context_lineage_trackers

    if session_id not in _context_lineage_trackers:
        from ..config import get_config
        config = get_config()
        storage_path = Path(config.storage_path) / "sessions"
        _context_lineage_trackers[session_id] = ContextLineageTracker(session_id, str(storage_path))

    return _context_lineage_trackers[session_id]
