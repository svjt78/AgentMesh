"""
Compaction Checker Processor (Phase 2 Implementation)

Checks if context compaction should be triggered based on thresholds.
Triggers CompactionManager if thresholds exceeded.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.config import get_config

logger = logging.getLogger(__name__)


class CompactionCheckerProcessor(BaseProcessor):
    """
    Checks if compaction should be triggered and executes compaction.

    - Checks token/event thresholds from configuration
    - Triggers CompactionManager if needed
    - Writes compaction events to session JSONL
    - Updates context with compacted events
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            config = get_config()
            modifications = {}

            # Check if compaction is enabled
            if not config.compaction.enabled:
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made={"status": "compaction_disabled"},
                )

            # Check if compaction should trigger
            check_threshold = self.config.get("check_threshold", True)

            if not check_threshold:
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made={"status": "threshold_check_disabled"},
                )

            # Get session events from context (if available)
            # In production, this would read from storage/sessions/{session_id}.jsonl
            # For Phase 2, we'll check observations as a proxy
            observations = context.get("observations", [])
            estimated_tokens = context.get("metadata", {}).get("estimated_tokens", 0)

            # Import CompactionManager
            from app.services.compaction_manager import CompactionManager

            compaction_manager = CompactionManager(session_id)

            # Check if compaction needed
            if compaction_manager.check_compaction_needed(observations, estimated_tokens):
                logger.info(
                    f"Compaction threshold exceeded for session={session_id}, "
                    f"triggering compaction"
                )

                # Trigger compaction
                method = config.compaction.method
                result = compaction_manager.compact_events(observations, method)

                # Write compaction events
                compaction_manager.write_compaction_event(result)

                # Update context with compacted events
                context["observations"] = result.compacted_events

                modifications["compaction_triggered"] = True
                modifications["compaction_id"] = result.compaction_id
                modifications["events_before"] = result.events_before_count
                modifications["events_after"] = result.events_after_count
                modifications["compression_ratio"] = result.compression_ratio

                logger.info(
                    f"Compaction completed for session={session_id}: "
                    f"{result.events_before_count} → {result.events_after_count} events"
                )
            else:
                modifications["compaction_triggered"] = False
                modifications["reason"] = "threshold_not_exceeded"

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made=modifications,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"CompactionChecker failed for session={session_id}: {e}",
                exc_info=True,
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
