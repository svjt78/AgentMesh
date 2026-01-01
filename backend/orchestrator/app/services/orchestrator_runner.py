"""
Orchestrator Runner - Production-grade meta-agent ReAct loop controller.

Demonstrates scalability patterns:
- Dynamic agent discovery (not hardcoded workflow)
- Advisory workflow mode (guidance, not prescription)
- Bounded meta-loop execution
- Agent invocation governance
- Evidence map compilation
- Multi-tier completion logic
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel

from .registry_manager import get_registry_manager, AgentMetadata, WorkflowDefinition
from .governance_enforcer import GovernanceEnforcer, create_governance_enforcer
from .context_compiler import ContextCompiler, create_context_compiler
from .agent_react_loop import create_agent_react_loop, AgentReActResult
from .storage import get_session_writer
from .progress_store import get_progress_store
from .checkpoint_manager import get_checkpoint_manager
from ..config import get_config
from ..models.checkpoint_models import CheckpointConfig, CheckpointInstance, CheckpointStatus, CheckpointResolution
import re
import time


class OrchestratorActionType(str, Enum):
    """Types of actions orchestrator can take."""
    INVOKE_AGENTS = "invoke_agents"
    WORKFLOW_COMPLETE = "workflow_complete"


class AgentInvocationRequest(BaseModel):
    """Agent invocation request from orchestrator."""
    agent_id: str
    reasoning: str  # Why this agent is needed


class OrchestratorAction(BaseModel):
    """Orchestrator's decided action."""
    type: OrchestratorActionType
    agent_requests: Optional[List[AgentInvocationRequest]] = []
    evidence_map: Optional[Dict[str, Any]] = None


class OrchestratorReasoning(BaseModel):
    """Orchestrator's reasoning and action."""
    reasoning: str
    workflow_state_assessment: str  # What has been done, what's missing
    action: OrchestratorAction


class OrchestratorResult(BaseModel):
    """Result of orchestrator execution."""
    session_id: str
    workflow_id: str
    status: str  # "completed", "incomplete", "error"
    completion_reason: Optional[str] = None
    evidence_map: Optional[Dict[str, Any]] = None
    agents_executed: List[str] = []
    total_iterations: int = 0
    total_agent_invocations: int = 0
    error: Optional[str] = None
    warnings: List[str] = []


