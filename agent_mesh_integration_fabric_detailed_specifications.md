# AgentMesh Integration Fabric (AIF)

**Version:** 1.0 (Prototype / Demo-Grade, Production-Oriented)

---

## 1. Purpose & Scope

The **AgentMesh Integration Fabric (AIF)** is an extension module to the existing **AgentMesh** application that enables production-grade integration between multi-agent AI systems and insurance core ecosystems.

The goal of AIF is to demonstrate, in a single-laptop Docker Compose setup, how **agentic AI systems can be safely, observably, and securely integrated with real-world insurer systems** (policy, claims, billing, underwriting), while meeting enterprise integration, security, and compliance expectations.

This is **not a standalone product**. It is a **first-class module within AgentMesh**, reusing its orchestration, bounded autonomy, observability, and governance foundations.

---

## 2. Design Principles

1. **AgentMesh-first** – Integration logic is exposed as AgentMesh tools and workflows, not a parallel orchestration engine.
2. **Config over code** – Integrations are defined via registries (JSON/YAML), not hard-coded logic.
3. **Bounded execution** – Every integration step is time-bound, idempotent, retry-safe, and auditable.
4. **Observable by default** – Every integration run produces structured events, traces, and replayable artifacts.
5. **Security as a feature** – PII masking, safe logging, and auditability are visible and demonstrable.
6. **Demo-safe, production-shaped** – Real vendor APIs when available; high-fidelity simulators when not.

---

## 3. High-Level Architecture

```
+-------------------+
|   AgentMesh UI    |
|-------------------|
| Agents | Tools    |
| Integrations UI   |
+---------+---------+
          |
          v
+-----------------------------+
| AgentMesh Orchestrator      |
| (bounded ReAct execution)   |
+-------------+---------------+
              |
              v
+-----------------------------------------+
| Integration Fabric Runtime (AIF)         |
|-----------------------------------------|
| • Workflow Runner                        |
| • Connector Executor                    |
| • Idempotency / Retry / DLQ             |
| • Security Policy Engine                |
| • Observability + Audit                 |
+-------------+---------------------------+
              |
              v
+-----------------------------------------+
| External Systems                         |
| REST APIs (Guidewire / DC / Socotra)    |
| Event / MQ (future)                     |
+-----------------------------------------+
```

---

## 4. Repository & Module Structure

```
agentmesh/
├── apps/
│   ├── core/                    # Existing AgentMesh app
│   └── integration-fabric/      # NEW AIF module
│       ├── backend/
│       │   ├── main.py
│       │   ├── workflow_runner.py
│       │   ├── connector_executor.py
│       │   ├── idempotency.py
│       │   ├── security_engine.py
│       │   ├── observability.py
│       │   └── audit.py
│       ├── registries/
│       │   ├── connectors.json
│       │   ├── auth_profiles.json
│       │   ├── workflows/
│       │   ├── security_policies.json
│       │   └── schemas/
│       ├── simulators/
│       │   ├── guidewire_sim.py
│       │   ├── duckcreek_sim.py
│       │   └── socotra_sim.py
│       └── tests/
│
├── ui/
│   └── integrations/            # NEW UI section
│       ├── Workflows.tsx
│       ├── Runs.tsx
│       ├── Connectors.tsx
│       ├── DLQ.tsx
│       └── Policies.tsx
│
├── docker-compose.yml
└── .env
```

---

## 5. Core Capabilities

### 5.1 Integration Workflows

**Definition**: A workflow is a declarative, ordered set of integration steps executed by AgentMesh via AIF.

**Workflow Schema (simplified)**:

```json
{
  "workflow_id": "claim_fnol_sync",
  "version": "1.0",
  "trigger": "ClaimOpened",
  "steps": [
    {
      "id": "fetch_claim",
      "type": "rest_call",
      "connector": "guidewire_claims",
      "operation": "GET /claims/{claim_id}",
      "idempotency": true,
      "retry_policy": "standard"
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
```

---

### 5.2 REST Connector Framework

**Connector Responsibilities**:
- REST request construction
- Authentication injection
- Timeout, retry, and circuit breaking
- Response normalization

**Connector Registry** (`connectors.json`):

```json
{
  "id": "guidewire_claims",
  "type": "REST",
  "base_url": "${GW_BASE_URL}",
  "auth_profile": "gw_oauth",
  "timeout_ms": 5000,
  "supports_idempotency": true
}
```

**Real vs Simulator Mode**:
- If credentials and base URL exist → real API
- Else → simulator service with identical contract

---

### 5.3 Authentication & SSO

#### MVP
- JWT-based RBAC
- Roles: `admin`, `integration_editor`, `viewer`, `approver`

#### SSO Plug-in Seam
- OIDC-compatible interface
- Pluggable provider (Keycloak / Authentik / Azure AD)
- Token validation abstraction

---

### 5.4 Idempotency & Reliability

- Each step generates an **idempotency key**:
  ```
  {workflow_run_id}:{step_id}:{business_key}
  ```
- Stored in Redis or file-backed store (demo)
- Duplicate execution → safe skip with recorded outcome

**Failure Policies**:
- retry
- skip
- pause_for_human
- dead_letter

---

### 5.5 Troubleshooting & Observability

**Captured per step**:
- Request metadata (sanitized)
- Response metadata
- Retry count
- Latency
- Status

**Features**:
- Live execution via SSE
- Replay from any step
- DLQ browser + reprocess
- Correlation ID per workflow run

---

### 5.6 Data Security (HIPAA / PII)

**Security Policy Engine**:

```json
{
  "policy_id": "claims_pii_masking",
  "rules": [
    {"field": "ssn", "action": "mask"},
    {"field": "dob", "action": "redact"},
    {"field": "medical_notes", "action": "drop"}
  ]
}
```

**Safe Logging**:
- No raw PII payloads stored
- Hash-only identifiers
- Redacted samples only

---

### 5.7 SOC2-Oriented Controls

Demonstrated Controls:
- RBAC for config changes
- Audit log for:
  - workflow edits
  - connector changes
  - approvals
- Evidence artifacts:
  - run report
  - config version
  - masking policy applied

---

## 6. UI Enhancements

### Integrations Dashboard
- Workflow list
- Connector status
- Recent runs

### Run Details View
- Step timeline
- Evidence map
- Masking indicators
- Replay button

### DLQ View
- Failed runs
- Root cause
- Reprocess action

---

## 7. Deployment Model

**Docker Compose Only** (single-laptop demo):

Services:
- agentmesh-backend
- agentmesh-ui
- integration-fabric-backend
- redis
- simulator-services

All secrets in a **single `.env` file at repo root**.

---

## 8. Demo Scenarios

1. Claim FNOL sync (REST, PII masking)
2. Claim status update with idempotency
3. Failure → DLQ → replay
4. Security audit evidence export

---

## 9. Non-Goals (Prototype Phase)

- No full ESB replacement
- No full BPM engine
- No real-time streaming (Kafka) in v1

---

## 10. Future Extensions

- Kafka / MQ connectors
- Schema registry
- Tenant isolation
- Policy-as-code
- K8s deployment

---

## 11. Summary

The AgentMesh Integration Fabric demonstrates how **agentic AI systems can safely integrate with insurer core systems at production scale**, while preserving observability, governance, and compliance. It elevates AgentMesh from an orchestration framework into a **credible enterprise integration platform for insurance ecosystems**.

