# Phase 8 Implementation Plan: Advanced Features

## Overview

Phase 8 adds advanced context engineering capabilities focusing on **intelligent automation**, **governance enforcement**, and **observability**. These features make the context engineering system more autonomous, secure, and auditable.

**Duration**: Weeks 15-16 (estimated)

**Goal**: Implement proactive memory, deterministic filtering, governance auditing, and advanced limits

---

## Feature Categories

### 1. Proactive Memory Preloading
**What**: Automatically retrieve relevant memories before agent execution (vs reactive agent-driven retrieval)

**Why**:
- Reduces agent iteration overhead (no tool calls needed for memory)
- Improves context quality (LLM gets relevant history upfront)
- Enables smarter context compilation

**How**:
- Use semantic similarity search (embeddings) to find relevant memories
- Preload top-K memories based on current task/input
- Add to context before agent invocation

**Benefits**:
- 30-50% reduction in agent iterations for memory-heavy tasks
- Better decision quality (agent sees history without asking)

### 2. Deterministic Context Filtering
**What**: Rule-based pre-processing of context before LLM sees it

**Why**:
- Remove noisy/irrelevant data deterministically
- Enforce security rules (PII filtering, sensitive data masking)
- Reduce token waste on obvious exclusions

**How**:
- Define filtering rules in governance policies
- Apply rules in processor pipeline (before Injector)
- Log all filtering decisions for audit

**Examples**:
- Filter out observations older than 30 days
- Remove debug logs from context
- Mask sensitive fields (SSN, credit cards)

### 3. Governance Auditing
**What**: Comprehensive logging of all context engineering decisions

**Why**:
- Compliance requirements (explain why data was included/excluded)
- Debugging context issues
- Cost attribution (which components consume tokens)

**How**:
- Log every processor decision
- Track context lineage end-to-end
- Generate audit reports

**Logged Events**:
- Context inclusions/exclusions
- Memory retrievals
- Artifact loads
- Filtering decisions
- Token budget enforcement

### 4. Governance Limits Enforcement
**What**: Hard limits on context engineering operations per invocation

**Why**:
- Cost control (prevent runaway memory/artifact loads)
- Performance (bound processing time)
- Security (rate limiting)

**Limits**:
- Max memories per invocation
- Max artifacts per invocation
- Max context compilation time
- Max total tokens per session

---

## Implementation Tasks

### Task 1: Proactive Memory Preloading ✅

**Files to Create/Modify**:
- `backend/orchestrator/app/services/processors/memory_retriever.py` (MODIFY)
- `backend/orchestrator/app/services/memory_manager.py` (MODIFY)
- `registries/system_config.json` (ADD: proactive_memory config)

**Steps**:

1. **Add Proactive Mode to Memory Config** (system_config.json)
```json
{
  "memory": {
    "enabled": false,
    "retrieval_mode": "reactive",  // "reactive" | "proactive"
    "proactive_settings": {
      "enabled": true,
      "max_memories_to_preload": 5,
      "similarity_threshold": 0.7,
      "use_embeddings": true,
      "embedding_model": "text-embedding-ada-002"
    }
  }
}
```

2. **Enhance MemoryManager with Similarity Search**
```python
class MemoryManager:
    def retrieve_memories_by_similarity(
        self,
        query_text: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Memory]:
        """Retrieve memories by semantic similarity to query."""
        # Generate embedding for query
        query_embedding = self._generate_embedding(query_text)

        # Load all memories and compute similarity
        memories = self._load_all_memories()
        scored_memories = []

        for memory in memories:
            memory_embedding = self._get_memory_embedding(memory)
            similarity = self._cosine_similarity(query_embedding, memory_embedding)

            if similarity >= threshold:
                scored_memories.append((memory, similarity))

        # Sort by similarity and return top K
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in scored_memories[:limit]]
```

3. **Enhance MemoryRetriever Processor for Proactive Mode**
```python
class MemoryRetriever(BaseProcessor):
    def process(self, context, agent_id, session_id):
        memory_config = self._load_memory_config()

        if memory_config.get("retrieval_mode") == "proactive":
            # Proactive: Auto-retrieve based on context
            query_text = self._build_query_from_context(context)

            memories = self.memory_manager.retrieve_memories_by_similarity(
                query_text=query_text,
                limit=memory_config["proactive_settings"]["max_memories_to_preload"],
                threshold=memory_config["proactive_settings"]["similarity_threshold"]
            )

            context["preloaded_memories"] = memories
            logger.info(f"Proactive memory: loaded {len(memories)} memories")

        return context
```

**Testing**:
- Enable proactive mode in system_config.json
- Submit workflow with memories in storage
- Verify memories auto-loaded in context_compiled events

---

### Task 2: Deterministic Context Filtering ✅

