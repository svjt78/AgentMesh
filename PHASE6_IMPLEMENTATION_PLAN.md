# Phase 6: Multi-Agent Context Controls - Implementation Plan

**Phase**: Multi-Agent Context Controls
**Status**: 🚧 IN PROGRESS
**Start Date**: January 2, 2026

---

## Overview

Phase 6 implements fine-grained control over context sharing between agents during handoffs. This enables:
- **Security**: Limit what each agent can see from other agents
- **Efficiency**: Reduce token usage by sharing only relevant context
- **Privacy**: Control sensitive data flow between agents
- **Flexibility**: Different handoff modes for different agent pairs

---

## Core Concepts

### 1. Handoff Modes

**Full Mode**:
- Complete context passed to receiving agent
- Includes all prior outputs, observations, original input
- Use case: Trusted agent relationships, comprehensive analysis needed

**Scoped Mode**:
- Only specific fields/outputs passed to receiving agent
- Configured per agent-pair in governance policies
- Use case: Security-sensitive handoffs, need-to-know principle

**Minimal Mode**:
- Only essential metadata and trigger passed
- Receiving agent starts with minimal context
- Use case: Independent analysis, privacy-critical handoffs

### 2. Context Scoping

Control what context components are shared:
- **Original Input**: Full input vs filtered fields
- **Prior Outputs**: All agent outputs vs specific agent outputs vs none
- **Observations**: Tool results vs filtered observations
- **Agent Identity**: Show/hide which agents processed before

### 3. Conversation Translation

Recast agent outputs into different formats:
- **Summarization**: Condense verbose outputs for downstream agents
- **Field Extraction**: Pull only specific fields from structured outputs
- **Role Translation**: Present agent outputs in different roles (e.g., system vs user)
- **Filtering**: Remove sensitive fields before passing to next agent

### 4. Governance Rules

Policy-based control over handoffs:
- Per agent-pair rules (fraud_agent → recommendation_agent)
- Default handoff policies
- Allowed fields whitelist/blacklist
- Audit logging of context sharing decisions

---

## Implementation Tasks

### Task 1: Enhance Agent Registry Schema ✅

**File**: `registries/agent_registry.json`

**Changes**: Add `context_requirements` fields for each agent:

```json
"context_requirements": {
  "requires_prior_outputs": ["intake", "coverage"],
  "max_context_tokens": 5000,

  // NEW FIELDS
  "context_scope": "scoped",  // "full" | "scoped" | "minimal"
  "handoff_mode": "scoped",   // Default for this agent receiving handoffs
  "conversation_translation": {
    "enabled": true,
    "recast_agent_outputs": true,
    "summarize_prior_outputs": false
  },
  "allowed_context_fields": [
    "fraud_score",
    "triggered_indicators",
    "recommendation"
  ],
  "blocked_context_fields": [
    "internal_notes",
    "investigator_comments"
  ]
}
```

---

### Task 2: Add Handoff Governance Policies

**File**: `registries/governance_policies.json`

**Changes**: Add new `multi_agent_handoffs` section:

```json
"multi_agent_handoffs": {
  "default_handoff_mode": "scoped",
  "enable_conversation_translation": true,
  "audit_all_handoffs": true,

  "agent_handoff_rules": [
    {
      "from_agent_id": "fraud_agent",
      "to_agent_id": "recommendation_agent",
      "handoff_mode": "scoped",
      "allowed_context_fields": [
        "fraud_score",
        "fraud_indicators",
        "risk_level"
      ],
      "conversation_translation": {
        "summarize": true,
        "max_tokens": 500
      }
    },
    {
      "from_agent_id": "intake_agent",
      "to_agent_id": "*",
      "handoff_mode": "full",
      "note": "Intake agent output is safe to share widely"
    }
  ]
}
```

---

### Task 3: Implement ContextScoper Service

**File**: `backend/orchestrator/app/services/context_scoper.py` (NEW)

**Purpose**: Apply scoping rules to context before passing between agents

**Key Methods**:

```python
class ContextScoper:
    def scope_context_for_handoff(
        self,
        context: CompiledContext,
        from_agent_id: str,
        to_agent_id: str,
        handoff_mode: str
    ) -> CompiledContext:
        """Apply scoping rules based on handoff mode."""

    def apply_full_mode(self, context: CompiledContext) -> CompiledContext:
        """Pass all context (no filtering)."""

    def apply_scoped_mode(
        self,
        context: CompiledContext,
        allowed_fields: List[str]
    ) -> CompiledContext:
        """Filter context to allowed fields only."""

    def apply_minimal_mode(self, context: CompiledContext) -> CompiledContext:
        """Pass only essential trigger information."""

    def get_handoff_rules(
        self,
        from_agent_id: str,
        to_agent_id: str
    ) -> HandoffRule:
        """Retrieve handoff rules from governance policies."""
```

