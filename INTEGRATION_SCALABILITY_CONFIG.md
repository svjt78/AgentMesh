# Integration Scalability Configuration Reference (Draft)

**Version:** 0.1
**Last Updated:** January 2026
**Target Audience:** System Administrators, DevOps Engineers, Platform Owners

---

## Table of Contents

1. [Configuration Files Overview](#configuration-files-overview)
2. [system_config.json (Integration Fabric)](#system_configjson-integration-fabric)
3. [connectors.json Extensions](#connectorsjson-extensions)
4. [workflows/*.json Extensions](#workflowsjson-extensions)
5. [auth_profiles.json Extensions](#auth_profilesjson-extensions)
6. [Override Rules](#override-rules)
7. [Validation Rules](#validation-rules)

---

## Configuration Files Overview

### File Locations

```
registries/integration/
├── system_config.json
├── connectors.json
├── workflows/
│   ├── claim_fnol_sync.json
│   ├── billing_sync.json
│   └── ...
└── auth_profiles.json
```

### Configuration Hierarchy

```
System Config (global defaults)
    ↓
Connector Config (per-connector overrides)
    ↓
Workflow Config (per-workflow overrides)
    ↓
Auth Profile Config (per-tenant limits)
```

**Override Priority (highest to lowest):**
1. Workflow overrides
2. Connector overrides
3. System defaults

---

## system_config.json (Integration Fabric)

**Purpose:** Global scalability defaults and channel-level policies.

**Location:** `registries/integration/system_config.json`

### Proposed Schema Additions

```json
{
  "version": "1.1",
  "event_driven_channels": ["pubsub", "mq", "event_bridge"],
  "throughput_limits": {
    "max_concurrency": 50,
    "qps_limit": 200,
    "burst_limit": 400,
    "queue_depth_limit": 1000,
    "backpressure_mode": "queue"
  },
  "retry_profiles": [
    {
      "policy_id": "standard",
      "max_attempts": 3,
      "base_backoff_ms": 250,
      "max_backoff_ms": 2000,
      "jitter_pct": 20
    }
  ],
  "circuit_breaker_defaults": {
    "failure_threshold": 5,
    "open_duration_ms": 30000,
    "half_open_attempts": 2
  },
  "event_channel_policies": {
    "mq": {"batch_size": 20, "poll_interval_ms": 500, "max_parallel_consumers": 8},
    "pubsub": {"batch_size": 50, "poll_interval_ms": 200, "max_parallel_consumers": 16}
  },
  "observability": {
    "metrics_sampling_rate": 0.1,
    "trace_retention_days": 14,
    "alert_thresholds": {
      "error_rate_pct": 2.5,
      "dlq_depth": 50,
      "latency_p95_ms": 2000
    }
  },
  "idempotency": {
    "idempotency_ttl_ms": 86400000,
    "dedup_scope": "workflow"
  }
}
```

### Field Definitions

#### throughput_limits

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `max_concurrency` | integer | 50 | 1-10000 | Global max parallel executions |
| `qps_limit` | integer | 200 | 1-100000 | Global requests per second |
| `burst_limit` | integer | 400 | 1-200000 | Short-term burst allowance |
| `queue_depth_limit` | integer | 1000 | 1-100000 | Max pending items |
| `backpressure_mode` | string | "queue" | `reject`, `queue`, `shed_load` | Behavior at capacity |

#### retry_profiles

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `policy_id` | string | - | - | Retry profile ID |
| `max_attempts` | integer | 3 | 1-10 | Max retries |
| `base_backoff_ms` | integer | 250 | 0-60000 | Base backoff |
| `max_backoff_ms` | integer | 2000 | 0-600000 | Cap for backoff |
| `jitter_pct` | integer | 20 | 0-100 | Random jitter % |

#### circuit_breaker_defaults

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `failure_threshold` | integer | 5 | 1-100 | Consecutive failures before open |
| `open_duration_ms` | integer | 30000 | 1000-3600000 | Open state duration |
| `half_open_attempts` | integer | 2 | 1-10 | Trial requests before close |

#### event_channel_policies

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `batch_size` | integer | 20 | 1-1000 | Items per poll |
| `poll_interval_ms` | integer | 500 | 50-60000 | Poll cadence |
| `max_parallel_consumers` | integer | 8 | 1-1000 | Concurrency per channel |

#### observability

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `metrics_sampling_rate` | number | 0.1 | 0-1 | Sampling for metrics |
| `trace_retention_days` | integer | 14 | 1-365 | Trace retention |
| `alert_thresholds.error_rate_pct` | number | 2.5 | 0-100 | Error rate threshold |
| `alert_thresholds.dlq_depth` | integer | 50 | 0-100000 | DLQ threshold |
| `alert_thresholds.latency_p95_ms` | integer | 2000 | 10-600000 | Latency threshold |

#### idempotency

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `idempotency_ttl_ms` | integer | 86400000 | 0-31536000000 | Dedup TTL |
| `dedup_scope` | string | "workflow" | `run`, `workflow`, `connector` | Idempotency key scope |

---

## connectors.json Extensions

**Purpose:** Per-connector scaling overrides and resilience policies.

**Location:** `registries/integration/connectors.json`

### Proposed Additions (per connector)

```json
{
  "connector_id": "guidewire_claims",
  "scaling": {
    "max_concurrency": 10,
    "qps_limit": 25,
    "burst_limit": 50
  },
  "retry_policy_id": "standard",
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
```

### Field Definitions

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `scaling.max_concurrency` | integer | system default | 1-10000 | Connector concurrency |
| `scaling.qps_limit` | integer | system default | 1-100000 | QPS cap |
| `scaling.burst_limit` | integer | system default | 1-200000 | Burst allowance |
| `retry_policy_id` | string | system default | - | Retry profile |
| `circuit_breaker.*` | object | system default | - | Circuit breaker overrides |
| `region_affinity.primary` | string | - | region code | Primary region |
| `region_affinity.fallbacks` | array | [] | region codes | Failover regions |

---

## workflows/*.json Extensions

**Purpose:** Per-workflow throughput and SLA controls.

**Location:** `registries/integration/workflows/*.json`

### Proposed Additions

```json
{
  "workflow_id": "claim_fnol_sync",
  "priority": "critical",
  "sla": {
    "max_latency_ms": 1500,
    "timeout_ms": 5000,
    "fast_fail_threshold": 2
  },
  "throughput": {
    "max_concurrency": 5,
    "queue_depth_limit": 100
  }
}
```

### Field Definitions

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `priority` | string | "standard" | `critical`, `standard`, `bulk` | Scheduling priority |
| `sla.max_latency_ms` | integer | - | 10-600000 | Target latency |
| `sla.timeout_ms` | integer | - | 10-600000 | Hard timeout |
| `sla.fast_fail_threshold` | integer | 0 | 0-10 | Failures before fast-fail |
| `throughput.max_concurrency` | integer | system default | 1-10000 | Workflow concurrency |
| `throughput.queue_depth_limit` | integer | system default | 1-100000 | Workflow queue depth |

---

## auth_profiles.json Extensions

**Purpose:** Per-tenant throttling and fairness policies.

**Location:** `registries/integration/auth_profiles.json`

### Proposed Additions

```json
{
  "profile_id": "guidewire_oidc",
  "tenant_limits": {
    "tenant_id": "enterprise-001",
    "qps_limit": 20,
    "burst_limit": 40,
    "priority_override": "critical"
  }
}
```

### Field Definitions

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `tenant_limits.tenant_id` | string | - | - | Tenant identifier |
| `tenant_limits.qps_limit` | integer | system default | 1-100000 | Tenant QPS |
| `tenant_limits.burst_limit` | integer | system default | 1-200000 | Tenant burst |
| `tenant_limits.priority_override` | string | none | `critical`, `standard`, `bulk` | Tenant priority override |

---

## Override Rules

1. Workflow settings override connector and system defaults.
2. Connector settings override system defaults.
3. System defaults apply when fields are missing.

---

## Validation Rules

- `max_concurrency`, `qps_limit`, and `burst_limit` must be positive integers.
- `queue_depth_limit` must be >= 1.
- `jitter_pct` must be 0-100.
- `event_channel_policies` keys must exist in `event_driven_channels`.
- SLA values must be >= 10 ms.

---

## Notes

This draft is configuration-only and intended to demonstrate scalability features in the registry. Runtime enforcement is out of scope for the current iteration.

