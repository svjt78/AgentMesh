# Phase 5: Observability & Lineage - Testing Guide

## Test Environment Setup

### 1. Enable Context Engineering

Edit `registries/system_config.json`:
```json
{
  "context_engineering": {
    "enabled": true,
    "processor_pipeline_enabled": true
  },
  "compaction": {
    "enabled": false
  },
  "memory": {
    "enabled": false
  },
  "artifacts": {
    "versioning_enabled": false
  }
}
```

### 2. Start Services

```bash
# Start all services
docker compose up

# Or run locally
# Terminal 1: Backend
cd backend/orchestrator
STORAGE_PATH=../../storage TOOLS_BASE_URL=http://localhost:8010 \
  python -m uvicorn app.main:app --reload --port 8016

# Terminal 2: Tools Gateway
cd tools/tools_gateway
python -m uvicorn app.main:app --reload --port 8010

# Terminal 3: Frontend
cd frontend
npm run dev
```

---

## Test 1: Submit Workflow and Verify Lineage Tracking

### Submit a test claim:
```bash
curl -X POST "http://localhost:8016/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "claims_triage",
    "input_data": {
      "claim_id": "CLM-TEST-001",
      "policy_id": "POL-12345",
      "claim_amount": 5000,
      "claim_date": "2026-01-02",
      "incident_description": "Minor vehicle damage",
      "claimant_id": "CUST-789"
    }
  }'
```

### Expected Response:
```json
{
  "session_id": "session_20260102_...",
  "workflow_id": "claims_triage",
  "status": "running",
  "stream_url": "http://localhost:8016/runs/{session_id}/stream"
}
```

### Wait for workflow to complete, then verify lineage file:
```bash
# Replace {session_id} with actual session ID
SESSION_ID="session_20260102_..."

# Check if lineage file exists
ls storage/sessions/${SESSION_ID}_context_lineage.jsonl

# View lineage file (should have one line per compilation)
cat storage/sessions/${SESSION_ID}_context_lineage.jsonl | jq
```

### Expected Output:
- File exists in `storage/sessions/`
- Contains JSONL lines (one per context compilation)
- Each line has: compilation_id, agent_id, tokens_before, tokens_after, processors_executed, etc.

---

## Test 2: Query Lineage API Endpoints

### Test 2.1: Get All Compilations
```bash
curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage" | jq
```

**Expected Response**:
```json
{
  "session_id": "session_...",
  "compilations": [
    {
      "compilation_id": "ctx_compile_...",
      "agent_id": "intake_agent",
      "timestamp": "2026-01-02T12:00:00Z",
      "tokens_before": 1500,
      "tokens_after": 1500,
      "components_before": {...},
      "components_after": {...},
      "processors_executed": [
        {
          "processor_id": "content_selector",
          "execution_time_ms": 2.5,
          "success": true,
          "modifications_made": {...}
        },
        ...
      ],
      "truncation_applied": false,
      "compaction_applied": false,
      "budget_allocation": {...},
      "budget_exceeded": false,
      "budget_utilization_percent": 18.75
    },
    ...
  ],
  "total_count": 5
}
```

### Test 2.2: Get Compilation Statistics
```bash
curl "http://localhost:8016/sessions/${SESSION_ID}/context-stats" | jq
```

**Expected Response**:
```json
{
  "session_id": "session_...",
  "total_compilations": 5,
  "agents": ["intake_agent", "fraud_agent", "coverage_agent", ...],
  "total_processors_executed": 35,
  "total_execution_time_ms": 125.5,
  "avg_tokens_before": 2500,
  "avg_tokens_after": 2400,
  "truncations": 0,
  "compactions": 0,
  "memories_retrieved": 0,
  "artifacts_resolved": 0,
  "timestamp": "2026-01-02T12:05:00Z"
}
```

### Test 2.3: Get Token Budget Timeline
```bash
curl "http://localhost:8016/sessions/${SESSION_ID}/token-budget-timeline" | jq
```

**Expected Response**:
```json
{
  "session_id": "session_...",
  "timeline": [
    {
      "compilation_id": "ctx_compile_001",
      "agent_id": "intake_agent",
      "timestamp": "2026-01-02T12:00:00Z",
      "tokens_before": 1500,
      "tokens_after": 1500,
      "budget_exceeded": false,
      "truncation_applied": false,
      "compaction_applied": false
    },
    ...
  ],
  "timestamp": "2026-01-02T12:05:00Z"
}
```

