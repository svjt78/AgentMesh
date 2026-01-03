"""
Agent ReAct Loop Controller - Production-grade ReAct pattern implementation.

Demonstrates scalability patterns:
- Stateless execution (scales horizontally)
- Bounded iteration (prevents runaway)
- Observable (full event logging)
- Resilient (error handling, timeouts)
- Modular (clean interfaces)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, ValidationError
import logging

from .registry_manager import get_registry_manager, AgentMetadata, ToolMetadata
from .governance_enforcer import GovernanceEnforcer, create_governance_enforcer
from .context_compiler import ContextCompiler, CompiledContext, create_context_compiler
from .storage import get_session_writer
from .progress_store import get_progress_store
from ..config import get_config

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions an agent can take."""
    USE_TOOLS = "use_tools"
    FINAL_OUTPUT = "final_output"


class ToolRequest(BaseModel):
    """Tool invocation request from agent."""
    tool_id: str
    parameters: Dict[str, Any]


class AgentAction(BaseModel):
    """Agent's decided action."""
    type: ActionType
    tool_requests: Optional[List[ToolRequest]] = []
    output: Optional[Dict[str, Any]] = None


class AgentReasoning(BaseModel):
    """Agent's reasoning and action."""
    reasoning: str
    action: AgentAction


class AgentReActResult(BaseModel):
    """Result of agent ReAct execution."""
    agent_id: str
    status: str  # "completed", "incomplete", "error"
    output: Optional[Dict[str, Any]] = None
    iterations_used: int = 0
    tool_calls_made: int = 0
    error: Optional[str] = None
    warnings: List[str] = []


