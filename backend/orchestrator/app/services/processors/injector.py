"""
Context Injection Processor

Final formatting and injection of context into LLM-ready format.
Produces a clean, traceable prompt boundary.
"""

import time
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.services.processors.base_processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class InjectorProcessor(BaseProcessor):
    """
    Final processor that formats context for LLM consumption.

    - Formats context into LLM-ready structure
    - Separates stable prefix from variable suffix (for caching)
    - Produces final compiled context
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            final_context = context.copy()
            modifications = {}

            format_type = self.config.get("format", "llm_ready")

            if format_type == "llm_ready":
                # Create LLM-ready context structure
                llm_context = {
                    "agent_id": agent_id,
                    "session_id": session_id,
                }

                # Include original input if present
                if "original_input" in context and context["original_input"]:
                    llm_context["original_input"] = context["original_input"]
                    modifications["included_original_input"] = True

                # Include prior outputs if present
                if "prior_outputs" in context and context["prior_outputs"]:
                    llm_context["prior_outputs"] = context["prior_outputs"]
                    modifications["prior_outputs_count"] = len(
                        context["prior_outputs"]
                    )

                # Include observations/messages if present
                if "message_observations" in context:
                    llm_context["observations"] = context["message_observations"]
                    modifications["observations_count"] = len(
                        context["message_observations"]
                    )
                elif "observations" in context:
                    llm_context["observations"] = context["observations"]
                    modifications["observations_count"] = len(context["observations"])

                # Preserve metadata
                if "metadata" in context:
                    llm_context["metadata"] = context["metadata"]

                final_context["compiled_context"] = llm_context
                modifications["format_applied"] = format_type

            # Phase 7: Apply prefix/suffix separation for caching
            final_context["metadata"] = final_context.get("metadata", {})
            caching_config = self._load_caching_config()

            if caching_config.get("enabled", False):
                prefix_data, suffix_data, cache_key = self._separate_prefix_suffix(
                    context=final_context,
                    agent_id=agent_id,
                    caching_config=caching_config
                )

                final_context["metadata"]["prefix_caching_ready"] = True
                final_context["metadata"]["cache_key"] = cache_key
                final_context["metadata"]["prefix_components"] = list(prefix_data.keys())
                final_context["metadata"]["suffix_components"] = list(suffix_data.keys())

                # Store separated components for LLM client to use
                final_context["prefix_cache"] = {
                    "data": prefix_data,
                    "cache_key": cache_key,
                    "cache_control": {"type": "ephemeral"}  # Anthropic format
                }
                final_context["suffix_data"] = suffix_data

                modifications["prefix_caching_applied"] = True
                modifications["cache_key"] = cache_key

                logger.info(
                    f"Prefix caching enabled for agent={agent_id}, "
                    f"cache_key={cache_key}, "
                    f"prefix_components={len(prefix_data)}, "
                    f"suffix_components={len(suffix_data)}"
                )
            else:
                final_context["metadata"]["prefix_caching_ready"] = False
                logger.debug("Prefix caching disabled in system config")

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=final_context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made=modifications if modifications else None,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Injector failed for agent={agent_id}: {e}", exc_info=True)
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _load_caching_config(self) -> Dict[str, Any]:
        """Load prefix caching configuration from system config."""
        try:
            import os
            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            config_file = Path(registry_path) / "system_config.json"

            with open(config_file, 'r') as f:
                config = json.load(f)

            caching_config = config.get("prefix_caching", {})
            return caching_config

        except Exception as e:
            logger.warning(f"Failed to load caching config: {e}")
            return {"enabled": False}

    def _separate_prefix_suffix(
        self,
        context: Dict[str, Any],
        agent_id: str,
        caching_config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Separate context into cacheable prefix and variable suffix.

        Returns:
            (prefix_data, suffix_data, cache_key)
        """
        stable_components = caching_config.get("stable_prefix_components", [
            "system_instructions",
            "agent_identity",
            "tool_schemas"
        ])
        variable_components = caching_config.get("variable_suffix_components", [
            "recent_observations",
            "current_task",
            "session_context"
        ])

        prefix_data = {}
        suffix_data = {}

        # Compiled context from earlier in pipeline
        compiled = context.get("compiled_context", {})

        # Stable components (prefix) - things that don't change
        if "agent_identity" in stable_components:
            prefix_data["agent_id"] = compiled.get("agent_id")
            prefix_data["session_id"] = compiled.get("session_id")

        # System instructions would come from agent registry
        # For now, we'll use agent_id as a proxy
        if "system_instructions" in stable_components:
            prefix_data["system_instructions"] = f"Agent: {agent_id}"

        # Tool schemas - these are stable for an agent
        if "tool_schemas" in stable_components:
            # Would normally load from registry, but for now just mark as included
            prefix_data["tool_schemas"] = "stable"

        # Variable components (suffix) - things that change each iteration
        if "session_context" in variable_components:
            if compiled.get("original_input"):
                suffix_data["original_input"] = compiled["original_input"]

        if "recent_observations" in variable_components:
            if compiled.get("observations"):
                suffix_data["observations"] = compiled["observations"]

        if "current_task" in variable_components or "prior_outputs" in variable_components:
            if compiled.get("prior_outputs"):
                suffix_data["prior_outputs"] = compiled["prior_outputs"]

        # Generate cache key based on stable components
        cache_key = self._generate_cache_key(agent_id, prefix_data)

        return prefix_data, suffix_data, cache_key

    def _generate_cache_key(
        self,
        agent_id: str,
        prefix_data: Dict[str, Any]
    ) -> str:
        """
        Generate cache key for prefix.

        Format: {agent_id}:{prefix_hash}
        """
        # Create deterministic hash of prefix data
        prefix_str = json.dumps(prefix_data, sort_keys=True)
        prefix_hash = hashlib.md5(prefix_str.encode()).hexdigest()[:8]

        cache_key = f"{agent_id}:{prefix_hash}"
        return cache_key
