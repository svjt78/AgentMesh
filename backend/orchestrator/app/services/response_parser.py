"""
Response Parser - Parse and validate LLM JSON responses.

Demonstrates scalability patterns:
- Robust JSON parsing with fallbacks
- Schema validation
- Error recovery
- Malformed response handling
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pydantic import ValidationError

from ..services.agent_react_loop import AgentReasoning, AgentAction, ActionType, ToolRequest
from ..services.orchestrator_runner import (
    OrchestratorReasoning,
    OrchestratorAction,
    OrchestratorActionType,
    AgentInvocationRequest
)


class ResponseParseError(Exception):
    """Custom exception for response parsing errors."""
    pass


def extract_json_from_response(content: str) -> str:
    """
    Extract JSON from LLM response.

    Handles cases where LLM wraps JSON in markdown code blocks or adds extra text.

    Demonstrates: Robust parsing with multiple extraction strategies.
    """
    # Strategy 1: Try to find JSON in markdown code block
    json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_block_pattern, content, re.DOTALL)
    if match:
        return match.group(1)

    # Strategy 2: Try to find JSON object directly
    json_object_pattern = r'\{.*\}'
    match = re.search(json_object_pattern, content, re.DOTALL)
    if match:
        return match.group(0)

    # Strategy 3: Content itself might be JSON
    return content.strip()


def parse_worker_agent_response(
    response_content: str,
    agent_id: str
) -> AgentReasoning:
    """
    Parse worker agent LLM response into AgentReasoning.

    Demonstrates: Structured response parsing with validation.

    Args:
        response_content: Raw LLM response
        agent_id: Agent ID for error context

    Returns:
        AgentReasoning object

    Raises:
        ResponseParseError: If response cannot be parsed
    """
    try:
        # Extract JSON
        json_str = extract_json_from_response(response_content)

        # Parse JSON
        data = json.loads(json_str)

        # Validate required fields
        if "reasoning" not in data:
            raise ResponseParseError("Missing required field: reasoning")

        if "action" not in data:
            raise ResponseParseError("Missing required field: action")

        action_data = data["action"]

        if "type" not in action_data:
            raise ResponseParseError("Missing required field: action.type")

        # Parse action type
        action_type_str = action_data["type"]
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            raise ResponseParseError(
                f"Invalid action type: {action_type_str}. Expected 'use_tools' or 'final_output'"
            )

        # Parse based on action type
        if action_type == ActionType.USE_TOOLS:
            # Parse tool requests
            if "tool_requests" not in action_data:
                raise ResponseParseError("use_tools action requires tool_requests field")

            tool_requests = []
            for tool_req_data in action_data["tool_requests"]:
                if "tool_id" not in tool_req_data:
                    raise ResponseParseError("Tool request missing tool_id")

                if "parameters" not in tool_req_data:
                    tool_req_data["parameters"] = {}

                tool_requests.append(ToolRequest(
                    tool_id=tool_req_data["tool_id"],
                    parameters=tool_req_data["parameters"]
                ))

            action = AgentAction(
                type=ActionType.USE_TOOLS,
                tool_requests=tool_requests
            )

        elif action_type == ActionType.FINAL_OUTPUT:
            # Parse output
            if "output" not in action_data:
                raise ResponseParseError("final_output action requires output field")

            action = AgentAction(
                type=ActionType.FINAL_OUTPUT,
                output=action_data["output"]
            )

        else:
            raise ResponseParseError(f"Unknown action type: {action_type}")

        # Build AgentReasoning
        return AgentReasoning(
            reasoning=data["reasoning"],
            action=action
        )

    except json.JSONDecodeError as e:
        raise ResponseParseError(f"Invalid JSON in response: {str(e)}")
    except ValidationError as e:
        raise ResponseParseError(f"Response validation failed: {str(e)}")
    except Exception as e:
        raise ResponseParseError(f"Unexpected error parsing response: {str(e)}")


def parse_orchestrator_response(
    response_content: str
) -> OrchestratorReasoning:
    """
    Parse orchestrator LLM response into OrchestratorReasoning.

    Demonstrates: Complex structured response parsing.

    Args:
        response_content: Raw LLM response

    Returns:
        OrchestratorReasoning object

    Raises:
        ResponseParseError: If response cannot be parsed
    """
    try:
        # Extract JSON
        json_str = extract_json_from_response(response_content)

        # Parse JSON
        data = json.loads(json_str)

        # Validate required fields
        if "reasoning" not in data:
            raise ResponseParseError("Missing required field: reasoning")

        if "workflow_state_assessment" not in data:
            raise ResponseParseError("Missing required field: workflow_state_assessment")

        if "action" not in data:
            raise ResponseParseError("Missing required field: action")

        action_data = data["action"]

        if "type" not in action_data:
            raise ResponseParseError("Missing required field: action.type")

        # Parse action type
        action_type_str = action_data["type"]
        try:
            action_type = OrchestratorActionType(action_type_str)
        except ValueError:
            raise ResponseParseError(
                f"Invalid action type: {action_type_str}. Expected 'invoke_agents' or 'workflow_complete'"
            )

        # Parse based on action type
        if action_type == OrchestratorActionType.INVOKE_AGENTS:
            # Parse agent requests
            if "agent_requests" not in action_data:
                raise ResponseParseError("invoke_agents action requires agent_requests field")

            agent_requests = []
            for agent_req_data in action_data["agent_requests"]:
                if "agent_id" not in agent_req_data:
                    raise ResponseParseError("Agent request missing agent_id")

                reasoning = agent_req_data.get("reasoning", "No reasoning provided")

                agent_requests.append(AgentInvocationRequest(
                    agent_id=agent_req_data["agent_id"],
                    reasoning=reasoning
                ))

            action = OrchestratorAction(
                type=OrchestratorActionType.INVOKE_AGENTS,
                agent_requests=agent_requests
            )

        elif action_type == OrchestratorActionType.WORKFLOW_COMPLETE:
            # Parse evidence map
            if "evidence_map" not in action_data:
                raise ResponseParseError("workflow_complete action requires evidence_map field")

            action = OrchestratorAction(
                type=OrchestratorActionType.WORKFLOW_COMPLETE,
                evidence_map=action_data["evidence_map"]
            )

        else:
            raise ResponseParseError(f"Unknown action type: {action_type}")

        # Build OrchestratorReasoning
        return OrchestratorReasoning(
            reasoning=data["reasoning"],
            workflow_state_assessment=data["workflow_state_assessment"],
            action=action
        )

    except json.JSONDecodeError as e:
        raise ResponseParseError(f"Invalid JSON in response: {str(e)}")
    except ValidationError as e:
        raise ResponseParseError(f"Response validation failed: {str(e)}")
    except Exception as e:
        raise ResponseParseError(f"Unexpected error parsing response: {str(e)}")


def create_fallback_worker_response(
    agent_id: str,
    error_message: str
) -> AgentReasoning:
    """
    Create fallback response when parsing fails.

    Demonstrates: Graceful degradation pattern.
    """
    return AgentReasoning(
        reasoning=f"[FALLBACK] Response parsing failed: {error_message}. Returning empty output.",
        action=AgentAction(
            type=ActionType.FINAL_OUTPUT,
            output={"error": "response_parse_failure", "details": error_message}
        )
    )


def create_fallback_orchestrator_response(
    error_message: str,
    executed_agents: list
) -> OrchestratorReasoning:
    """
    Create fallback response when orchestrator parsing fails.

    Demonstrates: Forced completion on parse failure.
    """
    return OrchestratorReasoning(
        reasoning=f"[FALLBACK] Response parsing failed: {error_message}. Forcing workflow completion.",
        workflow_state_assessment=f"Agents executed: {executed_agents}. Forced completion due to parse failure.",
        action=OrchestratorAction(
            type=OrchestratorActionType.WORKFLOW_COMPLETE,
            evidence_map={
                "decision": {"error": "response_parse_failure"},
                "supporting_evidence": [],
                "assumptions": ["Response parsing failed, forced completion"],
                "limitations": [error_message],
                "agent_chain": executed_agents
            }
        )
    )
