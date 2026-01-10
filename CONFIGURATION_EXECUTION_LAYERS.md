# Configuration and Execution Layers

This document explains how AgentMesh manages and executes configurations across different architectural layers.

---

## Overview

AgentMesh uses a **registry-driven architecture** where all behavior is defined in configuration files (JSON registries) and executed by specialized service layers. This separation enables zero-downtime configuration changes and complete flexibility without code modifications.

---

## Configuration Management Layer

### Registry Manager
**Location:** [`backend/orchestrator/app/services/registry_manager.py`](backend/orchestrator/app/services/registry_manager.py)

**Responsibilities:**
- Loads all configuration files at startup
- Provides centralized access to registries
- Supports hot-reloading (future enhancement)
- Validates registry structure

### Configuration Files

All configurations are stored in the [`registries/`](registries/) directory:

| Registry File | Purpose | Used By |
|--------------|---------|---------|
| [`agent_registry.json`](registries/agent_registry.json) | Agent definitions, capabilities, allowed tools, output schemas | OrchestratorRunner, AgentReActLoopController |
| [`tool_registry.json`](registries/tool_registry.json) | Tool catalog with descriptions, schemas | AgentReActLoopController, ToolsGatewayClient |
| [`model_profiles.json`](registries/model_profiles.json) | LLM model configurations (OpenAI/Anthropic) | LLMClient |
| [`governance_policies.json`](registries/governance_policies.json) | Access control, execution limits, handoff rules | GovernanceEnforcer |
| [`workflows/*.json`](registries/workflows/) | Workflow definitions (advisory mode) | OrchestratorRunner |
| [`context_strategies.json`](registries/context_strategies.json) | Token budgets, compaction settings, memory config | ContextCompiler, ContextProcessorPipeline |
| [`context_processor_pipeline.json`](registries/context_processor_pipeline.json) | Processor order and configuration | ContextProcessorPipeline |
| [`system_config.json`](registries/system_config.json) | System-wide feature toggles | All services |

---

## Execution Layers

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           Configuration Layer                        │
│  ┌───────────────────────────────────────────┐      │
│  │   Registry Manager                        │      │
│  │   - Loads 8 JSON config files             │      │
│  │   - Provides centralized access           │      │
│  └───────────────┬───────────────────────────┘      │
└──────────────────┼──────────────────────────────────┘
                   │ Configurations loaded into
                   ▼
┌─────────────────────────────────────────────────────┐
│           Execution Layers                           │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  1. Orchestrator Runner (Primary Engine)  │    │
│  │     - Executes meta-agent ReAct loop       │    │
│  │     - Coordinates agent invocations        │    │
│  │     - Manages workflow state               │    │
│  └────────────┬───────────────────────────────┘    │
│               │                                      │
│  ┌────────────▼───────────────────────────────┐    │
│  │  2. Agent ReAct Loop Controller            │    │
│  │     - Executes worker agent loops          │    │
│  │     - Manages tool invocations             │    │
│  │     - Validates outputs                    │    │
│  └────────────┬───────────────────────────────┘    │
│               │                                      │
│  ┌────────────▼───────────────────────────────┐    │
│  │  3. Governance Enforcer                    │    │
│  │     - Enforces access policies             │    │
│  │     - Validates permissions                │    │
│  │     - Enforces execution limits            │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  4. Context Processor Pipeline             │    │
│  │     - Executes 7 processors in order       │    │
│  │     - Applies context strategies           │    │
│  │     - Enforces token budgets               │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  5. LLM Client                             │    │
│  │     - Executes model configurations        │    │
│  │     - Manages API calls                    │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  6. Tools Gateway Client                   │    │
│  │     - Invokes tools from registry          │    │
│  │     - Validates tool schemas               │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Detailed Execution Layer Documentation

### 1. Orchestrator Runner (Primary Execution Engine)

**File:** [`backend/orchestrator/app/services/orchestrator_runner.py`](backend/orchestrator/app/services/orchestrator_runner.py)

