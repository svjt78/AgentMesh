"""
ConversationTranslator - Service for translating agent outputs during handoffs.

Implements:
- Field extraction from structured outputs
- Field filtering (remove blocked fields)
- Output condensation for token optimization
"""

import logging
from typing import Dict, Any, List, Optional

from app.models.handoff_models import ConversationTranslationConfig, HandoffRule

logger = logging.getLogger(__name__)


class ConversationTranslator:
    """
    Translates agent outputs for downstream consumption.

    Applies transformations like field extraction, filtering,
    and condensation to optimize context for receiving agents.
    """

    def __init__(self):
        """Initialize conversation translator."""
        logger.info("ConversationTranslator initialized")

    def translate_outputs(
        self,
        prior_outputs: Dict[str, Any],
        rule: Optional[HandoffRule]
    ) -> Dict[str, Any]:
        """
        Translate agent outputs based on handoff rule.

        Args:
            prior_outputs: Outputs from previous agents
            rule: Handoff rule with translation config

        Returns:
            Translated outputs
        """
        if not rule or not rule.conversation_translation:
            # No translation configured
            return prior_outputs

        translation_config = rule.conversation_translation
        if not translation_config.enabled:
            logger.debug("Conversation translation disabled for this rule")
            return prior_outputs

        logger.info(f"Translating outputs for rule: {rule.rule_id}")

        translated_outputs = {}

        for agent_id, output in prior_outputs.items():
            # Apply field extraction if configured
            if translation_config.extract_fields:
                output = self._extract_fields(output, translation_config.extract_fields)

            # Apply filtering if enabled (already done by scoper, but double-check)
            if translation_config.filter_enabled and rule.blocked_context_fields:
                output = self._filter_blocked_fields(output, rule.blocked_context_fields)

            # For now, skip summarization (would require LLM call)
            # TODO: Implement LLM-based summarization in future

            translated_outputs[agent_id] = output

        return translated_outputs

    def _extract_fields(
        self,
        output: Any,
        fields_to_extract: List[str]
    ) -> Dict[str, Any]:
        """Extract only specified fields from output."""
        if not isinstance(output, dict):
            logger.warning(f"Cannot extract fields from non-dict output: {type(output)}")
            return output

        extracted = {}
        for field in fields_to_extract:
            if field in output:
                extracted[field] = output[field]
            else:
                logger.debug(f"Field '{field}' not found in output for extraction")

        logger.debug(f"Extracted {len(extracted)}/{len(fields_to_extract)} fields")
        return extracted

    def _filter_blocked_fields(
        self,
        output: Any,
        blocked_fields: List[str]
    ) -> Any:
        """Remove blocked fields from output."""
        if not isinstance(output, dict):
            return output

        filtered = {
            key: value for key, value in output.items()
            if key not in blocked_fields
        }

        removed_count = len(output) - len(filtered)
        if removed_count > 0:
            logger.debug(f"Filtered out {removed_count} blocked fields")

        return filtered


# ============= Singleton Access =============

_conversation_translator: Optional[ConversationTranslator] = None


def get_conversation_translator() -> ConversationTranslator:
    """Get or create ConversationTranslator singleton."""
    global _conversation_translator

    if _conversation_translator is None:
        _conversation_translator = ConversationTranslator()

    return _conversation_translator
