"""
Compaction Manager

Manages context compaction (summarization of old session events).
Supports both rule-based and LLM-based compaction methods.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from app.config import get_config
from app.services.storage import write_event

logger = logging.getLogger(__name__)


@dataclass
class CompactionResult:
    """Result from a compaction operation"""

    compaction_id: str
    session_id: str
    method: str  # "rule_based" or "llm_based"
    events_before_count: int
    events_after_count: int
    tokens_before: int
    tokens_after: int
    compression_ratio: float
    summary_text: Optional[str] = None
    compacted_events: List[Dict[str, Any]] = None


class CompactionManager:
    """
    Manages session event compaction.

    Compaction reduces the size of session event logs by:
    - Rule-based: Filtering, deduplication, retention of critical events
    - LLM-based: Semantic summarization of event sequences

    Writes compaction summaries back to session JSONL and archives
    originals for auditability.
    """

    def __init__(self, session_id: str):
        """
        Initialize the compaction manager.

        Args:
            session_id: Session to manage compaction for
        """
        self.session_id = session_id
        self.config = get_config()
        self.compaction_config = self._load_compaction_config()

    def _load_compaction_config(self) -> Dict[str, Any]:
        """Load compaction configuration from context_strategies.json"""
        try:
            with open("registries/context_strategies.json", "r") as f:
                strategies = json.load(f)
            return strategies.get("compaction", {})
        except Exception as e:
            logger.error(f"Failed to load compaction config: {e}")
            return {
                "enabled": False,
                "trigger_strategy": "token_threshold",
                "token_threshold": 8000,
                "event_count_threshold": 100,
                "compaction_method": "rule_based",
            }

    def check_compaction_needed(
        self, events: List[Dict[str, Any]], estimated_tokens: int
    ) -> bool:
        """
        Check if compaction should be triggered.

        Args:
            events: Current session events
            estimated_tokens: Estimated total tokens in events

        Returns:
            True if compaction should trigger
        """
        if not self.compaction_config.get("enabled", False):
            return False

        trigger_strategy = self.compaction_config.get("trigger_strategy", "token_threshold")

        if trigger_strategy == "token_threshold":
            threshold = self.compaction_config.get("token_threshold", 8000)
            return estimated_tokens > threshold

        elif trigger_strategy == "event_count":
            threshold = self.compaction_config.get("event_count_threshold", 100)
            return len(events) > threshold

        elif trigger_strategy == "both":
            token_threshold = self.compaction_config.get("token_threshold", 8000)
            event_threshold = self.compaction_config.get("event_count_threshold", 100)
            return estimated_tokens > token_threshold or len(events) > event_threshold

        return False

    def compact_events(
        self, events: List[Dict[str, Any]], method: Optional[str] = None
    ) -> CompactionResult:
        """
        Compact session events.

        Args:
            events: Events to compact
            method: Compaction method ("rule_based" or "llm_based"), defaults to config

        Returns:
            CompactionResult with compaction details
        """
        if not method:
            method = self.compaction_config.get("compaction_method", "rule_based")

        logger.info(
            f"Starting compaction for session={self.session_id}, "
            f"method={method}, events={len(events)}"
        )

        # Estimate tokens before
        tokens_before = self._estimate_tokens(events)

        # Perform compaction
        if method == "rule_based":
            compacted_events, summary = self._rule_based_compact(events)
        elif method == "llm_based":
            compacted_events, summary = self._llm_based_summarize(events)
        else:
            logger.warning(f"Unknown compaction method: {method}, using rule_based")
            compacted_events, summary = self._rule_based_compact(events)

        # Estimate tokens after
        tokens_after = self._estimate_tokens(compacted_events)

        # Calculate compression ratio
        compression_ratio = (
            tokens_after / tokens_before if tokens_before > 0 else 0
        )

        # Generate compaction ID
        compaction_id = f"compact_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        result = CompactionResult(
            compaction_id=compaction_id,
            session_id=self.session_id,
            method=method,
            events_before_count=len(events),
            events_after_count=len(compacted_events),
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio,
            summary_text=summary,
            compacted_events=compacted_events,
        )

        logger.info(
            f"Compaction completed: {len(events)} → {len(compacted_events)} events, "
            f"{tokens_before} → {tokens_after} tokens, "
            f"compression={compression_ratio:.2%}"
        )

        return result

    def _rule_based_compact(
        self, events: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Rule-based compaction: Filter and retain critical events.

        Strategy:
        1. Keep recent events (last N)
        2. Keep critical event types (workflow_completed, agent_invocation_completed, etc.)
        3. Remove debug/noise events
        4. Deduplicate similar events
        """
        retention_policy = self.compaction_config.get("retention_policy", {})
        keep_recent = retention_policy.get("keep_recent_events", 20)
        critical_types = retention_policy.get("keep_critical_event_types", [])

        compacted = []
        removed_count = 0

        # Keep recent events
        recent_events = events[-keep_recent:] if len(events) > keep_recent else events

        # Keep critical events from older events
        older_events = events[:-keep_recent] if len(events) > keep_recent else []

        for event in older_events:
            event_type = event.get("event_type", "")

            # Keep critical event types
            if event_type in critical_types:
                compacted.append(event)
            else:
                removed_count += 1

        # Add all recent events
        compacted.extend(recent_events)

        # Generate summary
        summary = (
            f"Compacted {len(events)} events using rule-based filtering. "
            f"Retained {len(compacted)} events ({len(recent_events)} recent + "
            f"{len(compacted) - len(recent_events)} critical), "
            f"removed {removed_count} non-critical events."
        )

        return compacted, summary

    def _llm_based_summarize(
        self, events: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        LLM-based summarization: Use LLM to create semantic summary.

        Strategy:
        1. Keep critical events (checkpoints, completions)
        2. Summarize sequences of similar events
        3. Use LLM to generate concise narrative summary
        """
        llm_config = self.compaction_config.get("llm_summarization", {})
        preserve_critical = llm_config.get("preserve_critical_events", True)

        # For Phase 2, implement simplified LLM summarization
        # Full implementation would call LLM client

        retention_policy = self.compaction_config.get("retention_policy", {})
        critical_types = retention_policy.get("keep_critical_event_types", [])

        # Keep critical events
        critical_events = []
        other_events = []

        for event in events:
            if preserve_critical and event.get("event_type") in critical_types:
                critical_events.append(event)
            else:
                other_events.append(event)

        # Generate summary (simplified - full version would use LLM)
        summary = self._generate_summary_text(events, critical_events, other_events)

        # Return critical events + summary event
        summary_event = {
            "event_type": "compaction_summary",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": summary,
            "events_summarized": len(other_events),
            "method": "llm_based",
        }

        compacted = critical_events + [summary_event]

        return compacted, summary

    def _generate_summary_text(
        self,
        all_events: List[Dict[str, Any]],
        critical_events: List[Dict[str, Any]],
        other_events: List[Dict[str, Any]],
    ) -> str:
        """Generate summary text from events"""

        # Count event types
        event_type_counts = {}
        for event in other_events:
            event_type = event.get("event_type", "unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        # Build summary
        summary_parts = [
            f"Session processed {len(all_events)} events.",
            f"Preserved {len(critical_events)} critical events.",
        ]

        if event_type_counts:
            summary_parts.append("Event summary:")
            for event_type, count in sorted(
                event_type_counts.items(), key=lambda x: x[1], reverse=True
            ):
                summary_parts.append(f"  - {event_type}: {count}")

        return " ".join(summary_parts)

    def write_compaction_event(self, result: CompactionResult) -> None:
        """
        Write compaction event to session JSONL and create archive.

        Args:
            result: CompactionResult from compaction operation
        """
        # Write compaction_triggered event to session JSONL
        compaction_event = {
            "event_type": "compaction_triggered",
            "session_id": result.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "compaction_id": result.compaction_id,
            "trigger_reason": "threshold_exceeded",
            "events_before_count": result.events_before_count,
            "events_after_count": result.events_after_count,
            "tokens_before": result.tokens_before,
            "tokens_after": result.tokens_after,
            "compaction_method": result.method,
            "compression_ratio": result.compression_ratio,
        }

        write_event(result.session_id, compaction_event)

        # Write compaction_completed event
        completed_event = {
            "event_type": "compaction_completed",
            "session_id": result.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "compaction_id": result.compaction_id,
            "method": result.method,
            "events_compacted": result.events_before_count - result.events_after_count,
            "summary_text": result.summary_text,
            "compression_ratio": result.compression_ratio,
        }

        write_event(result.session_id, completed_event)

        # Write compaction archive for auditability
        self._write_compaction_archive(result)

        logger.info(
            f"Compaction events written for session={result.session_id}, "
            f"compaction_id={result.compaction_id}"
        )

    def _write_compaction_archive(self, result: CompactionResult) -> None:
        """Write compaction archive to storage/compactions/"""
        try:
            # Create compactions directory if it doesn't exist
            compactions_dir = Path("storage/compactions")
            compactions_dir.mkdir(parents=True, exist_ok=True)

            # Archive filename
            archive_filename = (
                f"{result.session_id}_compaction_{result.compaction_id}.json"
            )
            archive_path = compactions_dir / archive_filename

            # Archive data
            archive = {
                "compaction_id": result.compaction_id,
                "session_id": result.session_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "method": result.method,
                "events_compacted_count": result.events_before_count
                - result.events_after_count,
                "events_retained_count": result.events_after_count,
                "compression_ratio": result.compression_ratio,
                "summary": {
                    "summary_text": result.summary_text,
                    "tokens_before": result.tokens_before,
                    "tokens_after": result.tokens_after,
                },
                "original_events": result.compacted_events,
            }

            # Write to file
            with open(archive_path, "w") as f:
                json.dump(archive, f, indent=2)

            logger.info(f"Compaction archive written to {archive_path}")

        except Exception as e:
            logger.error(
                f"Failed to write compaction archive for session={result.session_id}: {e}",
                exc_info=True,
            )

    def _estimate_tokens(self, events: List[Dict[str, Any]]) -> int:
        """Estimate tokens in events (simplified: 4 chars ≈ 1 token)"""
        try:
            events_str = json.dumps(events)
            return len(events_str) // 4
        except:
            return 0
