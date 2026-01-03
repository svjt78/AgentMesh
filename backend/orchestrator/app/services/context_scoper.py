"""
ContextScoper - Service for scoping context during agent handoffs.

Implements:
- Handoff mode enforcement (full, scoped, minimal)
- Field-level filtering (allow/block lists)
- Token optimization through scoping
- Governance rule application
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.models.handoff_models import (
    HandoffMode,
    HandoffRule,
    HandoffPolicyConfig,
    ScopedContext,
    ContextSummary,
    create_context_summary,
)

logger = logging.getLogger(__name__)


class ContextScoper:
    """
    Applies scoping rules to context during agent handoffs.

    Scoping reduces token usage and enforces security by limiting
    what context each agent receives from prior agents.
    """

    def __init__(self):
        """Initialize context scoper with governance policies."""
        self.enabled = self._check_if_enabled()
        self.handoff_policy = self._load_handoff_policy()
        logger.info(f"ContextScoper initialized (enabled={self.enabled})")

    def _check_if_enabled(self) -> bool:
        """Check if multi-agent handoffs are enabled in system config."""
        try:
            import os
            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            config_file = Path(registry_path) / "system_config.json"

            with open(config_file, 'r') as f:
                config = json.load(f)

            enabled = config.get("multi_agent_handoffs", {}).get("enabled", False)
            return enabled

        except Exception as e:
            logger.warning(f"Failed to check handoff config, defaulting to disabled: {e}")
            return False

    def _load_handoff_policy(self) -> HandoffPolicyConfig:
        """Load handoff governance policies from registry."""
        try:
            import os
            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            policy_file = Path(registry_path) / "governance_policies.json"

            with open(policy_file, 'r') as f:
                policies = json.load(f)

            handoff_config = policies.get("policies", {}).get("multi_agent_handoffs", {})

            # Convert to HandoffPolicyConfig
            policy = HandoffPolicyConfig(
                default_handoff_mode=HandoffMode(handoff_config.get("default_handoff_mode", "scoped")),
                enable_conversation_translation=handoff_config.get("enable_conversation_translation", True),
                audit_all_handoffs=handoff_config.get("audit_all_handoffs", True),
                agent_handoff_rules=[
                    HandoffRule(**rule) for rule in handoff_config.get("agent_handoff_rules", [])
                ]
            )

            logger.info(f"Loaded {len(policy.agent_handoff_rules)} handoff rules")
            return policy

        except Exception as e:
            logger.error(f"Failed to load handoff policy: {e}")
            # Return default policy
            return HandoffPolicyConfig()

    def scope_context_for_handoff(
        self,
        prior_outputs: Dict[str, Any],
        observations: List[Dict[str, Any]],
        original_input: Optional[Dict[str, Any]],
        from_agent_id: str,
        to_agent_id: str
    ) -> ScopedContext:
        """
        Apply scoping rules to context for agent handoff.

        Args:
            prior_outputs: Outputs from previous agents
            observations: Observations from current agent
            original_input: Original workflow input
            from_agent_id: Source agent ID
            to_agent_id: Destination agent ID

        Returns:
            ScopedContext with filtered context
        """
        # If handoff scoping is disabled, return full context
        if not self.enabled:
            logger.debug("Handoff scoping disabled, returning full context")
            return ScopedContext(
                prior_outputs=prior_outputs.copy(),
                observations=observations.copy() if observations else [],
                original_input=original_input,
                handoff_mode=HandoffMode.FULL,
                fields_filtered=[],
                translation_applied=False
            )

        logger.info(
            f"Scoping context for handoff: {from_agent_id} → {to_agent_id}"
        )

        # Get handoff rule for this agent pair
        rule = self.handoff_policy.get_rule_for_handoff(from_agent_id, to_agent_id)

        if not rule:
            # No specific rule, use default mode
            handoff_mode = self.handoff_policy.default_handoff_mode
            logger.info(f"No specific rule found, using default mode: {handoff_mode}")
        else:
            handoff_mode = rule.handoff_mode
            logger.info(
                f"Applying rule '{rule.rule_id}': mode={handoff_mode}, "
                f"allowed_fields={rule.allowed_context_fields}"
            )

        # Apply scoping based on mode
        if handoff_mode == HandoffMode.FULL:
            scoped_context = self._apply_full_mode(
                prior_outputs, observations, original_input
            )
        elif handoff_mode == HandoffMode.SCOPED:
            scoped_context = self._apply_scoped_mode(
                prior_outputs, observations, original_input, rule
            )
        elif handoff_mode == HandoffMode.MINIMAL:
            scoped_context = self._apply_minimal_mode(original_input)
        else:
            logger.warning(f"Unknown handoff mode: {handoff_mode}, defaulting to scoped")
            scoped_context = self._apply_scoped_mode(
                prior_outputs, observations, original_input, rule
            )

        scoped_context.handoff_mode = handoff_mode

        logger.info(
            f"Context scoped: {len(prior_outputs)} → {len(scoped_context.prior_outputs)} "
            f"prior outputs, mode={handoff_mode}"
        )

        return scoped_context

    def _apply_full_mode(
        self,
        prior_outputs: Dict[str, Any],
        observations: List[Dict[str, Any]],
        original_input: Optional[Dict[str, Any]]
    ) -> ScopedContext:
        """Full mode: Pass all context without filtering."""
        return ScopedContext(
            prior_outputs=prior_outputs.copy(),
            observations=observations.copy() if observations else [],
            original_input=original_input,
            handoff_mode=HandoffMode.FULL,
            fields_filtered=[],
            translation_applied=False
        )

    def _apply_scoped_mode(
        self,
        prior_outputs: Dict[str, Any],
        observations: List[Dict[str, Any]],
        original_input: Optional[Dict[str, Any]],
        rule: Optional[HandoffRule]
    ) -> ScopedContext:
        """Scoped mode: Filter to allowed fields only."""

        if not rule or not rule.allowed_context_fields:
            # No field restrictions specified, pass all
            logger.warning("Scoped mode but no allowed_context_fields specified, passing all")
            return ScopedContext(
                prior_outputs=prior_outputs.copy(),
                observations=observations.copy() if observations else [],
                original_input=original_input,
                handoff_mode=HandoffMode.SCOPED,
                fields_filtered=[],
                translation_applied=False
            )

        # Filter prior outputs to allowed fields
        scoped_prior_outputs = {}
        fields_filtered = []

        for agent_id, output in prior_outputs.items():
            if isinstance(output, dict):
                # Filter fields in this agent's output
                scoped_output, filtered = self._filter_fields(
                    output,
                    rule.allowed_context_fields,
                    rule.blocked_context_fields
                )
                scoped_prior_outputs[agent_id] = scoped_output
                fields_filtered.extend(filtered)
            else:
                # Non-dict output, pass through
                scoped_prior_outputs[agent_id] = output

        return ScopedContext(
            prior_outputs=scoped_prior_outputs,
            observations=observations.copy() if observations else [],
            original_input=original_input,
            handoff_mode=HandoffMode.SCOPED,
            fields_filtered=fields_filtered,
            translation_applied=False
        )

    def _apply_minimal_mode(
        self,
        original_input: Optional[Dict[str, Any]]
    ) -> ScopedContext:
        """Minimal mode: Only essential trigger information."""

        # Extract minimal metadata from original input
        minimal_input = None
        if original_input:
            # Keep only basic identifiers
            minimal_input = {
                key: value for key, value in original_input.items()
                if key in ["claim_id", "policy_id", "workflow_id", "session_id"]
            }

        return ScopedContext(
            prior_outputs={},
            observations=[],
            original_input=minimal_input,
            handoff_mode=HandoffMode.MINIMAL,
            fields_filtered=list(original_input.keys()) if original_input else [],
            translation_applied=False
        )

    def _filter_fields(
        self,
        data: Dict[str, Any],
        allowed_fields: Optional[List[str]],
        blocked_fields: Optional[List[str]]
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Filter dictionary to allowed fields and remove blocked fields.

        Returns:
            (filtered_data, list_of_filtered_field_names)
        """
        filtered_data = {}
        filtered_fields = []

        for key, value in data.items():
            # Check if blocked
            if blocked_fields and key in blocked_fields:
                filtered_fields.append(key)
                continue

            # Check if allowed (if allow list specified)
            if allowed_fields:
                if key in allowed_fields:
                    filtered_data[key] = value
                else:
                    filtered_fields.append(key)
            else:
                # No allow list, include (unless blocked)
                filtered_data[key] = value

        return filtered_data, filtered_fields

    def get_handoff_rule(
        self,
        from_agent_id: str,
        to_agent_id: str
    ) -> Optional[HandoffRule]:
        """Get the handoff rule for a specific agent pair."""
        return self.handoff_policy.get_rule_for_handoff(from_agent_id, to_agent_id)


# ============= Singleton Access =============

_context_scoper: Optional[ContextScoper] = None


def get_context_scoper() -> ContextScoper:
    """Get or create ContextScoper singleton."""
    global _context_scoper

    if _context_scoper is None:
        _context_scoper = ContextScoper()

    return _context_scoper
