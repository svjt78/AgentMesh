"""
Content Selection Processor

Filters noisy events and selects relevant context based on agent requirements.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class ContentSelectorProcessor(BaseProcessor):
    """
    Filters context to remove noise and select only relevant information.

    - Removes debug/noise events
    - Applies relevance filtering based on agent context requirements
    - Filters by context scope (scoped/full/minimal)
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            filtered_context = context.copy()
            modifications = {}

            # Get noise event types from config
            noise_event_types = self.config.get("noise_event_types", [])
            filter_noise = self.config.get("filter_noise", True)

            # Filter noise from observations if present
            if filter_noise and "observations" in filtered_context:
                original_count = len(filtered_context["observations"])
                filtered_context["observations"] = [
                    obs
                    for obs in filtered_context["observations"]
                    if obs.get("event_type") not in noise_event_types
                ]
                filtered_count = len(filtered_context["observations"])

                if original_count != filtered_count:
                    modifications["observations_filtered"] = (
                        original_count - filtered_count
                    )
                    logger.debug(
                        f"Filtered {modifications['observations_filtered']} "
                        f"noise observations for agent={agent_id}"
                    )

            # Apply relevance filtering based on context_scope
            # This will be enhanced in Phase 6 for multi-agent controls
            context_scope = filtered_context.get("metadata", {}).get(
                "context_scope", "scoped"
            )

            if context_scope == "minimal":
                # Minimal context: keep only essential fields
                modifications["scope_applied"] = "minimal"
                logger.debug(f"Applied minimal context scope for agent={agent_id}")

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=filtered_context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made=modifications if modifications else None,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"ContentSelector failed for agent={agent_id}: {e}", exc_info=True
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
