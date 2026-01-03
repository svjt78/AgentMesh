"""
Memory Retriever Processor (Phase 3 Implementation)

Retrieves relevant memories from the Memory Layer during context compilation.
Supports both reactive (agent-controlled) and proactive (automatic) retrieval modes.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.config import get_config
from app.services.storage import write_event
from app.services.governance_auditor import get_governance_auditor

logger = logging.getLogger(__name__)


class MemoryRetrieverProcessor(BaseProcessor):
    """
    Retrieves relevant memories from the Memory Layer.

    - Reactive mode: Only retrieves when explicitly requested by agent
    - Proactive mode: Automatically retrieves relevant memories based on context
    - Adds retrieved memories to context for agent consumption
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            config = get_config()
            modifications = {}

            # Check if memory layer is enabled
            if not hasattr(config, 'memory') or not config.memory.enabled:
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made={"status": "memory_layer_disabled"},
                )

            # Get retrieval mode from config
            retrieval_mode = config.memory.retrieval_mode if hasattr(config.memory, 'retrieval_mode') else "reactive"

            # Import MemoryManager
            from app.services.memory_manager import get_memory_manager

            memory_manager = get_memory_manager()

            memories_retrieved = []

            if retrieval_mode == "reactive":
                # Reactive mode: Only retrieve if agent explicitly requests
                # Check if context has a memory_query field (set by agent)
                memory_query = context.get("memory_query")

                if memory_query:
                    logger.info(
                        f"Reactive memory retrieval triggered for agent={agent_id}, "
                        f"query={memory_query}"
                    )

                    # Retrieve memories matching query
                    memories = memory_manager.retrieve_memories(
                        query=memory_query.get("query"),
                        memory_type=memory_query.get("type"),
                        tags=memory_query.get("tags"),
                        limit=memory_query.get("limit", 5),
                        mode="reactive",
                    )

                    memories_retrieved = [
                        {
                            "memory_id": m.memory_id,
                            "memory_type": m.memory_type,
                            "content": m.content,
                            "created_at": m.created_at,
                            "tags": m.tags,
                        }
                        for m in memories
                    ]

                    # Add to context
                    if "memories" not in context:
                        context["memories"] = []
                    context["memories"].extend(memories_retrieved)

                    modifications["retrieval_mode"] = "reactive"
                    modifications["memories_retrieved"] = len(memories_retrieved)
                    modifications["query"] = memory_query.get("query")
                else:
                    modifications["retrieval_mode"] = "reactive"
                    modifications["memories_retrieved"] = 0
                    modifications["reason"] = "no_query_provided"

            elif retrieval_mode == "proactive":
                # Phase 8: Enhanced proactive mode with similarity search
                logger.info(
                    f"Proactive memory retrieval (similarity-based) triggered for agent={agent_id}"
                )

                # Load proactive settings from system config
                import os
                import json
                from pathlib import Path

                registry_path = os.environ.get("REGISTRY_PATH", "/registries")
                config_file = Path(registry_path) / "system_config.json"

                with open(config_file, 'r') as f:
                    system_config = json.load(f)

                proactive_settings = system_config.get("memory", {}).get("proactive_settings", {})

                if not proactive_settings.get("enabled", False):
                    logger.info("Proactive memory preloading disabled in config")
                    modifications["retrieval_mode"] = "proactive"
                    modifications["memories_retrieved"] = 0
                    modifications["reason"] = "proactive_preloading_disabled"
                else:
                    # Build query from original input
                    original_input = context.get("original_input", {})
                    query_text = self._build_query_from_context(original_input)

                    if not query_text:
                        logger.warning("Cannot build query from context, skipping proactive memory")
                        modifications["retrieval_mode"] = "proactive"
                        modifications["memories_retrieved"] = 0
                        modifications["reason"] = "no_query_text"
                    else:
                        # Use similarity search
                        max_memories = proactive_settings.get("max_memories_to_preload", 5)
                        similarity_threshold = proactive_settings.get("similarity_threshold", 0.7)
                        use_embeddings = proactive_settings.get("use_embeddings", False)

                        # Retrieve memories by similarity
                        scored_memories = memory_manager.retrieve_memories_by_similarity(
                            query_text=query_text,
                            limit=max_memories,
                            threshold=similarity_threshold,
                            use_embeddings=use_embeddings,
                        )

                        # Phase 8: Enforce governance limits
                        auditor = get_governance_auditor(session_id)

                        # Load governance limits
                        governance_limit = self._load_governance_limit("max_memory_retrievals_per_invocation", 10)

                        if len(scored_memories) > governance_limit:
                            logger.warning(
                                f"Memory limit exceeded: {len(scored_memories)} > {governance_limit}, truncating"
                            )

                            # Log governance limit enforcement
                            auditor.log_governance_limit_exceeded(
                                limit_type="max_memory_retrievals_per_invocation",
                                requested=len(scored_memories),
                                allowed=governance_limit,
                                action_taken="truncated",
                            )

                            # Truncate to limit
                            scored_memories = scored_memories[:governance_limit]

                        memories_retrieved = [
                            {
                                "memory_id": m.memory_id,
                                "memory_type": m.memory_type,
                                "content": m.content,
                                "created_at": m.created_at,
                                "tags": m.tags,
                                "similarity_score": score,  # Phase 8: Include similarity score
                            }
                            for m, score in scored_memories
                        ]

                        # Add to context
                        if "memories" not in context:
                            context["memories"] = []
                        context["memories"].extend(memories_retrieved)

                        modifications["retrieval_mode"] = "proactive"
                        modifications["memories_retrieved"] = len(memories_retrieved)
                        modifications["query"] = query_text
                        modifications["similarity_method"] = "embeddings" if use_embeddings else "keyword"
                        modifications["similarity_threshold"] = similarity_threshold

                        if memories_retrieved:
                            modifications["avg_similarity_score"] = sum(
                                m["similarity_score"] for m in memories_retrieved
                            ) / len(memories_retrieved)

            # Write memory retrieval event if memories were retrieved
            if memories_retrieved:
                memory_event = {
                    "event_type": "memory_retrieved",
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "retrieval_mode": retrieval_mode,
                    "query": modifications.get("query"),
                    "memories_found": len(memories_retrieved),
                    "memory_ids": [m["memory_id"] for m in memories_retrieved],
                }

                write_event(session_id, memory_event)

                logger.info(
                    f"Memory retrieval completed for session={session_id}: "
                    f"{len(memories_retrieved)} memories retrieved"
                )

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
                f"MemoryRetriever failed for session={session_id}: {e}",
                exc_info=True,
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _build_query_from_context(self, original_input: Any) -> str:
        """
        Build a query string from original input for similarity search.

        Phase 8: Extract relevant text from structured input.
        """
        query_parts = []

        if isinstance(original_input, dict):
            # Extract text from dict values (prioritize certain keys)
            priority_keys = ["description", "summary", "text", "content", "query", "question"]

            # First try priority keys
            for key in priority_keys:
                if key in original_input and isinstance(original_input[key], str):
                    query_parts.append(original_input[key])

            # Then add other string values
            for key, value in original_input.items():
                if key not in priority_keys and isinstance(value, str):
                    query_parts.append(value)

        elif isinstance(original_input, str):
            query_parts.append(original_input)

        # Combine and limit length (embeddings have token limits)
        query_text = " ".join(query_parts)
        query_text = query_text.strip()[:500]  # Limit to 500 chars

        return query_text

    def _load_governance_limit(self, limit_name: str, default: int) -> int:
        """
        Load a governance limit from governance policies.

        Phase 8: Governance limits enforcement.

        Args:
            limit_name: Name of the limit (e.g., "max_memory_retrievals_per_invocation")
            default: Default value if limit not found

        Returns:
            Limit value from governance policies or default
        """
        try:
            import os
            import json
            from pathlib import Path

            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            policy_file = Path(registry_path) / "governance_policies.json"

            with open(policy_file, 'r') as f:
                policies = json.load(f)

            context_governance = policies.get("policies", {}).get("context_governance", {})
            limit_value = context_governance.get(limit_name, default)

            return limit_value

        except Exception as e:
            logger.warning(f"Failed to load governance limit {limit_name}: {e}, using default={default}")
            return default
