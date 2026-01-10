# AgentMesh API Reference

Complete API documentation for AgentMesh Orchestrator and Integration Fabric services.

**Version**: 1.0.0
**Last Updated**: January 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Orchestrator API](#orchestrator-api)
   - [Workflow Execution](#workflow-execution)
   - [Session Management](#session-management)
   - [Checkpoints (HITL)](#checkpoints-hitl)
   - [Context Engineering](#context-engineering)
   - [Registry Management](#registry-management)
   - [System Operations](#system-operations)
4. [Integration Fabric API](#integration-fabric-api)
   - [Integration Runs](#integration-runs)
   - [Dead Letter Queue](#dead-letter-queue)
   - [Integration Registries](#integration-registries)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

---

## Overview

AgentMesh provides two main API services:

- **Orchestrator API** (port 8016): Core multi-agent workflow orchestration
- **Integration Fabric API** (port 8020): Enterprise system integrations

### Base URLs

```
Orchestrator API:       http://localhost:8016
Integration Fabric API: http://localhost:8020
```

### Interactive Documentation

Both services provide auto-generated Swagger UI documentation:

- Orchestrator: http://localhost:8016/docs
- Integration Fabric: http://localhost:8020/docs

---

## Authentication

**Current Version**: No authentication required (development/demo mode)

**Production Considerations**:
- Implement JWT or OAuth2 authentication
- Add API key authentication for service-to-service calls
- Use role-based access control (RBAC) for HITL endpoints

---

## Orchestrator API

Base URL: `http://localhost:8016`

### Workflow Execution

#### Create Workflow Run

Start a new workflow execution.

```http
POST /runs
Content-Type: application/json

{
  "workflow_id": "claims_triage",
  "input_data": {
    "claim_id": "CLM-001",
    "policy_id": "POL-001",
    "claim_date": "2024-03-15T08:30:00Z",
    "incident_date": "2024-03-14T17:30:00Z",
    "loss_type": "collision",
    "claim_amount": 12500.00,
    "claimant": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "(555) 123-4567"
    }
  },
  "session_id": "optional-custom-id",
  "options": {}
}
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "workflow_id": "claims_triage",
  "status": "running",
  "created_at": "2024-03-15T10:30:00Z",
  "stream_url": "/runs/session_20240315_abc123/stream",
  "session_url": "/sessions/session_20240315_abc123"
}
```

**Response Codes**:
- `200`: Workflow started successfully
- `400`: Invalid request body or workflow_id
- `500`: Internal server error

---

#### Stream Workflow Events (SSE)

Subscribe to real-time workflow events via Server-Sent Events.

```http
GET /runs/{session_id}/stream
Accept: text/event-stream
```

**Response**: SSE Stream

```
event: workflow_started
data: {"workflow_id": "claims_triage", "session_id": "session_...", "started_at": "..."}

event: orchestrator_reasoning
data: {"iteration": 1, "reasoning": "Analyzing claim data...", "timestamp": "..."}

event: agent_invocation_started
data: {"agent_id": "intake_agent", "invocation_id": "inv_123", "timestamp": "..."}

event: agent_reasoning
data: {"agent_id": "intake_agent", "iteration": 1, "reasoning": "Validating claim structure...", "timestamp": "..."}

event: tool_invocation
data: {"agent_id": "intake_agent", "tool_id": "schema_validator", "parameters": {...}, "timestamp": "..."}

event: tool_result
data: {"tool_id": "schema_validator", "result": {...}, "success": true, "timestamp": "..."}

event: agent_invocation_completed
data: {"agent_id": "intake_agent", "output": {...}, "status": "success", "timestamp": "..."}

event: checkpoint_created
data: {"checkpoint_id": "cp_abc", "intervention_type": "approval", "timeout_at": "...", "timestamp": "..."}

event: workflow_completed
data: {"status": "completed", "duration_ms": 5432, "agents_executed": [...], "timestamp": "..."}
```

**Event Types**:
- `workflow_started` - Workflow execution initiated
- `orchestrator_reasoning` - Meta-agent ReAct reasoning step
- `orchestrator_action` - Meta-agent decides which agents to invoke
- `agent_invocation_started` - Worker agent begins execution
- `agent_reasoning` - Worker agent ReAct reasoning step
- `agent_action` - Worker agent decides which tools to use
- `tool_invocation` - Tool execution initiated
- `tool_result` - Tool execution completed
- `agent_invocation_completed` - Worker agent finished
- `checkpoint_created` - HITL checkpoint created
- `checkpoint_waiting` - Workflow paused for human input
- `checkpoint_resolved` - Human responded to checkpoint
- `checkpoint_timeout` - Checkpoint timed out
- `workflow_completed` - Workflow finished successfully
- `workflow_error` - Workflow encountered error
- `validation_error` - Agent output validation failed
- `governance_violation` - Policy violation detected

---

#### Get Run Status

Get current status of a running workflow.

```http
GET /runs/{session_id}/status
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "status": "running",
  "workflow_id": "claims_triage",
  "current_agent": "fraud_agent",
  "progress_percent": 60
}
```

**Status Values**:
- `running` - Workflow is currently executing
- `completed` - Workflow completed successfully
- `failed` - Workflow encountered fatal error
- `waiting_checkpoint` - Paused for human intervention

---

### Session Management

#### List Sessions

Retrieve all workflow sessions with pagination.

```http
GET /sessions?limit=20&offset=0&status=completed
```

**Query Parameters**:
- `limit` (optional): Number of sessions to return (default: 20, max: 100)
- `offset` (optional): Number of sessions to skip (default: 0)
- `status` (optional): Filter by status (`running`, `completed`, `failed`)

**Response 200**:
```json
[
  {
    "session_id": "session_20240315_abc123",
    "workflow_id": "claims_triage",
    "status": "completed",
    "created_at": "2024-03-15T10:30:00Z",
    "completed_at": "2024-03-15T10:35:32Z",
    "duration_ms": 332000,
    "event_count": 42,
    "agents_executed": ["intake_agent", "coverage_agent", "fraud_agent", "recommendation_agent"]
  }
]
```

---

#### Get Session Details

Retrieve complete session information with event timeline.

```http
GET /sessions/{session_id}?event_type=agent_reasoning
```

**Query Parameters**:
- `event_type` (optional): Filter events by type (e.g., `agent_reasoning`, `tool_invocation`)

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "workflow_id": "claims_triage",
  "status": "completed",
  "created_at": "2024-03-15T10:30:00Z",
  "completed_at": "2024-03-15T10:35:32Z",
  "duration_ms": 332000,
  "input_data": {
    "claim_id": "CLM-001",
    ...
  },
  "output_data": {
    "recommendation": "APPROVE_CLAIM",
    "confidence": 0.92,
    ...
  },
  "agents_executed": ["intake_agent", "coverage_agent", "fraud_agent", "recommendation_agent"],
  "total_iterations": 12,
  "events": [
    {
      "event_type": "workflow_started",
      "timestamp": "2024-03-15T10:30:00Z",
      "data": {...}
    },
    ...
  ],
  "warnings": [],
  "errors": []
}
```

---

#### Delete Session

Delete a session and all associated data.

```http
DELETE /sessions/{session_id}
```

**Response 200**:
```json
{
  "success": true,
  "message": "Session session_20240315_abc123 deleted successfully"
}
```

**Response 404**:
```json
{
  "detail": "Session not found"
}
```

---

#### Get Evidence Map

Retrieve structured evidence map for explainability.

```http
GET /sessions/{session_id}/evidence
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "generated_at": "2024-03-15T10:35:32Z",
  "evidence_map": {
    "decision": {
      "outcome": "APPROVE_CLAIM",
      "confidence": 0.92,
      "rationale": "All checks passed with high confidence. No fraud signals detected.",
      "financial_exposure": 12500.00,
      "potential_savings": 0.00
    },
    "supporting_evidence": [
      {
        "agent_id": "intake_agent",
        "finding": "Claim data validated successfully",
        "weight": 85,
        "details": {...}
      },
      {
        "agent_id": "fraud_agent",
        "finding": "No fraud indicators detected",
        "weight": 95,
        "risk_score": 0.12,
        "details": {...}
      }
    ],
    "human_interventions": [
      {
        "checkpoint_id": "cp_abc123",
        "intervention_type": "approval",
        "timestamp": "2024-03-15T10:33:00Z",
        "reviewer": "claims_adjuster@example.com",
        "decision": "approved",
        "comments": "Verified claim details"
      }
    ],
    "agent_chain": [
      {"agent_id": "intake_agent", "order": 1},
      {"agent_id": "coverage_agent", "order": 2},
      {"agent_id": "fraud_agent", "order": 3},
      {"agent_id": "recommendation_agent", "order": 4}
    ],
    "assumptions": [
      "Policy coverage data is accurate and up-to-date",
      "Historical claim similarity search covers last 5 years"
    ],
    "limitations": [
      "Cannot access external police reports",
      "Weather data not available for incident location"
    ]
  }
}
```

---

### Checkpoints (HITL)

#### List Checkpoints

Retrieve all checkpoints with optional filtering.

```http
GET /checkpoints?status=active&limit=20
```

**Query Parameters**:
- `status` (optional): Filter by status (`active`, `resolved`, `timeout`)
- `limit` (optional): Number of checkpoints to return (default: 20)

**Response 200**:
```json
[
  {
    "checkpoint_id": "cp_abc123",
    "session_id": "session_20240315_xyz",
    "workflow_id": "claims_triage",
    "intervention_type": "approval",
    "status": "active",
    "created_at": "2024-03-15T10:33:00Z",
    "timeout_at": "2024-03-15T11:33:00Z",
    "required_roles": ["fraud_investigator"],
    "metadata": {
      "title": "Fraud Review Required",
      "description": "High fraud score detected (0.87)"
    }
  }
]
```

---

#### Get Checkpoint Details

Retrieve full checkpoint context and options.

```http
GET /checkpoints/{checkpoint_id}
```

**Response 200**:
```json
{
  "checkpoint_id": "cp_abc123",
  "session_id": "session_20240315_xyz",
  "workflow_id": "claims_triage",
  "intervention_type": "decision",
  "status": "active",
  "created_at": "2024-03-15T10:33:00Z",
  "timeout_at": "2024-03-15T11:33:00Z",
  "timeout_behavior": "auto_reject",
  "required_roles": ["fraud_investigator"],
  "context": {
    "agent_outputs": {
      "fraud_agent": {
        "fraud_score": 0.87,
        "risk_factors": ["Multiple claims in short period", "High claim amount"]
      }
    },
    "current_state": {
      "claim_id": "CLM-001",
      "claim_amount": 45000.00
    }
  },
  "options": [
    {"value": "auto_process", "label": "Auto Process"},
    {"value": "manual_review", "label": "Manual Review"},
    {"value": "escalate", "label": "Escalate to Senior Investigator"}
  ],
  "metadata": {
    "title": "Fraud Review Required",
    "description": "High fraud score detected (0.87)"
  }
}
```

---

#### Respond to Checkpoint

Submit a response to an active checkpoint.

```http
POST /checkpoints/{checkpoint_id}/respond
Content-Type: application/json

{
  "decision": "approved",
  "comments": "Verified claim with customer. Legitimate incident.",
  "data": {
    "corrected_amount": 15000.00
  },
  "responder_id": "user@example.com",
  "responder_role": "claims_adjuster"
}
```

**Request Fields**:
- `decision` (required): Decision value (`approved`, `rejected`, or custom option)
- `comments` (optional): Human comments/notes
- `data` (optional): Additional data or corrections
- `responder_id` (required): User identifier
- `responder_role` (required): User role

**Response 200**:
```json
{
  "checkpoint_id": "cp_abc123",
  "status": "resolved",
  "resolution": "approved",
  "resolved_at": "2024-03-15T10:45:00Z",
  "resolved_by": "user@example.com"
}
```

---

### Context Engineering

#### Get Context Lineage

Retrieve complete context compilation history for a session.

```http
GET /sessions/{session_id}/context-lineage
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "compilations": [
    {
      "compilation_id": "comp_1",
      "agent_id": "intake_agent",
      "timestamp": "2024-03-15T10:30:05Z",
      "processors_executed": [
        {"processor_id": "content_selector", "execution_time_ms": 2.5, "modifications_made": {"events_filtered": 3}},
        {"processor_id": "transformer", "execution_time_ms": 5.1, "modifications_made": {"messages_created": 8}},
        {"processor_id": "token_budget_enforcer", "execution_time_ms": 1.2, "modifications_made": {"tokens_within_budget": true}}
      ],
      "token_stats": {
        "input_tokens": 1250,
        "output_tokens": 450,
        "observation_tokens": 300,
        "total_tokens": 2000,
        "budget_utilization": 0.67
      }
    }
  ]
}
```

---

#### Get Context Statistics

Retrieve context compilation statistics for Token Analytics tab.

```http
GET /sessions/{session_id}/context-stats
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "total_compilations": 12,
  "total_truncations": 2,
  "total_compactions": 1,
  "average_tokens_per_compilation": 2340,
  "max_tokens_observed": 4500,
  "token_budget_violations": 0,
  "memory_retrievals": 3,
  "artifact_resolutions": 5
}
```

---

#### Get Token Budget Timeline

Retrieve token usage timeline data for visualization.

```http
GET /sessions/{session_id}/token-budget-timeline
```

**Response 200**:
```json
{
  "session_id": "session_20240315_abc123",
  "timeline": [
    {
      "timestamp": "2024-03-15T10:30:05Z",
      "agent_id": "intake_agent",
      "input_tokens": 1250,
      "output_tokens": 450,
      "observation_tokens": 300,
      "total_tokens": 2000,
      "budget_limit": 3000
    },
    ...
  ]
}
```

---

#### Trigger Session Compaction

Manually trigger session summarization/compaction.

```http
POST /sessions/{session_id}/trigger-compaction
```

**Response 200**:
```json
{
  "success": true,
  "compaction_id": "compact_xyz789",
  "events_summarized": 42,
  "tokens_saved": 3500,
  "summary": "Session compacted successfully. Original 42 events summarized into 8 key points."
}
```

---

### Registry Management

#### Get Registry

Retrieve a specific registry configuration.

```http
GET /registries/{registry_name}
```

**Registry Names**:
- `agents` - Agent definitions
- `tools` - Tool catalog
- `models` - Model profiles
- `workflows` - Workflow definitions
- `governance` - Governance policies
- `system_config` - System configuration

**Response 200**:
```json
{
  "version": "1.0.0",
  "last_updated": "2024-03-15T10:00:00Z",
  ...
}
```

---

#### Update Registry

Update a registry configuration (requires service restart).

```http
PUT /registries/{registry_name}
Content-Type: application/json

{
  "version": "1.1.0",
  ...
}
```

**Response 200**:
```json
{
  "status": "updated",
  "validation_result": {
    "valid": true,
    "warnings": []
  },
  "message": "Registry updated. Service restart required."
}
```

---

### System Operations

#### Health Check

Check service health and registry status.

```http
GET /health
```

**Response 200**:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "version": "1.0.0",
  "registries_loaded": true,
  "services": {
    "orchestrator": "healthy",
    "tools_gateway": "healthy"
  }
}
```

---

#### System Stats

Retrieve system statistics and metrics.

```http
GET /stats
```

**Response 200**:
```json
{
  "registries": {
    "agents_count": 7,
    "tools_count": 6,
    "workflows_count": 1,
    "model_profiles_count": 4
  },
  "executor": {
    "running_sessions": 2,
    "completed_sessions": 145,
    "failed_sessions": 3
  },
  "broadcaster": {
    "active_connections": 5,
    "total_events_broadcast": 3421
  },
  "uptime_seconds": 86400
}
```

---

## Integration Fabric API

Base URL: `http://localhost:8020`

The Integration Fabric provides production-grade integration patterns for connecting to external insurance core systems.

### Integration Runs

#### Create Integration Run

Start a new integration workflow execution.

```http
POST /runs
Content-Type: application/json

{
  "workflow_id": "claim_fnol_sync",
  "input_data": {
    "claim_id": "CLM-2024-0012",
    "policy_id": "POL-9087"
  },
  "simulate_failure": false
}
```

**Request Fields**:
- `workflow_id` (required): Integration workflow identifier
- `input_data` (required): Workflow input parameters
- `simulate_failure` (optional): Trigger failure for DLQ testing (default: false)

**Response 200**:
```json
{
  "run_id": "run_abc123",
  "workflow_id": "claim_fnol_sync",
  "status": "running",
  "created_at": "2024-03-15T10:30:00Z",
  "stream_url": "/runs/run_abc123/stream"
}
```

**Available Workflows**:
- `claim_fnol_sync` - Fetch claim from Guidewire, apply PII masking, audit
- `claim_status_update` - Idempotent claim status update
- `billing_sync` - Fetch billing data from Socotra, apply PCI guard, audit
- `integration_failure_drill` - Simulate integration failure for testing

---

#### List Integration Runs

Retrieve all integration runs with pagination.

```http
GET /runs?limit=20&offset=0
```

**Query Parameters**:
- `limit` (optional): Number of runs to return (default: 20)
- `offset` (optional): Number of runs to skip (default: 0)

**Response 200**:
```json
[
  {
    "run_id": "run_abc123",
    "workflow_id": "claim_fnol_sync",
    "status": "completed",
    "created_at": "2024-03-15T10:30:00Z",
    "completed_at": "2024-03-15T10:30:05Z",
    "duration_ms": 1250,
    "steps_executed": 3,
    "steps_failed": 0
  }
]
```

**Status Values**:
- `running` - Integration in progress
- `completed` - Integration completed successfully
- `failed` - Integration encountered fatal error
- `partial` - Some steps failed but workflow continued

---

#### Get Integration Run Details

Retrieve complete run information with step-by-step execution details.

```http
GET /runs/{run_id}
```

**Response 200**:
```json
{
  "run_id": "run_abc123",
  "workflow_id": "claim_fnol_sync",
  "status": "completed",
  "created_at": "2024-03-15T10:30:00Z",
  "completed_at": "2024-03-15T10:30:05Z",
  "duration_ms": 1250,
  "input_data": {
    "claim_id": "CLM-2024-0012",
    "policy_id": "POL-9087"
  },
  "steps": [
    {
      "step_id": "fetch_claim",
      "type": "rest_call",
      "connector": "guidewire_claims",
      "operation": "GET /claims/CLM-2024-0012",
      "status": "success",
      "idempotent": true,
      "cached": false,
      "attempts": 1,
      "duration_ms": 450,
      "timestamp": "2024-03-15T10:30:00Z",
      "request": {...},
      "response": {...}
    },
    {
      "step_id": "mask_pii",
      "type": "security_transform",
      "policy": "claims_pii_masking",
      "status": "success",
      "duration_ms": 20,
      "timestamp": "2024-03-15T10:30:01Z",
      "rules_applied": ["ssn_mask", "dob_mask"]
    },
    {
      "step_id": "audit",
      "type": "audit_event",
      "status": "success",
      "duration_ms": 10,
      "timestamp": "2024-03-15T10:30:01Z",
      "audit_record": {...}
    }
  ],
  "errors": [],
  "warnings": []
}
```

---

#### Stream Integration Run Events (SSE)

Subscribe to real-time integration workflow events.

```http
GET /runs/{run_id}/stream
Accept: text/event-stream
```

**Response**: SSE Stream

```
event: run_started
data: {"workflow_id": "claim_fnol_sync", "run_id": "run_abc123", "started_at": "..."}

event: step_started
data: {"step_id": "fetch_claim", "type": "rest_call", "connector": "guidewire_claims", "timestamp": "..."}

event: step_completed
data: {"step_id": "fetch_claim", "status": "success", "duration_ms": 450, "timestamp": "..."}

event: idempotent_skip
data: {"step_id": "fetch_claim", "cached_result": {...}, "timestamp": "..."}

event: step_error
data: {"step_id": "fetch_claim", "error": "Connection timeout", "retry_count": 3, "timestamp": "..."}

event: dlq_queued
data: {"item_id": "dlq_xyz789", "step_id": "fetch_claim", "error": "Max retries exceeded", "timestamp": "..."}

event: run_completed
data: {"status": "completed", "duration_ms": 1250, "steps_executed": 3, "timestamp": "..."}
```

**Event Types**:
- `run_started` - Integration workflow started
- `step_started` - Integration step started
- `step_completed` - Integration step completed successfully
- `idempotent_skip` - Step skipped due to idempotency cache hit
- `step_error` - Integration step encountered error
- `step_retry` - Step retry attempt
- `dlq_queued` - Failed step added to dead letter queue
- `run_completed` - Integration workflow finished
- `run_failed` - Integration workflow encountered fatal error

---

### Dead Letter Queue

#### List DLQ Items

Retrieve all dead letter queue items.

```http
GET /dlq
```

**Response 200**:
```json
[
  {
    "item_id": "dlq_xyz789",
    "run_id": "run_abc123",
    "workflow_id": "claim_fnol_sync",
    "step_id": "fetch_claim",
    "error": "Connection timeout to Guidewire API after 3 attempts",
    "retry_count": 3,
    "created_at": "2024-03-15T10:30:05Z",
    "payload": {
      "claim_id": "CLM-2024-0012",
      "policy_id": "POL-9087"
    },
    "metadata": {
      "connector": "guidewire_claims",
      "operation": "GET /claims/CLM-2024-0012"
    }
  }
]
```

---

#### Reprocess DLQ Item

Reprocess a failed integration step from the DLQ.

```http
POST /dlq/{item_id}/reprocess
```

**Response 200**:
```json
{
  "success": true,
  "message": "DLQ item dlq_xyz789 acknowledged for reprocessing.",
  "new_run_id": "run_retry_xyz789"
}
```

**Note**: In the current demo implementation, this endpoint is a stub and returns success without actual reprocessing.

---

### Integration Registries

#### Get Connectors

Retrieve all registered integration connectors.

```http
GET /registries/connectors
```

**Response 200**:
```json
{
  "version": "1.0.0",
  "connectors": [
    {
      "connector_id": "guidewire_claims",
      "name": "Guidewire Claims API",
      "type": "REST",
      "base_url": "${GW_BASE_URL}",
      "auth_profile": "gw_oauth",
      "timeout_ms": 5000,
      "supports_idempotency": true,
      "scaling": {
        "max_concurrency": 10,
        "qps_limit": 25,
        "burst_limit": 50
      },
      "circuit_breaker": {
        "failure_threshold": 5,
        "open_duration_ms": 30000,
        "half_open_attempts": 2
      },
      "region_affinity": {
        "primary": "us-west-2",
        "fallbacks": ["us-east-1"]
      }
    }
  ]
}
```

---

#### Get Auth Profiles

Retrieve all authentication profile configurations.

```http
GET /registries/auth-profiles
```

**Response 200**:
```json
{
  "version": "1.0.0",
  "auth_profiles": [
    {
      "profile_id": "gw_oauth",
      "type": "OIDC",
      "name": "Guidewire OAuth 2.0",
      "issuer": "${GW_OIDC_ISSUER}",
      "client_id": "${GW_CLIENT_ID}",
      "client_secret": "${GW_CLIENT_SECRET}",
      "scopes": ["claims.read", "claims.write"]
    },
    {
      "profile_id": "duckcreek_token",
      "type": "TOKEN",
      "name": "Duck Creek Bearer Token",
      "token": "${DUCKCREEK_TOKEN}",
      "header_name": "Authorization"
    }
  ]
}
```

---

#### Get Workflows

Retrieve all registered integration workflows.

```http
GET /registries/workflows
```

**Response 200**:
```json
{
  "version": "1.0.0",
  "workflows": [
    {
      "workflow_id": "claim_fnol_sync",
      "name": "Claim FNOL Sync",
      "description": "Synchronize FNOL data from Guidewire Claims",
      "trigger": "ClaimOpened",
      "priority": "critical",
      "sla": {
        "max_latency_ms": 1500,
        "timeout_ms": 5000
      },
      "throughput": {
        "max_concurrency": 5,
        "queue_depth_limit": 100
      },
      "steps": [
        {
          "id": "fetch_claim",
          "type": "rest_call",
          "connector": "guidewire_claims",
          "operation": "GET /claims/{claim_id}",
          "idempotency": true,
          "retry_policy": "standard",
          "failure_policy": "dead_letter"
        },
        {
          "id": "mask_pii",
          "type": "security_transform",
          "policy": "claims_pii_masking"
        },
        {
          "id": "audit",
          "type": "audit_event"
        }
      ]
    }
  ]
}
```

---

#### Get Security Policies

Retrieve all security policy definitions.

```http
GET /registries/security-policies
```

**Response 200**:
```json
{
  "version": "1.0.0",
  "policies": [
    {
      "policy_id": "claims_pii_masking",
      "name": "Claims PII Masking",
      "type": "PII_MASKING",
      "rules": [
        {
          "field": "claimant.ssn",
          "action": "mask",
          "pattern": "XXX-XX-####"
        },
        {
          "field": "claimant.dob",
          "action": "redact"
        },
        {
          "field": "medical_notes",
          "action": "tokenize"
        }
      ]
    },
    {
      "policy_id": "billing_pci_guard",
      "name": "Billing PCI Guard",
      "type": "PCI_GUARD",
      "rules": [
        {
          "field": "payment.card_number",
          "action": "mask",
          "pattern": "****-****-****-####"
        },
        {
          "field": "payment.cvv",
          "action": "redact"
        }
      ]
    }
  ]
}
```

---

#### Get System Configuration

Retrieve integration system configuration.

```http
GET /registries/system-config
```

**Response 200**:
```json
{
  "version": "1.0.0",
  "retry_policies": {
    "standard": {
      "max_attempts": 3,
      "backoff_seconds": 0.5
    },
    "aggressive": {
      "max_attempts": 5,
      "backoff_seconds": 0.25
    }
  },
  "idempotency": {
    "idempotency_ttl_ms": 86400000,
    "dedup_scope": "workflow"
  },
  "event_driven_channels": ["pubsub", "mq", "event_bridge"]
}
```

---

#### Health Check

Check Integration Fabric service health.

```http
GET /health
```

**Response 200**:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "version": "1.0.0",
  "registries_loaded": true,
  "connectors_available": 4
}
```

---

## Error Handling

### Standard Error Response Format

All API errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-03-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters or body |
| `WORKFLOW_NOT_FOUND` | 404 | Specified workflow_id does not exist |
| `SESSION_NOT_FOUND` | 404 | Specified session_id does not exist |
| `CHECKPOINT_NOT_FOUND` | 404 | Specified checkpoint_id does not exist |
| `GOVERNANCE_VIOLATION` | 403 | Operation violates governance policy |
| `EXECUTION_TIMEOUT` | 408 | Workflow execution exceeded timeout |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Handling Best Practices

1. **Retry Logic**: Implement exponential backoff for 5xx errors
2. **Idempotency**: Use session_id for retrying workflow creation
3. **Timeouts**: Set appropriate client timeouts (recommended: 60s)
4. **SSE Reconnection**: Implement reconnection logic with last_event_id

---

## Rate Limiting

**Current Version**: No rate limiting (development/demo mode)

**Production Considerations**:
- Implement per-user/IP rate limits (e.g., 100 requests/minute)
- Add burst allowances for spike traffic
- Return `429 Too Many Requests` with `Retry-After` header
- Use token bucket or sliding window algorithm

**Recommended Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710500000
```

---

## Versioning

**Current Version**: v1.0.0

**API Versioning Strategy**: URL path versioning (future)
- Current: `/runs`
- Future: `/v2/runs`

**Backward Compatibility**: Breaking changes will result in new API version.

---

## Additional Resources

- **Orchestrator Interactive Docs**: http://localhost:8016/docs
- **Integration Fabric Interactive Docs**: http://localhost:8020/docs
- **GitHub Repository**: https://github.com/yourusername/AgentMesh
- **Documentation**: [README.md](README.md)
- **Integration Guide**: [AIF.md](AIF.md)

---

**Last Updated**: January 2026
**API Version**: 1.0.0
