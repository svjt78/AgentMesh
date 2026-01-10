# Integration Scalability

This document describes the Integration Scalability configuration surface exposed in the Configuration UI. The controls are currently UI-only (local state) to demonstrate how scalability settings would be managed before backend wiring.

## Location
- UI: Configuration → Integration Scalability
- Component: `frontend/components/config/IntegrationScalabilityTab.tsx`

## Scope
Covers system defaults, retry profiles, event channels, connector scaling, workflow scaling, and tenant limits.

## System Defaults
Global throughput and backpressure defaults applied across integrations.

Fields:
- **Max Concurrency**: Cap on simultaneous integrations across the platform.
- **QPS Limit**: Max requests per second across all connectors.
- **Burst Limit**: Short-term allowance above steady-state QPS.
- **Queue Depth**: Maximum number of queued tasks waiting for execution.
- **Backpressure Mode**: Behavior at capacity (`queue`, `reject`, `shed_load`).

## Retry Profiles
Retry strategy templates used by connectors and workflows.

Fields:
- **Max Attempts**: Total tries before failure.
- **Base Backoff (ms)**: Initial wait before the first retry.
- **Max Backoff (ms)**: Upper bound on exponential delay.
- **Jitter %**: Randomization applied to spread retries.

## Event Channels
Configuration for MQ/pubsub-style channels.

Fields:
- **Enabled**: Toggle the channel policy on or off.
- **Batch Size**: Messages pulled per poll.
- **Poll Interval (ms)**: Time between polls.
- **Consumers**: Parallel consumers for the channel.

## Connector Scalability
Per-connector limits and circuit breaker settings.

Fields:
- **Max Concurrency**: Connector-specific in-flight cap.
- **QPS Limit**: Connector requests per second.
- **Burst Limit**: Connector short spike allowance.
- **Failure Threshold**: Errors before circuit opens.
- **Open Duration (ms)**: Time to keep breaker open before half-open.
- **Half-Open Attempts**: Trial requests to close the breaker.
- **Primary Region**: Preferred execution region.
- **Fallback Region**: Secondary region if primary is unhealthy.

## Workflow Scaling
Per-workflow scheduling and SLA controls.

Fields:
- **Priority**: `critical`, `standard`, or `bulk` scheduling tier.
- **Max Latency (ms)**: Target p95 completion latency.
- **Timeout (ms)**: Hard execution timeout.
- **Fast Fail**: Errors before short-circuiting.
- **Max Concurrency**: Concurrent runs allowed.
- **Queue Depth**: Maximum queued runs.

## Tenant Limits
Tenant-specific throttling and priority overrides.

Fields:
- **Tenant ID**: Tenant identifier for the limits.
- **Priority Override**: Forced scheduling tier for the tenant.
- **QPS Limit**: Tenant requests per second cap.
- **Burst Limit**: Tenant short spike allowance.

## Notes
- These settings are currently not persisted to backend registries.
- Tooltips in the UI provide short explanations for each field.

