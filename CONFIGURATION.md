# Configuration Parameters Guide

This document describes all configurable parameters in AgentMesh and how they control the multi-tier ReAct agentic workflow.

**Note:** This guide covers **environment variable configuration**. For **registry-based configuration** (agent definitions, tool access policies, workflow definitions), see the [Registry-Based Configuration](#registry-based-configuration) section at the end.

## Architecture Overview

AgentMesh uses a **meta-agent ReAct pattern** with two execution layers:

1. **Orchestrator Agent (Meta-Agent)** - Runs a ReAct loop to decide which worker agents to invoke
2. **Worker Agents** - Execute their own ReAct loops to use tools and generate structured outputs

This creates a hierarchical execution model: `Orchestrator → Worker Agents → Tools`

All parameters below control bounded execution at different layers to ensure workflows always terminate with predictable resource consumption.

---

## Parameter Categories

### 1. Orchestrator Agent Limits

Controls the meta-agent ReAct loop that coordinates the entire workflow.

```bash
ORCHESTRATOR_MAX_ITERATIONS=10
ORCHESTRATOR_ITERATION_TIMEOUT_SECONDS=30
```

#### ORCHESTRATOR_MAX_ITERATIONS
- **Default**: `10`
- **Used in**: `backend/orchestrator/app/services/orchestrator_runner.py:146`
- **Purpose**: Maximum number of reasoning cycles for the orchestrator agent

**What happens in each iteration:**
1. Orchestrator assesses workflow state (which agents executed, what outputs available)
2. Calls LLM to reason about next steps
3. Decides to either:
   - Invoke one or more worker agents
   - Signal workflow completion with evidence map
4. Collects agent results as observations for next iteration

**Termination behavior:**
- **Tier 1 (LLM signal)**: Orchestrator explicitly signals `workflow_complete` action
- **Tier 2 (Validation)**: System validates completion criteria (required agents executed, required outputs present)
- **Tier 3 (Forced)**: If max iterations reached, system forces completion with best available evidence map

Reference: `orchestrator_runner.py:210-230`

#### ORCHESTRATOR_ITERATION_TIMEOUT_SECONDS
- **Default**: `30`
- **Used in**: Configuration loaded but enforcement pending
- **Purpose**: Maximum time allowed per orchestrator reasoning cycle
- **Status**: Placeholder for timing-based safety mechanism (see `orchestrator_runner.py:634`)

---

### 2. Workflow Execution Limits

Session-wide constraints that apply across all orchestrator and agent activities.

```bash
WORKFLOW_MAX_DURATION_SECONDS=300
WORKFLOW_MAX_AGENT_INVOCATIONS=20
```

#### WORKFLOW_MAX_DURATION_SECONDS
- **Default**: `300` (5 minutes)
- **Used in**: `backend/orchestrator/app/services/orchestrator_runner.py:150`
- **Purpose**: Hard timeout for entire workflow execution

**Enforcement:**
- Checked before each orchestrator iteration
- If timeout approaching, orchestrator breaks loop and returns incomplete status
- Ensures workflows don't run indefinitely even if iteration limits haven't been reached

Reference: `orchestrator_runner.py:625-635`

#### WORKFLOW_MAX_AGENT_INVOCATIONS
- **Default**: `20`
- **Used in**: `backend/orchestrator/app/services/orchestrator_runner.py:432-442`
- **Purpose**: Maximum total number of agent invocations per workflow

**Enforcement:**
```python
total_invocations = sum(self.agent_invocations.values())
if total_invocations >= max_invocations:
    # Block further agent invocations, log event
    break
```

**Rationale:** Prevents runaway orchestrator behavior where it keeps invoking agents in a loop. Works in conjunction with per-agent duplicate limits.

---

### 3. Agent Execution Limits

Controls individual worker agent ReAct loops.

```bash
AGENT_DEFAULT_MAX_ITERATIONS=5
AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS=30
AGENT_MAX_DUPLICATE_INVOCATIONS=2
```

#### AGENT_DEFAULT_MAX_ITERATIONS
- **Default**: `5`
- **Used in**: `backend/orchestrator/app/services/agent_react_loop.py:144`
- **Purpose**: Maximum reasoning cycles per worker agent execution
- **Override**: Can be overridden per-agent in `agent_registry.json` via `max_iterations` field

**What happens in each agent iteration:**
1. Compile context (original input + prior agent outputs + observations)
2. Call LLM to reason about which tools to use
3. Parse action decision:
   - `use_tools`: Execute requested tools, add results to observations, continue loop
   - `final_output`: Validate output schema and return
4. Enforce governance policies on tool access

**Termination behavior:**
- If agent produces valid `final_output`, returns `status: "completed"`
- If max iterations reached without final output, returns `status: "incomplete"` with partial results
- Reference: `agent_react_loop.py:207-224`

#### AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS
- **Default**: `30`
- **Used in**: Configuration loaded, enforcement per agent
- **Purpose**: Maximum time per agent reasoning iteration
- **Override**: Can be overridden in registry via `iteration_timeout_seconds`

#### AGENT_MAX_DUPLICATE_INVOCATIONS
- **Default**: `2`
- **Used in**: `backend/orchestrator/app/services/governance_enforcer.py:105-122`
- **Purpose**: Maximum times the orchestrator can invoke the same agent in a single workflow

**Enforcement:**
```python
current_count = self._agent_invocation_counts.get(target_agent_id, 0)
if current_count >= max_duplicates:
    # Return PolicyViolation, block invocation
```

**Rationale:** Prevents orchestrator from repeatedly calling the same agent when it's not making progress. Complements the workflow-level `WORKFLOW_MAX_AGENT_INVOCATIONS` limit.

---

### 4. LLM Constraints

Controls interaction with LLM APIs (OpenAI, Anthropic) at the request and session level.

```bash
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3
LLM_MAX_TOKENS_PER_REQUEST=2000
LLM_MAX_TOKENS_PER_SESSION=50000
```

#### LLM_TIMEOUT_SECONDS
- **Default**: `30`
- **Used in**: `backend/orchestrator/app/services/llm_client.py`
- **Purpose**: API call timeout for LLM requests

**Behavior:** If LLM doesn't respond within timeout, request fails and triggers retry logic (if retries available).

#### LLM_MAX_RETRIES
- **Default**: `3`
- **Used in**: `backend/orchestrator/app/services/llm_client.py:146`
- **Purpose**: Maximum retry attempts for failed LLM calls

**Retry strategy:**
```python
for attempt in range(1, max_retries + 1):
    try:
        # Call LLM with exponential backoff
        # backoff_delay = initial_delay * (backoff_multiplier ** (attempt - 1))
    except Exception:
        if attempt < max_retries:
            time.sleep(backoff_delay)
            continue
```

**Configured per model profile** in `registries/model_profiles.json` with fields:
- `max_retries`: Number of attempts
- `backoff_multiplier`: Exponential factor (default: 2)
- `initial_delay_ms`: Starting delay (default: 1000ms)

#### LLM_MAX_TOKENS_PER_REQUEST
- **Default**: `2000`
- **Used in**: `backend/orchestrator/app/services/context_compiler.py`
- **Purpose**: Maximum context size per individual LLM call

**Context compilation:**
- `ContextCompiler` uses this to truncate context when building prompts
- Prioritizes recent agent outputs over older ones
- Ensures prompts fit within model's context window
- Prevents excessive token costs per call

#### LLM_MAX_TOKENS_PER_SESSION
- **Default**: `50000`
- **Used in**: `backend/orchestrator/app/services/llm_client.py:54`, `governance_enforcer.py`
- **Purpose**: Total token budget across all LLM calls in a workflow session

**Enforcement:**
```python
# Track cumulative token usage
self.total_tokens += response.tokens_used["total"]

# Check against limit before each call
if self.total_tokens >= max_session_tokens:
    # Raise PolicyViolation
```

**Rationale:** Prevents cost runaway in long-running workflows. Works across both orchestrator and worker agent LLM calls.

---

### 5. Governance Limits

Cross-cutting session-wide constraints for compliance and cost control.

```bash
MAX_TOOL_INVOCATIONS_PER_SESSION=50
MAX_LLM_CALLS_PER_SESSION=30
```

#### MAX_TOOL_INVOCATIONS_PER_SESSION
- **Default**: `50`
- **Used in**: `backend/orchestrator/app/services/governance_enforcer.py:64`
- **Purpose**: Total allowed tool invocations across all agents

**Tracking:**
```python
self._tool_invocation_count = 0

def check_tool_access(agent_id, tool_id):
    if self._tool_invocation_count >= MAX_TOOL_INVOCATIONS_PER_SESSION:
        # Return PolicyViolation
    self._tool_invocation_count += 1
```

**Scope:** Cumulative across all worker agents in the workflow. Prevents excessive external API calls or expensive tool operations.

#### MAX_LLM_CALLS_PER_SESSION
- **Default**: `30`
- **Used in**: `backend/orchestrator/app/services/governance_enforcer.py:65`
- **Purpose**: Total allowed LLM API calls in a workflow

**Tracking:**
```python
self._llm_call_count = 0
# Incremented on each orchestrator + agent LLM call
```

**Why this matters:**
- Complements `LLM_MAX_TOKENS_PER_SESSION` for cost control
- Prevents workflows with many short LLM calls from consuming excessive API quota
- Example: Orchestrator (10 iterations) + 5 agents (5 iterations each) = up to 35 calls

---

### 6. Safety Thresholds

Error recovery and circuit breaker mechanisms.

```bash
CONSECUTIVE_NO_PROGRESS_LIMIT=2
MALFORMED_RESPONSE_LIMIT=3
```

#### CONSECUTIVE_NO_PROGRESS_LIMIT
- **Default**: `2`
- **Used in**: Safety mechanism for detecting agent loops
- **Purpose**: Maximum iterations where agent makes no meaningful progress

**Detection criteria:**
- Same tool called repeatedly with identical parameters
- Tool results unchanged across iterations
- No new observations added to context

**Behavior:** If limit reached, agent terminates early rather than burning through all iterations.

**Status:** Framework in place, detection logic can be enhanced per use case.

#### MALFORMED_RESPONSE_LIMIT
- **Default**: `3`
- **Used in**: `backend/orchestrator/app/services/agent_react_loop.py:473-514`
- **Purpose**: Maximum output validation failures before agent errors

**Validation flow:**
1. Agent produces `final_output`
2. System validates against Pydantic schema (defined in `schemas/agent_outputs.py`)
3. If validation fails:
   - Increment `self._validation_failures`
   - Log `output_validation_failed` event with error details
   - Agent continues to next iteration to try again
4. If failures reach `MALFORMED_RESPONSE_LIMIT`:
   - Log `validation_failure_limit_exceeded` event
   - Agent terminates with error status

**Implementation:**
```python
if self._validation_failures >= max_failures:
    logger.error(
        f"Max validation failures ({max_failures}) exceeded for {agent_id}"
    )
    # Agent execution should terminate
```

Reference: `agent_react_loop.py:502-514`

**Rationale:** Prevents agents from endlessly producing invalid outputs due to LLM confusion or schema mismatches.

---

## Multi-Tier Execution Flow

Here's how these limits interact in a typical workflow execution:

```
┌─────────────────────────────────────────────────────────────────┐
│ WORKFLOW START                                                  │
│ ✓ Start WORKFLOW_MAX_DURATION_SECONDS timer                    │
│ ✓ Initialize session tracking (tokens, calls, invocations)     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR ITERATION 1                                        │
│ ✓ Check: iteration < ORCHESTRATOR_MAX_ITERATIONS                │
│ ✓ Check: elapsed_time < WORKFLOW_MAX_DURATION_SECONDS          │
│ ✓ Compile context, call LLM                                    │
│   • Check: llm_calls < MAX_LLM_CALLS_PER_SESSION               │
│   • Check: timeout < LLM_TIMEOUT_SECONDS                       │
│   • Retry up to LLM_MAX_RETRIES on failure                     │
│ ✓ Orchestrator decides: "Invoke Agent A, Agent B"              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────┴────────────────────┐
         ↓                                         ↓
┌─────────────────────┐                 ┌─────────────────────┐
│ AGENT A EXECUTION   │                 │ AGENT B EXECUTION   │
└─────────────────────┘                 └─────────────────────┘
         ↓                                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT A - ITERATION 1                                           │
│ ✓ Check: total_agents < WORKFLOW_MAX_AGENT_INVOCATIONS         │
│ ✓ Check: agent_a_count < AGENT_MAX_DUPLICATE_INVOCATIONS       │
│ ✓ Check: iteration < AGENT_DEFAULT_MAX_ITERATIONS              │
│ ✓ Compile context, call LLM                                    │
│   • Check: session tokens < LLM_MAX_TOKENS_PER_SESSION         │
│   • Check: request tokens < LLM_MAX_TOKENS_PER_REQUEST         │
│ ✓ Agent decides: "Use Tool X"                                  │
│ ✓ Check: tool_invocations < MAX_TOOL_INVOCATIONS_PER_SESSION   │
│ ✓ Execute Tool X, add result to observations                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT A - ITERATION 2                                           │
│ ✓ Agent decides: "Final output"                                │
│ ✓ Validate output against schema                               │
│   • If fails: validation_failures++                            │
│   • Check: validation_failures < MALFORMED_RESPONSE_LIMIT      │
│ ✓ Output valid → Return to orchestrator                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR ITERATION 2                                        │
│ ✓ Orchestrator receives Agent A, Agent B outputs               │
│ ✓ Assesses: All required agents executed, outputs complete     │
│ ✓ Decides: "Workflow complete"                                 │
│ ✓ Build evidence map from agent outputs                        │
│ ✓ Return final result                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Observability and Event Logging

All limit checks and boundary conditions are logged as structured events to:

1. **Persistent storage**: `storage/sessions/{session_id}.jsonl`
   - Full event history for replay and audit
   - Each event includes timestamp, session_id, agent_id, iteration number

2. **Real-time streaming**: Via `SSEBroadcaster` to frontend
   - Live updates during workflow execution
   - Event types for monitoring progress

### Key Event Types

| Event Type | Triggered When | Reference |
|------------|---------------|-----------|
| `orchestrator_started` | Workflow begins | `orchestrator_runner.py:135` |
| `orchestrator_reasoning` | Each orchestrator iteration | `orchestrator_runner.py:161` |
| `agent_invocation_denied` | Governance blocks agent call | `orchestrator_runner.py:424` |
| `workflow_limit_exceeded` | Workflow limits reached | `orchestrator_runner.py:436` |
| `agent_started` | Worker agent begins execution | `agent_react_loop.py:135` |
| `agent_reasoning` | Each agent iteration | `agent_react_loop.py:170` |
| `iteration_limit_exceeded` | Agent max iterations reached | `agent_react_loop.py:153` |
| `tool_invocation` | Tool successfully executed | `agent_react_loop.py:379` |
| `tool_denied` | Governance blocks tool access | `agent_react_loop.py:358` |
| `output_validation_failed` | Schema validation fails | `agent_react_loop.py:483` |
| `validation_failure_limit_exceeded` | Malformed response limit hit | `agent_react_loop.py:509` |
| `llm_call` | Every LLM API call (success/failure) | `llm_client.py:75` |
| `orchestrator_completed` | Workflow completes successfully | `orchestrator_runner.py:187` |
| `orchestrator_incomplete` | Max iterations without completion | `orchestrator_runner.py:211` |

### Event Structure

```json
{
  "event_type": "agent_reasoning",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "fraud_detection_agent",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "iteration": 2,
  "reasoning": "Need to call policy_snapshot tool to get coverage details",
  "action_type": "use_tools"
}
```

---

## Configuration Best Practices

### Development vs Production

**Development Settings** (faster iteration, more visibility):
```bash
ORCHESTRATOR_MAX_ITERATIONS=5
AGENT_DEFAULT_MAX_ITERATIONS=3
LLM_TIMEOUT_SECONDS=15
WORKFLOW_MAX_DURATION_SECONDS=120
```

**Production Settings** (higher limits, more resilient):
```bash
ORCHESTRATOR_MAX_ITERATIONS=15
AGENT_DEFAULT_MAX_ITERATIONS=7
LLM_TIMEOUT_SECONDS=60
WORKFLOW_MAX_DURATION_SECONDS=600
LLM_MAX_RETRIES=5
```

### Cost Control

For cost-sensitive environments, tighten:
```bash
LLM_MAX_TOKENS_PER_SESSION=20000
MAX_LLM_CALLS_PER_SESSION=15
MAX_TOOL_INVOCATIONS_PER_SESSION=25
```

### High-Throughput Scenarios

For complex workflows requiring more steps:
```bash
WORKFLOW_MAX_AGENT_INVOCATIONS=50
ORCHESTRATOR_MAX_ITERATIONS=20
AGENT_MAX_DUPLICATE_INVOCATIONS=3
```

### Testing and Debugging

For testing specific agents in isolation:
```bash
ORCHESTRATOR_MAX_ITERATIONS=1  # Skip orchestrator loop
AGENT_DEFAULT_MAX_ITERATIONS=10  # Give agent more room
MALFORMED_RESPONSE_LIMIT=5  # More lenient validation
```

---

## Registry Overrides

Several parameters can be overridden per-agent in `registries/agent_registry.json`:

```json
{
  "agent_id": "fraud_detection_agent",
  "max_iterations": 7,  // Overrides AGENT_DEFAULT_MAX_ITERATIONS
  "iteration_timeout_seconds": 45,  // Overrides AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS
  "max_context_tokens": 3000  // Overrides LLM_MAX_TOKENS_PER_REQUEST for this agent
}
```

**Priority order:** Agent-specific registry value > Environment variable > Hardcoded default

---

## Troubleshooting

### Workflow Times Out
- Check `WORKFLOW_MAX_DURATION_SECONDS` - may need to increase
- Review session JSONL to see which agents taking longest
- Consider increasing `LLM_TIMEOUT_SECONDS` if many retries

### Agent Reaches Max Iterations
- Check `AGENT_DEFAULT_MAX_ITERATIONS` - agent may need more reasoning cycles
- Review `agent_reasoning` events to see if agent is making progress
- Check for tool failures preventing agent from completing
- Verify agent's output schema matches expected format (validation failures)

### Validation Failures
- Check schema definition in `schemas/agent_outputs.py`
- Review `output_validation_failed` events for error details
- May need to increase `MALFORMED_RESPONSE_LIMIT` if agent needs more attempts
- Consider improving agent prompt to guide toward correct schema

### LLM Call Limits Reached
- Check `MAX_LLM_CALLS_PER_SESSION` - may be too restrictive
- Review workflow design - too many agents or iterations?
- Consider using cheaper models (Haiku vs Sonnet) for simple agents
- Check `llm_call` events to see distribution across orchestrator/agents

### Cost Overruns
- Reduce `LLM_MAX_TOKENS_PER_SESSION` and `MAX_LLM_CALLS_PER_SESSION`
- Use context truncation more aggressively (lower `LLM_MAX_TOKENS_PER_REQUEST`)
- Assign faster models to non-critical agents via `model_profile_id`
- Review `llm_call` events to identify high-token consumers

---

---

## Registry-Based Configuration

In addition to environment variables, AgentMesh uses **JSON registry files** for structural configuration. These registries define the agents, tools, workflows, and governance policies that make the system dynamic and registry-driven.

### Configuration Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Environment Variables (.env)                      │
│ → Execution limits, timeouts, token budgets                │
│ → Overrides registry defaults                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Registry Files (registries/*.json)                │
│ → Agent definitions, capabilities, schemas                 │
│ → Tool catalog and access policies                         │
│ → Workflow definitions                                     │
│ → Governance rules (who can invoke/use what)               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Hardcoded Defaults (config.py)                    │
│ → Fallback values if env vars not set                      │
└─────────────────────────────────────────────────────────────┘
```

**Priority:** Environment Variable > Registry Value > Hardcoded Default

### Registry Files

#### 1. Agent Registry (`registries/agent_registry.json`)

Defines all available agents, their capabilities, and execution parameters.

**Key configurable fields:**

```json
{
  "agent_id": "severity_agent",
  "name": "Severity & Complexity Agent",
  "capabilities": ["complexity_analysis", "severity_classification"],
  "allowed_tools": [],  // ← TOOL ACCESS CONTROL
  "model_profile_id": "default_gpt35",
  "max_iterations": 3,  // ← Per-agent override
  "iteration_timeout_seconds": 30,
  "output_schema": { /* JSON Schema */ },
  "context_requirements": {
    "requires_prior_outputs": ["intake", "coverage", "fraud"],
    "max_context_tokens": 5000  // ← Per-agent token limit
  }
}
```

**Important:**
- `capabilities` = What the agent can DO (skills, not tools)
- `allowed_tools` = Which external tools the agent can INVOKE
- If `allowed_tools` is empty `[]`, the agent uses only LLM reasoning

**Per-Agent Overrides:**
- `max_iterations` overrides `AGENT_DEFAULT_MAX_ITERATIONS`
- `iteration_timeout_seconds` overrides `AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS`
- `max_context_tokens` overrides `LLM_MAX_TOKENS_PER_REQUEST`

Reference: `backend/orchestrator/app/services/registry_manager.py:142-150`

#### 2. Tool Registry (`registries/tool_registry.json`)

Catalog of all available tools with LLM-friendly descriptions.

**Tool definition:**

```json
{
  "tool_id": "fraud_rules",
  "name": "Fraud Rules Engine",
  "description": "Evaluates claim data against fraud indicators...",
  "endpoint": "/invoke/fraud_rules",
  "input_schema": { /* What params the tool accepts */ },
  "output_schema": { /* What the tool returns */ },
  "lineage_tags": ["fraud_detection", "rule_based"]
}
```

**Available tools:**
1. `policy_snapshot` - Retrieve policy coverage details
2. `fraud_rules` - Rule-based fraud detection
3. `similarity` - Find similar historical claims
4. `schema_validator` - Validate claim data schema
5. `coverage_rules` - Coverage determination rules
6. `decision_rules` - Recommendation business rules

**Note:** The LLM reads tool descriptions to decide which tools to use. Write clear, actionable descriptions.

#### 3. Governance Policies (`registries/governance_policies.json`)

Defines **who can invoke/use what** - the authorization layer.

**Three governance dimensions:**

##### a) Agent Invocation Access

Controls which agents the orchestrator can invoke:

```json
{
  "agent_invocation_access": {
    "enforcement_level": "strict",
    "rules": [
      {
        "agent_id": "orchestrator_agent",
        "allowed_agents": ["intake_agent", "fraud_agent", "severity_agent", ...],
        "denied_agents": ["orchestrator_agent"]  // Can't invoke itself
      }
    ]
  }
}
```

**Enforcement:** `registry_manager.py:326`, `governance_enforcer.py:70`

##### b) Agent Tool Access

Controls which tools each agent can use:

```json
{
  "agent_tool_access": {
    "enforcement_level": "strict",
    "rules": [
      {
        "agent_id": "fraud_agent",
        "allowed_tools": ["fraud_rules", "similarity"],
        "denied_tools": ["policy_snapshot", "decision_rules"]
      },
      {
        "agent_id": "severity_agent",
        "allowed_tools": [],  // ← NO TOOLS - LLM reasoning only
        "denied_tools": ["fraud_rules", "policy_snapshot", "similarity", ...]
      }
    ]
  }
}
```

**Why the `severity_agent` has empty `allowed_tools`:**
- It performs **classification/analysis** using LLM reasoning
- Only needs context from prior agents (intake, coverage, fraud outputs)
- No external tool calls required
- If LLM tries to invoke a tool, governance blocks it

**Enforcement:** `governance_enforcer.py:150-164`

**Common error:** If you see `Tool access denied`, check:
1. Is the tool in `tool_registry.json`?
2. Is the tool in the agent's `allowed_tools` in both `agent_registry.json` AND `governance_policies.json`?
3. Is the agent confusing a **capability** with a **tool**?

##### c) Iteration Limits (Registry-based)

Per-agent iteration overrides:

```json
{
  "iteration_limits": {
    "global_max_iterations": 5,
    "agent_overrides": [
      {"agent_id": "orchestrator_agent", "max_iterations": 10},
      {"agent_id": "fraud_agent", "max_iterations": 5},
      {"agent_id": "intake_agent", "max_iterations": 3}
    ]
  }
}
```

**Priority:** Agent-specific override > `AGENT_DEFAULT_MAX_ITERATIONS` env var > `global_max_iterations`

#### 4. Model Profiles (`registries/model_profiles.json`)

Defines LLM model configurations with retry policies:

```json
{
  "profile_id": "default_gpt35",
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "temperature": 0.0,
  "max_tokens": 1500,
  "retry_policy": {
    "max_retries": 3,
    "backoff_multiplier": 2,
    "initial_delay_ms": 1000
  }
}
```

**Usage:** Agents reference model profiles via `model_profile_id` field. Allows different agents to use different models (e.g., Haiku for simple tasks, Sonnet for complex reasoning).

**Cost optimization:** Assign cheaper/faster models to non-critical agents.

#### 5. Workflow Definitions (`registries/workflows/*.json`)

Defines workflow goals, suggested agent sequences, and completion criteria.

**Example: `workflows/claims_triage.json`**

```json
{
  "workflow_id": "claims_triage",
  "goal": "Assess claim and provide recommendation",
  "mode": "advisory",  // ← Orchestrator adapts, not prescriptive
  "suggested_sequence": [
    "intake_agent",
    "coverage_agent",
    "fraud_agent",
    "severity_agent",
    "recommendation_agent",
    "explainability_agent"
  ],
  "required_agents": ["intake_agent", "recommendation_agent"],
  "optional_agents": ["fraud_agent", "severity_agent"],
  "completion_criteria": {
    "required_agents_executed": ["intake_agent", "recommendation_agent"],
    "required_outputs": ["decision", "supporting_evidence"],
    "min_agents_executed": 3
  }
}
```

**Advisory vs Prescriptive:**
- **Advisory mode** (current): Orchestrator uses workflow as guidance, can adapt based on state
- **Prescriptive mode** (not implemented): Strict sequence enforcement

Reference: `orchestrator_runner.py:268-275`

---

### How Governance Works

**Tool access check flow:**

```
Agent decides: "I need to use tool X"
                ↓
agent_react_loop.py:352 - Check governance
                ↓
governance_enforcer.py:150 - Call registry.is_tool_access_allowed()
                ↓
registry_manager.py:326 - Load governance_policies.json
                ↓
Check agent_tool_access rules:
  1. Is tool_id in denied_tools? → BLOCK
  2. Is tool_id in allowed_tools? → ALLOW
  3. Neither? → DENY (secure by default)
                ↓
If DENIED → Log event: "tool_denied"
         → Skip tool execution
         → Continue agent loop
```

**Agent invocation check flow:**

```
Orchestrator decides: "Invoke Agent Y"
                ↓
orchestrator_runner.py:418 - Check governance
                ↓
governance_enforcer.py:70 - Call registry.is_agent_invocation_allowed()
                ↓
registry_manager.py:311 - Load governance_policies.json
                ↓
Check agent_invocation_access rules:
  1. Is target_agent_id in denied_agents? → BLOCK
  2. Is target_agent_id in allowed_agents? → ALLOW
  3. Neither? → DENY
                ↓
Also check: AGENT_MAX_DUPLICATE_INVOCATIONS
         → Has agent been invoked too many times?
```

---

### Common Configuration Tasks

#### Add a New Tool

1. **Implement tool**: `tools/tools_gateway/app/tools/my_tool.py`
2. **Register endpoint**: `tools/tools_gateway/app/main.py`
3. **Add to registry**: `registries/tool_registry.json`
   ```json
   {
     "tool_id": "my_tool",
     "name": "My Custom Tool",
     "description": "WHEN to use: ... HOW to use: ...",
     "endpoint": "/invoke/my_tool",
     "input_schema": { /* params */ },
     "output_schema": { /* returns */ }
   }
   ```
4. **Grant access**: Update both files:
   - `registries/agent_registry.json` → agent's `allowed_tools`
   - `registries/governance_policies.json` → `agent_tool_access` rules

#### Add a New Agent

1. **Define in `agent_registry.json`**:
   ```json
   {
     "agent_id": "my_agent",
     "capabilities": ["analysis"],
     "allowed_tools": ["tool1", "tool2"],
     "model_profile_id": "default_gpt35",
     "max_iterations": 5,
     "output_schema": { /* JSON Schema */ }
   }
   ```

2. **Create output schema**: `backend/orchestrator/app/schemas/agent_outputs.py`
   ```python
   class MyAgentOutput(AgentOutputBase):
       field1: str
       field2: int
   ```

3. **Register schema**: `backend/orchestrator/app/schemas/validators.py`
   ```python
   AGENT_OUTPUT_SCHEMAS = {
       "my_agent": MyAgentOutput,
       ...
   }
   ```

4. **Grant orchestrator access**: `governance_policies.json`
   ```json
   {
     "agent_id": "orchestrator_agent",
     "allowed_agents": [..., "my_agent"]
   }
   ```

5. **Define tool access**: `governance_policies.json`
   ```json
   {
     "agent_id": "my_agent",
     "allowed_tools": ["tool1", "tool2"],
     "denied_tools": ["fraud_rules", ...]
   }
   ```

#### Change Agent's Tool Access

**Scenario:** Allow `severity_agent` to use `decision_rules` tool

1. **Update `agent_registry.json`**:
   ```json
   {
     "agent_id": "severity_agent",
     "allowed_tools": ["decision_rules"]  // Was: []
   }
   ```

2. **Update `governance_policies.json`**:
   ```json
   {
     "agent_id": "severity_agent",
     "allowed_tools": ["decision_rules"],
     "denied_tools": ["fraud_rules", "policy_snapshot", "similarity", "coverage_rules"]
   }
   ```

**Both must match** - registry defines capability, governance enforces it.

#### Adjust Agent Iteration Limits

**Option 1: Environment variable (global default)**
```bash
AGENT_DEFAULT_MAX_ITERATIONS=7
```

**Option 2: Registry (per-agent override)**
```json
// agent_registry.json
{
  "agent_id": "fraud_agent",
  "max_iterations": 10  // Overrides env var
}
```

**Option 3: Governance policy (registry-based)**
```json
// governance_policies.json
{
  "iteration_limits": {
    "agent_overrides": [
      {"agent_id": "fraud_agent", "max_iterations": 10}
    ]
  }
}
```

**Priority:** agent_registry.json > governance_policies.json > env var > hardcoded default

---

### Debugging Registry Issues

#### Tool Access Denied Error

**Error:** `Tool access denied: <tool_id> - Agent not permitted to use tool per governance policy`

**Troubleshooting checklist:**
1. ✓ Does tool exist in `tool_registry.json`?
2. ✓ Is tool in agent's `allowed_tools` in `agent_registry.json`?
3. ✓ Is tool in agent's `allowed_tools` in `governance_policies.json`?
4. ✓ Is tool NOT in agent's `denied_tools`?
5. ✓ Is the agent confusing a capability with a tool name?
   - Capabilities = skills the agent HAS
   - Tools = external APIs the agent CAN CALL

**Example:** `severity_classification` is a capability, not a tool. The `severity_agent` should NOT try to invoke it as a tool.

#### Agent Not Found

**Error:** `Agent 'xyz' not found in registry`

**Check:**
1. Is agent defined in `agent_registry.json`?
2. Is `agent_id` spelled correctly (case-sensitive)?
3. Did you reload the application after registry changes?

#### Schema Validation Failure

**Error:** `Output validation failed: field required`

**Check:**
1. Does `output_schema` in `agent_registry.json` match Pydantic model in `agent_outputs.py`?
2. Is agent registered in `validators.py` `AGENT_OUTPUT_SCHEMAS` dict?
3. Run: `python backend/orchestrator/test_schemas.py` to validate all schemas

---

## Layer 3: Hardcoded Defaults Reference

When environment variables and registry values are not specified, the system falls back to hardcoded defaults defined in the codebase. These defaults ensure the system can start with safe, sensible values.

### Configuration Model Defaults (`config.py`)

All hardcoded defaults are defined using Pydantic `Field(default=...)` syntax in [backend/orchestrator/app/config.py](backend/orchestrator/app/config.py).

#### Orchestrator Limits

```python
class OrchestratorLimits(BaseModel):
    max_iterations: int = Field(default=10)
    iteration_timeout_seconds: int = Field(default=30)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_iterations` | 10 | Maximum reasoning cycles for orchestrator meta-agent; prevents infinite coordination loops |
| `iteration_timeout_seconds` | 30 | Time limit per orchestrator reasoning cycle; ensures timely decisions |

**Reference**: [config.py:15-16](backend/orchestrator/app/config.py#L15-L16)

---

#### Workflow Limits

```python
class WorkflowLimits(BaseModel):
    max_duration_seconds: int = Field(default=300)
    max_agent_invocations: int = Field(default=20)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_duration_seconds` | 300 | Total workflow timeout (5 min); hard stop for entire claim processing |
| `max_agent_invocations` | 20 | Maximum total agent calls per workflow; prevents runaway orchestrator behavior |

**Reference**: [config.py:21-22](backend/orchestrator/app/config.py#L21-L22)

---

#### Agent Limits

```python
class AgentLimits(BaseModel):
    default_max_iterations: int = Field(default=5)
    default_iteration_timeout_seconds: int = Field(default=30)
    max_duplicate_invocations: int = Field(default=2)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `default_max_iterations` | 5 | Default ReAct loop iterations per worker agent; can be overridden per-agent in registry |
| `default_iteration_timeout_seconds` | 30 | Time limit per agent reasoning cycle; prevents stuck agents |
| `max_duplicate_invocations` | 2 | Maximum times orchestrator can re-invoke same agent; prevents repeat failures |

**Reference**: [config.py:27-29](backend/orchestrator/app/config.py#L27-L29)

---

#### LLM Limits

```python
class LLMLimits(BaseModel):
    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    max_tokens_per_request: int = Field(default=2000)
    max_tokens_per_session: int = Field(default=50000)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `timeout_seconds` | 30 | API call timeout for OpenAI/Anthropic requests; handles network issues |
| `max_retries` | 3 | Retry attempts for failed LLM calls; resilience against transient errors |
| `max_tokens_per_request` | 2000 | Context size limit per LLM call; prevents excessive prompt costs |
| `max_tokens_per_session` | 50000 | Total token budget across all LLM calls; prevents cost runaway in long workflows |

**Reference**: [config.py:34-37](backend/orchestrator/app/config.py#L34-L37)

---

#### Governance Limits

```python
class GovernanceLimits(BaseModel):
    max_tool_invocations_per_session: int = Field(default=50)
    max_llm_calls_per_session: int = Field(default=30)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_tool_invocations_per_session` | 50 | Total tool calls allowed across all agents; prevents excessive external API usage |
| `max_llm_calls_per_session` | 30 | Total LLM calls allowed per workflow; cost control and API quota management |

**Reference**: [config.py:42-43](backend/orchestrator/app/config.py#L42-L43)

---

#### Safety Thresholds

```python
class SafetyThresholds(BaseModel):
    consecutive_no_progress_limit: int = Field(default=2)
    malformed_response_limit: int = Field(default=3)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `consecutive_no_progress_limit` | 2 | Max iterations where agent makes no progress; triggers early termination |
| `malformed_response_limit` | 3 | Max output validation failures before agent errors; prevents endless invalid outputs |

**Reference**: [config.py:48-49](backend/orchestrator/app/config.py#L48-L49)

---

#### Schema Settings

```python
class SchemaSettings(BaseModel):
    default_version: str = Field(default="1.0")
    strict_validation: bool = Field(default=True)
    validation_failure_limit: int = Field(default=3)
    log_validation_sample: bool = Field(default=True)
    max_validation_sample_chars: int = Field(default=500)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `default_version` | "1.0" | Default schema version for agent outputs; supports versioned evolution |
| `strict_validation` | True | Enforce strict Pydantic validation; ensures type safety |
| `validation_failure_limit` | 3 | Max schema validation failures before agent terminates; same as malformed_response_limit |
| `log_validation_sample` | True | Log output sample on validation failure; aids debugging |
| `max_validation_sample_chars` | 500 | Characters to log in validation samples; balances detail vs log size |

**Reference**: [config.py:54-58](backend/orchestrator/app/config.py#L54-L58)

---

#### Service Configuration

```python
class Config(BaseModel):
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    tools_base_url: str = Field(default="http://tools_gateway:8010")
    storage_path: str = Field(default="/storage")
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `openai_api_key` | "" (empty) | OpenAI API key; empty means not configured |
| `anthropic_api_key` | "" (empty) | Anthropic API key; empty means not configured |
| `tools_base_url` | "http://tools_gateway:8010" | Tools gateway service URL; Docker Compose internal DNS |
| `storage_path` | "/storage" | Directory for JSONL session logs and evidence maps |

**Reference**: [config.py:65-72](backend/orchestrator/app/config.py#L65-L72)

---

### Service-Level Hardcoded Defaults

Beyond the config module, several services have hardcoded defaults for operational parameters.

#### LLM Client Defaults (`llm_client.py`)

**Retry Policy Defaults:**

```python
max_retries = retry_policy.get("max_retries", 3)
backoff_multiplier = retry_policy.get("backoff_multiplier", 2)
initial_delay = retry_policy.get("initial_delay_ms", 1000) / 1000.0
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_retries` | 3 | Retry attempts if model profile doesn't specify; handles API failures |
| `backoff_multiplier` | 2 | Exponential backoff factor (delay × 2^attempt); prevents API hammering |
| `initial_delay_ms` | 1000 | Starting retry delay (1 sec); gives API time to recover |

**Reference**: [llm_client.py:140-142](backend/orchestrator/app/services/llm_client.py#L140-L142), [247-249](backend/orchestrator/app/services/llm_client.py#L247-L249)

**LLM API Parameters:**

```python
# OpenAI
"temperature": self.model_profile.parameters.get("temperature", 0.3)
"max_tokens": self.model_profile.parameters.get("max_tokens", 2000)
"top_p": self.model_profile.parameters.get("top_p", 1.0)

# Anthropic (Claude)
"temperature": self.model_profile.parameters.get("temperature", 0.3)
"max_tokens": self.model_profile.parameters.get("max_tokens", 4000)
"top_p": self.model_profile.parameters.get("top_p", 1.0)
```

| Parameter | OpenAI Default | Anthropic Default | Purpose |
|-----------|----------------|-------------------|---------|
| `temperature` | 0.3 | 0.3 | Low randomness for consistent, focused reasoning |
| `max_tokens` | 2000 | 4000 | Response length limit; Claude supports longer outputs |
| `top_p` | 1.0 | 1.0 | Nucleus sampling; 1.0 = consider all tokens |

**Reference**: [llm_client.py:154-156](backend/orchestrator/app/services/llm_client.py#L154-L156) (OpenAI), [275-277](backend/orchestrator/app/services/llm_client.py#L275-L277) (Anthropic)

---

#### Context Compiler Defaults (`context_compiler.py`)

**Token Budget Defaults:**

```python
# Agent context
max_tokens = requirements.get("max_context_tokens", 8000)

# Orchestrator context
max_tokens = orchestrator.context_requirements.get("max_context_tokens", 10000)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Agent `max_context_tokens` | 8000 | Default token budget for worker agent prompts |
| Orchestrator `max_context_tokens` | 10000 | Default token budget for orchestrator prompts; higher for coordination |

**Reference**: [context_compiler.py:84](backend/orchestrator/app/services/context_compiler.py#L84), [145](backend/orchestrator/app/services/context_compiler.py#L145)

**Budget Allocation Percentages:**

```python
# Agent context allocation
budget_original = int(max_tokens * 0.3)   # 30% - original input
budget_prior = int(max_tokens * 0.5)      # 50% - prior agent outputs
budget_obs = int(max_tokens * 0.2)        # 20% - observations (tool results)

# Orchestrator context allocation
budget_original = int(max_tokens * 0.2)   # 20% - original input
budget_agents = int(max_tokens * 0.6)     # 60% - available agents info
budget_obs = int(max_tokens * 0.2)        # 20% - observations (agent results)
```

| Context Component | Agent Allocation | Orchestrator Allocation | Purpose |
|-------------------|------------------|------------------------|---------|
| Original Input | 30% | 20% | Claim data; less critical for orchestrator |
| Prior Outputs / Agent Info | 50% | 60% | Most important for decision-making |
| Observations | 20% | 20% | Tool results / agent results |

**Purpose**: Smart token budget allocation ensures most relevant context fits within limits. Prioritizes outputs over input.

**Reference**: [context_compiler.py:93-95](backend/orchestrator/app/services/context_compiler.py#L93-L95) (agent), [153-155](backend/orchestrator/app/services/context_compiler.py#L153-L155) (orchestrator)

---

#### Tools Gateway Client Defaults (`tools_gateway_client.py`)

```python
initial_delay = 1.0  # 1 second
backoff_multiplier = 2.0
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `initial_delay` | 1.0 sec | Starting retry delay for tool API calls |
| `backoff_multiplier` | 2.0 | Exponential backoff for tool retries |

**Reference**: [tools_gateway_client.py:106-107](backend/orchestrator/app/services/tools_gateway_client.py#L106-L107)

---

#### Governance Enforcer Defaults (`governance_enforcer.py`)

```python
max_duplicates = 2  # Configurable from env or governance
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_duplicates` | 2 | Hardcoded fallback for duplicate agent invocations (should use config) |

**Note**: This is currently hardcoded but should reference `config.agent.max_duplicate_invocations`. See [governance_enforcer.py:106](backend/orchestrator/app/services/governance_enforcer.py#L106)

**Governance Registry Fallbacks:**

```python
max_invocations = governance.policies.get("execution_constraints", {}).get(
    "max_tool_invocations_per_session", 50
)

max_calls = governance.policies.get("execution_constraints", {}).get(
    "max_llm_calls_per_session", 30
)
```

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_tool_invocations_per_session` | 50 | Fallback if governance registry doesn't specify |
| `max_llm_calls_per_session` | 30 | Fallback if governance registry doesn't specify |

**Reference**: [governance_enforcer.py:170](backend/orchestrator/app/services/governance_enforcer.py#L170), [243](backend/orchestrator/app/services/governance_enforcer.py#L243)

---

#### API Defaults

**Health Check API Version:**
```python
version: str = Field(default="1.0.0", description="API version")
```
- **Reference**: [api/models.py:125](backend/orchestrator/app/api/models.py#L125)

**Agent Output Schema Version:**
```python
version: str = Field(default="1.0", description="Schema version")
```
- **Reference**: [schemas/agent_outputs.py:22](backend/orchestrator/app/schemas/agent_outputs.py#L22)

**Session Listing Pagination:**
```python
limit: int = Query(default=20, ge=1, le=100)  # 20 sessions per page
offset: int = Query(default=0, ge=0)
```
- **Reference**: [api/sessions.py:27-28](backend/orchestrator/app/api/sessions.py#L27-L28)

---

### Complete Hardcoded Defaults Reference Table

| Category | Parameter | Default | Purpose | Location |
|----------|-----------|---------|---------|----------|
| **Orchestrator** | max_iterations | 10 | Max orchestrator reasoning cycles | config.py:15 |
| | iteration_timeout_seconds | 30 | Time per orchestrator cycle | config.py:16 |
| **Workflow** | max_duration_seconds | 300 | Total workflow timeout (5 min) | config.py:21 |
| | max_agent_invocations | 20 | Max total agent calls | config.py:22 |
| **Agent** | default_max_iterations | 5 | Default agent ReAct iterations | config.py:27 |
| | default_iteration_timeout | 30 | Time per agent iteration | config.py:28 |
| | max_duplicate_invocations | 2 | Max re-invocations of same agent | config.py:29 |
| **LLM** | timeout_seconds | 30 | API call timeout | config.py:34 |
| | max_retries | 3 | API retry attempts | config.py:35 |
| | max_tokens_per_request | 2000 | Context size per call | config.py:36 |
| | max_tokens_per_session | 50000 | Total token budget | config.py:37 |
| **Governance** | max_tool_invocations | 50 | Total tool calls per session | config.py:42 |
| | max_llm_calls | 30 | Total LLM calls per session | config.py:43 |
| **Safety** | consecutive_no_progress | 2 | Max no-progress iterations | config.py:48 |
| | malformed_response_limit | 3 | Max validation failures | config.py:49 |
| **Schema** | default_version | "1.0" | Schema version | config.py:54 |
| | strict_validation | True | Enforce strict validation | config.py:55 |
| | validation_failure_limit | 3 | Max schema failures | config.py:56 |
| | log_validation_sample | True | Log failed outputs | config.py:57 |
| | max_validation_sample_chars | 500 | Chars to log | config.py:58 |
| **Service** | tools_base_url | "http://tools_gateway:8010" | Tools gateway URL | config.py:69 |
| | storage_path | "/storage" | JSONL storage directory | config.py:72 |
| **LLM Retry** | backoff_multiplier | 2 | Exponential backoff factor | llm_client.py:141 |
| | initial_delay_ms | 1000 | Starting retry delay (1s) | llm_client.py:142 |
| **LLM Params (OpenAI)** | temperature | 0.3 | Low randomness | llm_client.py:154 |
| | max_tokens | 2000 | Response length | llm_client.py:155 |
| | top_p | 1.0 | Nucleus sampling | llm_client.py:156 |
| **LLM Params (Anthropic)** | temperature | 0.3 | Low randomness | llm_client.py:275 |
| | max_tokens | 4000 | Response length (higher) | llm_client.py:276 |
| | top_p | 1.0 | Nucleus sampling | llm_client.py:277 |
| **Context (Agent)** | max_context_tokens | 8000 | Agent prompt budget | context_compiler.py:84 |
| | original_input % | 30% | Input allocation | context_compiler.py:93 |
| | prior_outputs % | 50% | Outputs allocation | context_compiler.py:94 |
| | observations % | 20% | Observations allocation | context_compiler.py:95 |
| **Context (Orchestrator)** | max_context_tokens | 10000 | Orchestrator prompt budget | context_compiler.py:145 |
| | original_input % | 20% | Input allocation | context_compiler.py:153 |
| | agents_info % | 60% | Agent info allocation | context_compiler.py:154 |
| | observations % | 20% | Observations allocation | context_compiler.py:155 |
| **Tools Client** | initial_delay | 1.0 sec | Tool retry delay | tools_gateway_client.py:106 |
| | backoff_multiplier | 2.0 | Tool retry backoff | tools_gateway_client.py:107 |
| **API** | api_version | "1.0.0" | Health check version | api/models.py:125 |
| | schema_version | "1.0" | Agent output version | agent_outputs.py:22 |
| | pagination_limit | 20 | Sessions per page | sessions.py:27 |
| | pagination_offset | 0 | Starting offset | sessions.py:28 |

---

### Fallback Chain Example

**For `ORCHESTRATOR_MAX_ITERATIONS` (value = 10):**

```
1. Environment Variable Check (.env file)
   ├─ ORCHESTRATOR_MAX_ITERATIONS=15
   └─ FOUND? → Use 15 ✓

2. If not in .env, check os.getenv() default
   ├─ os.getenv("ORCHESTRATOR_MAX_ITERATIONS", "10")
   └─ Returns string "10" → Convert to int(10) ✓

3. If os.getenv() fails, use Field(default=)
   ├─ max_iterations: int = Field(default=10)
   └─ Pydantic model default ✓
```

**Result**: System always has a value, following priority: `.env` > `os.getenv("VAR", "default")` > `Field(default=...)`

---

### Design Principles for Defaults

All hardcoded defaults follow these principles:

1. **Safety First**: Low iteration limits prevent runaway loops
2. **Cost Control**: Moderate token budgets prevent excessive API costs
3. **Resilience**: Retry policies with backoff handle transient failures
4. **Usability**: Not too restrictive; allows reasonable workflow complexity
5. **Observability**: Logging enabled by default for debugging
6. **Fail-Safe**: Empty API keys don't crash; system checks before use
7. **Docker-Friendly**: Service URLs use Docker Compose internal DNS

---

## Related Documentation

- **Architecture Overview**: See `CLAUDE.md` for meta-agent pattern details
- **Registry Configuration**: See `registries/agent_registry.json` for per-agent overrides
- **API Reference**: See `http://localhost:8016/docs` when running
- **Event Streaming**: See `backend/orchestrator/app/services/sse_broadcaster.py`
- **Schema Validation**: See `backend/orchestrator/app/schemas/validators.py`

---

## Summary Reference Table

| Parameter | Default | Scope | Primary Enforcement Location |
|-----------|---------|-------|------------------------------|
| ORCHESTRATOR_MAX_ITERATIONS | 10 | Orchestrator | `orchestrator_runner.py:146` |
| ORCHESTRATOR_ITERATION_TIMEOUT_SECONDS | 30 | Orchestrator | Config only |
| WORKFLOW_MAX_DURATION_SECONDS | 300 | Workflow | `orchestrator_runner.py:150` |
| WORKFLOW_MAX_AGENT_INVOCATIONS | 20 | Workflow | `orchestrator_runner.py:432` |
| AGENT_DEFAULT_MAX_ITERATIONS | 5 | Agent | `agent_react_loop.py:144` |
| AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS | 30 | Agent | Config only |
| AGENT_MAX_DUPLICATE_INVOCATIONS | 2 | Governance | `governance_enforcer.py:105` |
| LLM_TIMEOUT_SECONDS | 30 | LLM | `llm_client.py` |
| LLM_MAX_RETRIES | 3 | LLM | `llm_client.py:146` |
| LLM_MAX_TOKENS_PER_REQUEST | 2000 | LLM | `context_compiler.py` |
| LLM_MAX_TOKENS_PER_SESSION | 50000 | Session | `llm_client.py:54` |
| MAX_TOOL_INVOCATIONS_PER_SESSION | 50 | Session | `governance_enforcer.py:64` |
| MAX_LLM_CALLS_PER_SESSION | 30 | Session | `governance_enforcer.py:65` |
| CONSECUTIVE_NO_PROGRESS_LIMIT | 2 | Safety | Agent loop |
| MALFORMED_RESPONSE_LIMIT | 3 | Safety | `agent_react_loop.py:502` |
