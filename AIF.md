# AgentMesh Integration Fabric (AIF)

## Overview
AgentMesh Integration Fabric (AIF) is a standalone FastAPI service that demonstrates production‑grade integration patterns for multi‑agent insurance systems. AIF is registry‑driven and focused on safe, observable integrations with insurer core ecosystems (Guidewire, Duck Creek, Socotra) and legacy mainframe adapters. The prototype runs inside the existing AgentMesh Docker Compose stack and is designed to be minimally disruptive to the core orchestrator.

## Architecture

```
+-------------------------+        +-------------------------------+
| AgentMesh UI            |        | AgentMesh Orchestrator        |
| /integrations           |        | (unchanged)                   |
+------------+------------+        +-------------------------------+
             |
             v
+------------------------------------------+
| Integration Fabric API (FastAPI)         |
|------------------------------------------|
| • Workflow Runner                        |
| • Connector Executor (simulated)         |
| • Idempotency + Retry + DLQ (file)       |
| • Security Policy Engine (simulated)     |
| • SSE Event Streaming                    |
+-------------+----------------------------+
              |
              v
+------------------------------------------+
| Simulated Core Systems (in‑process)      |
| Guidewire | Duck Creek | Socotra | Mainframe |
+------------------------------------------+
```

## Services
- `integration_fabric` FastAPI service, port `8020`
- Registry files under `registries/integration/`
- Runtime data under `storage/integration/`

## Endpoints

### Runs
- `POST /runs` — start an integration run
- `GET /runs` — list runs
- `GET /runs/{run_id}` — run detail
- `GET /runs/{run_id}/stream` — SSE stream

### DLQ
- `GET /dlq` — list DLQ items
- `POST /dlq/{item_id}/reprocess` — stub reprocess acknowledgement

### Registries
- `GET /registries/connectors`
- `GET /registries/auth-profiles`
- `GET /registries/workflows`
- `GET /registries/security-policies`
- `GET /registries/system-config`

## Registries
Location: `registries/integration/`

- `connectors.json` — REST connectors with base URLs and idempotency support
- `auth_profiles.json` — mock OIDC, token, API key, and service account profiles
- `security_policies.json` — PII/PCI masking policies (simulated)
- `system_config.json` — retry policies and feature flags
- `workflows/*.json` — integration workflows (FNOL sync, status update, billing sync, failure drill)
- Integration scalability UI configuration: `INTEGRATION_SCALABILITY.md`

## Demo Flows

1. FNOL Sync
   - `claim_fnol_sync`
   - REST call -> PII masking policy -> audit event

2. Claim Status Update
   - `claim_status_update`
   - Idempotent REST update + audit event

3. Billing Sync (PCI)
   - `billing_sync`
   - REST billing sync + PCI guard policy + audit event

4. Failure Drill + DLQ
   - `integration_failure_drill`
   - Simulated failure triggers DLQ item

## Example Run

```bash
POST http://localhost:8020/runs
Content-Type: application/json

{
  "workflow_id": "claim_fnol_sync",
  "input_data": {
    "claim_id": "CLM-2024-0012",
    "policy_id": "POL-9087"
  }
}
```

## Spec Alignment

### Implemented
- Separate AIF FastAPI service and Compose wiring
- Registry‑driven connectors, auth profiles, workflows, security policies
- File‑backed idempotency store and DLQ
- SSE run streaming and run audit trail (JSONL)
- Integrations UI section (connectors, workflows, runs, DLQ, policies)
- Mock OIDC adapter configuration in registry
- Event‑driven/MQ channels exposed as configuration only

### Planned / Not Implemented Yet
- External simulator services per vendor (Guidewire/Duck Creek/Socotra)
- Real auth/SSO enforcement (OIDC validation, RBAC)
- Replay/reprocess execution from DLQ items
- Safe logging pipeline with redaction/tokens
- Audit evidence export artifacts and SOC2 report pack
- Pub/sub or MQ connector execution
- Connector‑level circuit breaking and rate limits

## Limitations
- Connector responses are simulated in‑process (no real vendor endpoints).
- Security policy engine is configuration‑only (does not mutate payloads).
- DLQ reprocess endpoint is a stub for demo purposes.
- No multi‑tenant isolation or production auth enforcement.

## Where To Look
- API entrypoint: `backend/integration_fabric/app/main.py`
- Workflow runner: `backend/integration_fabric/app/services/workflow_runner.py`
- Registries: `registries/integration/`
- UI: `frontend/app/integrations/page.tsx`