**Logic Flow**:
1. Get handoff rules for agent pair
2. Determine handoff mode (policy override > receiving agent default > system default)
3. Apply scoping based on mode
4. Log scoping decision for audit

---

### Task 4: Implement ConversationTranslator Service

**File**: `backend/orchestrator/app/services/conversation_translator.py` (NEW)

**Purpose**: Transform agent outputs for downstream consumption

**Key Methods**:

```python
class ConversationTranslator:
    def translate_output(
        self,
        output: Dict[str, Any],
        from_agent_id: str,
        to_agent_id: str,
        translation_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate agent output based on config."""

    def summarize_output(
        self,
        output: Dict[str, Any],
        max_tokens: int
    ) -> str:
        """Summarize agent output to fit token budget."""

    def extract_fields(
        self,
        output: Dict[str, Any],
        fields: List[str]
    ) -> Dict[str, Any]:
        """Extract only specified fields from output."""

    def recast_role(
        self,
        output: Dict[str, Any],
        target_role: str
    ) -> Dict[str, Any]:
        """Recast output in different message role."""
```

**Translation Strategies**:
- **Field Extraction**: Pull specific fields from structured output
- **Summarization**: Use LLM to condense verbose outputs (optional)
- **Role Recasting**: Change message role (user → system, etc.)
- **Filtering**: Remove blocked fields

---

### Task 5: Enhance ContextCompiler for Scoping

**File**: `backend/orchestrator/app/services/context_compiler.py` (MODIFY)

**Changes**:

```python
class ContextCompiler:
    def __init__(self, session_id: Optional[str] = None):
        # ... existing code ...
        self.context_scoper = ContextScoper()
        self.conversation_translator = ConversationTranslator()

    def compile_for_agent(
        self,
        agent_id: str,
        original_input: Dict,
        prior_outputs: Dict,
        observations: List,
        from_agent_id: Optional[str] = None  # NEW: Track handoff source
    ) -> CompiledContext:
        """Compile context with handoff scoping."""

        # Apply scoping if this is a handoff
        if from_agent_id:
            scoped_context = self._apply_handoff_scoping(
                agent_id=agent_id,
                from_agent_id=from_agent_id,
                prior_outputs=prior_outputs,
                observations=observations
            )
        else:
            # First agent, no scoping needed
            scoped_context = {
                "prior_outputs": prior_outputs,
                "observations": observations
            }

        # Continue with normal compilation...

    def _apply_handoff_scoping(
        self,
        agent_id: str,
        from_agent_id: str,
        prior_outputs: Dict,
        observations: List
    ) -> Dict:
        """Apply handoff scoping rules."""

        # Get handoff rules
        handoff_rules = self.context_scoper.get_handoff_rules(
            from_agent_id, agent_id
        )

        # Apply scoping
        scoped_prior_outputs = self.context_scoper.scope_outputs(
            prior_outputs, handoff_rules
        )

        # Apply conversation translation if enabled
        if handoff_rules.get("conversation_translation", {}).get("enabled"):
            scoped_prior_outputs = self.conversation_translator.translate_outputs(
                scoped_prior_outputs, handoff_rules
            )

        return {
            "prior_outputs": scoped_prior_outputs,
            "observations": observations  # TODO: Add observation scoping
        }
```

---

### Task 6: Add Handoff Event Tracking

**File**: `backend/orchestrator/app/services/storage.py` (MODIFY)

**New Event Type**: `context_handoff`

```json
{
  "event_type": "context_handoff",
  "session_id": "session_xyz",
  "from_agent_id": "fraud_agent",
  "to_agent_id": "recommendation_agent",
  "handoff_mode": "scoped",
  "context_before_scoping": {
    "prior_outputs_count": 3,
    "total_tokens": 5000
  },
  "context_after_scoping": {
    "prior_outputs_count": 1,
    "total_tokens": 1200,
    "fields_included": ["fraud_score", "risk_level"],
    "fields_excluded": ["internal_notes"]
  },
  "conversation_translation_applied": true,
  "governance_rule_id": "fraud_to_recommendation_scoped",
  "timestamp": "2026-01-02T12:00:00Z"
}
```

---

### Task 7: Update OrchestratorRunner for Handoffs

**File**: `backend/orchestrator/app/services/orchestrator_runner.py` (MODIFY)

**Changes**: Track agent handoffs and pass source agent ID

```python
class OrchestratorRunner:
    def _invoke_agent(self, agent_id: str, task: str) -> Dict:
        # ... existing code ...

        # NEW: Track last agent for handoff scoping
        from_agent_id = self.last_invoked_agent_id

        # Compile context with handoff awareness
        compiled_context = self.context_compiler.compile_for_agent(
            agent_id=agent_id,
            original_input=self.original_input,
            prior_outputs=self.agent_outputs,
            observations=[],
            from_agent_id=from_agent_id  # NEW
        )

        # Update last invoked agent
        self.last_invoked_agent_id = agent_id

        # ... rest of invocation ...
```

