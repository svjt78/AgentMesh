"""
Governance Auditor (Phase 8 Implementation)

Centralized auditing service for all context engineering decisions.
Logs every context decision for compliance, debugging, and governance.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.storage import write_event

logger = logging.getLogger(__name__)


class GovernanceAuditor:
    """
    Centralized governance auditing for context engineering decisions.

    Phase 8: Advanced Features
    - Logs all context inclusion/exclusion decisions
    - Tracks token budget enforcement
    - Records memory and artifact access
    - Provides comprehensive audit trail for compliance
    """

    def __init__(self, session_id: str):
        """
        Initialize auditor for a session.

        Args:
            session_id: Session ID for event logging
        """
        self.session_id = session_id

    def log_context_decision(
        self,
        decision_type: str,
        component: str,
        action: str,
        rationale: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a context engineering decision.

        Args:
            decision_type: Type of decision ("inclusion", "exclusion", "filtering", "limiting", "token_budget")
            component: What component was affected ("memory", "artifact", "observation", "prior_output", etc.)
            action: Action taken ("included", "excluded", "masked", "truncated", "retrieved", etc.)
            rationale: Human-readable reason for the decision
            metadata: Additional structured data about the decision
        """
        try:
            event = {
                "event_type": "governance_audit",
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "decision_type": decision_type,
                "component": component,
                "action": action,
                "rationale": rationale,
                "metadata": metadata or {},
            }

            write_event(self.session_id, event)

            logger.debug(
                f"Governance audit logged: type={decision_type}, "
                f"component={component}, action={action}"
            )

        except Exception as e:
            logger.error(f"Failed to log governance decision: {e}", exc_info=True)

    def log_token_budget_decision(
        self,
        component: str,
        action: str,
        tokens_before: int,
        tokens_after: int,
        max_tokens: int,
        reason: str,
    ) -> None:
        """
        Log token budget enforcement decision.

        Args:
            component: What was truncated/limited
            action: "truncated" or "limited"
            tokens_before: Token count before enforcement
            tokens_after: Token count after enforcement
            max_tokens: Maximum token limit
            reason: Why enforcement was triggered
        """
        self.log_context_decision(
            decision_type="token_budget",
            component=component,
            action=action,
            rationale=reason,
            metadata={
                "tokens_before": tokens_before,
                "tokens_after": tokens_after,
                "max_tokens": max_tokens,
                "tokens_saved": tokens_before - tokens_after,
            },
        )

    def log_memory_retrieval(
        self,
        retrieval_mode: str,
        query: str,
        memories_found: int,
        memory_ids: list,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log memory retrieval decision.

        Args:
            retrieval_mode: "reactive" or "proactive"
            query: Query text used for retrieval
            memories_found: Number of memories retrieved
            memory_ids: List of memory IDs retrieved
            metadata: Additional metadata (similarity scores, etc.)
        """
        self.log_context_decision(
            decision_type="memory_retrieval",
            component="memory",
            action=f"retrieved_{memories_found}",
            rationale=f"Query: {query[:100]}, Mode: {retrieval_mode}",
            metadata={
                "retrieval_mode": retrieval_mode,
                "query": query,
                "memories_found": memories_found,
                "memory_ids": memory_ids,
                **(metadata or {}),
            },
        )

    def log_artifact_access(
        self,
        artifact_id: str,
        version: Optional[int],
        action: str,
        size_bytes: Optional[int] = None,
    ) -> None:
        """
        Log artifact access decision.

        Args:
            artifact_id: Artifact identifier
            version: Artifact version (if applicable)
            action: "loaded", "excluded", "limited"
            size_bytes: Artifact size (if known)
        """
        self.log_context_decision(
            decision_type="artifact_access",
            component="artifact",
            action=action,
            rationale=f"Artifact {artifact_id}" + (f" v{version}" if version else ""),
            metadata={
                "artifact_id": artifact_id,
                "version": version,
                "size_bytes": size_bytes,
            },
        )

    def log_filtering_decision(
        self,
        rule_id: str,
        field: str,
        items_filtered: int,
        items_masked: int,
        description: str,
    ) -> None:
        """
        Log content filtering decision.

        Args:
            rule_id: Filtering rule identifier
            field: Field that was filtered
            items_filtered: Number of items removed
            items_masked: Number of items masked
            description: Rule description
        """
        action = []
        if items_filtered > 0:
            action.append(f"filtered_{items_filtered}")
        if items_masked > 0:
            action.append(f"masked_{items_masked}")

        self.log_context_decision(
            decision_type="filtering",
            component=field,
            action="_and_".join(action) if action else "no_action",
            rationale=f"Rule: {rule_id} - {description}",
            metadata={
                "rule_id": rule_id,
                "field": field,
                "items_filtered": items_filtered,
                "items_masked": items_masked,
            },
        )

    def log_compaction_decision(
        self,
        events_before: int,
        events_after: int,
        tokens_before: int,
        tokens_after: int,
        method: str,
    ) -> None:
        """
        Log context compaction decision.

        Args:
            events_before: Event count before compaction
            events_after: Event count after compaction
            tokens_before: Token count before compaction
            tokens_after: Token count after compaction
            method: Compaction method ("rule_based" or "llm_based")
        """
        self.log_context_decision(
            decision_type="compaction",
            component="session_context",
            action="compacted",
            rationale=f"Compacted {events_before} events to {events_after} using {method}",
            metadata={
                "events_before": events_before,
                "events_after": events_after,
                "tokens_before": tokens_before,
                "tokens_after": tokens_after,
                "method": method,
                "compression_ratio": round(events_after / events_before, 2) if events_before > 0 else 0,
            },
        )

    def log_governance_limit_exceeded(
        self,
        limit_type: str,
        requested: int,
        allowed: int,
        action_taken: str,
    ) -> None:
        """
        Log governance limit enforcement.

        Args:
            limit_type: Type of limit ("max_memories", "max_artifacts", "max_tokens", etc.)
            requested: Amount requested
            allowed: Maximum allowed
            action_taken: How limit was enforced ("truncated", "rejected", "queued")
        """
        self.log_context_decision(
            decision_type="limiting",
            component=limit_type,
            action=action_taken,
            rationale=f"Governance limit exceeded: {requested} > {allowed} ({limit_type})",
            metadata={
                "limit_type": limit_type,
                "requested": requested,
                "allowed": allowed,
                "exceeded_by": requested - allowed,
            },
        )


# Convenience function for getting auditor in processors
def get_governance_auditor(session_id: str) -> GovernanceAuditor:
    """
    Get a GovernanceAuditor instance for a session.

    Args:
        session_id: Session ID for event logging

    Returns:
        GovernanceAuditor instance
    """
    return GovernanceAuditor(session_id)
