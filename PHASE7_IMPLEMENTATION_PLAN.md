# Phase 7 Implementation Plan: Prefix Caching & Optimization

**Phase**: Prefix Caching & Optimization
**Goal**: Reduce LLM costs through prompt caching
**Timeline**: Weeks 13-14 (from original spec)
**Date**: January 2, 2026

---

## Overview

Phase 7 implements **prompt caching** to reduce LLM costs by identifying and caching stable portions of context that don't change between LLM calls. This leverages provider-specific caching features (Anthropic's Prompt Caching, OpenAI's cached prompts) to reduce token processing costs.

### Key Concept: Prefix vs Suffix

**Prefix (Stable/Cacheable)**:
- System instructions
- Agent identity and capabilities
- Tool schemas (for tool-using agents)
- Workflow definitions
- Governance rules
- Static context that rarely changes

**Suffix (Variable/Uncacheable)**:
- Recent observations (tool results)
- Current task/iteration state
- Dynamic user input
- Session-specific data
- Context that changes every call

### Expected Cost Savings

Anthropic Prompt Caching:
- Cached prefix read: **90% cheaper** than regular tokens
- Cached prefix write: Same cost as regular tokens (first time)
- Break-even: After 1-2 cache hits

**Example**:
- Agent with 5000-token prefix (system + tools)
- 10 iterations = 50,000 tokens normally
- With caching: 5000 write + 45,000 cached read = **~85% cost reduction** on prefix

---

## Core Concepts

### 1. Stable Components (Prefix)

**Characteristics**:
- Doesn't change between iterations
- Same across multiple sessions for same agent
- Derived from registries (agent config, tool schemas)
- Can be computed once and reused

**Examples**:
```python
[
    "system_instructions",      # Agent's base prompt
    "agent_identity",           # Agent metadata
    "tool_schemas",            # Available tools
    "governance_rules",        # Access control policies
    "workflow_definition"      # Workflow context
]
```

### 2. Variable Components (Suffix)

**Characteristics**:
- Changes every iteration or session
- Unique to current execution state
- User-provided or dynamically generated
- Cannot be cached

**Examples**:
```python
[
    "recent_observations",     # Last 3 tool results
    "current_task",           # What to do this iteration
    "session_context",        # Session-specific data
    "iteration_metadata"      # Iteration number, etc.
]
```

### 3. Cache Key Generation

**Cache Key Format**: `{agent_id}:{model_profile}:{config_hash}`

- `agent_id`: Which agent (fraud_agent, coverage_agent, etc.)
- `model_profile`: LLM model being used (claude-3-5-sonnet, gpt-4, etc.)
- `config_hash`: Hash of agent config + tool schemas (detects changes)

**Invalidation**: Cache auto-invalidates when:
- Agent registry updated (new tools, changed prompt)
- Tool schemas modified
- Model profile changed

---

## Implementation Tasks

### Task 1: Configure Prefix Caching in System Config ✅

**File**: `registries/system_config.json`

**Add Section**:
```json
{
  "prefix_caching": {
    "enabled": false,
    "_description": "Enable LLM prompt prefix caching to reduce costs. Caches stable context components (system instructions, tools) across iterations.",
    "stable_prefix_components": [
      "system_instructions",
      "agent_identity",
      "tool_schemas",
      "governance_rules"
    ],
    "variable_suffix_components": [
      "recent_observations",
      "current_task",
      "session_context"
    ],
    "cache_ttl_minutes": 60,
    "_cache_providers": "Supported: anthropic (prompt caching), openai (cached prompts)"
  }
}
```

### Task 2: Enhance Injector Processor

**File**: `backend/orchestrator/app/services/processors/injector.py`

**Changes**:
1. Read prefix caching config from system_config.json
2. Separate context into prefix and suffix components
3. Mark prefix with cache control headers (Anthropic) or cache hints (OpenAI)
4. Return structured prompt with cache metadata