**Role:** Main execution engine that orchestrates the entire workflow

**Executes:**
- Meta-agent ReAct loop (Reason → Invoke Agents → Observe)
- Workflow definitions from `workflows/*.json`
- Agent discovery based on capabilities from `agent_registry.json`
- Multi-agent coordination and state management

**Configuration Dependencies:**
- `agent_registry.json` - Discovers available agents
- `workflows/*.json` - Advisory workflow guidance
- `system_config.json` - Feature toggles
- Environment variables - Execution limits

**Key Methods:**
```python
async def run_workflow(session_id: str, input_data: Dict)
    # 1. Load orchestrator agent config from registry
    # 2. Start meta-agent ReAct loop
    # 3. Invoke agents based on registry capabilities
    # 4. Coordinate multi-agent execution
    # 5. Compile final evidence map
```

---

### 2. Agent ReAct Loop Controller

**File:** [`backend/orchestrator/app/services/agent_react_loop.py`](backend/orchestrator/app/services/agent_react_loop.py)

**Role:** Executes individual worker agent ReAct loops

**Executes:**
- Worker agent ReAct loop (Reason → Use Tools → Observe)
- Agent-specific configurations (iterations, timeouts)
- Tool invocations based on allowed_tools
- Output schema validation

**Configuration Dependencies:**
- `agent_registry.json` - Agent configs (max_iterations, allowed_tools, output_schema)
- `tool_registry.json` - Tool definitions for LLM prompting
- `model_profiles.json` - Model selection per agent

**Key Methods:**
```python
async def run_agent_loop(agent_id: str, context: Dict)
    # 1. Load agent config from registry
    # 2. Check governance policies
    # 3. Compile context for agent
    # 4. Execute ReAct loop with tool invocations
    # 5. Validate output against schema
```

---

### 3. Governance Enforcer

**File:** [`backend/orchestrator/app/services/governance_enforcer.py`](backend/orchestrator/app/services/governance_enforcer.py)

**Role:** Enforces security and access policies

**Executes:**
- Agent access control policies
- Tool permission validation
- Execution limit enforcement
- Multi-agent handoff rules

**Configuration Dependencies:**
- `governance_policies.json` - All policy definitions
  - `agent_policies` - Agent access control
  - `tool_policies` - Tool permissions
  - `execution_limits` - Session/agent limits
  - `handoff_policies` - Context scoping rules

**Key Methods:**
```python
def check_agent_access(agent_id: str, invoker: str) -> bool
def check_tool_access(agent_id: str, tool_id: str) -> bool
def enforce_execution_limits(session_id: str) -> None
def get_handoff_mode(from_agent: str, to_agent: str) -> str
```

---

### 4. Context Processor Pipeline

**File:** [`backend/orchestrator/app/services/context_processor_pipeline.py`](backend/orchestrator/app/services/context_processor_pipeline.py)

**Role:** Executes ordered context compilation pipeline

**Executes:**
- 7 context processors in configured order
- Token budget enforcement
- Session compaction triggers
- Memory retrieval
- Artifact resolution

**Configuration Dependencies:**
- `context_processor_pipeline.json` - Processor order, enabled/disabled state
- `context_strategies.json` - Token budgets, compaction thresholds, memory settings

**Processor Execution Order:**
```python
1. ContentSelector      # Filter noise
2. CompactionChecker    # Trigger summarization
3. MemoryRetriever      # Load cross-session knowledge
4. ArtifactResolver     # Resolve large data handles
5. Transformer          # Convert to LLM format
6. TokenBudgetEnforcer  # Enforce token limits
7. Injector             # Final formatting
```

**Key Methods:**
```python
async def execute(context: List[Dict], agent_id: str, session_id: str)
    # 1. Load processor pipeline config
    # 2. Execute each enabled processor in order
    # 3. Track execution metrics
    # 4. Log to context lineage
```

---

