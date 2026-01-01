# Architectural Decisions

This document explains the key architectural decisions made in AgentMesh, the rationale behind them, alternatives considered, and trade-offs. Understanding these decisions is crucial for extending the system or adapting patterns to other domains.

---

## Table of Contents

1. [Orchestrator as ReAct Agent](#1-orchestrator-as-react-agent)
2. [Centralized LLM Control](#2-centralized-llm-control)
3. [Registry-Driven Architecture](#3-registry-driven-architecture)
4. [Flat-File Storage (JSONL/JSON)](#4-flat-file-storage-jsonljson)
5. [Mock Tools Instead of Real Integrations](#5-mock-tools-instead-of-real-integrations)
6. [Advisory Workflow Mode](#6-advisory-workflow-mode)
7. [Server-Sent Events for Live Streaming](#7-server-sent-events-for-live-streaming)
8. [Multi-Provider LLM Support](#8-multi-provider-llm-support)
9. [Bounded Execution (Iteration Limits & Timeouts)](#9-bounded-execution-iteration-limits--timeouts)
10. [Context Compilation & Token Management](#10-context-compilation--token-management)
11. [Structured Output Validation (Pydantic)](#11-structured-output-validation-pydantic)
12. [Multi-Tier Completion](#12-multi-tier-completion)
13. [Governance via Policies Not Code](#13-governance-via-policies-not-code)
14. [Monolithic Orchestrator vs Distributed Agents](#14-monolithic-orchestrator-vs-distributed-agents)
15. [Simplifications for Prototype](#15-simplifications-for-prototype)

---

## 1. Orchestrator as ReAct Agent

### Decision

The **orchestrator itself is a ReAct agent** that discovers and invokes other agents dynamically. It executes its own reasoning-action loop, where actions are "invoke agent X" rather than "use tool Y".

### Alternatives Considered

**Option A: Hardcoded Workflow Execution**
- Orchestrator executes a fixed sequence: intake → coverage → fraud → ...
- Simple DAG-based execution

**Option B: Simple Workflow Manager**
- Orchestrator reads workflow definition and executes in order
- No reasoning, just sequential execution

**Option C: Event-Driven Orchestration**
- Agents publish events, orchestrator routes based on event types
- More decoupled but complex

### Why ReAct Pattern?

**Advantages**:
1. **Adaptability**: Orchestrator can decide which agents to invoke based on current state
2. **Consistency**: Same ReAct pattern for both meta-agent and workers
3. **Dynamic Discovery**: Agents discovered from registry, not hardcoded
4. **Explainability**: Orchestrator's reasoning is logged and auditable
5. **Flexibility**: Can skip optional agents, retry failed agents, or invoke in different orders

**Example**: If fraud score is low, orchestrator might skip expensive detailed investigation agents.

### Trade-offs

**Pros**:
- Handles complex scenarios better than fixed workflows
- New agents can be added without changing orchestrator code
- Reasoning provides transparency

**Cons**:
- More complex than simple workflow manager
- Requires orchestrator to make LLM calls (cost)
- Additional iteration tracking needed
- Potential for orchestrator to make suboptimal decisions

### Production Evolution

In production, consider:
- **Hybrid approach**: Use orchestrator ReAct for complex cases, hardcoded workflows for simple cases
- **Human-in-the-loop**: Orchestrator proposes plan, human approves before execution
- **Fallback to deterministic**: If orchestrator fails to decide, fall back to default sequence

---

## 2. Centralized LLM Control

### Decision

The **orchestrator service manages all LLM calls** for both itself and worker agents. Worker agents don't have direct LLM access; orchestrator calls LLM on their behalf.

### Alternatives Considered

**Option A: Distributed Agent Services**
- Each agent is a separate microservice with its own LLM client
- Agents make their own LLM calls

**Option B: Shared LLM Gateway**
- Centralized LLM gateway service
- All services call gateway, which routes to providers

**Option C: Agent-Level LLM Clients**
- Each agent has embedded LLM client
- Full autonomy

### Why Centralized?

**Advantages**:
1. **Unified Governance**: Single point for token budgets, rate limiting, cost tracking
2. **Simplified Deployment**: Fewer services to manage
3. **Cost Control**: Easier to enforce session-level token limits
4. **Consistent Prompting**: All prompts managed in one place
5. **Observability**: All LLM calls logged centrally

**Example**: Session-level token budget (50,000 tokens) enforced in one place across all agents.

### Trade-offs

**Pros**:
- Simplified architecture
- Easier governance
- Lower operational complexity
- Unified monitoring

**Cons**:
- Orchestrator becomes single point of failure
- Can't scale agents independently
- All agents share orchestrator's resource limits
- Tight coupling between orchestrator and agents

### Production Evolution

For production scale:
1. **LLM Gateway Pattern**: Extract LLM client into separate service
2. **Agent Services**: Move agents to separate services, all calling LLM gateway
3. **API Gateway**: Add API gateway for rate limiting, auth, routing
4. **Horizontal Scaling**: Scale LLM gateway and agent services independently

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │
┌────▼─────────┐     ┌─────────────┐
│ API Gateway  │────▶│ LLM Gateway │
└────┬─────────┘     └─────────────┘
     │                       ▲
     ├───────────┬───────────┼────────┐
     │           │           │        │
┌────▼────┐ ┌───▼────┐ ┌───▼────┐ ┌─▼──────┐
│Orchestr │ │ Agent1 │ │ Agent2 │ │ AgentN │
│Service  │ │Service │ │Service │ │Service │
└─────────┘ └────────┘ └────────┘ └────────┘
```

---

## 3. Registry-Driven Architecture

### Decision

**All agents, tools, workflows, and governance policies are defined in JSON registries**, not in code. The system discovers and validates entities at runtime from these files.

### Alternatives Considered

**Option A: Code-Based Configuration**
- Agents defined as Python classes
- Tools registered via decorators
- Workflows defined in code

**Option B: Database-Driven**
- Agents, tools, workflows stored in database
- Admin UI for configuration

**Option C: Hybrid**
- Core agents in code
- User-defined agents in registry

### Why JSON Registries?

**Advantages**:
1. **Zero-Code Extensibility**: Add agents without changing code
2. **Version Control**: Registries tracked in git
3. **Hot-Reload**: Update registry without restarting (if implemented)
4. **Validation**: JSON Schema validation on load
5. **Transparency**: Configuration is explicit and auditable
6. **Portability**: Easy to export/import configurations

**Example**: Adding a new agent requires only:
1. Add JSON entry to `agent_registry.json`
2. Create output schema class
3. Done - orchestrator discovers it automatically

### Registry Files

1. **agent_registry.json**: Agent definitions, capabilities, constraints
2. **tool_registry.json**: Tool catalog with schemas
3. **model_profiles.json**: LLM model configurations
4. **governance_policies.json**: Access control policies
5. **workflows/*.json**: Workflow definitions

### Trade-offs

**Pros**:
- Highly flexible and extensible
- Configuration as code (gitops)
- Easy to test different configurations
- No deployment needed for config changes

**Cons**:
- JSON can become large and complex
- No IDE autocomplete for registry editing
- Manual consistency checks needed
- Schema validation only at runtime

### Production Evolution

1. **Registry UI**: Build web UI for editing registries
2. **Registry Versioning**: Version registries separately from code
3. **Registry Validation**: CI/CD pipeline validates all registries
4. **Registry API**: RESTful API for registry management
5. **Migration to Database**: Store registries in DB for production, export to JSON for version control

---

## 4. Flat-File Storage (JSONL/JSON)

### Decision

**Session events stored as JSONL files**, one file per session. **Artifacts (evidence maps) stored as JSON files**. No database.

### Alternatives Considered

**Option A: PostgreSQL**
- Sessions table with JSON columns
- Events as rows with foreign key to session
- Full text search, indexing

**Option B: MongoDB**
- Sessions as documents
- Events as nested arrays
- Flexible schema

**Option C: Time-Series DB**
- InfluxDB or TimescaleDB
- Events as time-series data
- Optimized for append and query

**Option D: Event Store**
- EventStoreDB or Apache Kafka
- Full event sourcing
- Event replay capabilities

### Why Flat Files?

**Advantages**:
1. **Simplicity**: No database setup or management
2. **Debuggability**: Easy to inspect with cat/less/jq
3. **Portability**: Copy storage/ directory to move data
4. **Append-Only**: JSONL naturally append-only
5. **Human-Readable**: Can read and understand events directly

**Example**: Inspect session with:
```bash
cat storage/sessions/session_123.jsonl | jq .
```

### Format Choice: JSONL

Each line is a complete JSON object (event):
```jsonl
{"event_type": "workflow_started", "timestamp": "...", "data": {...}}
{"event_type": "agent_invocation", "timestamp": "...", "data": {...}}
{"event_type": "workflow_completed", "timestamp": "...", "data": {...}}
```

**Why JSONL?**
- Streamable: Can read line-by-line
- Append-friendly: Just append new lines
- Parseable: Each line is valid JSON
- No schema migration: Events can have different structures

### Trade-offs

**Pros**:
- Zero setup time
- Perfect for prototype/demo
- Easy to debug and inspect
- No database costs

**Cons**:
- No indexing (slow for large datasets)
- No querying (must scan entire file)
- No transactions
- No concurrent write safety (solved with file locking)
- Doesn't scale beyond thousands of sessions

### Production Migration Path

**Phase 1** (Current): Flat files
**Phase 2**: Add SQLite for local caching
**Phase 3**: PostgreSQL for production

```sql
-- Production schema
CREATE TABLE sessions (
    session_id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    input_data JSONB NOT NULL,
    output_data JSONB,
    metadata JSONB
);

CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    session_id VARCHAR REFERENCES sessions(session_id),
    event_type VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_data JSONB NOT NULL
);

CREATE INDEX idx_session_status ON sessions(status);
CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(event_type);
```

**Migration Strategy**:
1. Abstract storage interface (`StorageInterface`)
2. Implement `FlatFileStorage` (current)
3. Implement `PostgresStorage` (production)
4. Switch via environment variable
5. Migrate existing JSONL files to database

---

## 5. Mock Tools Instead of Real Integrations

### Decision

**All tools are mocked implementations** that return realistic but fake data. No real external API calls.

### Alternatives Considered

**Option A: Real Integrations**
- Connect to actual policy systems, fraud databases, etc.
- Production-ready tools

**Option B: Sandbox/Demo APIs**
- Use vendor-provided demo environments
- Limited functionality

**Option C: Hybrid**
- Real integrations for core tools
- Mocked for complex/expensive tools

### Why Mock Tools?

**Advantages**:
1. **No External Dependencies**: Runs anywhere without setup
2. **Deterministic**: Predictable outputs for testing
3. **Fast**: No network latency
4. **Free**: No API costs or vendor accounts needed
5. **Demo-Friendly**: Always available, no rate limits
6. **Privacy**: No real claim data needed

**Example**: `fraud_rules` tool returns realistic fraud indicators based on claim data patterns, without calling actual fraud detection APIs.

### Mock Implementation Quality

Mocks are **realistic enough** to demonstrate patterns:
- Fraud tool detects multiple theft claims as suspicious
- Coverage tool calculates deductibles based on policy limits
- Similarity tool finds claims with matching characteristics

But **not production-ready**:
- No real machine learning models
- Simplified business logic
- No actual database lookups

### Trade-offs

**Pros**:
- Easy to run and demo
- No vendor dependencies
- Perfect for learning and testing
- Fast execution

**Cons**:
- Not production-ready
- Simplified logic may miss edge cases
- Can't demonstrate real integration patterns
- Need to be replaced for production

### Production Migration

**Tool Interface Stays Same**:
```python
# Tools API contract
POST /invoke/{tool_id}
{
  "claim_id": "...",
  "claim_data": {...}
}

# Response
{
  "success": true,
  "result": {...}
}
```

**Only Implementation Changes**:
```python
# Mock (current)
def execute_fraud_rules(params):
    # Simple if/then logic
    if params["claim_amount"] > 50000:
        return {"risk_score": 0.8}

# Production
def execute_fraud_rules(params):
    # Call actual fraud API
    response = requests.post(
        "https://fraud-api.company.com/analyze",
        json=params,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return response.json()
```

**Migration Checklist**:
- [ ] Identify production API endpoints
- [ ] Obtain API credentials
- [ ] Map mock response to actual API response
- [ ] Add error handling for API failures
- [ ] Implement retry logic
- [ ] Add caching for expensive calls
- [ ] Update tool registry with new parameters

---

## 6. Advisory Workflow Mode

### Decision

Workflows are defined in **"advisory" mode**, meaning the orchestrator treats them as guidance rather than strict requirements. The orchestrator can adapt the sequence, skip optional agents, or invoke agents multiple times based on runtime state.

### Alternatives Considered

**Option A: Strict Workflow**
- Fixed sequence: A → B → C → D
- Orchestrator cannot deviate
- Simple DAG execution

**Option B: No Workflow**
- Orchestrator has full autonomy
- No guidance at all
- Maximum flexibility

**Option C: Conditional Workflow**
- Workflow defines conditional branches
- Orchestrator follows branches based on conditions

### Why Advisory Mode?

**Advantages**:
1. **Flexibility with Guidance**: Provides structure but allows adaptation
2. **Handles Unexpected Scenarios**: Orchestrator can respond to surprises
3. **Efficient**: Can skip unnecessary agents
4. **Graceful Degradation**: Continues if optional agent fails
5. **Learning**: Orchestrator can improve decisions over time

**Example Adaptations**:
- **Skip fraud agent** if all prior indicators are clean
- **Re-invoke coverage agent** if new information emerges
- **Invoke severity agent early** if initial data suggests complexity

### Workflow Definition

```json
{
  "workflow_id": "claims_triage",
  "mode": "advisory",
  "suggested_sequence": ["intake", "coverage", "fraud", "severity", "recommendation"],
  "required_agents": ["intake_agent", "explainability_agent"],
  "optional_agents": ["fraud_agent", "severity_agent"],
  "completion_criteria": {
    "required_agents_executed": ["intake_agent"],
    "min_agents_executed": 3
  }
}
```

**Orchestrator Behavior**:
- Reads suggested_sequence as guidance
- Must execute required_agents
- May skip optional_agents if not needed
- Must meet completion_criteria to finish

### Trade-offs

**Pros**:
- Handles edge cases better
- More efficient (skips unnecessary work)
- Explainable (reasoning logged)
- Resilient to failures

**Cons**:
- Non-deterministic execution order
- Harder to predict behavior
- Orchestrator might make poor decisions
- Debugging is more complex

### Production Considerations

**When to Use Advisory Mode**:
- Complex, variable scenarios
- High autonomy desired
- Edge cases common

**When to Use Strict Mode**:
- Regulated processes (compliance)
- Predictable workflows
- Audit requirements demand fixed sequence

**Hybrid Approach**:
```json
{
  "mode": "strict_with_escape_hatch",
  "strict_sequence": ["intake", "coverage", "recommendation"],
  "escape_conditions": [
    {
      "condition": "fraud_score > 0.8",
      "action": "insert_agent_before_recommendation",
      "agent": "detailed_fraud_investigation"
    }
  ]
}
```

---

## 7. Server-Sent Events for Live Streaming

### Decision

**Server-Sent Events (SSE)** used for real-time workflow execution updates to frontend, not WebSockets or polling.

### Alternatives Considered

**Option A: WebSockets**
- Bidirectional communication
- Full-duplex connection

**Option B: Long Polling**
- Client polls every N seconds
- Simple HTTP

**Option C: GraphQL Subscriptions**
- GraphQL-based real-time updates
- Requires GraphQL setup

**Option D: No Real-Time**
- Client polls /status endpoint
- Refresh page to see updates

### Why SSE?

**Advantages**:
1. **Unidirectional**: Server → Client only (perfect for our use case)
2. **Built-in Reconnection**: Browser handles reconnects automatically
3. **Simple Protocol**: Just HTTP with specific headers
4. **Event IDs**: Built-in support for resume-from-last-event
5. **Firewall-Friendly**: Works through corporate firewalls (HTTP)
6. **Standard**: Native browser EventSource API

**Example**:
```javascript
const eventSource = new EventSource('/runs/session_123/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};

// Automatic reconnection built-in
eventSource.onerror = () => {
  console.log('Connection lost, reconnecting...');
};
```

### SSE Format

```
id: 20240315_abc123
event: agent_invocation
data: {"agent_id": "fraud_agent", "status": "started"}

id: 20240315_abc124
event: tool_invocation
data: {"tool_id": "fraud_rules", "result": {...}}

id: 20240315_abc125
event: workflow_completed
data: {"status": "completed"}
```

### Trade-offs

**Pros**:
- Simple to implement (server and client)
- Native browser support
- Built-in reconnection
- Efficient (single connection)

**Cons**:
- One-way only (can't send client messages)
- Limited browser support (IE11 doesn't support)
- Connection limits (browsers limit concurrent connections)
- Proxy/firewall buffering issues

### Production Considerations

**Nginx Configuration**:
```nginx
location /runs/ {
    proxy_pass http://orchestrator:8000;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

**CloudFront Configuration**:
```json
{
  "ViewerProtocolPolicy": "redirect-to-https",
  "Compress": false,
  "StreamingDistribution": true
}
```

**Scaling**:
- Use Redis Pub/Sub for multi-instance broadcasting
- Sticky sessions for SSE connections
- Connection pooling limits

**Alternative for Scale**: Consider switching to WebSockets + Socket.IO for 1000+ concurrent sessions.

---

## 8. Multi-Provider LLM Support

### Decision

**Support both OpenAI and Anthropic (Claude)** from day one, with agent-level model selection.

### Alternatives Considered

**Option A: OpenAI Only**
- Single provider, simpler
- GPT-3.5/GPT-4

**Option B: LangChain Abstraction**
- Use LangChain for multi-provider
- Higher-level abstractions

**Option C: Build Provider-Agnostic Interface**
- Custom abstraction layer
- Support any provider

### Why Multi-Provider?

**Advantages**:
1. **Avoid Vendor Lock-In**: Can switch providers easily
2. **Cost Optimization**: Use cheaper models where possible
3. **Model Selection**: Different models for different agents
4. **Redundancy**: Fallback if one provider is down
5. **Experimentation**: Compare model performance

**Example**:
- Intake agent: GPT-3.5 Turbo (cheap, simple validation)
- Fraud agent: Claude 3.5 Sonnet (complex reasoning)
- Orchestrator: GPT-4 Turbo (coordination)

### Implementation

**Model Profiles** (`model_profiles.json`):
```json
{
  "profile_id": "default_gpt35",
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "parameters": {"temperature": 0.3, "max_tokens": 2000}
},
{
  "profile_id": "claude_sonnet_35",
  "provider": "anthropic",
  "model_name": "claude-3-5-sonnet-20241022",
  "parameters": {"temperature": 0.3, "max_tokens": 4000}
}
```

**Agent Assignment** (`agent_registry.json`):
```json
{
  "agent_id": "fraud_agent",
  "model_profile_id": "claude_sonnet_35"
}
```

**Unified LLM Client** (`llm_client.py`):
```python
class BaseLLMClient(ABC):
    @abstractmethod
    def call(self, messages, **kwargs) -> LLMResponse:
        pass

class OpenAILLMClient(BaseLLMClient):
    def call(self, messages, **kwargs):
        response = openai.ChatCompletion.create(...)
        return LLMResponse(...)

class AnthropicLLMClient(BaseLLMClient):
    def call(self, messages, **kwargs):
        response = anthropic.messages.create(...)
        return LLMResponse(...)

def create_llm_client(model_profile):
    if model_profile.provider == "openai":
        return OpenAILLMClient(model_profile)
    elif model_profile.provider == "anthropic":
        return AnthropicLLMClient(model_profile)
```

### Trade-offs

**Pros**:
- Flexibility in model selection
- Cost optimization opportunities
- Vendor independence
- Can experiment with best model per agent

**Cons**:
- More complex implementation
- Need API keys for multiple providers
- Different providers have different quirks
- Prompt engineering may differ per model

### Production Strategy

**Cost Optimization**:
```
Intake Agent:        GPT-3.5 Turbo  ($0.50/1M tokens)
Coverage Agent:      GPT-3.5 Turbo  ($0.50/1M tokens)
Fraud Agent:         Claude Sonnet  ($3/1M tokens)
Severity Agent:      GPT-3.5 Turbo  ($0.50/1M tokens)
Recommendation:      Claude Sonnet  ($3/1M tokens)
Explainability:      GPT-4 Turbo    ($10/1M tokens)
Orchestrator:        GPT-4 Turbo    ($10/1M tokens)

Total cost per claim: ~$0.02 - $0.05
```

**Fallback Strategy**:
```python
def call_llm_with_fallback(messages):
    try:
        return call_primary_provider(messages)
    except ProviderError:
        return call_fallback_provider(messages)
```

---

## 9. Bounded Execution (Iteration Limits & Timeouts)

### Decision

**Hard limits enforced** on iterations, timeouts, and token budgets to prevent runaway loops and cost explosion.

### Alternatives Considered

**Option A: No Limits**
- Agents run until they complete
- Trust LLM to terminate

**Option B: Soft Limits**
- Warning at threshold
- Continue anyway

**Option C: Dynamic Limits**
- Adjust limits based on complexity

### Why Hard Limits?

**Advantages**:
1. **Cost Protection**: Prevent token budget explosions
2. **Reliability**: Workflows always terminate
3. **Predictability**: Known worst-case duration
4. **Safety**: Prevent infinite loops
5. **Resource Control**: Bounded resource consumption

**Example Scenario**:
- Agent enters infinite reasoning loop
- Without limits: $1000+ in API costs
- With limits: Stops at iteration 5, costs $1

### Limit Types

**1. Iteration Limits**
```python
# Worker agents: max 5 iterations
# Orchestrator: max 10 iterations

if self.iteration >= self.agent.max_iterations:
    return incomplete_result()
```

**2. Timeouts**
```python
# Per-iteration timeout: 30 seconds
# Workflow timeout: 300 seconds

@timeout(seconds=30)
def execute_iteration():
    ...
```

**3. Token Budgets**
```python
# Per-request: 2000 tokens
# Per-session: 50000 tokens

if session_tokens + request_tokens > MAX_TOKENS:
    raise TokenBudgetExceeded()
```

**4. Duplicate Invocation Limits**
```python
# Same agent max 2 times
if agent_invocations["fraud_agent"] >= 2:
    return already_invoked_error()
```

### Multi-Tier Completion

Ensures workflows always complete gracefully:

**Tier 1**: LLM explicitly signals completion
```python
if action.type == ActionType.FINAL_OUTPUT:
    return validate_and_complete(action.output)
```

**Tier 2**: Completion criteria met
```python
if meets_completion_criteria():
    return auto_complete()
```

**Tier 3**: Max iterations reached
```python
if iteration >= max_iterations:
    return forced_complete_with_partial()
```

### Trade-offs

**Pros**:
- Predictable costs
- Guaranteed termination
- Production-safe
- Easy to reason about

**Cons**:
- May cut off before optimal solution
- Some complex cases need more iterations
- Requires tuning per use case

### Production Tuning

**Monitor Completion Rates**:
```sql
SELECT
  completion_reason,
  COUNT(*) as count,
  AVG(iterations_used) as avg_iterations
FROM sessions
GROUP BY completion_reason;

-- Results:
-- all_objectives_achieved: 85%, 3.2 avg iterations
-- max_iterations_reached: 12%, 5.0 avg iterations
-- timeout: 3%, 4.8 avg iterations
```

**Adjust Based on Data**:
- If 20%+ hit max iterations → increase limit
- If <5% use >3 iterations → decrease limit
- If costs high → reduce token budgets
- If quality low → increase timeouts

**Per-Use-Case Limits**:
```json
{
  "workflow_id": "simple_claim",
  "constraints": {
    "max_orchestrator_iterations": 5,
    "max_agent_iterations": 3
  }
},
{
  "workflow_id": "complex_litigation",
  "constraints": {
    "max_orchestrator_iterations": 20,
    "max_agent_iterations": 10
  }
}
```

---

## 10. Context Compilation & Token Management

### Decision

**Agent-specific context compilation** with token budgets to prevent context bloat (major cost driver).

### Why Important?

**Problem**: Passing all prior outputs to every agent causes:
- Exponential context growth
- Wasted tokens on irrelevant data
- Slow LLM calls
- Cost explosion

**Example**:
```
Iteration 1: Intake agent (1000 tokens)
Iteration 2: Coverage agent receives intake output (1000) + own context (1000) = 2000
Iteration 3: Fraud agent receives intake + coverage (2000) + own (1500) = 3500
Iteration 4: Severity agent receives all prior (3500) + own (2000) = 5500
...
Iteration 7: Final agent receives 15,000+ tokens of irrelevant context
```

**Cost Impact**:
- Without context management: 50,000 tokens × $0.0015/1k = $0.075/claim
- With context management: 10,000 tokens × $0.0015/1k = $0.015/claim
- **Savings**: 80% cost reduction

### Solution: Selective Context Compilation

**1. Agent Declares Dependencies**
```json
{
  "agent_id": "fraud_agent",
  "context_requirements": {
    "requires_prior_outputs": ["intake", "coverage"],
    "max_context_tokens": 6000
  }
}
```

**2. Context Compiler Selects Relevant Data**
```python
def compile_for_agent(agent_id, original_input, prior_outputs):
    # Get agent's requirements
    agent = registry.get_agent(agent_id)
    requires = agent.context_requirements.requires_prior_outputs
    max_tokens = agent.context_requirements.max_context_tokens

    # Budget allocation
    budget_original = max_tokens * 0.3  # 30% for original input
    budget_prior = max_tokens * 0.5     # 50% for prior outputs
    budget_obs = max_tokens * 0.2       # 20% for observations

    # Select only required outputs
    context = {
        "original_input": truncate(original_input, budget_original),
        "prior_outputs": {
            agent_id: truncate(prior_outputs[agent_id], budget_prior / len(requires))
            for agent_id in requires
            if agent_id in prior_outputs
        },
        "observations": select_recent(observations, budget_obs)
    }

    return context
```

**3. Token Estimation**
```python
def estimate_tokens(data):
    # Simple heuristic: 1 token ≈ 4 characters
    # Production: use tiktoken
    text = json.dumps(data)
    return len(text) // 4
```

### Trade-offs

**Pros**:
- Massive cost savings
- Faster LLM calls (less context)
- Prevents context limits (200k tokens)
- Agent-specific relevance

**Cons**:
- Agent might miss relevant information
- Requires manual dependency declaration
- Truncation might cut important data
- Token estimation is approximate

### Production Enhancements

**1. Semantic Context Selection**
```python
def select_relevant_context(agent_id, prior_outputs, max_tokens):
    # Use embeddings to find most relevant outputs
    agent_goal = get_agent_goal(agent_id)
    relevance_scores = {
        output_id: cosine_similarity(
            embed(agent_goal),
            embed(output_summary)
        )
        for output_id, output_summary in prior_outputs.items()
    }

    # Select top-k most relevant
    sorted_outputs = sorted(
        relevance_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    selected = {}
    tokens_used = 0
    for output_id, score in sorted_outputs:
        output_tokens = estimate_tokens(prior_outputs[output_id])
        if tokens_used + output_tokens <= max_tokens:
            selected[output_id] = prior_outputs[output_id]
            tokens_used += output_tokens

    return selected
```

**2. Hierarchical Summarization**
```python
def summarize_prior_outputs(outputs):
    # Use LLM to summarize prior outputs
    summary = llm_call(
        f"Summarize these outputs in 200 tokens:\n{outputs}"
    )
    return summary  # Compressed context
```

**3. Token Accounting**
```python
class TokenBudget:
    def __init__(self, max_tokens):
        self.max_tokens = max_tokens
        self.used_tokens = 0

    def allocate(self, tokens):
        if self.used_tokens + tokens > self.max_tokens:
            raise TokenBudgetExceeded()
        self.used_tokens += tokens

    def remaining(self):
        return self.max_tokens - self.used_tokens
```

---

## 11. Structured Output Validation (Pydantic)

### Decision

**All agent outputs validated against Pydantic schemas** before accepting as complete.

### Why Validation?

**Problem**: LLMs sometimes produce:
- Malformed JSON
- Missing required fields
- Wrong data types
- Out-of-range values

**Without Validation**:
```python
output = llm_call(...)  # Returns JSON string
data = json.loads(output)  # Might fail
result = data["fraud_score"]  # Might not exist
if result > 0.8:  # Might be string "high" instead of number
    ...
```

**With Validation**:
```python
output = llm_call(...)
validated = FraudAgentOutput(**output)  # Pydantic validation
# Now guaranteed to have:
# - validated.fraud_score (float, 0-1)
# - validated.risk_band (Enum: low/medium/high/critical)
# - validated.triggered_indicators (List[FraudIndicator])
```

### Schema Definition

```python
class FraudAgentOutput(AgentOutputBase):
    """Output schema for fraud_agent."""

    fraud_score: float = Field(..., ge=0.0, le=1.0)
    risk_band: RiskBand = Field(...)
    triggered_indicators: List[FraudIndicator] = Field(default_factory=list)
    rationale: str = Field(...)

    @validator('fraud_score')
    def score_range_check(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('fraud_score must be between 0 and 1')
        return v
```

### Validation Flow

```python
def _validate_output(self, output: Dict[str, Any]) -> bool:
    try:
        # Validate against schema
        validated_output = validate_agent_output(self.agent_id, output)

        # Log success
        self._log_event("output_validated", {
            "agent_id": self.agent_id,
            "schema_version": validated_output.version
        })

        return True

    except SchemaValidationError as e:
        # Log failure with details
        self._log_event("output_validation_failed", {
            "agent_id": self.agent_id,
            "error": str(e)
        })

        logger.error(f"Output validation failed for {self.agent_id}: {str(e)}")

        return False
```

### Trade-offs

**Pros**:
- Type safety
- Early error detection
- Self-documenting schemas
- IDE autocomplete
- Prevents propagation of bad data

**Cons**:
- Schema must be kept in sync with registry
- Validation adds latency (minimal)
- LLM might struggle with complex schemas
- Requires schema evolution strategy

### Production Enhancements

**1. Schema Evolution**
```python
class FraudAgentOutputV2(FraudAgentOutputV1):
    """Version 2 with additional fields."""

    version: str = "2.0"
    ml_model_version: str = Field(...)
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(...)

    class Config:
        # Allow extra fields for forward compatibility
        extra = "allow"
```

**2. Automatic Schema Repair**
```python
def repair_output(output, schema):
    """Attempt to fix common validation errors."""

    # Fix type mismatches
    if "fraud_score" in output and isinstance(output["fraud_score"], str):
        try:
            output["fraud_score"] = float(output["fraud_score"])
        except ValueError:
            output["fraud_score"] = 0.0  # Default

    # Fill missing required fields with defaults
    if "risk_band" not in output:
        output["risk_band"] = "medium"  # Safe default

    return output
```

**3. Schema Metrics**
```python
def track_validation_metrics():
    """Track validation success rate per agent."""

    # Metrics:
    # - validation_success_rate_by_agent
    # - validation_failure_reasons
    # - schema_repair_success_rate

    if fraud_agent_validation_success_rate < 0.95:
        alert("Fraud agent output schema issues")
```

---

## 12. Multi-Tier Completion

### Decision

**Three-tier completion logic** ensures workflows always terminate gracefully.

### Tiers

**Tier 1: LLM Explicit Completion**
- LLM signals `action_type: "WORKFLOW_COMPLETE"`
- Provides complete evidence map
- **Ideal outcome**

**Tier 2: Validation-Based Completion**
- LLM signals completion, but evidence map validated against criteria
- Must have required outputs, agents executed, etc.
- **Safety check**

**Tier 3: Forced Completion**
- Max iterations reached
- System builds evidence map from available data
- **Graceful degradation**

### Implementation

```python
while iteration < max_iterations:
    reasoning = call_llm_for_orchestrator_reasoning(...)

    if reasoning.action.type == OrchestratorActionType.WORKFLOW_COMPLETE:
        # Tier 1: LLM signals completion
        evidence_map = reasoning.action.evidence_map

        # Tier 2: Validate
        validation = validate_completion_criteria(evidence_map)

        if validation["valid"]:
            return OrchestratorResult(
                status="completed",
                completion_reason="all_objectives_achieved",
                evidence_map=evidence_map
            )
        else:
            # Validation failed - continue loop
            warnings.append(f"Validation failed: {validation['reason']}")
            continue

    elif reasoning.action.type == OrchestratorActionType.INVOKE_AGENTS:
        # Execute agent invocations
        execute_agent_invocations(...)
        continue

# Tier 3: Forced completion
evidence_map = build_evidence_map_from_available_data()
return OrchestratorResult(
    status="incomplete",
    completion_reason="max_iterations_reached",
    evidence_map=evidence_map,
    warnings=["Orchestrator reached max iterations"]
)
```

### Completion Criteria Validation

```python
def validate_completion_criteria(evidence_map):
    criteria = workflow.completion_criteria

    # Check required agents executed
    for agent_id in criteria.required_agents_executed:
        if agent_id not in agents_executed:
            return {
                "valid": False,
                "reason": f"Required agent '{agent_id}' not executed"
            }

    # Check minimum agent count
    if len(agents_executed) < criteria.min_agents_executed:
        return {
            "valid": False,
            "reason": f"Only {len(agents_executed)} agents executed (min: {criteria.min_agents_executed})"
        }

    # Check required outputs present
    for output_key in criteria.required_outputs:
        if output_key not in evidence_map:
            return {
                "valid": False,
                "reason": f"Required output '{output_key}' missing"
            }

    return {"valid": True}
```

### Trade-offs

**Pros**:
- Guaranteed termination
- Graceful degradation
- Always produces result (even if partial)
- Safety against LLM hallucination

**Cons**:
- Tier 3 results may be incomplete
- Adds complexity
- Need to handle partial results downstream

### Production Metrics

```sql
SELECT
  completion_reason,
  COUNT(*) as count,
  AVG(total_iterations) as avg_iterations,
  AVG(total_agent_invocations) as avg_invocations
FROM sessions
GROUP BY completion_reason;

-- Target:
-- all_objectives_achieved: >90%
-- max_iterations_reached: <10%
-- timeout: <1%
-- error: <1%
```

---

## 13. Governance via Policies Not Code

### Decision

**Access control and execution constraints defined in policies** (JSON), not hardcoded.

### Why Policy-Driven?

**Hardcoded Governance**:
```python
def check_tool_access(agent_id, tool_id):
    # Hardcoded rules
    if agent_id == "fraud_agent":
        return tool_id in ["fraud_rules", "similarity"]
    elif agent_id == "coverage_agent":
        return tool_id in ["policy_snapshot", "coverage_rules"]
    # ... need to update code for every change
```

**Policy-Driven Governance**:
```json
{
  "agent_tool_access": {
    "rules": [
      {
        "agent_id": "fraud_agent",
        "allowed_tools": ["fraud_rules", "similarity"]
      }
    ]
  }
}
```

```python
def check_tool_access(agent_id, tool_id):
    # Read from policy
    return registry.is_tool_access_allowed(agent_id, tool_id)
```

### Policy Types

**1. Agent Invocation Access**
```json
{
  "agent_invocation_access": {
    "enforcement_level": "strict",
    "rules": [
      {
        "agent_id": "orchestrator_agent",
        "allowed_agents": ["intake_agent", "fraud_agent", ...],
        "denied_agents": ["orchestrator_agent"]
      }
    ]
  }
}
```

**2. Tool Access**
```json
{
  "agent_tool_access": {
    "enforcement_level": "strict",
    "rules": [
      {
        "agent_id": "fraud_agent",
        "allowed_tools": ["fraud_rules", "similarity"]
      }
    ]
  }
}
```

**3. Iteration Limits**
```json
{
  "iteration_limits": {
    "global_max_iterations": 5,
    "agent_overrides": [
      {
        "agent_id": "orchestrator_agent",
        "max_iterations": 10
      }
    ]
  }
}
```

**4. Execution Constraints**
```json
{
  "execution_constraints": {
    "max_workflow_duration_seconds": 300,
    "max_tool_invocations_per_session": 50,
    "max_llm_calls_per_session": 30
  }
}
```

### Enforcement

```python
class GovernanceEnforcer:
    def check_agent_invocation(self, invoker, target):
        # Check registry-based access
        if not registry.is_agent_invocation_allowed(invoker, target):
            return EnforcementResult(
                allowed=False,
                violation=PolicyViolation(
                    type="agent_invocation_denied",
                    reason=f"{invoker} cannot invoke {target}"
                )
            )

        # Check duplicate invocation limit
        if invocation_count[target] >= max_duplicates:
            return EnforcementResult(
                allowed=False,
                violation=PolicyViolation(
                    type="max_invocations_exceeded",
                    reason=f"{target} already invoked {invocation_count[target]} times"
                )
            )

        return EnforcementResult(allowed=True)
```

### Trade-offs

**Pros**:
- Change policies without code changes
- Audit trail (policy versions in git)
- Role-based access (future)
- Centralized compliance

**Cons**:
- Policy language limitations
- No complex conditional logic
- Requires policy validation

### Production Evolution

**1. Policy Versioning**
```json
{
  "version": "2.0",
  "effective_date": "2024-04-01",
  "deprecated_policies": ["v1.0"],
  "migration_guide": "..."
}
```

**2. Dynamic Policy Updates**
```python
@app.post("/admin/policies/reload")
async def reload_policies():
    """Hot-reload policies without restart."""
    get_registry_manager().load_governance()
    return {"status": "reloaded"}
```

**3. Policy Audit Logs**
```python
class AuditLogger:
    def log_policy_violation(self, violation):
        # Log to audit system
        audit_log.write({
            "timestamp": now(),
            "violation_type": violation.type,
            "agent_id": violation.agent_id,
            "target": violation.target,
            "reason": violation.reason,
            "session_id": violation.session_id
        })
```

---

## 14. Monolithic Orchestrator vs Distributed Agents

### Decision (Current)

**Monolithic orchestrator** that manages all agents and LLM calls in a single service.

### Why Monolithic for Prototype?

**Advantages**:
1. **Simplicity**: Easier to develop and debug
2. **Consistency**: Single codebase for all agents
3. **Performance**: No network overhead between agents
4. **Deployment**: Single service to deploy
5. **Development Speed**: Faster iteration

### Production Evolution: Distributed Architecture

```
Current (Monolithic):
┌────────────────────────────┐
│   Orchestrator Service     │
│  ┌─────────────────────┐   │
│  │  Orchestrator Agent │   │
│  └─────────┬───────────┘   │
│            │               │
│  ┌─────────▼───────────┐   │
│  │   Worker Agents     │   │
│  │  - Intake          │   │
│  │  - Coverage        │   │
│  │  - Fraud           │   │
│  └─────────────────────┘   │
└────────────────────────────┘

Production (Distributed):
┌─────────────────┐
│  Orchestrator   │
│    Service      │
└────────┬────────┘
         │
    ┌────┴─────┬──────┬──────┐
    │          │      │      │
┌───▼───┐  ┌──▼──┐ ┌─▼──┐ ┌─▼──┐
│Intake │  │Cover│ │Fraud│ │Rec │
│Service│  │ age │ │Svc  │ │Svc │
└───────┘  └─────┘ └────┘ └────┘
```

### Migration Path

**Phase 1** (Current): Monolithic
**Phase 2**: Extract agent interfaces
**Phase 3**: Deploy agents as separate services
**Phase 4**: Kubernetes with auto-scaling

```python
# Phase 2: Interface extraction
class AgentInterface(ABC):
    @abstractmethod
    async def execute(self, context) -> AgentResult:
        pass

class LocalAgent(AgentInterface):
    """Current: In-process execution"""
    async def execute(self, context):
        loop = create_agent_react_loop(...)
        return loop.execute(context)

class RemoteAgent(AgentInterface):
    """Future: Remote service call"""
    async def execute(self, context):
        response = await httpx.post(
            f"http://agent-service/execute",
            json=context
        )
        return AgentResult(**response.json())

# Orchestrator doesn't care which implementation
agent = agent_factory.create(agent_id)  # Could be local or remote
result = await agent.execute(context)
```

### Trade-offs

**Monolithic Pros**:
- Simple deployment
- No network latency
- Easier debugging
- Shared memory

**Distributed Pros**:
- Independent scaling
- Technology diversity (polyglot)
- Fault isolation
- Team autonomy

**Decision**: Start monolithic, evolve to distributed when scale demands it.

---

## 15. Simplifications for Prototype

### Acceptable Simplifications

These simplifications are **appropriate for a prototype** but would need addressing for production:

#### 1. No Database
**Current**: Flat files (JSONL/JSON)
**Production**: PostgreSQL/MongoDB

**Justification**: Easier to inspect and debug during development.

#### 2. Mock Tools
**Current**: Realistic but fake data
**Production**: Real API integrations

**Justification**: No external dependencies needed.

#### 3. Single Workflow
**Current**: Only `claims_triage` implemented
**Production**: Multiple workflows

**Justification**: Demonstrates all patterns sufficiently.

#### 4. No Authentication
**Current**: Open API endpoints
**Production**: JWT/OAuth required

**Justification**: Simplifies demo.

#### 5. No Distributed Tracing
**Current**: Basic logging
**Production**: OpenTelemetry + Jaeger

**Justification**: Logging sufficient for debugging.

#### 6. Single Tenant
**Current**: No isolation
**Production**: Multi-tenant with data isolation

**Justification**: Prototype scope.

#### 7. No Caching
**Current**: All tools execute fresh
**Production**: Cache policy lookups, tool results

**Justification**: Simpler logic.

#### 8. Synchronous Tool Calls
**Current**: Sequential execution
**Production**: Parallel tool invocation

**Justification**: Easier to reason about.

### Core Patterns Fully Represented

Despite simplifications, these **production patterns are fully demonstrated**:

- ✅ Loose coupling via registries
- ✅ Dynamic discovery
- ✅ Bounded ReAct loops
- ✅ Governance enforcement
- ✅ Complete observability
- ✅ Multi-provider LLM
- ✅ Event streaming
- ✅ Evidence maps
- ✅ Context management
- ✅ Structured outputs

**Conclusion**: The simplifications **do not compromise** the demonstration of scalability patterns. They make the prototype easier to run and understand while maintaining architectural integrity.

---

## Summary

AgentMesh demonstrates **production-grade patterns** for building scalable multi-agent systems:

1. **ReAct orchestrator** for dynamic coordination
2. **Centralized LLM management** for governance
3. **Registry-driven discovery** for zero-code extensibility
4. **Bounded execution** for cost control
5. **Policy-based governance** for compliance
6. **Multi-tier completion** for reliability
7. **Evidence maps** for explainability
8. **SSE streaming** for real-time UX

These decisions create a system that is:
- **Scalable**: Can grow from prototype to production
- **Observable**: Complete audit trails
- **Governable**: Policy-driven constraints
- **Explainable**: Evidence maps for every decision
- **Cost-Effective**: Token budgets and model selection
- **Reliable**: Always terminates, graceful degradation

For questions or discussions about these decisions, please open an issue or discussion in the repository.

---

**Document Version**: 1.0
**Last Updated**: 2024-12-23
**Author**: AgentMesh Team
