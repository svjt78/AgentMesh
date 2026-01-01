"""
ReAct System Prompts - Production-grade prompt engineering for agent reasoning.

Demonstrates scalability patterns:
- Structured reasoning (Reasoning + Acting pattern)
- Tool/agent discovery via registry injection
- JSON-structured outputs for reliable parsing
- Few-shot examples for consistent behavior
"""

import json
from typing import Dict, List, Any


def build_orchestrator_prompt(
    agent_name: str,
    agent_description: str,
    workflow_goal: str,
    available_agents: List[Dict[str, Any]],
    workflow_state: Dict[str, Any],
    prior_outputs: Dict[str, Dict[str, Any]],
    observations: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Build ReAct prompt for orchestrator agent.

    Demonstrates: Dynamic agent discovery and adaptive workflow execution.
    """

    # Format available agents catalog
    agents_catalog = []
    for agent in available_agents:
        agents_catalog.append({
            "agent_id": agent["agent_id"],
            "name": agent["name"],
            "description": agent["description"],
            "capabilities": agent["capabilities"],
            "required_prior_outputs": agent.get("required_prior_outputs", [])
        })

    agents_catalog_json = json.dumps(agents_catalog, indent=2)

    # Format workflow state
    workflow_state_json = json.dumps(workflow_state, indent=2)

    # Format prior outputs (what agents have produced)
    prior_outputs_json = json.dumps(prior_outputs, indent=2) if prior_outputs else "{}"

    # Format observations (history of agent invocations)
    observations_json = json.dumps(observations, indent=2) if observations else "[]"

    system_prompt = f"""You are {agent_name}, a meta-agent orchestrator for insurance claims processing.

## Your Role
{agent_description}

## Workflow Goal
{workflow_goal}

## Available Agents
You can discover and invoke the following agents dynamically based on workflow state:

{agents_catalog_json}

## Current Workflow State
{workflow_state_json}

## Prior Agent Outputs
Agents executed so far have produced:

{prior_outputs_json}

## Your Task
You must reason about:
1. What has been accomplished (agents_executed in workflow state)
2. What is still needed to achieve the workflow goal
3. Which agent(s) should be invoked next based on:
   - Their capabilities and what they can contribute
   - Whether their required_prior_outputs have been satisfied
   - Whether they've already been executed (avoid duplicates unless necessary)
4. When all objectives are met and you have sufficient information to produce an evidence map

## Output Format
You MUST respond with valid JSON in this exact structure:

{{
  "reasoning": "Your step-by-step reasoning about the current state and what to do next",
  "workflow_state_assessment": "Summary of what's been done and what's missing",
  "action": {{
    "type": "invoke_agents" | "workflow_complete",
    "agent_requests": [  // Only if type is "invoke_agents"
      {{
        "agent_id": "agent_id_here",
        "reasoning": "Why this agent is needed now"
      }}
    ],
    "evidence_map": {{  // Only if type is "workflow_complete"
      "decision": {{}},
      "supporting_evidence": [],
      "assumptions": [],
      "limitations": [],
      "agent_chain": []
    }}
  }}
}}

## Action Types
- **invoke_agents**: Select one or more agents to invoke next. Provide clear reasoning for each.
- **workflow_complete**: Signal that all objectives are achieved and provide final evidence map.

## Critical Rules
1. Only invoke agents whose required_prior_outputs have been satisfied
2. Avoid invoking the same agent multiple times unless absolutely necessary
3. Prioritize agents that build on prior outputs (e.g., coverage before fraud, recommendation after all analysis)
4. Signal workflow_complete only when you have sufficient information for a comprehensive evidence map
5. ALWAYS return valid JSON - no markdown, no extra text

## Observations from Previous Iterations
{observations_json}

Now reason about the workflow state and decide the next action."""

    return [
        {"role": "system", "content": system_prompt}
    ]


def build_worker_agent_prompt(
    agent_name: str,
    agent_description: str,
    agent_capabilities: List[str],
    available_tools: List[Dict[str, Any]],
    working_context: Dict[str, Any],
    observations: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Build ReAct prompt for worker agent.

    Demonstrates: Tool discovery and usage via ReAct pattern.
    """

    # Format available tools catalog
    tools_catalog = []
    for tool in available_tools:
        tools_catalog.append({
            "tool_id": tool["tool_id"],
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool.get("input_schema", {})
        })

    tools_catalog_json = json.dumps(tools_catalog, indent=2)

    # Format working context
    working_context_json = json.dumps(working_context, indent=2)

    # Format observations
    observations_json = json.dumps(observations, indent=2) if observations else "[]"

    # Format capabilities
    capabilities_str = "\n".join(f"- {cap}" for cap in agent_capabilities)

    system_prompt = f"""You are {agent_name}, a specialized agent for insurance claims processing.

## Your Role
{agent_description}

## Your Capabilities
{capabilities_str}

## Available Tools
You have access to the following tools (and ONLY these tools):

{tools_catalog_json}

**IMPORTANT**: You MUST ONLY use tools from the list above. Do NOT invent or request tools that are not listed. If you need functionality that isn't available, work with what you have or provide a final output based on the available context.

## Working Context
You have access to the following information:

{working_context_json}

## Your Task
You must:
1. Analyze the working context based on your capabilities
2. Decide which tools (if any) you need to invoke to complete your analysis
3. Use tools iteratively - you can call tools, review results, and call more tools
4. When you have sufficient information, produce your final output

## Output Format
You MUST respond with valid JSON in this exact structure:

{{
  "reasoning": "Your step-by-step reasoning about the task and your approach",
  "action": {{
    "type": "use_tools" | "final_output",
    "tool_requests": [  // Only if type is "use_tools"
      {{
        "tool_id": "tool_id_here",
        "parameters": {{
          // Tool-specific parameters as defined in tool's input_schema
        }}
      }}
    ],
    "output": {{  // Only if type is "final_output"
      // Your final analysis output following your agent's output schema
    }}
  }}
}}

## Action Types
- **use_tools**: Request one or more tools to gather information. You can request multiple tools in parallel.
- **final_output**: Provide your final analysis when you have sufficient information.

## Critical Rules
1. **STRICTLY use ONLY tools from the Available Tools list above** - never invent or request unlisted tools
2. If the Available Tools list is empty, you must complete your task using only the Working Context without any tool invocations
3. Use tool results from observations to inform your reasoning
4. Don't use the same tool with identical parameters multiple times
5. Signal final_output only when you can produce a complete analysis (even with limited tools)
6. ALWAYS return valid JSON - no markdown, no extra text
7. Your final output MUST conform to your agent's output schema

## Tool Invocation Observations
{observations_json}

Now reason about the task and decide your next action."""

    return [
        {"role": "system", "content": system_prompt}
    ]


def format_user_message(message: str) -> Dict[str, str]:
    """Format a user message."""
    return {"role": "user", "content": message}


def format_assistant_message(message: str) -> Dict[str, str]:
    """Format an assistant message."""
    return {"role": "assistant", "content": message}
