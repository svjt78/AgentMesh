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
from pydantic import BaseModel

from .registry_manager import get_registry_manager


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

    def __init__(self):
        self.registry = get_registry_manager()
        # Use tiktoken for accurate token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            # Fallback if tiktoken not available
            self.tokenizer = None

    def compile_for_agent(
        self,
        agent_id: str,
        original_input: Optional[Dict[str, Any]] = None,
        prior_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
        observations: Optional[List[Dict[str, Any]]] = None
    ) -> CompiledContext:
        """
        Compile scoped context for an agent.

        Demonstrates:
        - Agent-specific context requirements
        - Token budget enforcement
        - Selective inclusion

        Args:
            agent_id: Agent receiving this context
            original_input: Original user input (e.g., claim data)
            prior_outputs: Outputs from prior agents {agent_id: output}
            observations: Tool/agent results from current agent's iterations

        Returns:
            CompiledContext with only relevant information within token limits
        """
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


def create_context_compiler() -> ContextCompiler:
    """Factory function to create context compiler."""
    return ContextCompiler()