**Files to Create/Modify**:
- `backend/orchestrator/app/services/processors/content_filter.py` (NEW)
- `registries/governance_policies.json` (ADD: filtering_rules)

**Steps**:

1. **Add Filtering Rules to Governance Policies**
```json
{
  "policies": {
    "context_filtering": {
      "enabled": true,
      "rules": [
        {
          "rule_id": "filter_old_observations",
          "description": "Remove observations older than 30 days",
          "field": "observations",
          "condition": {
            "type": "age_threshold",
            "max_age_days": 30
          }
        },
        {
          "rule_id": "mask_pii",
          "description": "Mask SSN and credit card numbers",
          "field": "original_input",
          "condition": {
            "type": "regex_mask",
            "patterns": [
              {"pattern": "\\d{3}-\\d{2}-\\d{4}", "replacement": "***-**-****"},
              {"pattern": "\\d{4}-\\d{4}-\\d{4}-\\d{4}", "replacement": "****-****-****-****"}
            ]
          }
        },
        {
          "rule_id": "remove_debug_logs",
          "description": "Filter out debug-level log observations",
          "field": "observations",
          "condition": {
            "type": "field_value_match",
            "match_field": "log_level",
            "match_value": "debug"
          }
        }
      ]
    }
  }
}
```

2. **Create ContentFilter Processor**
```python
class ContentFilterProcessor(BaseProcessor):
    """
    Deterministic content filtering based on governance rules.

    Applies pre-LLM filtering to remove noise, mask PII, enforce security.
    """

    def process(self, context, agent_id, session_id):
        filtering_rules = self._load_filtering_rules()

        if not filtering_rules.get("enabled"):
            return context

        filtered_context = context.copy()
        filtering_log = []

        for rule in filtering_rules["rules"]:
            result = self._apply_rule(rule, filtered_context)

            if result["modified"]:
                filtering_log.append({
                    "rule_id": rule["rule_id"],
                    "field": rule["field"],
                    "items_filtered": result["items_filtered"],
                    "description": rule["description"]
                })

        # Log filtering decisions
        if filtering_log:
            self._log_filtering_event(session_id, filtering_log)

        filtered_context["metadata"]["filtering_applied"] = True
        filtered_context["metadata"]["filtering_log"] = filtering_log

        return filtered_context

    def _apply_rule(self, rule, context):
        """Apply a single filtering rule to context."""
        condition_type = rule["condition"]["type"]

        if condition_type == "age_threshold":
            return self._filter_by_age(rule, context)
        elif condition_type == "regex_mask":
            return self._mask_by_regex(rule, context)
        elif condition_type == "field_value_match":
            return self._filter_by_field_match(rule, context)

        return {"modified": False, "items_filtered": 0}
```

3. **Add to Processor Pipeline**
```json
{
  "processors": [
    {"processor_id": "content_selector", "enabled": true, "order": 1},
    {"processor_id": "content_filter", "enabled": true, "order": 2},
    {"processor_id": "compaction_checker", "enabled": true, "order": 3},
    {"processor_id": "memory_retriever", "enabled": false, "order": 4},
    {"processor_id": "artifact_resolver", "enabled": true, "order": 5},
    {"processor_id": "transformer", "enabled": true, "order": 6},
    {"processor_id": "token_budget_enforcer", "enabled": true, "order": 7},
    {"processor_id": "injector", "enabled": true, "order": 8}
  ]
}
```

**Testing**:
- Add filtering rules to governance_policies.json
- Submit claim with PII (SSN, credit card)
- Verify masked in context, logged in filtering_applied event

---

### Task 3: Governance Auditing ✅

**Files to Create/Modify**:
- `backend/orchestrator/app/services/governance_auditor.py` (NEW)
- `backend/orchestrator/app/services/processors/base_processor.py` (MODIFY)

**Steps**:

1. **Create GovernanceAuditor Service**
```python
class GovernanceAuditor:
    """
    Centralized governance auditing for all context engineering decisions.

    Logs every context decision for compliance and debugging.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.storage = get_session_writer()

    def log_context_decision(
        self,
        decision_type: str,
        component: str,
        action: str,
        rationale: str,
        metadata: Dict[str, Any]
    ):
        """Log a context engineering decision."""
        event = {
            "event_type": "governance_audit",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision_type": decision_type,  # "inclusion", "exclusion", "filtering", "limiting"
            "component": component,  # "memory", "artifact", "observation", "prior_output"
            "action": action,  # "included", "excluded", "masked", "truncated"
            "rationale": rationale,
            "metadata": metadata
        }

        self.storage.write_event(self.session_id, event)

    def log_token_budget_decision(self, budget_decision: Dict):
        """Log token budget enforcement decision."""
        self.log_context_decision(
            decision_type="token_budget",
            component=budget_decision["component"],
            action=budget_decision["action"],
            rationale=budget_decision["reason"],
            metadata=budget_decision
        )

    def log_memory_retrieval(self, memories: List[Memory], query: str, mode: str):
        """Log memory retrieval decision."""
        self.log_context_decision(
            decision_type="memory_retrieval",
            component="memory",
            action=f"retrieved_{len(memories)}",
            rationale=f"Query: {query}, Mode: {mode}",
            metadata={
                "memory_count": len(memories),
                "memory_ids": [m.memory_id for m in memories],
                "retrieval_mode": mode
            }
        )
```