---

### Task 8: API Endpoints for Handoff Configuration

**File**: `backend/orchestrator/app/api/governance.py` (NEW)

**Endpoints**:

```python
@router.get("/governance/handoff-rules")
async def get_handoff_rules():
    """Get all handoff rules."""

@router.get("/governance/handoff-rules/{from_agent}/{to_agent}")
async def get_specific_handoff_rule(from_agent: str, to_agent: str):
    """Get handoff rule for specific agent pair."""

@router.put("/governance/handoff-rules")
async def update_handoff_rules(rules: List[HandoffRule]):
    """Update handoff governance rules."""
```

---

## Implementation Order

### Step 1: Foundation (Day 1)
1. ✅ Create implementation plan (this document)
2. Update agent registry schema
3. Add handoff governance policies
4. Create data models (HandoffRule, HandoffMode enums)

### Step 2: Core Services (Day 1-2)
5. Implement ContextScoper service
6. Implement ConversationTranslator service
7. Add handoff event tracking

### Step 3: Integration (Day 2)
8. Enhance ContextCompiler with scoping
9. Update OrchestratorRunner for handoff tracking
10. Add API endpoints

### Step 4: Testing (Day 2-3)
11. Test full mode handoffs
12. Test scoped mode handoffs
13. Test minimal mode handoffs
14. Test conversation translation
15. Verify governance enforcement

### Step 5: Documentation (Day 3)
16. Document Phase 6 implementation
17. Create testing guide
18. Update overall progress

---

## Data Models

### HandoffRule

```python
class HandoffMode(str, Enum):
    FULL = "full"
    SCOPED = "scoped"
    MINIMAL = "minimal"

class HandoffRule(BaseModel):
    from_agent_id: str
    to_agent_id: str  # "*" for wildcard
    handoff_mode: HandoffMode
    allowed_context_fields: Optional[List[str]] = None
    blocked_context_fields: Optional[List[str]] = None
    conversation_translation: Optional[Dict[str, Any]] = None
    audit_enabled: bool = True
```

### ContextHandoffEvent

```python
class ContextHandoffEvent(BaseModel):
    event_type: Literal["context_handoff"]
    session_id: str
    from_agent_id: str
    to_agent_id: str
    handoff_mode: HandoffMode
    context_before_scoping: Dict[str, Any]
    context_after_scoping: Dict[str, Any]
    conversation_translation_applied: bool
    governance_rule_id: Optional[str]
    timestamp: str
```

---

## Testing Strategy

### Test Scenarios

**Scenario 1: Full Mode Handoff**
- fraud_agent → coverage_agent (trusted relationship)
- All context passed
- No filtering applied
- Verify: Receiving agent sees all prior outputs

**Scenario 2: Scoped Mode Handoff**
- fraud_agent → recommendation_agent
- Only fraud_score, risk_level passed
- internal_notes filtered out
- Verify: Receiving agent only sees allowed fields

**Scenario 3: Minimal Mode Handoff**
- sensitive_agent → external_agent
- Only trigger and essential metadata
- No prior outputs shared
- Verify: Receiving agent starts fresh

**Scenario 4: Conversation Translation**
- Verbose agent → downstream agent
- Output summarized to 500 tokens
- Role recast to system message
- Verify: Output condensed and reformatted

**Scenario 5: Governance Enforcement**
- Attempt to pass blocked fields
- Verify: Blocked fields removed
- Verify: Handoff event logged with audit trail

---

## Success Criteria

- [ ] Context scoping logic implemented
- [ ] Handoff modes (full/scoped/minimal) functional
- [ ] Conversation translation working
- [ ] Governance rules enforced
- [ ] Handoff events logged for audit
- [ ] API endpoints for handoff configuration
- [ ] All test scenarios passing
- [ ] Documentation complete

---

## Integration with Previous Phases

### Phase 1 (Foundation)
- Handoff scoping uses processor pipeline
- Scoping applied as early-stage processor

### Phase 3 (Memory Layer)
- Memory retrieval respects handoff scoping
- Memories tagged with agent accessibility

### Phase 5 (Observability)
- Handoff events tracked in lineage
- Token savings from scoping visible in metrics

---

## Risk Mitigation

**Risk**: Over-scoping removes critical context
**Mitigation**: Default to "full" mode, require explicit scoping rules

**Risk**: Conversation translation loses information
**Mitigation**: Log original output, make translation optional

**Risk**: Performance overhead from scoping logic
**Mitigation**: Cache handoff rules, optimize field filtering

**Risk**: Governance rule conflicts
**Mitigation**: Clear precedence order (specific > default > agent config)

---

**Status**: 🚧 Implementation starting
**Next Step**: Update agent registry schema
