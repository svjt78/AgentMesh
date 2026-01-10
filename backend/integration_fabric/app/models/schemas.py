from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ThroughputLimits(BaseModel):
    max_concurrency: Optional[int] = None
    qps_limit: Optional[int] = None
    burst_limit: Optional[int] = None
    queue_depth_limit: Optional[int] = None
    backpressure_mode: Optional[str] = None


class CircuitBreakerConfig(BaseModel):
    failure_threshold: Optional[int] = None
    open_duration_ms: Optional[int] = None
    half_open_attempts: Optional[int] = None


class EventChannelPolicy(BaseModel):
    batch_size: Optional[int] = None
    poll_interval_ms: Optional[int] = None
    max_parallel_consumers: Optional[int] = None


class AlertThresholds(BaseModel):
    error_rate_pct: Optional[float] = None
    dlq_depth: Optional[int] = None
    latency_p95_ms: Optional[int] = None


class ObservabilityConfig(BaseModel):
    metrics_sampling_rate: Optional[float] = None
    trace_retention_days: Optional[int] = None
    alert_thresholds: Optional[AlertThresholds] = None


class IdempotencyConfig(BaseModel):
    idempotency_ttl_ms: Optional[int] = None
    dedup_scope: Optional[str] = None


class RegionAffinity(BaseModel):
    primary: Optional[str] = None
    fallbacks: List[str] = Field(default_factory=list)


class SlaConfig(BaseModel):
    max_latency_ms: Optional[int] = None
    timeout_ms: Optional[int] = None
    fast_fail_threshold: Optional[int] = None


class TenantLimit(BaseModel):
    tenant_id: str
    qps_limit: Optional[int] = None
    burst_limit: Optional[int] = None
    priority_override: Optional[str] = None


class ConnectorMetadata(BaseModel):
    connector_id: str
    name: str
    description: str
    type: str
    base_url: str
    auth_profile: Optional[str] = None
    timeout_ms: int = 5000
    supports_idempotency: bool = False
    simulator_profile: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    scaling: Optional[ThroughputLimits] = None
    retry_policy_id: Optional[str] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    region_affinity: Optional[RegionAffinity] = None


class AuthProfile(BaseModel):
    profile_id: str
    name: str
    type: str
    config: Dict[str, Any]
    tenant_limits: List[TenantLimit] = Field(default_factory=list)


class SecurityRule(BaseModel):
    field: str
    action: str


class SecurityPolicy(BaseModel):
    policy_id: str
    name: str
    description: str
    rules: List[SecurityRule]


class WorkflowStep(BaseModel):
    id: str
    type: str
    connector: Optional[str] = None
    operation: Optional[str] = None
    policy: Optional[str] = None
    idempotency: bool = False
    retry_policy: Optional[str] = None
    failure_policy: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    description: str
    version: str
    trigger: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: Optional[str] = None
    sla: Optional[SlaConfig] = None
    throughput: Optional[ThroughputLimits] = None


class RetryPolicy(BaseModel):
    policy_id: str
    max_attempts: int
    backoff_seconds: float


class SystemConfig(BaseModel):
    version: str
    retry_policies: List[RetryPolicy]
    features: Dict[str, Any] = Field(default_factory=dict)
    throughput_limits: Optional[ThroughputLimits] = None
    circuit_breaker_defaults: Optional[CircuitBreakerConfig] = None
    event_channel_policies: Dict[str, EventChannelPolicy] = Field(default_factory=dict)
    observability: Optional[ObservabilityConfig] = None
    idempotency: Optional[IdempotencyConfig] = None


class RunRequest(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]
    simulate_failure: bool = False


class RunResponse(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    created_at: str
    stream_url: str
    run_url: str


class RunStepResult(BaseModel):
    step_id: str
    status: str
    attempts: int
    idempotency_key: Optional[str] = None
    connector: Optional[str] = None
    operation: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    output: Dict[str, Any] = Field(default_factory=dict)


class RunDetail(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    input_data: Dict[str, Any]
    steps: List[RunStepResult]
    events: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class RunListItem(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None


class RunListResponse(BaseModel):
    runs: List[RunListItem]
    total_count: int


class DLQItem(BaseModel):
    item_id: str
    run_id: str
    step_id: str
    workflow_id: str
    error: str
    created_at: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class DLQListResponse(BaseModel):
    items: List[DLQItem]
    total_count: int


class RegistryOperationResponse(BaseModel):
    success: bool
    message: str


class ConnectorListResponse(BaseModel):
    connectors: List[ConnectorMetadata]
    total_count: int


class AuthProfileListResponse(BaseModel):
    profiles: List[AuthProfile]
    total_count: int


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowDefinition]
    total_count: int


class SecurityPolicyListResponse(BaseModel):
    policies: List[SecurityPolicy]
    total_count: int


class SystemConfigResponse(BaseModel):
    config: SystemConfig
