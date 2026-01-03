"""
Token Budget Enforcement Processor

Enforces token limits and truncates context if needed.
This is a critical processor that prevents context bloat.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class TokenBudgetEnforcerProcessor(BaseProcessor):
    """
    Enforces token budget limits.

    - Counts tokens in context
    - Truncates if exceeds agent's max_context_tokens
    - Prioritizes recent observations
    - Logs truncation events

    Uses simplified token counting for Phase 1.
    Phase 5 will integrate with existing ContextCompiler token counting logic.
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            enforce_limits = self.config.get("enforce_limits", True)

            if not enforce_limits:
                # Passthrough if enforcement disabled
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                )

            # Get max tokens from context metadata (set by registry)
            max_tokens = context.get("metadata", {}).get("max_context_tokens", 10000)

            # Simplified token estimation (4 chars ≈ 1 token)
            # Full implementation will use tiktoken
            estimated_tokens = self._estimate_tokens(context)

            modifications = {
                "estimated_tokens": estimated_tokens,
                "max_tokens": max_tokens,
            }

            if estimated_tokens > max_tokens:
                # Truncation needed
                truncated_context = self._truncate_context(
                    context, estimated_tokens, max_tokens
                )
                final_tokens = self._estimate_tokens(truncated_context)

                modifications["truncation_applied"] = True
                modifications["tokens_before"] = estimated_tokens
                modifications["tokens_after"] = final_tokens

                logger.warning(
                    f"Context truncated for agent={agent_id}: "
                    f"{estimated_tokens} → {final_tokens} tokens "
                    f"(max: {max_tokens})"
                )

                execution_time_ms = (time.time() - start_time) * 1000

                return self._create_result(
                    context=truncated_context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made=modifications,
                )

            # Within budget
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
                f"TokenBudgetEnforcer failed for agent={agent_id}: {e}",
                exc_info=True,
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _estimate_tokens(self, context: Dict[str, Any]) -> int:
        """Simplified token estimation (4 chars ≈ 1 token)"""
        import json

        try:
            context_str = json.dumps(context)
            return len(context_str) // 4
        except:
            return 0

    def _truncate_context(
        self, context: Dict[str, Any], current_tokens: int, max_tokens: int
    ) -> Dict[str, Any]:
        """
        Truncate context to fit within budget.

        Prioritizes:
        1. Original input (always keep if possible)
        2. Prior outputs (keep required ones)
        3. Recent observations over old ones
        """
        truncated = context.copy()
        truncation_strategy = self.config.get("truncation_strategy", "prioritize_recent")

        # Simple strategy: Truncate observations from oldest first
        if "observations" in truncated and truncated["observations"]:
            # Keep only recent observations
            target_reduction = current_tokens - max_tokens
            removed_count = 0

            while removed_count < len(truncated["observations"]) and target_reduction > 0:
                # Remove oldest observation
                truncated["observations"].pop(0)
                removed_count += 1
                # Re-estimate
                current_tokens = self._estimate_tokens(truncated)
                target_reduction = current_tokens - max_tokens

        return truncated