### 5. LLM Client

**File:** [`backend/orchestrator/app/services/llm_client.py`](backend/orchestrator/app/services/llm_client.py)

**Role:** Manages LLM API calls with model-specific configurations

**Executes:**
- Model profile configurations
- Multi-provider support (OpenAI/Anthropic)
- Retry logic and timeout handling
- Token counting and limits

**Configuration Dependencies:**
- `model_profiles.json` - Model configurations
  - `provider` (openai/anthropic)
  - `model_name`
  - `temperature`, `max_tokens`
  - `supports_json_mode`, `supports_streaming`

**Key Methods:**
```python
async def call_llm(messages: List[Dict], model_profile_id: str)
    # 1. Load model profile from registry
    # 2. Select provider (OpenAI/Anthropic)
    # 3. Apply model-specific parameters
    # 4. Make API call with retry logic
```

---

### 6. Tools Gateway Client

**File:** [`backend/orchestrator/app/services/tools_gateway_client.py`](backend/orchestrator/app/services/tools_gateway_client.py)

**Role:** Invokes tools from the tools gateway

**Executes:**
- Tool invocations based on registry definitions
- Input/output schema validation
- HTTP communication with tools gateway

**Configuration Dependencies:**
- `tool_registry.json` - Tool endpoints, schemas, descriptions

**Key Methods:**
```python
async def invoke_tool(tool_id: str, parameters: Dict)
    # 1. Load tool config from registry
    # 2. Validate input against schema
    # 3. Call tools gateway endpoint
    # 4. Validate output against schema
```

---

## Complete Execution Flow

Here's how a claim submission flows through all execution layers:

```
┌──────────────────────────────────────────────────────────┐
│ 1. USER REQUEST                                          │
│    POST /runs with claim data                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. API LAYER (FastAPI)                                   │
│    - Create session                                      │
│    - Start background execution                          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. ORCHESTRATOR RUNNER                                   │
│    ├─ Load orchestrator config from agent_registry.json │
│    ├─ Check system_config.json feature toggles          │
│    └─ Start meta-agent ReAct loop                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. REGISTRY MANAGER                                      │
│    - Provide agent definitions                           │
│    - Provide workflow guidance                           │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 5. GOVERNANCE ENFORCER                                   │
│    - Check agent access policies                         │
│    - Validate execution limits                           │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 6. CONTEXT PROCESSOR PIPELINE                            │
│    ├─ Load context_processor_pipeline.json              │
│    ├─ Load context_strategies.json                      │
│    └─ Execute 7 processors in order                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 7. LLM CLIENT                                            │
│    ├─ Load model profile from model_profiles.json       │
│    └─ Call OpenAI/Anthropic API                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 8. ORCHESTRATOR DECISION                                 │
│    "Invoke intake_agent and coverage_agent"              │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 9. AGENT REACT LOOP CONTROLLER (for each agent)         │
│    ├─ Load agent config from agent_registry.json        │
│    ├─ Check allowed_tools from governance               │
│    ├─ Compile agent-specific context                    │
│    └─ Execute agent ReAct loop                          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 10. TOOLS GATEWAY CLIENT                                 │
│     ├─ Load tool definitions from tool_registry.json    │
│     └─ Invoke tools (fraud_rules, policy_snapshot, etc.)│
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 11. AGENT OUTPUTS                                        │
│     - Validate against output_schema                     │
│     - Return to orchestrator                             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 12. ORCHESTRATOR CONTINUES                               │
│     - Apply multi-agent handoff rules                    │
│     - Invoke next agents based on outputs                │
│     - Compile evidence map                               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 13. FINAL RESULT                                         │
│     - Store evidence as artifact                         │
│     - Stream via SSE to frontend                         │
│     - Log all events to JSONL                            │
└──────────────────────────────────────────────────────────┘
```

---

## Configuration Lifecycle

### Startup