**New Method**: `_separate_prefix_suffix()`
```python
def _separate_prefix_suffix(
    self,
    context: Dict[str, Any],
    agent_id: str
) -> tuple[List[Dict], List[Dict]]:
    """
    Separate context into cacheable prefix and variable suffix.

    Returns:
        (prefix_messages, suffix_messages)
    """
    # Prefix: System, agent identity, tools
    prefix = [
        {"role": "system", "content": system_prompt, "cache_control": {"type": "ephemeral"}},
        {"role": "system", "content": tool_schemas_text, "cache_control": {"type": "ephemeral"}}
    ]

    # Suffix: Recent observations, current task
    suffix = [
        {"role": "user", "content": current_task_prompt}
    ]

    return prefix, suffix
```

**New Method**: `_generate_cache_key()`
```python
def _generate_cache_key(
    self,
    agent_id: str,
    model_profile_id: str,
    config_hash: str
) -> str:
    """Generate cache key for prefix."""
    return f"{agent_id}:{model_profile_id}:{config_hash}"
```

### Task 3: Enhance LLM Client for Caching

**File**: `backend/orchestrator/app/services/llm_client.py`

**Changes**:
1. Add support for Anthropic Prompt Caching
2. Add support for OpenAI cached prompts
3. Track cache hits/misses
4. Log cache metrics in LLM call events

**Anthropic Integration**:
```python
# Add cache_control to messages
messages = [
    {
        "role": "system",
        "content": "System instructions...",
        "cache_control": {"type": "ephemeral"}  # Mark for caching
    },
    {"role": "user", "content": "Current task..."}
]

response = anthropic.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages,
    # Cache automatically managed by Anthropic
)

# Check usage for cache metrics
usage = response.usage
cache_creation_tokens = usage.cache_creation_input_tokens
cache_read_tokens = usage.cache_read_input_tokens
```

**OpenAI Integration**:
```python
# Use stored_completions for caching (if available)
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "System instructions..."},
        {"role": "user", "content": "Current task..."}
    ],
    # OpenAI auto-caches recent prompts (no explicit API)
)
```

### Task 4: Add Cache Metrics Tracking

**File**: `backend/orchestrator/app/services/llm_client.py`

**Enhance LLM Call Event**:
```json
{
  "event_type": "llm_call",
  "agent_id": "fraud_agent",
  "model": "claude-3-5-sonnet-20241022",
  "tokens": {
    "input_tokens": 5000,
    "output_tokens": 500,
    "cache_creation_input_tokens": 3000,  // NEW
    "cache_read_input_tokens": 0          // NEW (0 on first call)
  },
  "cache_metrics": {                      // NEW
    "cache_enabled": true,
    "cache_key": "fraud_agent:claude-3-5-sonnet:abc123",
    "cache_hit": false,                   // First call
    "cache_savings_tokens": 0,
    "cache_savings_cost_usd": 0.0
  }
}
```

**On subsequent calls**:
```json
{
  "tokens": {
    "input_tokens": 5000,
    "cache_creation_input_tokens": 0,     // No new cache
    "cache_read_input_tokens": 3000       // Read from cache
  },
  "cache_metrics": {
    "cache_hit": true,
    "cache_savings_tokens": 3000,
    "cache_savings_cost_usd": 0.015       // Saved ~$0.015
  }
}
```

### Task 5: Update Agent Registry Schema

**File**: `registries/agent_registry.json`

**Add to agent definitions**:
```json
{
  "agent_id": "fraud_agent",
  "context_requirements": {
    "prefix_caching_eligible": true,     // NEW
    "stable_context_components": [       // NEW (optional override)
      "system_instructions",
      "tool_schemas",
      "fraud_rules"
    ]
  }
}
```

### Task 6: Testing & Validation

**Test Cases**:
1. ✅ Feature disabled by default (no caching)
2. ✅ Enable caching, verify cache_control added to Anthropic messages
3. ✅ Verify cache hit on second LLM call (same agent, same iteration)
4. ✅ Verify cache metrics in llm_call events
5. ✅ Verify cost savings calculation
6. ✅ Verify cache invalidation on config change

