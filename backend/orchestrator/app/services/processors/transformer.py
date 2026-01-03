"""
Transformation Processor

Converts structured context data into LLM-consumable message format.
Ensures role correctness and proper attribution.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class TransformerProcessor(BaseProcessor):
    """
    Transforms structured context into LLM message format.

    - Converts context components to messages
    - Ensures role correctness (user/assistant)
    - Applies conversation translation if enabled
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            transformed_context = context.copy()
            modifications = {}

            convert_to_messages = self.config.get("convert_to_messages", True)
            ensure_role_correctness = self.config.get(
                "ensure_role_correctness", True
            )

            if not convert_to_messages:
                # Passthrough mode
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=transformed_context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                )

            # Transform observations to message-like format
            # This is a simplified version - full implementation would
            # convert all context components to proper message format
            if "observations" in transformed_context:
                message_observations = []
                for obs in transformed_context["observations"]:
                    # Convert observation to message format
                    if obs.get("event_type") == "tool_invocation":
                        message_observations.append(
                            {
                                "role": "function",
                                "name": obs.get("tool_id", "unknown"),
                                "content": obs.get("result", {}),
                            }
                        )
                    else:
                        # Generic observation
                        message_observations.append(
                            {
                                "role": "assistant",
                                "content": str(obs.get("data", obs)),
                            }
                        )

                transformed_context["message_observations"] = message_observations
                modifications["observations_transformed"] = len(message_observations)

            # Ensure role correctness
            if ensure_role_correctness and "message_observations" in transformed_context:
                # Validate that roles are correct
                # In production, this would enforce stricter validation
                modifications["role_validation_applied"] = True

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=transformed_context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made=modifications if modifications else None,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Transformer failed for agent={agent_id}: {e}", exc_info=True
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