```python
# 1. Application starts
app = FastAPI()

# 2. Registry Manager initializes
registry_manager = RegistryManager()
registry_manager.load_all_registries()  # Loads 8 JSON files

# 3. Services initialize with registry access
orchestrator = OrchestratorRunner(registry_manager)
governance = GovernanceEnforcer(registry_manager)
context_pipeline = ContextProcessorPipeline(registry_manager)
llm_client = LLMClient(registry_manager)

# 4. Ready to execute workflows
```

### Runtime Execution

```python
# For each workflow execution:
async def execute_workflow(session_id, input_data):
    # 1. Load fresh configs from registry manager
    orchestrator_config = registry_manager.get_agent("orchestrator_agent")

    # 2. Execute using loaded configs
    result = await orchestrator.run_workflow(
        session_id=session_id,
        input_data=input_data,
        config=orchestrator_config
    )

    # 3. All execution layers read from registry as needed
    return result
```

### Hot-Reload (Future Enhancement)

```python
# Watch for registry file changes
async def watch_registries():
    for change in watch("/registries/**/*.json"):
        registry_manager.reload(change.file)
        # Services automatically use new configs on next execution
```

---

## Key Design Principles

### 1. **Separation of Concerns**
- **Configuration Layer:** Defines WHAT to do (registries)
- **Execution Layer:** Defines HOW to do it (services)

### 2. **Zero Hardcoding**
- All behavior defined in registries
- Code is configuration-agnostic
- Add new agents/tools without code changes

### 3. **Centralized Management**
- Registry Manager is single source of truth
- All services read from same registries
- Consistent configuration across system

### 4. **Dynamic Discovery**
- Orchestrator discovers agents at runtime
- Agents discover tools at runtime
- No compile-time dependencies

### 5. **Policy-Driven Security**
- Governance policies in configuration
- Enforced at execution time
- Auditable and modifiable

---

## API Endpoints for Configuration

The frontend can access and modify configurations via API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/registries/agents` | GET | List all agents |
| `/registries/agents/{agent_id}` | GET | Get agent config |
| `/registries/tools` | GET | List all tools |
| `/registries/workflows` | GET | List workflows |
| `/registries/governance` | GET | Get governance policies |
| `/registries/context-strategies` | GET | Get context config |
| `/registries/system-config` | GET | Get feature toggles |

**Frontend Interface:**
- Configuration UI: [http://localhost:3016/config](http://localhost:3016/config)
- 8 tabs for different registry types
- Live editing with validation

---

## Summary

| Component | Type | Responsibility |
|-----------|------|----------------|
| **Registry Manager** | Configuration Management | Loads and provides access to all registries |
| **Orchestrator Runner** | Primary Execution Engine | Executes meta-agent ReAct loop, coordinates workflow |
| **Agent ReAct Loop Controller** | Agent Execution | Executes worker agent loops, manages tools |
| **Governance Enforcer** | Security Execution | Enforces policies and access control |
| **Context Processor Pipeline** | Context Execution | Executes context compilation pipeline |
| **LLM Client** | Model Execution | Executes LLM API calls with model configs |
| **Tools Gateway Client** | Tool Execution | Invokes tools from registry |

**Key Insight:** The **Orchestrator Runner** is the main execution engine that coordinates all other execution layers, reading configurations from the **Registry Manager** and delegating to specialized services.

---

## Related Documentation

- [ARCHITECTURE_SIMPLIFIED.md](ARCHITECTURE_SIMPLIFIED.md) - High-level architecture overview
- [CLAUDE.md](CLAUDE.md) - Developer guide with configuration examples
- [DECISIONS.md](DECISIONS.md) - Architectural decisions
- [docs/CONFIGURATION_REFERENCE.md](docs/CONFIGURATION_REFERENCE.md) - Registry file documentation
- [docs/DEVELOPER_GUIDE_CONTEXT_PROCESSORS.md](docs/DEVELOPER_GUIDE_CONTEXT_PROCESSORS.md) - Context processor development