2. **Enhance BaseProcessor to Use Auditor**
```python
class BaseProcessor(ABC):
    def __init__(self, config: Dict[str, Any], session_id: str = None):
        self.config = config
        self.session_id = session_id
        self.auditor = GovernanceAuditor(session_id) if session_id else None

    def _audit_decision(self, decision_type, component, action, rationale, metadata=None):
        """Convenience method for auditing from processors."""
        if self.auditor:
            self.auditor.log_context_decision(
                decision_type, component, action, rationale, metadata or {}
            )
```

3. **Update Processors to Audit Decisions**

Example in TokenBudgetEnforcer:
```python
class TokenBudgetEnforcer(BaseProcessor):
    def process(self, context, agent_id, session_id):
        # ... truncation logic ...

        if truncated:
            self._audit_decision(
                decision_type="token_budget",
                component="prior_outputs",
                action="truncated",
                rationale=f"Exceeded max_tokens ({max_tokens}), truncated to fit",
                metadata={
                    "tokens_before": tokens_before,
                    "tokens_after": tokens_after,
                    "truncation_strategy": "prioritize_recent"
                }
            )
```

**Testing**:
- Run workflow with auditing enabled
- Check for governance_audit events in session JSONL
- Verify all decisions logged

---

### Task 4: Governance Limits Enforcement ✅

**Files to Create/Modify**:
- `backend/orchestrator/app/services/governance_enforcer.py` (MODIFY)
- `registries/governance_policies.json` (ADD: context_governance limits)

**Steps**:

1. **Add Limits to Governance Policies** (already exists from plan, but verify)
```json
{
  "policies": {
    "context_governance": {
      "max_context_tokens_per_agent": 10000,
      "max_memory_retrievals_per_invocation": 10,
      "max_artifact_loads_per_invocation": 5,
      "max_context_compilation_time_ms": 5000,
      "context_auditing": {
        "log_all_compilations": true,
        "log_truncations": true,
        "log_compactions": true
      }
    }
  }
}
```

2. **Enhance MemoryRetriever to Enforce Limits**
```python
class MemoryRetriever(BaseProcessor):
    def process(self, context, agent_id, session_id):
        governance_limits = self._load_governance_limits()
        max_memories = governance_limits.get("max_memory_retrievals_per_invocation", 10)

        # Get memories (reactive or proactive)
        memories = self._retrieve_memories(context, agent_id)

        # Enforce limit
        if len(memories) > max_memories:
            logger.warning(
                f"Memory limit exceeded: {len(memories)} > {max_memories}, truncating"
            )
            memories = memories[:max_memories]

            self._audit_decision(
                decision_type="limiting",
                component="memory",
                action="truncated",
                rationale=f"Exceeded max_memory_retrievals_per_invocation ({max_memories})",
                metadata={
                    "requested": len(memories),
                    "allowed": max_memories
                }
            )

        context["memories"] = memories
        return context
```

3. **Enhance ArtifactResolver to Enforce Limits**
```python
class ArtifactResolver(BaseProcessor):
    def process(self, context, agent_id, session_id):
        governance_limits = self._load_governance_limits()
        max_artifacts = governance_limits.get("max_artifact_loads_per_invocation", 5)

        artifact_handles = self._extract_artifact_handles(context)

        # Enforce limit
        if len(artifact_handles) > max_artifacts:
            logger.warning(
                f"Artifact limit exceeded: {len(artifact_handles)} > {max_artifacts}"
            )
            artifact_handles = artifact_handles[:max_artifacts]

            self._audit_decision(
                decision_type="limiting",
                component="artifact",
                action="truncated",
                rationale=f"Exceeded max_artifact_loads_per_invocation ({max_artifacts})",
                metadata={
                    "requested": len(artifact_handles),
                    "allowed": max_artifacts
                }
            )

        # Load artifacts
        artifacts = [self._load_artifact(h) for h in artifact_handles]
        context["artifacts"] = artifacts

        return context
```

