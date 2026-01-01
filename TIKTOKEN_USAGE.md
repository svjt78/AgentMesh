# Purpose of tiktoken in AgentMesh

## Overview

`tiktoken` is OpenAI's official tokenizer library used in AgentMesh for **accurate token counting** in the context management system. It ensures that context sent to LLMs stays within token limits while maximizing the relevant information included.

## Primary Use Case

The library is primarily used in the `ContextCompiler` service ([context_compiler.py](backend/orchestrator/app/services/context_compiler.py)) to manage token budgets when compiling context from multiple sources for agent execution.

## Key Functions

### 1. Token Budget Management

**Location**: [context_compiler.py:278-293](backend/orchestrator/app/services/context_compiler.py#L278-L293)

The `_count_tokens()` method accurately counts tokens in data structures (JSON objects, strings, etc.) to ensure context sent to LLMs stays within configured limits.

```python
def _count_tokens(self, data: Any) -> int:
    if self.tokenizer:
        # Accurate counting with tiktoken
        text = json.dumps(data) if not isinstance(data, str) else data
        return len(self.tokenizer.encode(text))
    else:
        # Fallback: rough estimate (4 chars ≈ 1 token)
        text = json.dumps(data) if not isinstance(data, str) else data
        return len(text) // 4
```

### 2. Context Compilation with Token Budgets

**Location**: [context_compiler.py:61-125](backend/orchestrator/app/services/context_compiler.py#L61-L125)

When compiling context for agent execution, the system allocates token budgets across different context sections:

- **30%** for original input (user's claim data)
- **50%** for prior agent outputs (results from previous agents)
- **20%** for observations (tool execution results)

This ensures the most critical information is preserved when context needs to be truncated.

### 3. Prevents Context Overflow

Each agent has a `max_context_tokens` limit defined in `registries/agent_registry.json`. The `ContextCompiler` uses tiktoken to:

- Calculate accurate token counts for all context components
- Truncate older/less relevant context when exceeding limits
- Prioritize recent agent outputs over older ones
- Ensure workflows don't fail due to context window overflows

## Implementation Details

### Initialization

**Location**: [context_compiler.py:40-47](backend/orchestrator/app/services/context_compiler.py#L40-L47)

```python
def __init__(self):
    self.registry = get_registry_manager()
    # Use tiktoken for accurate token counting
    try:
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except:
        # Fallback if tiktoken not available
        self.tokenizer = None
```

The system initializes a tiktoken encoder for GPT-3.5-turbo's tokenization scheme, which provides consistent token counting across different model providers (OpenAI and Anthropic).

### Fallback Mechanism

If tiktoken is unavailable, the system falls back to a rough estimate of **4 characters ≈ 1 token**. This ensures the system remains functional even if the library is not installed, though with less accurate token counting.

## Why This Matters for AgentMesh

### The Meta-Agent Pattern Challenge

AgentMesh uses a **meta-agent ReAct pattern** where:

1. The **orchestrator agent** (meta-agent) runs a ReAct loop to decide which worker agents to invoke
2. **Worker agents** run their own nested ReAct loops to decide which tools to use
3. Each agent execution produces outputs that become context for subsequent agents

This creates a compounding context problem:
- Original claim data
- Multiple agent outputs (fraud detection, policy verification, damage assessment, etc.)
- Tool execution observations
- Workflow metadata

Without accurate token counting, the system would either:
- Truncate too aggressively (losing critical information)
- Exceed token limits (causing LLM API failures)

### Token-Aware Context Management

`tiktoken` enables **intelligent context truncation**:

- Preserves the most recent and relevant agent outputs
- Ensures workflow state doesn't exceed model context windows
- Allows the orchestrator to make informed decisions about which prior outputs to include
- Prevents workflow failures due to context overflow

## Configuration

Token limits are configured per-agent in `registries/agent_registry.json`:

```json
{
  "agent_id": "fraud_detection_agent",
  "context_requirements": {
    "max_context_tokens": 8000
  }
}
```

The orchestrator agent typically has a higher limit (e.g., 10000 tokens) since it needs to see outputs from all worker agents.

## Dependencies

Install via requirements.txt:

```
tiktoken>=0.5.1
```

Docker deployments automatically include this dependency through the orchestrator service's requirements.txt.

## Related Documentation

- [CLAUDE.md](CLAUDE.md) - Project overview and architecture
- [context_compiler.py](backend/orchestrator/app/services/context_compiler.py) - Implementation
- [agent_registry.json](registries/agent_registry.json) - Agent token limit configurations