class OrchestratorRunner:
    """
    Production-grade orchestrator ReAct loop controller.

    Manages meta-agent that discovers and invokes worker agents dynamically.

    Demonstrates:
    - Dynamic agent discovery from registry
    - Advisory workflow mode (adapt based on state)
    - Multi-tier completion logic
    - Agent invocation governance
    - Evidence map compilation
    - Bounded meta-loop execution
    """

    def __init__(
        self,
        session_id: str,
        workflow_id: str,
        llm_client: Optional[Any] = None
    ):
        self.session_id = session_id
        self.workflow_id = workflow_id
        self.llm_client = llm_client

        # Dependencies
        self.registry = get_registry_manager()
        self.governance = create_governance_enforcer(session_id)
        self.context_compiler = create_context_compiler()
        self.storage = get_session_writer()
        self.progress_store = get_progress_store()
        self.checkpoint_manager = get_checkpoint_manager()
        self.config = get_config()

        # Load workflow and orchestrator agent
        self.workflow = self.registry.get_workflow(workflow_id)
        if not self.workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found in registry")

        self.orchestrator_agent = self.registry.get_agent("orchestrator_agent")
        if not self.orchestrator_agent:
            raise ValueError("Orchestrator agent not found in registry")

        # State
        self.observations: List[Dict[str, Any]] = []  # Orchestrator's observations (agent results)
        self.iteration = 0
        self.agent_invocations: Dict[str, int] = {}  # Track invocation counts
        self.prior_outputs: Dict[str, Dict[str, Any]] = {}  # Accumulate agent outputs
        self.agents_executed_order: List[str] = []  # Track execution order

    def execute(
        self,
        original_input: Dict[str, Any]
    ) -> OrchestratorResult:
        """
        Execute orchestrator ReAct loop.

        Demonstrates:
        - Dynamic agent discovery and selection
        - Advisory workflow guidance
        - Multi-tier completion detection
        - Full observability

        Args:
            original_input: Original user input (claim data)

        Returns:
            OrchestratorResult with evidence map or error
        """
        self._log_event("orchestrator_started", {
            "workflow_id": self.workflow_id,
            "workflow_mode": self.workflow.mode,
            "max_iterations": self.orchestrator_agent.max_iterations,
            "workflow_goal": self.workflow.goal
        })

        warnings = []

        try:
            # HITL Checkpoint: Pre-Workflow
            pre_workflow_checkpoint = self._check_pre_workflow_checkpoint(original_input)
            if pre_workflow_checkpoint:
                self._log_event("checkpoint_created", {
                    "checkpoint_id": pre_workflow_checkpoint.checkpoint_id,
                    "checkpoint_instance_id": pre_workflow_checkpoint.checkpoint_instance_id,
                    "checkpoint_name": pre_workflow_checkpoint.checkpoint_name,
                    "trigger_point": "pre_workflow"
                })

                # Wait for resolution
                resolution = self._wait_for_checkpoint_resolution(pre_workflow_checkpoint)

                # Handle resolution
                if resolution.action == "reject":
                    return OrchestratorResult(
                        session_id=self.session_id,
                        workflow_id=self.workflow_id,
                        status="cancelled",
                        completion_reason="pre_workflow_rejected",
                        agents_executed=[],
                        total_iterations=0,
                        total_agent_invocations=0,
                        warnings=["Workflow rejected at pre-workflow checkpoint"]
                    )

                # Apply data updates if provided
                if resolution.data_updates:
                    original_input.update(resolution.data_updates)

            # Orchestrator ReAct Loop
            while self.iteration < self.orchestrator_agent.max_iterations:
                self.iteration += 1

                # Check workflow timeout
                if self._check_workflow_timeout():
                    warnings.append("Workflow timeout approaching")
                    break

                # Step 1: Compile context for orchestrator
                compiled_context = self._compile_orchestrator_context(original_input)

                # Step 2: Call LLM for orchestrator reasoning (Phase 3 integration point)
                reasoning = self._call_llm_for_orchestrator_reasoning(compiled_context)

                # Log orchestrator reasoning
                self._log_event("orchestrator_reasoning", {
                    "iteration": self.iteration,
                    "reasoning": reasoning.reasoning,
                    "workflow_state_assessment": reasoning.workflow_state_assessment,
                    "action_type": reasoning.action.type.value
                })

                # Step 3: Handle orchestrator action
                if reasoning.action.type == OrchestratorActionType.INVOKE_AGENTS:
                    # Execute agent invocations
                    success = self._execute_agent_invocations(
                        reasoning.action.agent_requests or [],
                        original_input
                    )
                    if not success:
                        warnings.append("Some agent invocations failed")

                    # HITL Checkpoint: After-Agent (check each executed agent)
                    for agent_request in (reasoning.action.agent_requests or []):
                        agent_id = agent_request.agent_id
                        agent_output = self.prior_outputs.get(agent_id)

                        if agent_output:
                            checkpoint = self._check_after_agent_checkpoint(agent_id, agent_output)
                            if checkpoint:
                                self._log_event("checkpoint_created", {
                                    "checkpoint_id": checkpoint.checkpoint_id,
                                    "checkpoint_instance_id": checkpoint.checkpoint_instance_id,
                                    "checkpoint_name": checkpoint.checkpoint_name,
                                    "trigger_point": "after_agent",
                                    "agent_id": agent_id
                                })

                                # Wait for resolution
                                resolution = self._wait_for_checkpoint_resolution(checkpoint)

                                # Handle resolution
                                if resolution.action == "cancel_workflow":
                                    return OrchestratorResult(
                                        session_id=self.session_id,
                                        workflow_id=self.workflow_id,
                                        status="cancelled",
                                        completion_reason="hitl_cancelled_after_agent",
                                        agents_executed=self.agents_executed_order,
                                        total_iterations=self.iteration,
                                        total_agent_invocations=sum(self.agent_invocations.values()),
                                        warnings=[f"Workflow cancelled at {agent_id} checkpoint"]
                                    )

                                # Apply data updates if provided
                                if resolution.data_updates:
                                    self.prior_outputs[agent_id].update(resolution.data_updates)

                    # Continue loop

                elif reasoning.action.type == OrchestratorActionType.WORKFLOW_COMPLETE:
                    # Tier 1: LLM explicit completion signal
                    evidence_map = reasoning.action.evidence_map

                    # HITL Checkpoint: Before-Completion
                    completion_checkpoint = self._check_before_completion_checkpoint(evidence_map)
                    if completion_checkpoint:
                        self._log_event("checkpoint_created", {
                            "checkpoint_id": completion_checkpoint.checkpoint_id,
                            "checkpoint_instance_id": completion_checkpoint.checkpoint_instance_id,
                            "checkpoint_name": completion_checkpoint.checkpoint_name,
                            "trigger_point": "before_completion"
                        })

                        # Wait for resolution
                        resolution = self._wait_for_checkpoint_resolution(completion_checkpoint)

                        # Handle resolution
                        if resolution.action == "reject":
                            # Don't complete - continue loop for revision
                            warnings.append("Completion rejected at checkpoint - continuing workflow")
                            continue

                        elif resolution.action == "request_revision":
                            # Add human feedback to observations
                            self.observations.append({
                                "type": "human_feedback",
                                "feedback": resolution.comments or "Revision requested",
                                "requested_changes": resolution.data_updates
                            })
                            warnings.append("Revision requested at checkpoint - continuing workflow")
                            continue

                    # Tier 2: Validate against completion criteria
                    validation_result = self._validate_completion_criteria(evidence_map)

                    if validation_result["valid"]:
                        self._log_event("orchestrator_completed", {
                            "completion_reason": "all_objectives_achieved",
                            "total_iterations": self.iteration,
                            "agents_executed": self.agents_executed_order,
                            "total_agent_invocations": sum(self.agent_invocations.values())
                        })

                        return OrchestratorResult(
                            session_id=self.session_id,
                            workflow_id=self.workflow_id,
                            status="completed",
                            completion_reason="all_objectives_achieved",
                            evidence_map=evidence_map,
                            agents_executed=self.agents_executed_order,
                            total_iterations=self.iteration,
                            total_agent_invocations=sum(self.agent_invocations.values()),
                            warnings=warnings
                        )
                    else:
                        # Validation failed - continue loop
                        warnings.append(f"Completion validation failed: {validation_result['reason']}")
                        self._log_event("completion_validation_failed", validation_result)

            # Tier 3: Forced completion (max iterations reached)
            self._log_event("orchestrator_incomplete", {
                "completion_reason": "max_iterations_reached",
                "total_iterations": self.iteration,
                "agents_executed": self.agents_executed_order
            })

            # Build best available evidence map
            evidence_map = self._build_evidence_map()

            return OrchestratorResult(
                session_id=self.session_id,
                workflow_id=self.workflow_id,
                status="incomplete",
                completion_reason="max_iterations_reached",
                evidence_map=evidence_map,
                agents_executed=self.agents_executed_order,
                total_iterations=self.iteration,
                total_agent_invocations=sum(self.agent_invocations.values()),
                warnings=warnings + ["Orchestrator reached max iterations without completing"]
            )

        except Exception as e:
            self._log_event("orchestrator_error", {
                "error": str(e),
                "iteration": self.iteration
            })

            return OrchestratorResult(
                session_id=self.session_id,
                workflow_id=self.workflow_id,
                status="error",
                completion_reason="error",
                error=str(e),
                agents_executed=self.agents_executed_order,
                total_iterations=self.iteration,
                total_agent_invocations=sum(self.agent_invocations.values())
            )

    # ============= Private Methods =============

    def _compile_orchestrator_context(
        self,
        original_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compile context for orchestrator's ReAct iteration.

        Includes:
        - Original input
        - Workflow definition (advisory guidance)
        - Available agents (from registry)
        - Prior agent outputs
        - Observations (agent execution results)
        """
        # Get available agents from registry (governance-filtered)
        available_agents = self.registry.get_agents_for_orchestrator()

        # Workflow guidance (advisory mode)
        workflow_guidance = {
            "goal": self.workflow.goal,
            "suggested_sequence": self.workflow.suggested_sequence,
            "required_agents": self.workflow.required_agents,
            "optional_agents": self.workflow.optional_agents,
            "completion_criteria": self.workflow.completion_criteria
        }

        # Current state
        workflow_state = {
            "agents_executed": self.agents_executed_order,
            "agents_remaining": [
                a.agent_id for a in available_agents
                if a.agent_id not in self.agents_executed_order
            ],
            "iteration": self.iteration,
            "max_iterations": self.orchestrator_agent.max_iterations
        }

        context = {
            "original_input": original_input,
            "workflow_guidance": workflow_guidance,
            "available_agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "description": a.description,
                    "capabilities": a.capabilities,
                    "required_prior_outputs": a.context_requirements.get("requires_prior_outputs", [])
                }
                for a in available_agents
            ],
            "workflow_state": workflow_state,
            "prior_outputs": self.prior_outputs,
            "observations": self.observations
        }

        return context

    def _call_llm_for_orchestrator_reasoning(
        self,
        context: Dict[str, Any]
    ) -> OrchestratorReasoning:
        """
        Call LLM to get orchestrator's reasoning and action.

        Demonstrates: Meta-agent LLM integration with dynamic agent discovery.
        """
        from ..prompts.react_prompts import build_orchestrator_prompt
        from .response_parser import parse_orchestrator_response, create_fallback_orchestrator_response, ResponseParseError
        from .llm_client import create_llm_client

        if not self.llm_client:
            # Stub fallback - follows suggested_sequence
            suggested_sequence = self.workflow.suggested_sequence or []
            executed = set(self.agents_executed_order)

            next_agent_id = None
            for agent_id in suggested_sequence:
                if agent_id not in executed:
                    next_agent_id = agent_id
                    break

            if next_agent_id:
                return OrchestratorReasoning(
                    reasoning=f"[STUB] Iteration {self.iteration}: Following suggested sequence",
                    workflow_state_assessment=f"Executed: {executed}. Next: {next_agent_id}",
                    action=OrchestratorAction(
                        type=OrchestratorActionType.INVOKE_AGENTS,
                        agent_requests=[
                            AgentInvocationRequest(
                                agent_id=next_agent_id,
                                reasoning=f"Next in suggested sequence"
                            )
                        ]
                    )
                )
            else:
                return OrchestratorReasoning(
                    reasoning=f"[STUB] All suggested agents executed",
                    workflow_state_assessment=f"Executed: {executed}. Workflow complete.",
                    action=OrchestratorAction(
                        type=OrchestratorActionType.WORKFLOW_COMPLETE,
                        evidence_map=self._build_evidence_map()
                    )
                )

        try:
            # Build orchestrator ReAct prompt
            messages = build_orchestrator_prompt(
                agent_name=self.orchestrator_agent.name,
                agent_description=self.orchestrator_agent.description,
                workflow_goal=self.workflow.goal,
                available_agents=context["available_agents"],
                workflow_state=context["workflow_state"],
                prior_outputs=self.prior_outputs,
                observations=self.observations
            )

            # Get model profile
            model_profile = self.registry.get_model_profile(self.orchestrator_agent.model_profile_id)
            if not model_profile:
                raise RuntimeError(f"Model profile '{self.orchestrator_agent.model_profile_id}' not found")

            # Create LLM client for orchestrator's model
            llm_client = create_llm_client(model_profile, self.session_id)

            # Call LLM
            llm_response = llm_client.call(messages)

            # Parse response
            reasoning = parse_orchestrator_response(llm_response.content)

            return reasoning

        except ResponseParseError as e:
            # Parsing failed - return fallback
            self._log_event("llm_response_parse_error", {
                "error": str(e),
                "iteration": self.iteration
            })
            return create_fallback_orchestrator_response(str(e), self.agents_executed_order)

        except Exception as e:
            # LLM call failed - return error fallback
            self._log_event("llm_call_error", {
                "error": str(e),
                "iteration": self.iteration
            })
            return create_fallback_orchestrator_response(f"LLM call failed: {str(e)}", self.agents_executed_order)

    def _execute_agent_invocations(
        self,
        agent_requests: List[AgentInvocationRequest],
        original_input: Dict[str, Any]
    ) -> bool:
        """
        Execute requested agent invocations.

        Demonstrates:
        - Agent invocation governance
        - Agent ReAct loop coordination
        - Output accumulation
        - Observation tracking
        """
        all_success = True

        for agent_req in agent_requests:
            # Governance check
            access_check = self.governance.check_agent_invocation(
                "orchestrator_agent",
                agent_req.agent_id
            )

            if not access_check.allowed:
                self._log_event("agent_invocation_denied", {
                    "agent_id": agent_req.agent_id,
                    "reason": access_check.violation.reason if access_check.violation else "unknown"
                })
                all_success = False
                continue

            # Check workflow-level agent invocation limit
            total_invocations = sum(self.agent_invocations.values())
            max_invocations = self.config.workflow.max_agent_invocations

            if total_invocations >= max_invocations:
                self._log_event("workflow_limit_exceeded", {
                    "limit_type": "max_agent_invocations",
                    "current": total_invocations,
                    "max": max_invocations
                })
                all_success = False
                break

            # Execute agent via AgentReActLoopController
            agent_result = self._invoke_agent(
                agent_req.agent_id,
                original_input
            )

            if agent_result.status == "completed":
                # Add to prior_outputs for subsequent agents
                self.prior_outputs[agent_req.agent_id] = agent_result.output

                # Track execution
                self.agents_executed_order.append(agent_req.agent_id)
                self.agent_invocations[agent_req.agent_id] = \
                    self.agent_invocations.get(agent_req.agent_id, 0) + 1

                # Add to observations for orchestrator's next iteration
                self.observations.append({
                    "iteration": self.iteration,
                    "agent_id": agent_req.agent_id,
                    "reasoning": agent_req.reasoning,
                    "result": agent_result.output,
                    "iterations_used": agent_result.iterations_used,
                    "tool_calls_made": agent_result.tool_calls_made,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

                self._log_event("agent_invocation_completed", {
                    "orchestrator_iteration": self.iteration,
                    "agent_id": agent_req.agent_id,
                    "agent_iterations": agent_result.iterations_used,
                    "agent_tool_calls": agent_result.tool_calls_made
                })

            elif agent_result.status == "incomplete":
                # Partial output - still add to context
                self.prior_outputs[agent_req.agent_id] = agent_result.output
                self.agents_executed_order.append(agent_req.agent_id)

                self._log_event("agent_invocation_incomplete", {
                    "agent_id": agent_req.agent_id,
                    "reason": "max_iterations_reached"
                })
                all_success = False

            else:
                # Error
                self._log_event("agent_invocation_error", {
                    "agent_id": agent_req.agent_id,
                    "error": agent_result.error
                })
                all_success = False

        return all_success

    def _invoke_agent(
        self,
        agent_id: str,
        original_input: Dict[str, Any]
    ) -> AgentReActResult:
        """
        Invoke agent via AgentReActLoopController.

        Demonstrates: Composition of ReAct loops (meta-loop → agent loop).
        """
        # Create agent ReAct loop controller
        agent_loop = create_agent_react_loop(
            session_id=self.session_id,
            agent_id=agent_id,
            llm_client=self.llm_client,
            tools_client=None  # Phase 4 integration point
        )

        # Execute agent's ReAct loop
        result = agent_loop.execute(
            context_data={},
            original_input=original_input,
            prior_outputs=self.prior_outputs
        )

        return result

    def _validate_completion_criteria(
        self,
        evidence_map: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate workflow completion criteria (Tier 2 completion).

        Checks:
        - Required agents executed
        - Required outputs present
        - Minimum agent count
        - Evidence map structure
        """
        if not self.workflow.completion_criteria:
            return {"valid": True}

        criteria = self.workflow.completion_criteria

        # Check required agents executed
        required_agents = criteria.get("required_agents_executed", [])
        for agent_id in required_agents:
            if agent_id not in self.agents_executed_order:
                return {
                    "valid": False,
                    "reason": f"Required agent '{agent_id}' not executed"
                }

        # Check minimum agent count
        min_agents = criteria.get("min_agents_executed", 0)
        if len(self.agents_executed_order) < min_agents:
            return {
                "valid": False,
                "reason": f"Only {len(self.agents_executed_order)} agents executed (min: {min_agents})"
            }

        # Check required outputs present
        required_outputs = criteria.get("required_outputs", [])
        if not evidence_map:
            if required_outputs:
                return {
                    "valid": False,
                    "reason": "Evidence map missing but required outputs specified"
                }
        else:
            for output_key in required_outputs:
                if output_key not in evidence_map:
                    return {
                        "valid": False,
                        "reason": f"Required output '{output_key}' missing from evidence map"
                    }

        return {"valid": True}

    def _build_evidence_map(self) -> Dict[str, Any]:
        """
        Build evidence map from all agent outputs (Tier 3 completion fallback).

        Demonstrates: Evidence compilation for explainability.

        Evidence map structure:
        {
            "decision": {...},
            "supporting_evidence": [...],
            "assumptions": [...],
            "limitations": [...],
            "agent_chain": [...]
        }
        """
        # If explainability agent ran, use its output
        if "explainability_agent" in self.prior_outputs:
            return self.prior_outputs["explainability_agent"]

        # Otherwise, compile from available outputs
        evidence_map = {
            "decision": {},
            "supporting_evidence": [],
            "assumptions": [],
            "limitations": ["Incomplete workflow - evidence map auto-generated"],
            "agent_chain": self.agents_executed_order.copy()
        }

        # Extract recommendation if available
        if "recommendation_agent" in self.prior_outputs:
            rec_output = self.prior_outputs["recommendation_agent"]
            evidence_map["decision"] = {
                "outcome": rec_output.get("recommended_action"),
                "confidence": rec_output.get("confidence"),
                "recommended_action": rec_output.get("recommended_action")
            }

        # Compile supporting evidence from all agents
        for agent_id, output in self.prior_outputs.items():
            evidence_map["supporting_evidence"].append({
                "source": agent_id,
                "evidence_type": "agent_output",
                "summary": str(output)[:200]  # Truncate for brevity
            })

        return evidence_map

    def _check_workflow_timeout(self) -> bool:
        """
        Check if workflow is approaching timeout.

        Demonstrates: Time-based safety mechanism.
        """
        # This will be implemented with actual timing in Phase 6
        # For now, just check iteration count as proxy
        max_duration = self.config.workflow.max_duration_seconds
        # TODO: Track actual elapsed time
        return False

    # ============= HITL Checkpoint Methods =============

    def _check_pre_workflow_checkpoint(
        self,
        original_input: Dict[str, Any]
    ) -> Optional[CheckpointInstance]:
        """Check if pre-workflow checkpoint is configured and should trigger."""
        hitl_checkpoints = self.workflow.hitl_checkpoints if hasattr(self.workflow, 'hitl_checkpoints') else []

        for checkpoint_config_dict in hitl_checkpoints:
            if checkpoint_config_dict.get("trigger_point") == "pre_workflow":
                # Convert dict to CheckpointConfig model
                checkpoint_config = CheckpointConfig(**checkpoint_config_dict)

                # Evaluate trigger condition (if exists)
                if self._evaluate_checkpoint_condition(checkpoint_config, None, original_input):
                    # Create checkpoint
                    return self.checkpoint_manager.create_checkpoint(
                        session_id=self.session_id,
                        workflow_id=self.workflow_id,
                        checkpoint_config=checkpoint_config,
                        context_data={"original_input": original_input}
                    )

        return None

    def _check_after_agent_checkpoint(
        self,
        agent_id: str,
        agent_output: Optional[Dict[str, Any]]
    ) -> Optional[CheckpointInstance]:
        """Check if after-agent checkpoint is configured and should trigger."""
        if not agent_output:
            return None

        hitl_checkpoints = self.workflow.hitl_checkpoints if hasattr(self.workflow, 'hitl_checkpoints') else []

        for checkpoint_config_dict in hitl_checkpoints:
            if (checkpoint_config_dict.get("trigger_point") == "after_agent" and
                checkpoint_config_dict.get("agent_id") == agent_id):

                # Convert dict to CheckpointConfig model
                checkpoint_config = CheckpointConfig(**checkpoint_config_dict)

                # Evaluate trigger condition (if exists)
                if self._evaluate_checkpoint_condition(checkpoint_config, agent_output, {}):
                    # Create checkpoint with agent output as context
                    return self.checkpoint_manager.create_checkpoint(
                        session_id=self.session_id,
                        workflow_id=self.workflow_id,
                        checkpoint_config=checkpoint_config,
                        context_data={
                            "agent_id": agent_id,
                            "agent_output": agent_output,
                            "prior_outputs": self.prior_outputs
                        }
                    )

        return None

    def _check_before_completion_checkpoint(
        self,
        evidence_map: Dict[str, Any]
    ) -> Optional[CheckpointInstance]:
        """Check if before-completion checkpoint is configured."""
        hitl_checkpoints = self.workflow.hitl_checkpoints if hasattr(self.workflow, 'hitl_checkpoints') else []

        for checkpoint_config_dict in hitl_checkpoints:
            if checkpoint_config_dict.get("trigger_point") == "before_completion":
                # Convert dict to CheckpointConfig model
                checkpoint_config = CheckpointConfig(**checkpoint_config_dict)

                # Create checkpoint with evidence map as context
                return self.checkpoint_manager.create_checkpoint(
                    session_id=self.session_id,
                    workflow_id=self.workflow_id,
                    checkpoint_config=checkpoint_config,
                    context_data={
                        "evidence_map": evidence_map,
                        "agents_executed": self.agents_executed_order,
                        "prior_outputs": self.prior_outputs
                    }
                )

        return None

    def _wait_for_checkpoint_resolution(
        self,
        checkpoint: CheckpointInstance
    ) -> CheckpointResolution:
        """
        Wait for checkpoint to be resolved (blocking with polling).

        Uses exponential backoff to reduce CPU usage during wait.
        Handles timeout logic.
        """
        poll_interval = 1.0  # Start with 1 second
        max_poll_interval = 10.0

        while True:
            # Check if resolved
            current = self.checkpoint_manager.get_checkpoint(checkpoint.checkpoint_instance_id)

            if current and current.status == CheckpointStatus.RESOLVED:
                self._log_event("checkpoint_resolved", {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "checkpoint_instance_id": checkpoint.checkpoint_instance_id,
                    "action": current.resolution.action,
                    "user_id": current.resolution.user_id
                })
                return current.resolution

            # Check timeout
            timeout_action = self.checkpoint_manager.check_timeout(checkpoint.checkpoint_instance_id)
            if timeout_action:
                self._log_event("checkpoint_timeout", {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "checkpoint_instance_id": checkpoint.checkpoint_instance_id,
                    "timeout_action": timeout_action
                })
                return self._handle_checkpoint_timeout(checkpoint, timeout_action)

            # Poll with exponential backoff
            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, max_poll_interval)

    def _handle_checkpoint_timeout(
        self,
        checkpoint: CheckpointInstance,
        timeout_action: str
    ) -> CheckpointResolution:
        """Create resolution based on timeout action."""
        return CheckpointResolution(
            action=timeout_action,
            user_id="system",
            user_role="system",
            comments=f"Checkpoint timed out - automatic action: {timeout_action}",
            resolved_at=datetime.utcnow().isoformat() + "Z"
        )

    def _evaluate_checkpoint_condition(
        self,
        checkpoint_config: CheckpointConfig,
        agent_output: Optional[Dict[str, Any]],
        original_input: Dict[str, Any]
    ) -> bool:
        """
        Evaluate trigger condition for conditional checkpoints.

        Supports simple expressions like "fraud_score > 0.7"
        """
        if not checkpoint_config.trigger_condition:
            return True  # No condition = always trigger

        condition_type = checkpoint_config.trigger_condition.type
        condition_expr = checkpoint_config.trigger_condition.condition

        if condition_type == "output_based" and agent_output:
            return self._evaluate_expression(condition_expr, agent_output)
        elif condition_type == "input_based":
            return self._evaluate_expression(condition_expr, original_input)
        elif condition_type == "always":
            return True

        return True  # Default to triggering

    def _evaluate_expression(self, expression: str, data: Dict[str, Any]) -> bool:
        """
        Safely evaluate simple comparison expressions.

        Supported: field > value, field < value, field == value
        No eval() - manual parsing for security.
        """
        try:
            # Parse expression: "fraud_score > 0.7"
            pattern = r'(\w+(?:\.\w+)*)\s*([><=]+)\s*([0-9.]+|"[^"]*")'
            match = re.match(pattern, expression.strip())

            if not match:
                return True  # If can't parse, trigger anyway

            field_path, operator, value_str = match.groups()

            # Extract field value (support nested: fraud.score)
            field_value = data
            for part in field_path.split('.'):
                if isinstance(field_value, dict) and part in field_value:
                    field_value = field_value[part]
                else:
                    return False  # Field doesn't exist

            # Parse value (number or string)
            if value_str.startswith('"'):
                value = value_str.strip('"')
            else:
                value = float(value_str)

            # Evaluate comparison
            if operator == '>':
                return field_value > value
            elif operator == '<':
                return field_value < value
            elif operator == '==':
                return field_value == value
            elif operator == '>=':
                return field_value >= value
            elif operator == '<=':
                return field_value <= value

        except Exception as e:
            # On any error, default to triggering
            return True

        return False

    def _log_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Log event to storage AND progress store for real-time streaming."""
        event = {
            "event_type": event_type,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "orchestrator_iteration": self.iteration,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data
        }

        # Write to storage (existing - for persistence and replay)
        self.storage.write_event(self.session_id, event)

        # Write to progress store (NEW - for real-time SSE streaming)
        self.progress_store.add_event(self.session_id, event)


def create_orchestrator_runner(
    session_id: str,
    workflow_id: str,
    llm_client: Optional[Any] = None
) -> OrchestratorRunner:
    """Factory function to create OrchestratorRunner."""
    return OrchestratorRunner(
        session_id=session_id,
        workflow_id=workflow_id,
        llm_client=llm_client
    )