4. **Add Compilation Time Limit to ContextProcessorPipeline**
```python
class ContextProcessorPipeline:
    def execute(self, raw_context, agent_id):
        governance_limits = self._load_governance_limits()
        max_time_ms = governance_limits.get("max_context_compilation_time_ms", 5000)

        start_time = time.time()

        # Execute processors
        context = raw_context
        for processor in self.processors:
            context = processor.process(context, agent_id, self.session_id)

            # Check time limit
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > max_time_ms:
                logger.error(
                    f"Context compilation timeout: {elapsed_ms}ms > {max_time_ms}ms"
                )
                raise TimeoutError(
                    f"Context compilation exceeded time limit ({max_time_ms}ms)"
                )

        return context
```

**Testing**:
- Set low limits (e.g., max_memories=2)
- Submit workflow requesting many memories
- Verify limit enforced, audit event logged

---

## Event Schema Extensions

### New Event: `governance_audit`
```json
{
  "event_type": "governance_audit",
  "session_id": "session_xyz",
  "timestamp": "2026-01-02T18:00:00Z",
  "decision_type": "token_budget",
  "component": "prior_outputs",
  "action": "truncated",
  "rationale": "Exceeded max_tokens (5000), truncated to fit",
  "metadata": {
    "tokens_before": 7000,
    "tokens_after": 5000,
    "truncation_strategy": "prioritize_recent"
  }
}
```

### New Event: `content_filtered`
```json
{
  "event_type": "content_filtered",
  "session_id": "session_xyz",
  "timestamp": "2026-01-02T18:00:00Z",
  "filtering_log": [
    {
      "rule_id": "mask_pii",
      "field": "original_input",
      "items_filtered": 2,
      "description": "Mask SSN and credit card numbers"
    }
  ]
}
```

### New Event: `memory_preloaded`
```json
{
  "event_type": "memory_preloaded",
  "session_id": "session_xyz",
  "timestamp": "2026-01-02T18:00:00Z",
  "retrieval_mode": "proactive",
  "query": "claim processing for auto insurance",
  "memories_found": 3,
  "memory_ids": ["mem_001", "mem_002", "mem_003"],
  "similarity_scores": [0.92, 0.87, 0.81]
}
```

---

## Configuration Changes

### system_config.json Additions

```json
{
  "memory": {
    "enabled": false,
    "retrieval_mode": "reactive",
    "proactive_settings": {
      "enabled": true,
      "max_memories_to_preload": 5,
      "similarity_threshold": 0.7,
      "use_embeddings": true,
      "embedding_model": "text-embedding-ada-002"
    }
  }
}
```

### governance_policies.json Additions

```json
{
  "policies": {
    "context_filtering": {
      "enabled": false,
      "rules": []
    },
    "context_governance": {
      "max_context_tokens_per_agent": 10000,
      "max_memory_retrievals_per_invocation": 10,
      "max_artifact_loads_per_invocation": 5,
      "max_context_compilation_time_ms": 5000,
      "context_auditing": {
        "log_all_compilations": true,
        "log_truncations": true,
        "log_compactions": true,
        "log_filtering": true
      }
    }
  }
}
```

---

## Success Criteria

- [ ] Proactive memory preloading works (embeddings-based similarity)
- [ ] Deterministic filtering rules apply (PII masking, age filtering)
- [ ] All context decisions logged in governance_audit events
- [ ] Governance limits enforced (memories, artifacts, compilation time)
- [ ] Audit events queryable for compliance reports
- [ ] Feature flags allow disabling each feature independently
- [ ] Zero overhead when features disabled

---

## Testing Strategy

### Unit Tests
- Test each filtering rule in isolation
- Test memory similarity scoring
- Test governance limit enforcement

### Integration Tests
- End-to-end workflow with proactive memory
- Workflow with PII in input (verify masking)
- Workflow exceeding governance limits (verify truncation)

### Compliance Tests
- Generate audit report from governance_audit events
- Verify all context decisions logged
- Test filtering compliance (PII never in LLM prompt)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Embedding generation slow | Cache embeddings, use async generation |
| Filtering rules too complex | Start with simple rules, iterate |
| Audit event volume high | Use log rotation, archive to external storage |
| Governance limits too strict | Make configurable per agent, monitor rejections |

---

## Phase 8 Deliverables

1. **Proactive Memory**: MemoryManager similarity search, MemoryRetriever proactive mode
2. **Content Filtering**: ContentFilterProcessor with rule engine
3. **Governance Auditing**: GovernanceAuditor service, audit events in all processors
4. **Governance Limits**: Enforcement in MemoryRetriever, ArtifactResolver, ContextProcessorPipeline
5. **Documentation**: PHASE8_IMPLEMENTATION_PLAN.md, CONTEXT_ENGINEERING_PHASE8_PROGRESS.md
6. **Configuration**: Updated system_config.json, governance_policies.json

---

**Status**: Ready for implementation

**Next Steps**: Start with Task 1 (Proactive Memory Preloading)