---

## Technical Design

### Cache Flow

```
Agent Iteration 1:
├─ ContextCompiler.compile_for_agent()
├─ ContextProcessorPipeline.execute()
├─ Injector.process()
│   ├─ Check if prefix_caching enabled
│   ├─ Separate prefix (system, tools) from suffix (observations, task)
│   ├─ Mark prefix messages with cache_control
│   └─ Return {prefix: [...], suffix: [...], cache_key: "..."}
├─ LLMClient.call()
│   ├─ Combine prefix + suffix
│   ├─ Call Anthropic API with cache_control
│   ├─ API creates cache (cache_creation_input_tokens = 3000)
│   └─ Log llm_call event with cache_metrics
└─ Cache stored (TTL: 60 min)

Agent Iteration 2 (same agent, within TTL):
├─ ContextCompiler.compile_for_agent()
├─ Injector.process() [same prefix, different suffix]
├─ LLMClient.call()
│   ├─ Anthropic detects matching prefix
│   ├─ Reads from cache (cache_read_input_tokens = 3000)
│   ├─ Only processes suffix as new tokens
│   └─ Log cache hit (savings = 3000 tokens)
└─ Cost: ~90% cheaper on prefix
```

### Cost Calculation

**Anthropic Pricing** (Claude 3.5 Sonnet):
- Input tokens: $3.00 per million
- Cache write (creation): $3.75 per million (25% more)
- Cache read: $0.30 per million (90% cheaper)

**Example Workflow** (5 iterations, 3000-token prefix):
- Iteration 1: 3000 cache write = $0.01125
- Iterations 2-5: 4 × 3000 cache read = 4 × $0.0009 = $0.0036
- **Total**: $0.01485 vs $0.045 (no cache) = **67% savings**

---

## Configuration Schema

### System Config

```json
{
  "prefix_caching": {
    "enabled": false,
    "stable_prefix_components": ["system_instructions", "tool_schemas"],
    "variable_suffix_components": ["recent_observations", "current_task"],
    "cache_ttl_minutes": 60
  }
}
```

### Agent Override

```json
{
  "agent_id": "fraud_agent",
  "context_requirements": {
    "prefix_caching_eligible": true,
    "stable_context_components": ["system_instructions", "tool_schemas", "fraud_rules"]
  }
}
```

---

## Success Criteria

- [ ] System config has `prefix_caching` section
- [ ] Injector processor separates prefix/suffix
- [ ] Cache control headers added to Anthropic messages
- [ ] LLM client tracks cache metrics
- [ ] Cache hit/miss logged in llm_call events
- [ ] Cost savings calculated and logged
- [ ] Feature disabled by default (backward compatible)
- [ ] Testing with real Anthropic API shows cache hits

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cache invalidation complexity | Use simple hash of agent config + tools |
| Provider API changes | Abstract caching logic, provider-agnostic interface |
| Cost tracking accuracy | Use actual API response metrics, not estimates |
| Cache TTL too long | Default 60 min, configurable per agent |
| Prefix too large | Monitor cache_creation costs, optimize prefix size |

---

## Future Enhancements

- **Cross-session caching**: Cache prefix across sessions (same agent)
- **Semantic caching**: Cache by semantic similarity, not exact match
- **Multi-level caching**: L1 (in-memory), L2 (Redis), L3 (provider)
- **Cache warming**: Pre-cache common agent prefixes on startup
- **Analytics dashboard**: UI showing cache hit rates, cost savings

---

**Phase 7 Complexity**: Medium (provider integration, metrics tracking)

**Estimated Implementation Time**: 6-8 hours

**Dependencies**:
- Real Anthropic API key (for testing)
- LLMClient already integrated (Phase 3 requirement)

**Next Phase**: Phase 8: Advanced Features (proactive memory, deterministic filtering, governance auditing)
