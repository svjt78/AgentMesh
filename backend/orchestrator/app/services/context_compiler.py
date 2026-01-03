"""
Context Compiler - Production-grade context management.

Demonstrates scalability patterns:
- Selective context inclusion (prevents bloat)
- Token budget management
- Reference-based architecture (artifacts by ID)
- Prioritization (recent vs old)
- Intelligent summarization
"""

from typing import Dict, List, Optional, Any
import tiktoken
import logging
from datetime import datetime
from pydantic import BaseModel

from .registry_manager import get_registry_manager
from app.config import get_config
from .context_scoper import get_context_scoper
from .conversation_translator import get_conversation_translator
from .storage import get_session_writer
from app.models.handoff_models import (
    ContextHandoffEvent,
    create_context_summary,
    calculate_token_savings
)

logger = logging.getLogger(__name__)


class CompiledContext(BaseModel):
    """Compiled context ready for agent consumption."""
    agent_id: str
    original_input: Optional[Dict[str, Any]] = None
    prior_outputs: Dict[str, Any] = {}  # {step_id: output}
    observations: List[Dict[str, Any]] = []  # Tool/agent results from current agent's iterations
    metadata: Dict[str, Any] = {}
    estimated_tokens: int = 0


class ContextCompiler:
    """
    Production-grade context compiler.

    Demonstrates scalability patterns:
    - Prevents context bloat (major LLM cost driver)
    - Token-aware compilation
    - Reference-based for large objects
    - Configurable per agent
    """

    def __init__(self, session_id: Optional[str] = None):
        self.registry = get_registry_manager()
        self.config = get_config()
        self.session_id = session_id or "unknown"

        # Use tiktoken for accurate token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            # Fallback if tiktoken not available
            self.tokenizer = None

        # Initialize processor pipeline if context engineering is enabled
        self.pipeline = None
        if self.config.context_engineering.enabled and self.config.context_engineering.processor_pipeline_enabled:
            try:
                from .context_processor_pipeline import ContextProcessorPipeline
                self.pipeline = ContextProcessorPipeline(self.session_id, self.registry)
                logger.info(
                    f"Context engineering enabled for session={self.session_id}, "
                    f"using processor pipeline with {self.pipeline.get_processor_count()} processors"
                )
            except Exception as e:
                logger.error(f"Failed to initialize processor pipeline: {e}", exc_info=True)
                self.pipeline = None

    def compile_for_agent(
        self,
        agent_id: str,
        original_input: Optional[Dict[str, Any]] = None,
        prior_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        from_agent_id: Optional[str] = None
    ) -> CompiledContext:
        """
        Compile scoped context for an agent.

        Demonstrates:
        - Agent-specific context requirements
        - Token budget enforcement
        - Selective inclusion
        - Handoff scoping (Phase 6)

        Args:
            agent_id: Agent receiving this context
            original_input: Original user input (e.g., claim data)
            prior_outputs: Outputs from prior agents {agent_id: output}
            observations: Tool/agent results from current agent's iterations
            from_agent_id: Source agent ID for handoff scoping (Phase 6)

        Returns:
            CompiledContext with only relevant information within token limits
        """
        # Apply handoff scoping if this is a handoff (Phase 6)
        if from_agent_id and prior_outputs:
            prior_outputs, observations = self._apply_handoff_scoping(
                from_agent_id=from_agent_id,
                to_agent_id=agent_id,
                prior_outputs=prior_outputs,
                observations=observations or [],
                original_input=original_input
            )

        # If context engineering is enabled, use processor pipeline
        if self.pipeline:
            return self._compile_with_pipeline(
                agent_id,
                original_input,
                prior_outputs,
                observations
            )

        # Otherwise, use legacy compilation logic
        agent = self.registry.get_agent(agent_id)
        if not agent:
            # Unknown agent, return minimal context
            return CompiledContext(
                agent_id=agent_id,
                original_input=original_input or {},
                estimated_tokens=self._count_tokens(original_input or {})
            )

        # Get agent's context requirements
        requirements = agent.context_requirements
        max_tokens = requirements.get("max_context_tokens", 8000)
        requires_prior = requirements.get("requires_prior_outputs", [])

        context = CompiledContext(agent_id=agent_id)

        # Budget allocation strategy:
        # - Original input: 30% of budget
        # - Prior outputs: 50% of budget
        # - Observations: 20% of budget
        budget_original = int(max_tokens * 0.3)
        budget_prior = int(max_tokens * 0.5)
        budget_obs = int(max_tokens * 0.2)

        # 1. Include original input (if agent needs it)
        if original_input:
            input_truncated = self._fit_to_budget(original_input, budget_original)
            context.original_input = input_truncated

        # 2. Include prior outputs (only what agent needs)
        if prior_outputs and requires_prior:
            context.prior_outputs = self._select_prior_outputs(
                prior_outputs,
                requires_prior,
                budget_prior
            )

        # 3. Include observations (most recent first)
        if observations:
            context.observations = self._select_observations(
                observations,
                budget_obs
            )

        # 4. Add metadata
        context.metadata = {
            "max_tokens": max_tokens,
            "requires_prior_outputs": requires_prior,
            "truncation_applied": False  # TODO: track if truncation occurred
        }

        # 5. Calculate final token count
        context.estimated_tokens = self._count_tokens_context(context)

        return context

    def compile_for_orchestrator(
        self,
        workflow_id: str,
        original_input: Dict[str, Any],
        agent_outputs: Optional[Dict[str, Any]] = None,
        observations: Optional[List[Dict[str, Any]]] = None
    ) -> CompiledContext:
        """
        Compile context for orchestrator agent.

        Demonstrates: Orchestrator has broader context needs.
        """
        orchestrator = self.registry.get_agent("orchestrator_agent")
        if not orchestrator:
            raise ValueError("orchestrator_agent not found in registry")

        max_tokens = orchestrator.context_requirements.get("max_context_tokens", 10000)

        context = CompiledContext(agent_id="orchestrator_agent")

        # Budget allocation for orchestrator:
        # - Original input: 20%
        # - Agent outputs: 60%
        # - Observations: 20%
        budget_original = int(max_tokens * 0.2)
        budget_agents = int(max_tokens * 0.6)
        budget_obs = int(max_tokens * 0.2)

        # Include original input (claim data)
        context.original_input = self._fit_to_budget(original_input, budget_original)

        # Include agent outputs (results from invoked agents)
        if agent_outputs:
            context.prior_outputs = self._fit_to_budget(agent_outputs, budget_agents)

        # Include observations (from orchestrator's own iterations)
        if observations:
            context.observations = self._select_observations(observations, budget_obs)

        # Metadata
        context.metadata = {
            "workflow_id": workflow_id,
            "max_tokens": max_tokens
        }

        context.estimated_tokens = self._count_tokens_context(context)

        return context

    # ============= Context Engineering Pipeline Integration =============

    def _compile_with_pipeline(
        self,
        agent_id: str,
        original_input: Optional[Dict[str, Any]] = None,
        prior_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
        observations: Optional[List[Dict[str, Any]]] = None
    ) -> CompiledContext:
        """
        Compile context using the processor pipeline.

        This method integrates with the context engineering features.
        """
        logger.debug(f"Compiling context with pipeline for agent={agent_id}")

        # Get agent config for metadata
        agent = self.registry.get_agent(agent_id)
        max_tokens = agent.context_requirements.get("max_context_tokens", 8000) if agent else 8000

        # Get budget allocation (from agent override or default)
        budget_allocation = self._get_budget_allocation(agent)

        # Count tokens before compilation
        tokens_before = (
            self._count_tokens(original_input or {}) +
            self._count_tokens(prior_outputs or {}) +
            self._count_tokens(observations or [])
        )

        components_before = {
            "original_input": self._count_tokens(original_input or {}),
            "prior_outputs": self._count_tokens(prior_outputs or {}),
            "observations": self._count_tokens(observations or []),
        }

        # Build raw context for pipeline
        raw_context = {
            "agent_id": agent_id,
            "original_input": original_input or {},
            "prior_outputs": prior_outputs or {},
            "observations": observations or [],
            "metadata": {
                "max_context_tokens": max_tokens,
                "session_id": self.session_id,
            }
        }

        # Execute processor pipeline
        compiled_dict = self.pipeline.execute(raw_context, agent_id)

        # Extract compiled context from pipeline result
        compiled_context_data = compiled_dict.get("compiled_context", {})

        # Build CompiledContext from pipeline output
        context = CompiledContext(
            agent_id=agent_id,
            original_input=compiled_context_data.get("original_input"),
            prior_outputs=compiled_context_data.get("prior_outputs", {}),
            observations=compiled_context_data.get("observations", []),
            metadata=compiled_dict.get("metadata", {}),
        )

        # Estimate tokens after compilation
        context.estimated_tokens = self._count_tokens_context(context)

        components_after = {
            "original_input": self._count_tokens(context.original_input or {}),
            "prior_outputs": self._count_tokens(context.prior_outputs or {}),
            "observations": self._count_tokens(context.observations or []),
        }

        # Extract processor execution log from pipeline
        processor_execution_log = compiled_dict.get("metadata", {}).get("processor_execution_log", [])

        # Convert to ProcessorExecution objects for lineage tracker
        from .context_lineage_tracker import ProcessorExecution, get_context_lineage_tracker

        processor_executions = [
            ProcessorExecution(
                processor_id=log["processor_id"],
                execution_time_ms=log.get("execution_time_ms", 0),
                success=log.get("success", False),
                modifications_made=log.get("modifications_made", {}),
                error=log.get("error")
            )
            for log in processor_execution_log
        ]

        # Extract metadata about modifications
        truncation_applied = any(
            "truncation" in log.get("modifications_made", {}).get("status", "")
            for log in processor_execution_log
        )

        compaction_applied = any(
            log.get("modifications_made", {}).get("compaction_applied", False)
            for log in processor_execution_log
        )

        # Extract memory and artifact info
        memories_retrieved = 0
        memory_ids = []
        artifacts_resolved = 0
        artifact_handles = []

        for log in processor_execution_log:
            mods = log.get("modifications_made", {})
            if "memories_retrieved" in mods:
                memories_retrieved = mods["memories_retrieved"]
            if "memory_ids" in context.metadata:
                memory_ids = context.metadata["memory_ids"]
            if "artifacts_resolved" in mods:
                artifacts_resolved = mods["artifacts_resolved"]
            if "artifact_handles" in mods:
                artifact_handles = mods["artifact_handles"]

        # Record compilation in lineage tracker
        try:
            lineage_tracker = get_context_lineage_tracker(self.session_id)
            lineage_tracker.record_compilation(
                agent_id=agent_id,
                tokens_before=tokens_before,
                tokens_after=context.estimated_tokens,
                components_before=components_before,
                components_after=components_after,
                processors_executed=processor_executions,
                budget_allocation=budget_allocation,
                max_tokens=max_tokens,
                truncation_applied=truncation_applied,
                compaction_applied=compaction_applied,
                memories_retrieved=memories_retrieved,
                memory_ids=memory_ids,
                artifacts_resolved=artifacts_resolved,
                artifact_handles=artifact_handles,
            )
        except Exception as e:
            logger.error(f"Failed to record compilation lineage: {e}", exc_info=True)

        logger.debug(
            f"Context compiled with pipeline for agent={agent_id}, "
            f"estimated_tokens={context.estimated_tokens}"
        )

        return context

    # ============= Private Helpers =============

    def _select_prior_outputs(
        self,
        all_outputs: Dict[str, Dict[str, Any]],
        required_ids: List[str],
        budget: int
    ) -> Dict[str, Any]:
        """
        Select prior outputs based on requirements and budget.

        Demonstrates: Selective inclusion, prioritization.
        """
        selected = {}
        remaining_budget = budget

        # Prioritize required outputs
        for output_id in required_ids:
            if output_id in all_outputs and remaining_budget > 0:
                output = all_outputs[output_id]
                output_tokens = self._count_tokens(output)

                if output_tokens <= remaining_budget:
                    selected[output_id] = output
                    remaining_budget -= output_tokens
                else:
                    # Truncate or summarize
                    selected[output_id] = self._fit_to_budget(output, remaining_budget)
                    remaining_budget = 0
                    break

        return selected

    def _select_observations(
        self,
        observations: List[Dict[str, Any]],
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Select observations within budget, prioritizing recent ones.

        Demonstrates: Recency bias for iterative reasoning.
        """
        selected = []
        remaining_budget = budget

        # Reverse order (most recent first)
        for obs in reversed(observations):
            obs_tokens = self._count_tokens(obs)

            if obs_tokens <= remaining_budget:
                selected.insert(0, obs)  # Maintain chronological order
                remaining_budget -= obs_tokens
            else:
                # Budget exhausted
                break

        return selected

    def _fit_to_budget(
        self,
        data: Any,
        budget: int
    ) -> Any:
        """
        Fit data to token budget through truncation.

        Demonstrates: Graceful degradation when context is large.

        Note: This is a simple truncation. Production could use:
        - Intelligent summarization (extract key fields)
        - Compression (remove verbose fields)
        - Reference storage (store large objects as artifacts)
        """
        data_tokens = self._count_tokens(data)

        if data_tokens <= budget:
            return data

        # Simple truncation strategy: convert to string, truncate, note limitation
        if isinstance(data, dict):
            # Truncate by removing least important keys
            # For now, just return as-is and let LLM handle
            # TODO: Implement intelligent field prioritization
            return data
        elif isinstance(data, list):
            # Truncate list to fit budget
            truncated = []
            remaining = budget
            for item in data:
                item_tokens = self._count_tokens(item)
                if item_tokens <= remaining:
                    truncated.append(item)
                    remaining -= item_tokens
                else:
                    break
            return truncated
        else:
            return data

    def _count_tokens(self, data: Any) -> int:
        """
        Count tokens in data structure.

        Demonstrates: Token-aware context management.
        """
        if self.tokenizer:
            # Accurate counting with tiktoken
            import json
            text = json.dumps(data) if not isinstance(data, str) else data
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: rough estimate (4 chars ≈ 1 token)
            import json
            text = json.dumps(data) if not isinstance(data, str) else data
            return len(text) // 4

    def _estimate_context_tokens(
        self,
        prior_outputs: Optional[Dict[str, Any]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        original_input: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Estimate total tokens for context components.

        Phase 6: Helper for handoff event tracking.
        """
        total = 0
        if original_input:
            total += self._count_tokens(original_input)
        if prior_outputs:
            total += self._count_tokens(prior_outputs)
        if observations:
            total += self._count_tokens(observations)
        return total

    def _apply_handoff_scoping(
        self,
        from_agent_id: str,
        to_agent_id: str,
        prior_outputs: Dict[str, Any],
        observations: List[Dict[str, Any]],
        original_input: Optional[Dict[str, Any]]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Apply handoff scoping rules to context (Phase 6).

        Returns:
            (scoped_prior_outputs, scoped_observations)
        """
        try:
            scoper = get_context_scoper()
            translator = get_conversation_translator()

            # Calculate token counts before scoping
            tokens_before = self._estimate_context_tokens(
                prior_outputs=prior_outputs,
                observations=observations,
                original_input=original_input
            )

            # Apply scoping
            scoped_context = scoper.scope_context_for_handoff(
                prior_outputs=prior_outputs,
                observations=observations,
                original_input=original_input,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id
            )

            # Apply conversation translation if configured
            rule = scoper.get_handoff_rule(from_agent_id, to_agent_id)
            translation_applied = False
            translation_strategies = []

            if rule and rule.conversation_translation and rule.conversation_translation.enabled:
                scoped_outputs = translator.translate_outputs(
                    scoped_context.prior_outputs,
                    rule
                )
                scoped_context.prior_outputs = scoped_outputs
                scoped_context.translation_applied = True
                translation_applied = True

                # Track which strategies were applied
                if rule.conversation_translation.extract_fields:
                    translation_strategies.append("extract_fields")
                if rule.conversation_translation.filter_enabled:
                    translation_strategies.append("filter")

            # Calculate token counts after scoping
            tokens_after = self._estimate_context_tokens(
                prior_outputs=scoped_context.prior_outputs,
                observations=scoped_context.observations,
                original_input=scoped_context.original_input
            )

            # Create context summaries
            context_before = create_context_summary(
                prior_outputs=prior_outputs,
                observations=observations,
                token_count=tokens_before
            )

            context_after = create_context_summary(
                prior_outputs=scoped_context.prior_outputs,
                observations=scoped_context.observations,
                token_count=tokens_after
            )

            # Calculate savings
            tokens_saved, tokens_saved_percentage = calculate_token_savings(
                context_before, context_after
            )

            # Log handoff event
            handoff_event = ContextHandoffEvent(
                session_id=self.session_id,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                timestamp=datetime.utcnow().isoformat(),
                handoff_mode=scoped_context.handoff_mode,
                governance_rule_id=rule.rule_id if rule else None,
                context_before_scoping=context_before,
                context_after_scoping=context_after,
                tokens_saved=tokens_saved,
                tokens_saved_percentage=tokens_saved_percentage,
                conversation_translation_applied=translation_applied,
                translation_strategies=translation_strategies,
                audit_note=f"Fields filtered: {len(scoped_context.fields_filtered)}"
            )

            # Write event to storage
            storage = get_session_writer()
            storage.write_event(self.session_id, handoff_event.dict())

            logger.info(
                f"Handoff scoping applied: {from_agent_id}→{to_agent_id}, "
                f"mode={scoped_context.handoff_mode}, "
                f"tokens_saved={tokens_saved} ({tokens_saved_percentage:.1f}%), "
                f"fields_filtered={len(scoped_context.fields_filtered)}"
            )

            return scoped_context.prior_outputs, scoped_context.observations

        except Exception as e:
            logger.error(f"Failed to apply handoff scoping: {e}", exc_info=True)
            # Fallback: return original context
            return prior_outputs, observations

    def _get_budget_allocation(self, agent: Optional[Any]) -> Dict[str, int]:
        """
        Get budget allocation percentages for context components.

        Checks for agent-specific override, otherwise uses defaults.

        Args:
            agent: Agent configuration

        Returns:
            Dictionary with allocation percentages
        """
        default_allocation = {
            "original_input_percentage": 30,
            "prior_outputs_percentage": 50,
            "observations_percentage": 20,
        }

        if agent and "context_requirements" in agent:
            context_reqs = agent["context_requirements"]
            if "budget_allocation_override" in context_reqs:
                override = context_reqs["budget_allocation_override"]
                return {
                    "original_input_percentage": override.get("original_input_percentage", 30),
                    "prior_outputs_percentage": override.get("prior_outputs_percentage", 50),
                    "observations_percentage": override.get("observations_percentage", 20),
                }

        return default_allocation

    def _count_tokens_context(self, context: CompiledContext) -> int:
        """Count total tokens in compiled context."""
        total = 0
        if context.original_input:
            total += self._count_tokens(context.original_input)
        if context.prior_outputs:
            total += self._count_tokens(context.prior_outputs)
        if context.observations:
            total += self._count_tokens(context.observations)
        return total


def create_context_compiler(session_id: Optional[str] = None) -> ContextCompiler:
    """Factory function to create context compiler."""
    return ContextCompiler(session_id=session_id)