### Test 2.4: Get Specific Compilation Details
```bash
# Get compilation ID from previous query
COMPILATION_ID="ctx_compile_..."

curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage/${COMPILATION_ID}" | jq
```

**Expected Response**: Full ContextCompilation object with all details

---

## Test 3: Frontend Visualization Testing

### 3.1: Navigate to Replay Page
1. Open browser to `http://localhost:3016`
2. Navigate to session replay (or go directly to `http://localhost:3016/replay/{session_id}`)
3. Verify session summary shows correctly

### 3.2: Test Context Engineering Tab
1. Click "Context Engineering" tab
2. Verify three sections appear:
   - Context Compilation Timeline
   - Token Budget Analysis
   - Context Compilation Lineage

### 3.3: Test ContextTimeline Component
**Expected Behavior**:
- Shows all compilations in chronological order
- Each compilation shows:
  - Agent ID
  - Timestamp
  - Tokens before → after
  - Status badge (Normal/Truncated/Over Budget/Compacted)
  - Token reduction amount
  - Visual bar showing token utilization

**Verify**:
- Color coding: Green (normal), Yellow (truncated), Orange (over budget), Red (compacted)
- Token bar fills proportionally to utilization percentage
- Hover shows full details

### 3.4: Test TokenBudgetChart Component
**Expected Behavior**:
- Shows one card per compilation
- Stacked horizontal bar with three colors:
  - Blue: Original Input
  - Green: Prior Outputs
  - Purple: Observations
- Component breakdown shows token count and percentage
- Budget allocation percentages shown at bottom

**Verify**:
- Stacked bar adds up to 100% width
- Token counts shown in each bar segment (if > 0)
- Component cards show correct token counts
- Percentages add up to 100%

### 3.5: Test ContextLineageTree Component
**Expected Behavior**:
- Shows all compilations in collapsed state
- Click to expand shows processor pipeline
- Each processor shows:
  - Execution order number
  - Processor ID
  - Execution time
  - Success/failure status
  - Modifications made (if any)

**Verify**:
- Click toggles expand/collapse
- Green border for successful processors
- Red border for failed processors
- Modifications displayed in readable format
- Execution times shown in milliseconds

---

## Test 4: Verify Processor Execution Logging

### Check processor execution details:
```bash
# Get lineage for session
curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage" | jq '.compilations[0].processors_executed'
```

**Expected Output**:
```json
[
  {
    "processor_id": "content_selector",
    "execution_time_ms": 2.5,
    "success": true,
    "modifications_made": {
      "status": "content_selected"
    },
    "error": null
  },
  {
    "processor_id": "compaction_checker",
    "execution_time_ms": 1.2,
    "success": true,
    "modifications_made": {
      "compaction_needed": false
    },
    "error": null
  },
  {
    "processor_id": "memory_retriever",
    "execution_time_ms": 0.8,
    "success": true,
    "modifications_made": {
      "status": "memory_layer_disabled"
    },
    "error": null
  },
  {
    "processor_id": "artifact_resolver",
    "execution_time_ms": 0.5,
    "success": true,
    "modifications_made": {
      "status": "artifact_versioning_disabled"
    },
    "error": null
  },
  {
    "processor_id": "transformer",
    "execution_time_ms": 15.3,
    "success": true,
    "modifications_made": {
      "messages_created": 3
    },
    "error": null
  },
  {
    "processor_id": "token_budget_enforcer",
    "execution_time_ms": 5.1,
    "success": true,
    "modifications_made": {
      "budget_enforced": true,
      "truncation_applied": false
    },
    "error": null
  },
  {
    "processor_id": "injector",
    "execution_time_ms": 1.5,
    "success": true,
    "modifications_made": {
      "compiled_context_created": true
    },
    "error": null
  }
]
```

**Verify**:
- All enabled processors appear
- Execution times are reasonable (< 100ms for most)
- All show success: true (if workflow completed successfully)
- modifications_made contains relevant data

---

## Test 5: Token Budget Analysis

### Verify token tracking is accurate:
```bash
# Get a compilation with component breakdown
curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage" | jq '.compilations[0] | {
  agent_id,
  tokens_before,
  tokens_after,
  components_before,
  components_after,
  budget_allocation
}'
```