class AgentReActLoopController:
    """
    Production-grade ReAct loop controller for worker agents.

    Manages the Reasoning + Acting loop:
    1. Compile context
    2. Call LLM for reasoning
    3. Parse action decision
    4. If use_tools: invoke tools, add to observations, loop
    5. If final_output: validate and return
    6. Enforce iteration limits and governance

    Demonstrates:
    - Bounded execution (max iterations)
    - Governance enforcement
    - Full observability (JSONL logging)
    - Error resilience
    """

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        llm_client: Optional[Any] = None,  # Will be provided in Phase 3
        tools_client: Optional[Any] = None,  # Will be provided in Phase 4
        from_agent_id: Optional[str] = None  # Phase 6: Track handoff source for context scoping
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.llm_client = llm_client
        self.tools_client = tools_client
        self.from_agent_id = from_agent_id  # Phase 6: Store for handoff scoping

        # Dependencies
        self.registry = get_registry_manager()
        self.governance = create_governance_enforcer(session_id)
        self.context_compiler = create_context_compiler(session_id)
        self.storage = get_session_writer()
        self.progress_store = get_progress_store()

        # Agent metadata
        self.agent = self.registry.get_agent(agent_id)
        if not self.agent:
            raise ValueError(f"Agent '{agent_id}' not found in registry")

        # State
        self.observations: List[Dict[str, Any]] = []
        self.iteration = 0
        self.tool_calls_made = 0
        self._validation_failures = 0  # Track validation failures for safety threshold

    def execute(
        self,
        context_data: Dict[str, Any],
        original_input: Optional[Dict[str, Any]] = None,
        prior_outputs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> AgentReActResult:
        """
        Execute ReAct loop for agent.

        Demonstrates:
        - Complete ReAct pattern
        - Bounded iteration
        - Full observability

        Args:
            context_data: Additional context for this execution
            original_input: Original user input
            prior_outputs: Outputs from prior agents

        Returns:
            AgentReActResult with output or error
        """
        self._log_event("agent_started", {
            "agent_id": self.agent_id,
            "max_iterations": self.agent.max_iterations
        })

        warnings = []

        try:
            # ReAct Loop
            while self.iteration < self.agent.max_iterations:
                self.iteration += 1

                # Check iteration limit governance
                limit_check = self.governance.check_iteration_limit(
                    self.agent_id,
                    self.iteration
                )
                if not limit_check.allowed:
                    self._log_event("iteration_limit_exceeded", {
                        "iteration": self.iteration,
                        "max": self.agent.max_iterations
                    })
                    warnings.append(f"Max iterations ({self.agent.max_iterations}) reached")
                    break

                # Step 1: Compile context
                compiled_context = self._compile_context(
                    original_input,
                    prior_outputs
                )

                # Step 2: Call LLM for reasoning (Phase 3 integration point)
                reasoning = self._call_llm_for_reasoning(compiled_context)

                # Log reasoning
                self._log_event("agent_reasoning", {
                    "agent_id": self.agent_id,
                    "iteration": self.iteration,
                    "reasoning": reasoning.reasoning,
                    "action_type": reasoning.action.type.value
                })

                # Step 3: Handle action
                if reasoning.action.type == ActionType.USE_TOOLS:
                    # Execute tools and add observations
                    success = self._execute_tools(reasoning.action.tool_requests or [])
                    if not success:
                        warnings.append("Some tool executions failed")
                    # Continue loop

                elif reasoning.action.type == ActionType.FINAL_OUTPUT:
                    # Validate output
                    output = reasoning.action.output
                    if self._validate_output(output):
                        self._log_event("agent_completed", {
                            "agent_id": self.agent_id,
                            "iterations_used": self.iteration,
                            "tool_calls_made": self.tool_calls_made,
                            "output_keys": list(output.keys()) if output else []
                        })

                        return AgentReActResult(
                            agent_id=self.agent_id,
                            status="completed",
                            output=output,
                            iterations_used=self.iteration,
                            tool_calls_made=self.tool_calls_made,
                            warnings=warnings
                        )
                    else:
                        warnings.append("Output validation failed, continuing loop")

            # Loop exhausted without final_output
            self._log_event("agent_incomplete", {
                "agent_id": self.agent_id,
                "iterations_used": self.iteration,
                "reason": "max_iterations_reached"
            })

            # Return best available output (last observation or partial)
            partial_output = self._extract_partial_output()

            return AgentReActResult(
                agent_id=self.agent_id,
                status="incomplete",
                output=partial_output,
                iterations_used=self.iteration,
                tool_calls_made=self.tool_calls_made,
                warnings=warnings + ["Agent reached max iterations without completing"]
            )

        except Exception as e:
            self._log_event("agent_error", {
                "agent_id": self.agent_id,
                "error": str(e),
                "iteration": self.iteration
            })

            return AgentReActResult(
                agent_id=self.agent_id,
                status="error",
                error=str(e),
                iterations_used=self.iteration,
                tool_calls_made=self.tool_calls_made
            )

    # ============= Private Methods =============

    def _compile_context(
        self,
        original_input: Optional[Dict[str, Any]],
        prior_outputs: Optional[Dict[str, Dict[str, Any]]]
    ) -> CompiledContext:
        """Compile scoped context for this agent."""
        return self.context_compiler.compile_for_agent(
            agent_id=self.agent_id,
            original_input=original_input,
            prior_outputs=prior_outputs,
            observations=self.observations,
            from_agent_id=self.from_agent_id  # Phase 6: Pass handoff source for scoping
        )

    def _call_llm_for_reasoning(
        self,
        context: CompiledContext
    ) -> AgentReasoning:
        """
        Call LLM to get agent's reasoning and action.

        Demonstrates: Real-time LLM integration with ReAct pattern.
        """
        from ..prompts.react_prompts import build_worker_agent_prompt
        from .response_parser import parse_worker_agent_response, create_fallback_worker_response, ResponseParseError
        from .llm_client import create_llm_client

        if not self.llm_client:
            # Stub fallback if no LLM client provided
            return AgentReasoning(
                reasoning=f"[STUB] Agent {self.agent_id} iteration {self.iteration} reasoning",
                action=AgentAction(
                    type=ActionType.FINAL_OUTPUT,
                    output={"stub": True, "agent": self.agent_id}
                )
            )

        try:
            # Get available tools for this agent
            available_tools = self.registry.get_tools_for_agent(self.agent_id)
            tools_list = [
                {
                    "tool_id": tool.tool_id,
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema
                }
                for tool in available_tools
            ]

            # Build ReAct prompt
            messages = build_worker_agent_prompt(
                agent_name=self.agent.name,
                agent_description=self.agent.description,
                agent_capabilities=self.agent.capabilities,
                available_tools=tools_list,
                working_context=context.dict(),
                observations=self.observations
            )

            # Get model profile
            model_profile = self.registry.get_model_profile(self.agent.model_profile_id)
            if not model_profile:
                raise RuntimeError(f"Model profile '{self.agent.model_profile_id}' not found")

            # Create LLM client for this agent's model
            llm_client = create_llm_client(model_profile, self.session_id)

            # Call LLM
            llm_response = llm_client.call(messages)

            # Parse response
            reasoning = parse_worker_agent_response(llm_response.content, self.agent_id)

            return reasoning

        except ResponseParseError as e:
            # Parsing failed - return fallback
            self._log_event("llm_response_parse_error", {
                "agent_id": self.agent_id,
                "error": str(e),
                "iteration": self.iteration
            })
            return create_fallback_worker_response(self.agent_id, str(e))

        except Exception as e:
            # LLM call failed - return error fallback
            self._log_event("llm_call_error", {
                "agent_id": self.agent_id,
                "error": str(e),
                "iteration": self.iteration
            })
            return create_fallback_worker_response(self.agent_id, f"LLM call failed: {str(e)}")

    def _execute_tools(
        self,
        tool_requests: List[ToolRequest]
    ) -> bool:
        """
        Execute requested tools and add results to observations.

        Demonstrates:
        - Governance enforcement
        - Error handling
        - Observation accumulation
        """
        all_success = True

        for tool_req in tool_requests:
            # Governance check
            access_check = self.governance.check_tool_access(
                self.agent_id,
                tool_req.tool_id
            )

            if not access_check.allowed:
                self._log_event("tool_denied", {
                    "agent_id": self.agent_id,
                    "tool_id": tool_req.tool_id,
                    "reason": access_check.violation.reason if access_check.violation else "unknown"
                })
                all_success = False
                continue

            # Execute tool (Phase 4 integration point)
            tool_result = self._invoke_tool(tool_req.tool_id, tool_req.parameters)

            if tool_result.get("success"):
                # Add to observations
                self.observations.append({
                    "iteration": self.iteration,
                    "tool_id": tool_req.tool_id,
                    "parameters": tool_req.parameters,
                    "result": tool_result.get("result"),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

                self._log_event("tool_invocation", {
                    "agent_id": self.agent_id,
                    "iteration": self.iteration,
                    "tool_id": tool_req.tool_id,
                    "success": True
                })

                self.tool_calls_made += 1
            else:
                self._log_event("tool_error", {
                    "agent_id": self.agent_id,
                    "tool_id": tool_req.tool_id,
                    "error": tool_result.get("error")
                })
                all_success = False

        return all_success

    def _invoke_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke tool via tools gateway.

        Phase 4 integration point: This will use ToolsGatewayClient.
        """
        if not self.tools_client:
            # Stub for Phase 2
            return {
                "success": True,
                "result": {"stub": True, "tool": tool_id}
            }

        # Phase 4: Real implementation
        # return self.tools_client.invoke(tool_id, parameters)
        raise NotImplementedError("Tools Gateway integration in Phase 4")

    def _validate_output(
        self,
        output: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Validate agent output against schema.

        Demonstrates:
        - Production-grade validation with Pydantic schemas
        - Configurable failure limits
        - Comprehensive observability (dual logging)
        - Context engineering (session/agent/iteration tracking)

        Returns:
            True if validation passes, False otherwise
        """
        from ..schemas.validators import validate_agent_output, SchemaValidationError

        # Basic null check
        if not output:
            logger.warning(
                f"Output validation failed for {self.agent_id}: output is None or empty "
                f"[session={self.session_id}, iter={self.iteration}]"
            )
            return False

        config = get_config()

        try:
            # Validate using Pydantic schema
            validated = validate_agent_output(self.agent_id, output)

            # Log successful validation event (structured)
            self._log_event("output_validated", {
                "agent_id": self.agent_id,
                "iteration": self.iteration,
                "schema_version": validated.version,
                "validation_attempt": self._validation_failures + 1
            })

            # Reset failure counter on success
            self._validation_failures = 0

            logger.info(
                f"Output validation succeeded for {self.agent_id} "
                f"[session={self.session_id}, iter={self.iteration}, version={validated.version}]"
            )

            return True

        except SchemaValidationError as e:
            # Increment failure counter
            self._validation_failures += 1

            # Get configurable limit
            max_failures = config.schema.validation_failure_limit

            # Prepare output sample for logging (if enabled)
            output_sample = None
            if config.schema.log_validation_sample:
                output_str = str(output)
                max_chars = config.schema.max_validation_sample_chars
                output_sample = output_str[:max_chars] + ("..." if len(output_str) > max_chars else "")

            # Log validation failure event (structured for observability)
            self._log_event("output_validation_failed", {
                "agent_id": self.agent_id,
                "iteration": self.iteration,
                "validation_attempt": self._validation_failures,
                "max_attempts": max_failures,
                "error_message": str(e),
                "error_details": e.errors if hasattr(e, 'errors') else [],
                "will_retry": self._validation_failures < max_failures,
                "output_sample": output_sample
            })

            # Python log for real-time monitoring
            logger.warning(
                f"Output validation failed for {self.agent_id} "
                f"[session={self.session_id}, iter={self.iteration}, "
                f"attempt={self._validation_failures}/{max_failures}]: {str(e)}"
            )

            # Check if limit exceeded
            if self._validation_failures >= max_failures:
                logger.error(
                    f"Max validation failures ({max_failures}) exceeded for {self.agent_id}. "
                    f"[session={self.session_id}] Agent execution should terminate."
                )

                # Log critical threshold event
                self._log_event("validation_failure_limit_exceeded", {
                    "agent_id": self.agent_id,
                    "iteration": self.iteration,
                    "total_failures": self._validation_failures,
                    "limit": max_failures
                })

            return False

        except Exception as e:
            # Catch any unexpected validation errors
            self._validation_failures += 1

            logger.error(
                f"Unexpected validation error for {self.agent_id} "
                f"[session={self.session_id}, iter={self.iteration}]: {str(e)}",
                exc_info=True
            )

            self._log_event("output_validation_error", {
                "agent_id": self.agent_id,
                "iteration": self.iteration,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })

            return False

    def _extract_partial_output(self) -> Optional[Dict[str, Any]]:
        """Extract best available partial output when max iterations reached."""
        if self.observations:
            # Return last observation result
            last_obs = self.observations[-1]
            return {
                "partial": True,
                "last_observation": last_obs.get("result"),
                "iterations_completed": self.iteration
            }
        return {"partial": True, "no_output": True}

    def _log_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Log event to storage AND progress store for real-time streaming."""
        event = {
            "event_type": event_type,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data
        }

        # Write to storage (existing - for persistence and replay)
        self.storage.write_event(self.session_id, event)

        # Write to progress store (NEW - for real-time SSE streaming)
        self.progress_store.add_event(self.session_id, event)


def create_agent_react_loop(
    session_id: str,
    agent_id: str,
    llm_client: Optional[Any] = None,
    tools_client: Optional[Any] = None,
    from_agent_id: Optional[str] = None  # Phase 6: Track handoff source
) -> AgentReActLoopController:
    """Factory function to create AgentReActLoopController."""
    return AgentReActLoopController(
        session_id=session_id,
        agent_id=agent_id,
        llm_client=llm_client,
        tools_client=tools_client,
        from_agent_id=from_agent_id  # Phase 6: Pass handoff source
    )
