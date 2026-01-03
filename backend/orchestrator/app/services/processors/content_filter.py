"""
Content Filter Processor (Phase 8 Implementation)

Deterministic pre-LLM filtering of context data based on governance rules.
Removes noise, masks PII, enforces security policies before LLM sees context.
"""

import time
import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.services.storage import write_event

logger = logging.getLogger(__name__)


class ContentFilterProcessor(BaseProcessor):
    """
    Applies deterministic filtering rules to context before LLM consumption.

    Phase 8: Advanced Features
    - Age-based filtering (remove old observations)
    - Regex masking (PII protection - SSN, credit cards, etc.)
    - Field value matching (remove debug logs, etc.)
    - All filtering decisions logged for audit
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            filtering_rules = self._load_filtering_rules()

            # If filtering disabled globally, skip
            if not filtering_rules.get("enabled", False):
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made={"status": "filtering_disabled"},
                )

            filtered_context = context.copy()
            filtering_log = []

            # Apply each rule
            for rule in filtering_rules.get("rules", []):
                if not rule.get("enabled", True):
                    continue  # Skip disabled rules

                result = self._apply_rule(rule, filtered_context)

                if result["modified"]:
                    filtering_log.append({
                        "rule_id": rule["rule_id"],
                        "field": rule["field"],
                        "items_filtered": result.get("items_filtered", 0),
                        "items_masked": result.get("items_masked", 0),
                        "description": rule["description"],
                    })

                    logger.info(
                        f"Filter rule applied: {rule['rule_id']} - "
                        f"field={rule['field']}, filtered={result.get('items_filtered', 0)}, "
                        f"masked={result.get('items_masked', 0)}"
                    )

            # Add metadata to context
            if "metadata" not in filtered_context:
                filtered_context["metadata"] = {}

            filtered_context["metadata"]["filtering_applied"] = len(filtering_log) > 0
            filtered_context["metadata"]["filtering_rules_triggered"] = len(filtering_log)

            # Log filtering event if any rules were applied
            if filtering_log:
                self._log_filtering_event(session_id, agent_id, filtering_log)

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=filtered_context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made={
                    "filtering_applied": len(filtering_log) > 0,
                    "rules_triggered": len(filtering_log),
                    "filtering_log": filtering_log,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"ContentFilter failed for session={session_id}: {e}",
                exc_info=True,
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _load_filtering_rules(self) -> Dict[str, Any]:
        """Load filtering rules from governance policies."""
        try:
            import os

            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            policy_file = Path(registry_path) / "governance_policies.json"

            with open(policy_file, "r") as f:
                policies = json.load(f)

            filtering_config = policies.get("policies", {}).get("context_filtering", {})
            return filtering_config

        except Exception as e:
            logger.error(f"Failed to load filtering rules: {e}", exc_info=True)
            return {"enabled": False, "rules": []}

    def _apply_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a single filtering rule to context.

        Returns dict with: {"modified": bool, "items_filtered": int, "items_masked": int}
        """
        condition_type = rule["condition"]["type"]

        if condition_type == "age_threshold":
            return self._filter_by_age(rule, context)
        elif condition_type == "regex_mask":
            return self._mask_by_regex(rule, context)
        elif condition_type == "field_value_match":
            return self._filter_by_field_match(rule, context)
        else:
            logger.warning(f"Unknown filter condition type: {condition_type}")
            return {"modified": False}

    def _filter_by_age(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter items older than threshold.

        Example: Remove observations older than 30 days.
        """
        field = rule["field"]
        max_age_days = rule["condition"]["max_age_days"]

        if field not in context or not isinstance(context[field], list):
            return {"modified": False, "items_filtered": 0}

        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        original_count = len(context[field])

        # Filter items with timestamp older than cutoff
        filtered_items = []
        for item in context[field]:
            # Try to extract timestamp
            timestamp = None
            if isinstance(item, dict):
                timestamp = item.get("timestamp") or item.get("created_at")

            if timestamp:
                try:
                    item_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if item_date.replace(tzinfo=None) >= cutoff_date:
                        filtered_items.append(item)
                except Exception:
                    # Keep item if can't parse timestamp
                    filtered_items.append(item)
            else:
                # Keep item if no timestamp
                filtered_items.append(item)

        context[field] = filtered_items
        items_removed = original_count - len(filtered_items)

        return {
            "modified": items_removed > 0,
            "items_filtered": items_removed,
        }

    def _mask_by_regex(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask patterns using regex replacement.

        Example: Mask SSN (123-45-6789 → ***-**-****)
        """
        field = rule["field"]
        patterns = rule["condition"]["patterns"]

        if field not in context:
            return {"modified": False, "items_masked": 0}

        total_masked = 0

        # Apply masking to string fields
        def mask_text(text: str) -> tuple[str, int]:
            """Mask text and return (masked_text, count_of_masks)"""
            if not isinstance(text, str):
                return text, 0

            masked_text = text
            mask_count = 0

            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                replacement = pattern_config["replacement"]

                # Count matches before replacement
                matches = re.findall(pattern, masked_text)
                mask_count += len(matches)

                # Apply replacement
                masked_text = re.sub(pattern, replacement, masked_text)

            return masked_text, mask_count

        # Apply masking based on field type
        if isinstance(context[field], str):
            # String field
            context[field], total_masked = mask_text(context[field])

        elif isinstance(context[field], dict):
            # Dict field - recurse through values
            for key, value in context[field].items():
                if isinstance(value, str):
                    context[field][key], count = mask_text(value)
                    total_masked += count

        elif isinstance(context[field], list):
            # List field - process each item
            for i, item in enumerate(context[field]):
                if isinstance(item, str):
                    context[field][i], count = mask_text(item)
                    total_masked += count
                elif isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str):
                            item[key], count = mask_text(value)
                            total_masked += count

        return {
            "modified": total_masked > 0,
            "items_masked": total_masked,
        }

    def _filter_by_field_match(
        self, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter items by field value match.

        Example: Remove observations where log_level == "debug"
        """
        field = rule["field"]
        match_field = rule["condition"]["match_field"]
        match_value = rule["condition"]["match_value"]

        if field not in context or not isinstance(context[field], list):
            return {"modified": False, "items_filtered": 0}

        original_count = len(context[field])

        # Filter items where match_field != match_value
        filtered_items = []
        for item in context[field]:
            if isinstance(item, dict):
                if item.get(match_field) != match_value:
                    filtered_items.append(item)
            else:
                # Keep non-dict items
                filtered_items.append(item)

        context[field] = filtered_items
        items_removed = original_count - len(filtered_items)

        return {
            "modified": items_removed > 0,
            "items_filtered": items_removed,
        }

    def _log_filtering_event(
        self, session_id: str, agent_id: str, filtering_log: List[Dict[str, Any]]
    ) -> None:
        """Log filtering event for audit trail."""
        event = {
            "event_type": "content_filtered",
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "filtering_log": filtering_log,
            "total_rules_triggered": len(filtering_log),
        }

        write_event(session_id, event)

        logger.info(
            f"Content filtering event logged for session={session_id}: "
            f"{len(filtering_log)} rules applied"
        )