**Expected Output**:
```json
{
  "agent_id": "fraud_agent",
  "tokens_before": 5000,
  "tokens_after": 4800,
  "components_before": {
    "original_input": 1000,
    "prior_outputs": 3000,
    "observations": 1000
  },
  "components_after": {
    "original_input": 800,
    "prior_outputs": 3000,
    "observations": 1000
  },
  "budget_allocation": {
    "original_input_percentage": 30,
    "prior_outputs_percentage": 50,
    "observations_percentage": 20
  }
}
```

**Verify**:
- tokens_before = sum of components_before
- tokens_after = sum of components_after
- Component counts are sensible
- Budget allocation adds to 100%

---

## Test 6: Performance Testing

### Measure lineage tracking overhead:
```bash
# Run workflow WITHOUT context engineering
# Edit system_config.json: context_engineering.enabled = false
# Submit claim and measure time

# Run workflow WITH context engineering
# Edit system_config.json: context_engineering.enabled = true
# Submit claim and measure time

# Compare times
```

**Expected Overhead**:
- < 50ms total overhead for lineage tracking
- Most time spent in processor pipeline itself
- Lineage file write is async (non-blocking)

---

## Test 7: Edge Cases

### Test 7.1: No Compilations (Session without context engineering)
```bash
# Disable context engineering
# Submit workflow
# Check lineage file should NOT exist

ls storage/sessions/${SESSION_ID}_context_lineage.jsonl
# Should return "No such file"

# Query API should return empty
curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage" | jq
# Should return empty array or graceful error
```

### Test 7.2: Large Number of Compilations
```bash
# Run long workflow with many agents
# Check lineage file size

wc -l storage/sessions/${SESSION_ID}_context_lineage.jsonl
# Should show one line per compilation

# Verify API pagination works
curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage?limit=10&offset=0" | jq '.total_count'
```

### Test 7.3: Failed Processor
```bash
# Temporarily break a processor (e.g., invalid config)
# Run workflow
# Check lineage shows failed processor

curl "http://localhost:8016/sessions/${SESSION_ID}/context-lineage" | jq '.compilations[].processors_executed[] | select(.success == false)'
```

**Expected**: Processor marked as failed with error message

---

## Success Criteria

✅ **Backend**:
- [ ] Lineage file created for each session with context engineering enabled
- [ ] Each compilation logged with complete details
- [ ] All 4 API endpoints return correct data
- [ ] Processor execution times logged accurately
- [ ] Token counts tracked correctly (before/after)

✅ **Frontend**:
- [ ] Context Engineering tab appears in Replay page
- [ ] ContextTimeline shows all compilations with correct colors
- [ ] TokenBudgetChart shows stacked bars correctly
- [ ] ContextLineageTree expandable and shows processor details
- [ ] All visualizations load data from API correctly

✅ **Performance**:
- [ ] Lineage tracking adds < 50ms overhead
- [ ] Lineage file size reasonable (< 1MB for 100 compilations)
- [ ] API responses fast (< 200ms for typical queries)

✅ **Accuracy**:
- [ ] Token counts match actual context size
- [ ] Processor execution order correct
- [ ] Modifications tracked accurately
- [ ] Timestamps in chronological order

---

## Troubleshooting

### Issue: Lineage file not created
**Solution**: Check `context_engineering.enabled: true` in `system_config.json`

### Issue: API returns empty compilations
**Solution**: Workflow may not have compiled any contexts. Check if agents were invoked.

### Issue: Visualizations don't load
**Solution**:
1. Check browser console for errors
2. Verify API endpoints return data
3. Check CORS settings in backend

### Issue: Processor execution times all 0ms
**Solution**: Timing may be too fast. Check actual values in lineage file.

### Issue: Token counts seem wrong
**Solution**: Check tokenizer being used. Default is tiktoken for gpt-3.5-turbo.

---

## Additional Testing

### Integration Testing
- Test with Phase 2 (Compaction) enabled
- Test with Phase 3 (Memory) enabled
- Test with Phase 4 (Artifacts) enabled
- Verify lineage tracks all features

### Load Testing
- Run 100 sequential workflows
- Check lineage file performance
- Verify no memory leaks

### UI Testing
- Test on different screen sizes
- Test expand/collapse interactions
- Test with very long agent names
- Test with 0 compilations

---

## Next Steps After Testing

1. Review lineage data for insights
2. Identify slow processors for optimization
3. Analyze token usage patterns
4. Adjust budget allocations based on actual usage
5. Add custom visualizations as needed

---

**Testing Status**: Ready for testing

**Estimated Testing Time**: 30-45 minutes for full test suite

**Prerequisites**: Docker running, or local services started
