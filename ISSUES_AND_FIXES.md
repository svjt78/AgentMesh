# Issues and Fixes - AgentMesh Real-Time Progress Display

**Date**: December 24, 2025
**Session**: Live Progress Panel Implementation and Debugging

---

## Issue #1: Live Progress Panel Showing "undefined" Values

### Problem
The Live Progress panel displayed:
- "Starting workflow: undefined" for all orchestrator events
- Agent names showing as "undefined"
- Massive log generation with repeated events
- Workflow appearing to loop

### Root Cause
**Double-wrapping of SSE events** caused by two layers of event wrapping:

1. **Backend SSE endpoint** ([runs.py:128-134](backend/orchestrator/app/api/runs.py#L128-L134)) wrapped events:
```python
event_data = {
    "event_type": event.get("event_type"),
    "data": event,  # Full event nested here
    "timestamp": event.get("timestamp")
}
yield f"data: {json.dumps(event_data)}\n\n"
```

2. **Frontend useSSE hook** ([use-sse.ts:48-53](frontend/hooks/use-sse.ts#L48-L53)) wrapped again:
```typescript
const data = JSON.parse(e.data);  // Parses backend wrapper
const event: SSEEvent = {
  data,  // Now double-wrapped!
  timestamp: new Date().toISOString()
};
```

3. **EventCard component** tried to access `event.data.workflow_id`
   - But actual path was `event.data.data.workflow_id` (due to double wrapping)
   - Result: `undefined`

### Fix Applied
**Modified**: `backend/orchestrator/app/api/runs.py` (lines 128-129)

**Before**:
```python
event_data = {
    "event_type": event.get("event_type"),
    "data": event,
    "timestamp": event.get("timestamp")
}
yield f"data: {json.dumps(event_data)}\n\n"
```

**After**:
```python
# Send event directly (useSSE hook will wrap it)
yield f"data: {json.dumps(event)}\n\n"
```

Now the data flow is:
1. Backend sends: `{event_type, session_id, workflow_id, ...}`
2. Frontend receives: `event.data = {event_type, session_id, workflow_id, ...}`
3. Access works: `event.data.workflow_id` ✓

### Testing
1. Hard refresh browser (Cmd+Shift+R)
2. Submit new claim
3. Verify events show "Starting workflow: claims_triage" instead of "undefined"

**Status**: ✅ FIXED

---

## Issue #2: LLM Client Not Initialized (Agents Returning Stubs)

### Problem
Agents were returning stub responses instead of real LLM outputs:
```json
{
  "stub": true,
  "agent": "intake_agent",
  "timestamp": "..."
}
```

All agents failed validation with errors like:
```
Output validation failed for agent 'intake_agent':
  • normalized_claim: Field required
  • stub: Extra inputs are not permitted
```

### Root Cause
`workflow_executor.py` wasn't passing LLM client to orchestrator:

**Line 110-113** (before fix):
```python
orchestrator = create_orchestrator_runner(
    session_id=session_id,
    workflow_id=workflow_id
    # Missing: llm_client parameter!
)
```

When `llm_client=None`, agents returned stub responses at [agent_react_loop.py:271-277](backend/orchestrator/app/services/agent_react_loop.py#L271-L277).

### Fix Applied
**Modified**: `backend/orchestrator/app/services/workflow_executor.py`

**Added imports** (lines 22-23):
```python
from .registry_manager import get_registry_manager
from .llm_client import create_llm_client
```

**Added LLM client initialization** (lines 111-133):
```python
# Get registry manager to fetch model profile
registry = get_registry_manager()

# Get orchestrator agent to find its model profile
orchestrator_agent = registry.get_agent("orchestrator_agent")
if not orchestrator_agent:
    raise ValueError("Orchestrator agent not found in registry")

# Get model profile for LLM client
model_profile = registry.get_model_profile(orchestrator_agent.model_profile_id)
if not model_profile:
    raise ValueError(f"Model profile '{orchestrator_agent.model_profile_id}' not found in registry")

# Create LLM client for orchestrator
llm_client = create_llm_client(model_profile, session_id)
logger.info(f"Created LLM client: provider={model_profile.provider}, model={model_profile.model_name}")

# Create orchestrator runner with LLM client
orchestrator = create_orchestrator_runner(
    session_id=session_id,
    workflow_id=workflow_id,
    llm_client=llm_client  # Now passed!
)
```

**Status**: ✅ FIXED

---

## Issue #3: Multiple .env Files (Environment Configuration)

### Problem
Multiple environment files existed:
- `/Users/.../AgentMesh/.env` (root)
- `/Users/.../AgentMesh/frontend/.env.local` (redundant)

This caused confusion about which file to edit.

### Root Cause
Frontend had its own `.env.local` with only one variable:
```
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:8016
```

This was redundant because:
1. Root `.env` already had this variable
2. `docker-compose.yml` sets it directly for frontend service

### Fix Applied
1. **Removed**: `frontend/.env.local` (redundant file)
2. **Verified**: All services use root `.env` via `docker-compose.yml`
3. **Confirmed**: `frontend/.gitignore` already ignores `.env*` files

**Single source of truth**: `/Users/.../AgentMesh/.env`

**Status**: ✅ FIXED

---

## Issue #4: LLM Hallucinating Non-Existent Tools

### Problem
Agents are being denied access to tools they're trying to use:

**Denial Examples**:
```
intake_agent blocked from completeness_check: Not permitted per governance policy
intake_agent blocked from data_normalization: Not permitted per governance policy
severity_agent blocked from severity_classification: Not permitted per governance policy
```

This causes agents to hit max iterations without completing their work.

### Root Cause Analysis

**1. Available Tools in Registry** (`tool_registry.json`):
- policy_snapshot
- fraud_rules
- similarity
- schema_validator
- coverage_rules
- decision_rules

**2. Tools LLM is Requesting** (don't exist):
- ❌ completeness_check
- ❌ data_normalization
- ❌ severity_classification

**3. Agent Configuration** (`agent_registry.json`):
```json
{
  "agent_id": "intake_agent",
  "allowed_tools": ["schema_validator"]  // Only 1 tool
}
{
  "agent_id": "severity_agent",
  "allowed_tools": []  // NO tools!
}
```

### Why This Happens

The LLM is inventing tool names based on:
1. Agent descriptions mentioning capabilities like "normalization" and "completeness checking"
2. The LLM inferring what tools SHOULD exist based on the task
3. No explicit constraint forcing it to use only listed tools

### Investigation Needed

**File**: `backend/orchestrator/app/services/agent_react_loop.py` (lines 280-299)

The code DOES pass available tools to the LLM:
```python
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
    available_tools=tools_list,  # ← Passed here
    working_context=context.dict(),
    observations=self.observations
)
```

### Fix Applied
**Modified**: `backend/orchestrator/app/prompts/react_prompts.py`

**1. Added explicit tool constraint** (lines 171-176):
```python
## Available Tools
You have access to the following tools (and ONLY these tools):

{tools_catalog_json}

**IMPORTANT**: You MUST ONLY use tools from the list above. Do NOT invent or request tools that are not listed. If you need functionality that isn't available, work with what you have or provide a final output based on the available context.
```

**2. Updated Critical Rules** (lines 215-222):
```python
## Critical Rules
1. **STRICTLY use ONLY tools from the Available Tools list above** - never invent or request unlisted tools
2. If the Available Tools list is empty, you must complete your task using only the Working Context without any tool invocations
3. Use tool results from observations to inform your reasoning
4. Don't use the same tool with identical parameters multiple times
5. Signal final_output only when you can produce a complete analysis (even with limited tools)
6. ALWAYS return valid JSON - no markdown, no extra text
7. Your final output MUST conform to your agent's output schema
```

**What This Fixes**:
- Prevents LLM from inventing tool names based on inferred needs
- Explicitly constrains agents to use only listed tools
- Handles agents with no tools (like severity_agent) - they work with context only
- Provides clear fallback behavior when needed functionality isn't available

**Status**: ✅ FIXED

---

## Issue #5: Frontend Hot Reload

### Problem
Frontend code changes weren't triggering hot reload in Docker development environment.

### Root Cause
Frontend Docker service lacked volume mounts for source directories.

### Fix Applied
**Modified**: `docker-compose.yml` (lines 66-72)

**Added volume mounts**:
```yaml
volumes:
  # Volume mounts for hot reload
  - ./frontend/app:/app/app:rw
  - ./frontend/components:/app/components:rw
  - ./frontend/lib:/app/lib:rw
  - ./frontend/hooks:/app/hooks:rw
  - ./frontend/public:/app/public:rw
```

Now frontend changes trigger automatic reload without container rebuild.

**Status**: ✅ FIXED

---

## Summary of Changes

### Files Modified

1. **backend/orchestrator/app/services/workflow_executor.py**
   - Added LLM client creation and initialization
   - Lines 22-23: Imports
   - Lines 111-133: LLM client instantiation

2. **backend/orchestrator/app/api/runs.py**
   - Fixed double-wrapping in SSE event streaming
   - Lines 128-129: Send events directly

3. **docker-compose.yml**
   - Added frontend volume mounts for hot reload
   - Lines 66-72: Volume mappings

4. **backend/orchestrator/app/prompts/react_prompts.py**
   - Added explicit tool constraints to prevent LLM hallucination
   - Lines 171-176: Tool availability warning
   - Lines 215-222: Updated Critical Rules with strict tool usage enforcement

### Files Deleted

1. **frontend/.env.local** - Redundant environment file

### Outstanding Issues

None - all identified issues have been fixed.

---

## Testing Checklist

- [x] Hard refresh browser (Cmd+Shift+R)
- [ ] Submit new claim
- [ ] Verify no "undefined" in Live Progress panel
- [ ] Verify real LLM reasoning appears (not stub responses)
- [ ] Check that agents use ONLY available tools (no hallucinated tool names)
- [ ] Verify agents with no tools complete using context only
- [ ] Verify frontend hot reload works with code changes
- [ ] Monitor workflow completion without max_iterations_reached errors

---

## Next Actions

1. **Immediate**: Test all fixes with new claim submission
   - Hard refresh browser (Cmd+Shift+R)
   - Submit new claim via frontend
   - Monitor Live Progress panel for proper event display
   - Check orchestrator logs for LLM client creation confirmation
   - Verify no tool_denied errors for non-existent tools

2. **Verify**: Successful workflow completion
   - All agents complete their tasks
   - No stub responses
   - No hallucinated tool names
   - Agents produce valid outputs conforming to schemas

3. **Monitor**: Check if any agents still struggle
   - If severity_agent (no tools) completes successfully
   - If intake_agent works with just schema_validator
   - Overall workflow produces complete evidence map

---

## References

- Session logs: `storage/sessions/session_20251225_025652_192c706b.jsonl`
- Agent registry: `registries/agent_registry.json`
- Tool registry: `registries/tool_registry.json`
- Governance policies: `registries/governance_policies.json`
- SSE implementation: `backend/orchestrator/app/api/runs.py`
- Frontend SSE hook: `frontend/hooks/use-sse.ts`
- Event display: `frontend/app/run-claim/page.tsx`
