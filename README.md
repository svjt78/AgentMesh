# AgentMesh - Production-Scale Multi-Agentic Insurance Framework

**Flagship demonstration of scalable multi-agent solutions using Bounded ReAct Agents**

> A fully working, dockerized prototype demonstrating production-grade patterns for building scalable multi-agent systems for insurance claims processing.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [AIF Quick Start](#aif-quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Using the System](#using-the-system)
- [Development Guide](#development-guide)
- [API Documentation](#api-documentation)
- [Deployment Considerations](#deployment-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AgentMesh is a **production-ready multi-agent orchestration platform** specifically designed for insurance claims processing. It demonstrates how to build scalable, observable, and governable AI agent systems that can be deployed in regulated enterprise environments.

### What Problems Does It Solve?

1. **Agent Coordination**: How do multiple specialized AI agents work together without hardcoded workflows?
2. **Governance**: How do you enforce policies and limits in autonomous agent systems?
3. **Observability**: How do you track and replay complex multi-agent decision chains?
4. **Scalability**: How do you design agent systems that can scale horizontally?
5. **Explainability**: How do you generate transparent, auditable evidence maps for AI-driven decisions in regulated industries?
6. **Human-in-the-Loop Accountability**: How do you integrate human oversight with audit trails for critical decision points?

### Key Innovations

- **Meta-Agent Orchestration**: The orchestrator itself is a ReAct agent that dynamically discovers and invokes worker agents
- **Registry-Driven Architecture**: All agents, tools, and workflows defined in JSON registries (zero hardcoding)
- **Bounded Execution**: Hard iteration limits, timeouts, and token budgets prevent runaway loops
- **Complete Observability**: Every event logged to JSONL streams for full replay capability
- **Multi-Tier Completion**: LLM signal → validation → forced completion ensures workflows always terminate
- **Evidence Maps**: Structured explainability artifacts for every decision
- **Human-in-the-Loop (HITL)**: Configurable checkpoints for human intervention, approval, and decision-making
- **Checkpoint System**: Pause/resume workflows with timeout behaviors and role-based access control
- **Advanced Configuration**: System-wide config via JSON registry with environment variable overrides

---

## Key Features

### ✅ **7 Specialized Agents**
- **1 Orchestrator Agent**: Meta-agent that coordinates workflow execution
- **6 Worker Agents**:
  - Intake Agent: Validates and normalizes claim data
  - Coverage Agent: Determines policy coverage and eligibility
  - Fraud Agent: Detects fraud signals and risk patterns
  - Severity Agent: Assesses claim complexity
  - Recommendation Agent: Determines next best action
  - Explainability Agent: Compiles evidence maps

### ✅ **6 Mock Tools**
- Policy Snapshot: Retrieves policy coverage details
- Fraud Rules Engine: Evaluates fraud detection rules
- Similarity Search: Finds similar historical claims
- Schema Validator: Validates claim data structure
- Coverage Rules: Determines coverage eligibility
- Decision Rules: Recommends processing actions

### ✅ **Multi-Provider LLM Support**
- **OpenAI**: GPT-3.5 Turbo, GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- Agent-level model selection for cost optimization

### ✅ **Production-Grade Features**
- Dynamic agent discovery from registries
- Policy-driven governance enforcement
- Token-aware context management
- Iteration limits and timeouts
- Complete event streaming (JSONL)
- Real-time SSE (Server-Sent Events) broadcasting
- Structured output validation (Pydantic)
- Multi-tier workflow completion
- Evidence map generation

### ✅ **Executive UI**
- Next.js frontend with live progress monitoring
- Real-time SSE event streaming
- **Multi-tab Observability Interface**:
  - **Event Timeline**: Complete session event replay with filtering
  - **Token Analytics**: Context compilation statistics and token budget visualization
  - **Explainability**: Evidence-based decision explanation with 6 key sections
- Evidence map visualization with decision rationale, confidence scores, and financial metrics
- Human interventions audit trail with complete accountability
- Accountability (HITL checkpoints) configuration and dashboard
- Configuration management UI for registry editing (including Context Engineering tab)
- Interactive workflow diagram visualization with human touchpoint nodes (ReactFlow)
- Contextual help tooltips throughout the interface
- Session management with listing, filtering, and deletion
- Responsive design with Tailwind CSS

### ✅ **Integration Fabric (AIF)**
- **Standalone FastAPI service** (port 8020) for enterprise integration with insurer core systems
- **4 Production Connectors**: Guidewire Claims, Duck Creek Policy, Socotra Billing, Mainframe Legacy Adapter
- **4 Demo Workflows**: FNOL Sync, Claim Status Update, Billing Sync, Integration Failure Drill
- **Idempotency by Design**: File-backed deduplication prevents duplicate external API calls
- **Dead Letter Queue (DLQ)**: Failed operations automatically queued for investigation and replay
- **Security Policies**: PII/PCI masking rules (configuration-only in demo)
- **Retry & Circuit Breaker**: Configurable retry policies and circuit breaker settings per connector
- **SSE Event Streaming**: Real-time run progress via `/runs/{run_id}/stream`
- **Complete Audit Trail**: Every integration step logged to `storage/integration/runs/`
- **Integrations UI**: Complete management interface at `/integrations`
- **Configuration UI**: Integration Scalability tab (10th tab in Configuration page)

**📚 Complete Documentation:**
- **Quick Start**: [AIF.md](AIF.md) - Service overview and workflow execution
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md#integration-fabric-api) - Complete endpoint documentation
- **Scalability Config**: [INTEGRATION_SCALABILITY.md](INTEGRATION_SCALABILITY.md) - UI configuration guide
- **Architecture**: [agent_mesh_integration_fabric_detailed_specifications.md](agent_mesh_integration_fabric_detailed_specifications.md) - Complete specifications

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│  - Run Workflow Form - Live Progress    - Evidence Map     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP + SSE
┌─────────────────────────▼───────────────────────────────────┐
│              Orchestrator API (FastAPI)                      │
│  - Workflow Executor  - SSE Broadcaster  - Session Manager  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌─────▼──────┐ ┌────────▼────────┐
│ Registry       │ │ LLM Client │ │ Tools Gateway   │
│ Manager        │ │ (OpenAI/   │ │ (Mock Tools)    │
│ - Agents       │ │  Anthropic)│ │ - Fraud Rules   │
│ - Tools        │ └────────────┘ │ - Policy Lookup │
│ - Models       │                │ - Coverage Calc │
│ - Workflows    │                └─────────────────┘
│ - Governance   │
└────────────────┘
```

### Orchestration Flow

```
1. User submits claim via Frontend
2. API creates workflow session
3. Orchestrator Agent (meta-agent) starts ReAct loop:
   a. Assesses workflow state
   b. Decides which worker agent(s) to invoke
   c. Invokes worker agent(s) via AgentReActLoopController
   d. Worker agent executes its own ReAct loop with tools
   e. Worker agent returns structured output
   f. Orchestrator compiles results and continues
4. Orchestrator builds final evidence map
5. Results streamed to frontend via SSE
6. Session saved to JSONL for replay
```

### Scalability Patterns Demonstrated

1. **Loose Coupling**: Registry-driven discovery
2. **Bounded Execution**: Iteration limits, timeouts, token budgets
3. **Stateless Services**: Can scale horizontally
4. **Event Sourcing**: JSONL event streams for replay
5. **Policy-Driven Governance**: Runtime enforcement
6. **Multi-Provider LLM**: Avoid vendor lock-in
7. **Context Management**: Token-aware compilation
8. **Structured Outputs**: Pydantic validation
9. **Observability**: Complete audit trails
10. **Graceful Degradation**: Multi-tier completion

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (v20.10+)
- **LLM API Key**: OpenAI or Anthropic API key
- **System Requirements**:
  - 8GB RAM minimum (16GB recommended)
  - 10GB free disk space
  - Ports available: 3016 (frontend), 8016 (orchestrator), 8010 (tools), 8020 (integration fabric)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd AgentMesh
```

2. **Configure environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key(s)
nano .env
```

Required environment variables:
```bash
OPENAI_API_KEY=your-openai-api-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

3. **Start the platform**

```bash
# Start all services
docker compose up

# Or run in detached mode
docker compose up -d
```

4. **Verify services are running**

```bash
# Check service health
curl http://localhost:8016/health
curl http://localhost:8010/health
curl http://localhost:8020/health

# View logs
docker compose logs -f orchestrator
```

5. **Access the UI**

- **Frontend Home**: http://localhost:3016
- **Run Workflow**: http://localhost:3016/run-claim
- **Observability (Sessions List)**: http://localhost:3016/replay
- **Observability Detail (Multi-tab Interface)**: http://localhost:3016/replay/{session_id}
  - Event Timeline tab - Complete session event replay
  - Token Analytics tab - Context compilation and token budgets
  - Explainability tab - Evidence-based decision explanation
- **Memory Browser**: http://localhost:3016/memory
- **Artifact Versions**: http://localhost:3016/artifacts
- **Interventions (HITL) Dashboard**: http://localhost:3016/hitl
- **Configuration UI**: http://localhost:3016/config
  - Agents, Tools, Models, Workflows tabs
  - Governance Policies, System Config tabs
  - Accountability (HITL) tab
  - **Context Engineering tab** - Configure context strategies and processor pipeline
- **Integrations (AIF)**: http://localhost:3016/integrations
- **API Documentation**: http://localhost:8016/docs
- **AIF API Documentation**: http://localhost:8020/docs
- **API Health**: http://localhost:8016/health

### AIF Quick Start

- **Docs**: `AIF.md`
- **UI**: Open http://localhost:3016/integrations and run the FNOL sync or failure drill workflows
- **API**:

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

### Run Your First Workflow

#### Option 1: Via Frontend UI

1. Navigate to http://localhost:3016/run-claim
2. Fill in claim details or load sample data
3. Click "Submit Claim"
4. Watch agents execute in real-time
5. View the final Evidence Map

#### Option 2: Via API (cURL)

```bash
# Submit a clean claim
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "claims_triage",
    "input_data": {
      "claim_id": "CLM-TEST-001",
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
    }
  }'
```

Response:
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

#### Option 3: Via Sample Data

```bash
# Use pre-built sample claims
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "claims_triage",
    "input_data": '$(cat sample_data/sample_claim_clean.json)'
  }'
```

### Monitor Live Execution

```bash
# Stream events via SSE
curl -N http://localhost:8016/runs/{session_id}/stream
```

### View Results

```bash
# Get complete session details
curl http://localhost:8016/sessions/{session_id}

# Get evidence map
curl http://localhost:8016/sessions/{session_id}/evidence
```

---

## Project Structure

```
AgentMesh/
├── backend/
│   └── orchestrator/           # Main orchestrator service
│       ├── app/
│       │   ├── api/            # API endpoints
│       │   │   ├── models.py   # Request/response schemas
│       │   │   ├── runs.py     # Workflow execution endpoints
│       │   │   ├── sessions.py # Session retrieval endpoints
│       │   │   ├── checkpoints.py # HITL checkpoint endpoints
│       │   │   └── registries.py  # Registry management endpoints
│       │   ├── config.py       # Configuration management
│       │   ├── main.py         # FastAPI application
│       │   ├── prompts/        # ReAct prompt templates
│       │   │   └── react_prompts.py
│       │   ├── schemas/        # Agent output schemas
│       │   │   ├── agent_outputs.py
│       │   │   └── validators.py
│       │   └── services/       # Core services
│       │       ├── agent_react_loop.py        # Worker agent ReAct loop
│       │       ├── checkpoint_manager.py      # HITL checkpoint coordination
│       │       ├── checkpoint_store.py        # Checkpoint persistence
│       │       ├── context_compiler.py        # Token-aware context management
│       │       ├── governance_enforcer.py     # Policy enforcement
│       │       ├── llm_client.py              # Multi-provider LLM client
│       │       ├── orchestrator_runner.py     # Meta-agent ReAct loop
│       │       ├── progress_store.py          # Workflow progress tracking
│       │       ├── registry_manager.py        # Dynamic discovery
│       │       ├── response_parser.py         # JSON response parsing
│       │       ├── sse_broadcaster.py         # SSE event streaming
│       │       ├── storage.py                 # JSONL/JSON operations
│       │       ├── tools_gateway_client.py    # Tools invocation
│       │       └── workflow_executor.py       # Background execution
│       ├── Dockerfile
│       └── requirements.txt
│   └── integration_fabric/     # Integration Fabric API
│       ├── app/
│       │   ├── api/            # API endpoints
│       │   │   ├── runs.py     # Workflow execution and SSE streaming
│       │   │   ├── dlq.py      # Dead letter queue management
│       │   │   └── registries.py  # Registry access endpoints
│       │   ├── models/
│       │   │   └── schemas.py  # Pydantic models for workflows
│       │   ├── services/       # Core services
│       │   │   ├── workflow_runner.py      # Integration orchestration
│       │   │   ├── connector_executor.py   # REST connector simulation
│       │   │   ├── idempotency_store.py    # Deduplication cache
│       │   │   ├── dlq_store.py            # Failed operation queue
│       │   │   ├── run_store.py            # Execution state storage
│       │   │   ├── security_engine.py      # PII/PCI policy engine (stub)
│       │   │   ├── registry_manager.py     # Integration registry loader
│       │   │   └── sse_broadcaster.py      # Real-time event streaming
│       │   ├── config.py       # Configuration management
│       │   └── main.py         # FastAPI application
│       ├── Dockerfile
│       └── requirements.txt
│
├── tools/
│   └── tools_gateway/          # Mock tools service
│       ├── app/
│       │   ├── main.py         # Tools API
│       │   └── tools/          # Tool implementations
│       ├── Dockerfile
│       └── requirements.txt
│
├── frontend/                   # Next.js UI
│   ├── app/
│   │   ├── run-claim/          # Submit claim page
│   │   ├── replay/             # Observability interface
│   │   │   ├── page.tsx        # Sessions list/index page
│   │   │   └── [sessionId]/    # Multi-tab session detail
│   │   │       └── page.tsx    # Event Timeline, Token Analytics, Explainability tabs
│   │   ├── memory/             # Memory browser page
│   │   ├── artifacts/          # Artifact versions page
│   │   ├── hitl/               # Human-in-the-Loop dashboard
│   │   ├── integrations/       # Integration Fabric UI
│   │   │   └── page.tsx        # Workflow runs, connectors, DLQ, policies
│   │   ├── config/             # Configuration management UI
│   │   │   └── page.tsx        # Multi-tab config (10 tabs)
│   │   └── layout.tsx
│   ├── components/
│   │   ├── Navigation.tsx      # Navigation component (updated labels)
│   │   ├── InfoTooltip.tsx     # Contextual help tooltips (NEW)
│   │   ├── config/             # Config UI components
│   │   │   ├── ContextEngineeringTab.tsx       # Context strategies config (NEW)
│   │   │   ├── IntegrationScalabilityTab.tsx   # Integration scalability config (NEW)
│   │   │   └── workflow-diagram/
│   │   │       ├── WorkflowDiagram.tsx    # Workflow visualization
│   │   │       ├── NodeDetailsPanel.tsx   # Node details view
│   │   │       ├── DiagramControls.tsx    # Diagram filters
│   │   │       ├── types.ts              # TypeScript types
│   │   │       └── nodes/
│   │   │           └── HumanTouchpointNode.tsx  # Human approval node (NEW)
│   │   └── visualization/      # Data visualization components
│   │       ├── ContextTimeline.tsx        # Context compilation timeline (NEW)
│   │       ├── TokenBudgetChart.tsx       # Token usage chart (NEW)
│   │       └── ContextLineageTree.tsx     # Processor execution tree (NEW)
│   ├── hooks/
│   │   └── use-sse.ts          # SSE subscription hook
│   ├── lib/
│   │   ├── api-client.ts       # API client utility
│   │   ├── demo-evidence.ts    # Demo evidence map data (NEW)
│   │   └── diagram/            # Workflow diagram utilities
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
│
├── registries/                 # Configuration-driven registries
│   ├── agent_registry.json     # Agent definitions
│   ├── tool_registry.json      # Tool catalog
│   ├── model_profiles.json     # LLM configurations
│   ├── governance_policies.json # Access control policies
│   ├── system_config.json      # System-wide configuration
│   ├── workflows/
│   │   └── claims_triage.json  # Workflow definition with HITL checkpoints
│   └── integration/            # Integration Fabric registries
│       ├── connectors.json     # REST connectors (Guidewire, Duck Creek, Socotra, Mainframe)
│       ├── auth_profiles.json  # Auth strategies (OAuth, Token, API Key, Service Account)
│       ├── security_policies.json  # PII/PCI masking rules
│       ├── system_config.json  # Retry policies, timeout settings
│       └── workflows/          # Integration workflow definitions
│           ├── claim_fnol_sync.json
│           ├── claim_status_update.json
│           ├── billing_sync.json
│           └── integration_failure_drill.json
│
├── storage/                    # Persistent storage
│   ├── sessions/               # JSONL event streams
│   ├── artifacts/              # Evidence maps
│   ├── checkpoints/            # HITL checkpoint data
│   ├── compactions/            # Compacted session data
│   └── integration/            # Integration Fabric storage
│       ├── runs/               # Integration run executions
│       │   ├── {run_id}.json       # Run metadata and state
│       │   └── {run_id}_events.jsonl  # Step-by-step event log
│       ├── idempotency/        # Deduplication cache
│       │   └── {idempotency_key}.json  # Cached operation results (24h TTL)
│       └── dlq/                # Dead letter queue
│           └── items.jsonl     # Failed operations (append-only)
│
├── sample_data/                # Sample claims for testing
│   ├── sample_claim_clean.json
│   ├── sample_claim_fraud.json
│   ├── sample_claim_edge_case.json
│   └── README.md
│
├── docker-compose.yml          # Service orchestration
├── .env                        # Environment configuration
├── README.md                   # This file
├── API_REFERENCE.md            # Complete API documentation (NEW)
├── AIF.md                      # Integration Fabric quick reference (NEW)
├── INTEGRATION_SCALABILITY.md  # Integration Scalability UI guide (NEW)
├── INTEGRATION_SCALABILITY_CONFIG.md  # Registry schema reference (NEW)
├── agent_mesh_integration_fabric_detailed_specifications.md  # Complete AIF specs (NEW)
├── CLAUDE.md                   # Claude Code development guidelines
├── DECISIONS.md                # Architectural decisions
├── IMPLEMENTATION_PROGRESS.md  # Development progress
├── EXPLAINABILITY_TAB_DOCUMENTATION.md  # Explainability interface guide
├── HUMAN_IN_THE_LOOP.md        # HITL feature documentation
├── CONFIGURATION.md            # Configuration management guide
├── AGENTS.md                   # Agent design documentation
├── ISSUES_AND_FIXES.md         # Known issues and solutions
├── REGISTRY_MANAGEMENT_PLAN.md # Registry design patterns
└── TIKTOKEN_USAGE.md           # Token counting implementation

```

---

## Configuration

### Environment Variables

All configuration is managed via environment variables in `.env`:

#### LLM Provider Configuration

```bash
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API Key (Claude)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Note**: You need at least one API key. Both can be configured for model comparison.

#### Service URLs

```bash
# Internal Docker network URLs
TOOLS_BASE_URL=http://tools_gateway:8010

# External ports
ORCHESTRATOR_PORT=8016
FRONTEND_PORT=3016
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:8016
```

#### Execution Limits

```bash
# Orchestrator Agent
ORCHESTRATOR_MAX_ITERATIONS=10
ORCHESTRATOR_ITERATION_TIMEOUT_SECONDS=30

# Workflow
WORKFLOW_MAX_DURATION_SECONDS=300
WORKFLOW_MAX_AGENT_INVOCATIONS=20

# Worker Agents (defaults)
AGENT_DEFAULT_MAX_ITERATIONS=5
AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS=30
AGENT_MAX_DUPLICATE_INVOCATIONS=2

# LLM
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3
LLM_MAX_TOKENS_PER_REQUEST=2000
LLM_MAX_TOKENS_PER_SESSION=50000

# Governance
MAX_TOOL_INVOCATIONS_PER_SESSION=50
MAX_LLM_CALLS_PER_SESSION=30

# Safety
CONSECUTIVE_NO_PROGRESS_LIMIT=2
MALFORMED_RESPONSE_LIMIT=3
```

### Registry Files

#### Agent Registry (`registries/agent_registry.json`)

Defines all agents with capabilities, tool access, and output schemas.

**Key fields**:
- `agent_id`: Unique identifier
- `capabilities`: List of capabilities (for discovery)
- `allowed_tools`: Tools this agent can invoke
- `allowed_agents`: Agents this agent can invoke (for orchestrator)
- `model_profile_id`: Reference to LLM model
- `max_iterations`: Iteration limit
- `output_schema`: Expected output structure (JSON Schema)
- `context_requirements`: Dependencies on prior agent outputs

#### Tool Registry (`registries/tool_registry.json`)

Catalog of all available tools with LLM-friendly descriptions.

**Key fields**:
- `tool_id`: Unique identifier
- `name`: Human-readable name
- `description`: When and how to use this tool (for LLM reasoning)
- `endpoint`: HTTP endpoint URL
- `input_schema`: Expected parameters (JSON Schema)
- `output_schema`: Response structure
- `lineage_tags`: Categories for discovery

#### Model Profiles (`registries/model_profiles.json`)

LLM model configurations for multi-provider support.

**Key fields**:
- `profile_id`: Unique identifier
- `provider`: "openai" or "anthropic"
- `model_name`: Model identifier (e.g., "gpt-3.5-turbo", "claude-3-5-sonnet-20241022")
- `parameters`: Temperature, max_tokens, etc.
- `json_mode`: Whether to use JSON mode (OpenAI only)
- `constraints`: Token limits
- `retry_policy`: Retry configuration

#### Governance Policies (`registries/governance_policies.json`)

Access control and execution constraints.

**Policy Types**:
- **Agent Invocation Access**: Which agents can invoke which agents
- **Agent Tool Access**: Which tools each agent can use
- **Iteration Limits**: Max iterations per agent
- **Execution Constraints**: Global limits (duration, tool calls, LLM calls)

#### System Configuration (`registries/system_config.json`)

System-wide execution limits and safety thresholds.

**Key sections**:
- `orchestrator`: Meta-agent iteration limits and timeouts
- `workflow`: Session-wide constraints (max duration, agent invocations)
- `agent`: Worker agent default limits
- `llm`: API interaction settings, token budgets
- `governance`: Cross-cutting session limits
- `safety`: Error recovery and circuit breaker mechanisms
- `schema`: Output validation configuration
- `checkpoint`: HITL checkpoint defaults
- `context_engineering`: Master toggle and pipeline enablement

**Note**: Values in this file override hardcoded defaults in `config.py`. API keys and service URLs remain in `.env` for security.

#### Workflow Definition (`registries/workflows/claims_triage.json`)

Workflow configuration in **advisory mode** with optional HITL checkpoints.

**Key fields**:
- `workflow_id`: Unique identifier
- `mode`: "advisory" (orchestrator can adapt)
- `goal`: High-level objective
- `suggested_sequence`: Recommended agent order
- `required_agents`: Must execute
- `optional_agents`: May skip
- `completion_criteria`: When workflow is complete
- `constraints`: Max duration, iterations, invocations
- `checkpoints`: HITL intervention points (optional)
  - `checkpoint_id`: Unique identifier
  - `trigger`: When to pause (before_agent, after_agent, condition)
  - `intervention_type`: approval, data_input, decision, escalation
  - `timeout_behavior`: auto_approve, auto_reject, cancel, wait_indefinitely
  - `required_roles`: Role-based access control

---

## Using the System

### Submitting Claims

#### Via Frontend

1. **Navigate**: http://localhost:3016/run-claim
2. **Fill Form**: Enter claim details
3. **Submit**: Click "Submit Claim"
4. **Monitor**: Watch live progress in right panel
5. **View Evidence**: Click "View Evidence Map" when complete

#### Via API

```bash
POST /runs
Content-Type: application/json

{
  "workflow_id": "claims_triage",
  "input_data": {
    "claim_id": "CLM-001",
    "policy_id": "POL-001",
    ...
  }
}
```

Response includes `stream_url` for SSE monitoring.

### Integration Fabric (AIF)

#### Via Frontend

1. **Navigate**: http://localhost:3016/integrations
2. **Select Workflow**: Choose FNOL sync, status update, or failure drill
3. **Run Workflow**: Trigger run and inspect traces, DLQ, and policies

#### Via API

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

### Monitoring Execution

#### Real-Time SSE Stream

```bash
# Browser EventSource
const eventSource = new EventSource('http://localhost:8016/runs/{session_id}/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};

# cURL
curl -N http://localhost:8016/runs/{session_id}/stream
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

#### Session Replay

```bash
GET /sessions/{session_id}

# Returns complete event timeline
```

### Viewing Results

#### Evidence Map (Explainability Tab)

The Explainability tab in the Observability interface provides comprehensive, transparent documentation of how the system arrived at its decision.

**Access via UI**: http://localhost:3016/replay/{session_id} → Explainability tab

**Access via API**:
```bash
GET /sessions/{session_id}/evidence
```

Returns structured evidence map with **6 key sections**:

1. **Decision**
   - Final outcome (APPROVE_CLAIM, DENY_CLAIM, REQUIRES_MANUAL_REVIEW)
   - Confidence score (0-100%) with visual progress bar
   - Decision rationale (comprehensive explanation)
   - Financial exposure and potential savings

2. **Supporting Evidence**
   - Agent-by-agent findings with detailed analysis
   - Evidence weights (relative importance 0-100%)
   - Fraud risk scores when applicable
   - Source traceability for each piece of evidence

3. **Human Interventions**
   - Complete audit trail of human touchpoints
   - Intervention type, timestamp, reviewer details
   - Actions taken and decision impact
   - Comments and observations

4. **Agent Execution Chain**
   - Visual sequence of agents invoked
   - Execution order and flow
   - Agent capabilities utilized

5. **Assumptions**
   - Key assumptions underlying the decision
   - Dependencies that could affect outcome
   - Data quality and completeness assumptions

6. **Limitations**
   - Acknowledged constraints and data gaps
   - Known uncertainties in the analysis
   - Areas requiring human judgment

**Strategic Value**:
- Regulatory compliance and audit trails
- Customer communication (denial explanations)
- SIU investigation support
- Quality assurance and continuous improvement
- Legal defensibility

**See**: [EXPLAINABILITY_TAB_DOCUMENTATION.md](EXPLAINABILITY_TAB_DOCUMENTATION.md) for complete user guide

#### Session Details

```bash
GET /sessions/{session_id}
```

Returns complete session with:
- Input data
- Output data
- All events
- Agents executed
- Warnings and errors
- Execution statistics

### Human-in-the-Loop (HITL)

AgentMesh supports pausing workflows at configurable checkpoints for human intervention.

#### Accessing the HITL Dashboard

```bash
# Navigate to HITL page
http://localhost:3016/hitl
```

The dashboard displays:
- **Active Checkpoints**: Workflows waiting for human intervention
- **Checkpoint Details**: Agent outputs, context, and decision options
- **Action Buttons**: Approve, Reject, Provide Input, or Escalate
- **Timeout Countdown**: Time remaining before auto-action

#### Checkpoint Types

**1. Approval/Rejection**
- Binary decision (approve or reject)
- Example: Approve high-value claim for processing

**2. Data Input/Correction**
- Provide or correct data
- Example: Enter missing policy details

**3. Decision Selection**
- Choose from multiple options
- Example: Select claim assignment (auto-process vs manual review)

**4. Escalation Handling**
- Handle escalated cases requiring expert review
- Example: Fraud investigation decision

#### Responding to Checkpoints

**Via UI**:
1. Navigate to http://localhost:3016/hitl
2. Select checkpoint from active list
3. Review context and agent outputs
4. Make decision (approve/reject/input data)
5. Optionally add comments
6. Submit response

**Via API**:
```bash
POST /checkpoints/{checkpoint_id}/respond
Content-Type: application/json

{
  "decision": "approved",
  "comments": "Verified with customer",
  "data": {
    "corrected_amount": 15000.00
  },
  "responder_id": "user@example.com",
  "responder_role": "claims_adjuster"
}
```

#### Timeout Behaviors

Configured per checkpoint in workflow definition:
- `auto_approve`: Automatically approve after timeout
- `auto_reject`: Automatically reject after timeout
- `cancel`: Cancel workflow after timeout
- `wait_indefinitely`: No timeout, wait for human response

#### Role-Based Access Control

Checkpoints can require specific roles:
- `reviewer`: Basic review permissions
- `approver`: Approval authority
- `admin`: Full administrative access
- `fraud_investigator`: Fraud case handling
- `claims_adjuster`: Claims adjustment permissions

Example workflow checkpoint configuration:
```json
{
  "checkpoint_id": "fraud_review",
  "trigger": {
    "type": "after_agent",
    "agent_id": "fraud_agent"
  },
  "intervention_type": "decision",
  "required_roles": ["fraud_investigator"],
  "timeout_seconds": 3600,
  "timeout_behavior": "escalate",
  "metadata": {
    "title": "Fraud Review Required",
    "description": "High fraud score detected"
  }
}
```

### Configuration Management

The platform includes a web-based configuration management UI.

#### Accessing the Config UI

```bash
# Navigate to configuration page
http://localhost:3016/config
```

**Configuration Tabs** (10 tabs total):

1. **Orchestrator** - Meta-agent settings, iteration limits, timeout configuration
2. **Agents** - Worker agent definitions, capabilities, allowed tools, output schemas
3. **Tools** - Tool catalog with endpoints, descriptions, input/output schemas
4. **Model Profiles** - LLM provider settings (OpenAI, Anthropic), temperature, token limits
5. **Workflows** - Workflow definitions, suggested sequences, completion criteria
6. **Accountability (HITL)** - Human-in-the-loop checkpoint configuration
7. **Governance** - Access control policies, agent/tool permissions, execution constraints
8. **Controllability (System)** - System-wide limits, safety thresholds, circuit breakers
9. **Context Engineering** - Token budgets, compaction settings, memory layer, artifact management
10. **Integration Scalability** - Throughput limits (concurrency, QPS, burst), retry profiles, circuit breaker settings, tenant limits

**Features**:
- View and edit all registry files
- Validate JSON syntax and schema compliance
- Live preview of configuration changes
- Export/import configurations
- Syntax highlighting and error detection

**Note**: Configuration changes require service restart to take effect. Integration Scalability settings are UI-only (local state) and not yet persisted to backend.

---

## Frontend Technology Stack

The frontend is built with modern React and Next.js patterns:

### Core Technologies

- **Next.js 16**: React framework with App Router
- **React 19**: Latest React with concurrent features
- **TypeScript 5**: Full type safety
- **Tailwind CSS 4**: Utility-first CSS framework
- **React Flow**: Interactive workflow diagram visualization
- **Heroicons**: SVG icon library

### Key Libraries

- **dagre**: Graph layout algorithm for workflow diagrams
- **date-fns**: Date manipulation and formatting
- **clsx**: Conditional class name composition

### Frontend Architecture

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── run-claim/           # Claim submission UI
│   ├── replay/              # Observability interface
│   │   ├── page.tsx        # Sessions list with management
│   │   └── [sessionId]/    # Multi-tab session detail view
│   ├── memory/              # Memory browser
│   ├── artifacts/           # Artifact versions browser
│   ├── hitl/                # HITL checkpoint dashboard
│   ├── config/              # Registry configuration editor (8 tabs)
│   └── layout.tsx           # Root layout with navigation
├── components/              # Reusable React components
│   ├── Navigation.tsx       # Main navigation bar (updated labels)
│   ├── InfoTooltip.tsx      # Contextual help tooltips (NEW)
│   ├── config/              # Configuration UI components
│   │   ├── ContextEngineeringTab.tsx  # Context strategies (NEW)
│   │   └── workflow-diagram/
│   │       ├── nodes/
│   │       │   └── HumanTouchpointNode.tsx  # Human approval nodes (NEW)
│   │       └── ...
│   └── visualization/       # Data visualization components (NEW)
│       ├── ContextTimeline.tsx        # Context compilation timeline
│       ├── TokenBudgetChart.tsx       # Token usage charts
│       └── ContextLineageTree.tsx     # Processor execution tree
├── hooks/                   # Custom React hooks
│   └── use-sse.ts          # Server-Sent Events subscription
├── lib/                     # Utilities and helpers
│   ├── api-client.ts       # API client with fetch wrappers
│   ├── demo-evidence.ts    # Demo evidence map data (NEW)
│   └── diagram/            # Workflow diagram utilities
└── public/                  # Static assets
```

### Real-Time Features

**Server-Sent Events (SSE)**:
- Live workflow progress updates
- Real-time agent reasoning display
- Tool invocation streaming
- Error and warning notifications

**Implementation** (`hooks/use-sse.ts`):
```typescript
// Custom hook for SSE subscription
const { events, status, error } = useSSE(sessionId);
```

### State Management

- **React Server Components**: For static content
- **Client Components**: For interactive UI with `use client`
- **URL State**: Session IDs and filters in URL params
- **SSE State**: Real-time updates via EventSource API

### Styling Approach

- **Tailwind CSS**: Utility-first for rapid development
- **Component-Scoped**: No global CSS conflicts
- **Responsive Design**: Mobile-first approach
- **Dark Mode Ready**: CSS variables for theming

---

## Dependencies & Package Management

### Backend Dependencies

**Python 3.11+ Required**

Core dependencies (`backend/orchestrator/requirements.txt`):

```
# Web Framework
fastapi==0.104.1              # Modern async web framework
uvicorn[standard]==0.24.0     # ASGI server
python-multipart==0.0.6       # Form data parsing

# Data Validation
pydantic==2.5.0               # Data validation and schemas
pydantic-settings==2.1.0      # Settings management

# LLM Providers
openai==1.6.1                 # OpenAI GPT-3.5/GPT-4
anthropic==0.8.1              # Anthropic Claude
tiktoken==0.5.2               # Token counting for OpenAI

# Environment & Config
python-dotenv==1.0.0          # .env file loading

# HTTP Client
httpx==0.25.2                 # Async HTTP for tools gateway

# JSON Processing
orjson==3.9.10                # Fast JSON serialization

# Utilities
python-dateutil==2.8.2        # Date/time utilities
```

### Frontend Dependencies

**Node.js 20+ Required**

Production dependencies (`frontend/package.json`):

```json
{
  "dependencies": {
    "@heroicons/react": "^2.2.0",    // Icon library
    "clsx": "^2.1.1",                // Class name utility
    "dagre": "^0.8.5",               // Graph layout algorithm
    "date-fns": "^4.1.0",            // Date utilities
    "next": "16.1.1",                // React framework
    "react": "19.2.3",               // React library
    "react-dom": "19.2.3",           // React DOM
    "reactflow": "^11.11.4"          // Workflow diagrams
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",    // Tailwind CSS
    "@types/dagre": "^0.7.53",       // TypeScript types
    "@types/node": "^20",            // Node.js types
    "@types/react": "^19",           // React types
    "@types/react-dom": "^19",       // React DOM types
    "eslint": "^9",                  // Linter
    "eslint-config-next": "16.1.1",  // Next.js ESLint config
    "tailwindcss": "^4",             // CSS framework
    "typescript": "^5"               // TypeScript compiler
  }
}
```

### Installing Dependencies

**Docker (Recommended)**:
Dependencies are automatically installed during Docker build.

**Local Development**:

```bash
# Backend
cd backend/orchestrator
pip install -r requirements.txt

# Tools Gateway
cd tools/tools_gateway
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Version Pinning

- **Backend**: Exact versions pinned for reproducibility
- **Frontend**: Caret (`^`) for compatible updates
- **Production**: Consider using lock files (`package-lock.json`, `pip freeze`)

---

## Development Guide

### Adding a New Agent

1. **Define Agent in Registry** (`registries/agent_registry.json`)

```json
{
  "agent_id": "pricing_agent",
  "name": "Pricing Agent",
  "description": "Calculates claim settlement amounts based on coverage and damage",
  "capabilities": [
    "price_calculation",
    "settlement_estimation"
  ],
  "allowed_tools": [
    "pricing_rules",
    "market_comparables"
  ],
  "model_profile_id": "default_gpt35",
  "max_iterations": 5,
  "iteration_timeout_seconds": 30,
  "output_schema": {
    "type": "object",
    "required": ["settlement_amount", "calculation_basis"],
    "properties": {
      "settlement_amount": {"type": "number"},
      "calculation_basis": {"type": "string"},
      "breakdown": {"type": "object"}
    }
  },
  "context_requirements": {
    "requires_prior_outputs": ["coverage", "severity"],
    "max_context_tokens": 6000
  }
}
```

2. **Create Output Schema** (`backend/orchestrator/app/schemas/agent_outputs.py`)

```python
class PricingAgentOutput(AgentOutputBase):
    """Output schema for pricing_agent."""

    settlement_amount: float = Field(..., ge=0.0)
    calculation_basis: str = Field(...)
    breakdown: Dict[str, float] = Field(default_factory=dict)
```

3. **Update Schema Registry** (`backend/orchestrator/app/schemas/validators.py`)

```python
AGENT_OUTPUT_SCHEMAS: Dict[str, Type[AgentOutputBase]] = {
    # ... existing agents
    "pricing_agent": PricingAgentOutput,
}
```

4. **Add to Orchestrator's Allowed Agents**

In `agent_registry.json`, update orchestrator's `allowed_agents`:

```json
{
  "agent_id": "orchestrator_agent",
  "allowed_agents": [
    "intake_agent",
    "coverage_agent",
    "fraud_agent",
    "severity_agent",
    "pricing_agent",  // Add here
    "recommendation_agent",
    "explainability_agent"
  ]
}
```

5. **Test the Agent**

```bash
# Agent will be automatically discovered and invoked by orchestrator
# when its capabilities match the workflow needs
```

### Adding a New Tool

1. **Implement Tool** (`tools/tools_gateway/app/tools/my_tool.py`)

```python
from typing import Dict, Any

def execute_my_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    My custom tool implementation.

    Args:
        parameters: Tool input parameters

    Returns:
        Tool execution result
    """
    # Tool logic here
    result = {
        "success": True,
        "data": {
            # Tool-specific output
        }
    }
    return result
```

2. **Register Tool Endpoint** (`tools/tools_gateway/app/main.py`)

```python
from .tools.my_tool import execute_my_tool

@app.post("/invoke/my_tool")
async def invoke_my_tool(request: Request):
    """Execute my custom tool."""
    try:
        params = await request.json()
        result = execute_my_tool(params)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

3. **Define Tool in Registry** (`registries/tool_registry.json`)

```json
{
  "tool_id": "my_tool",
  "name": "My Custom Tool",
  "description": "Detailed description of what this tool does and when to use it. Include examples of scenarios where this tool should be invoked.",
  "endpoint": "http://tools_gateway:8010/invoke/my_tool",
  "input_schema": {
    "type": "object",
    "required": ["param1"],
    "properties": {
      "param1": {
        "type": "string",
        "description": "Description of parameter"
      }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "result": {"type": "object"}
    }
  },
  "lineage_tags": ["category1", "category2"]
}
```

4. **Grant Tool Access to Agent**

In `agent_registry.json`, add tool to agent's `allowed_tools`:

```json
{
  "agent_id": "my_agent",
  "allowed_tools": [
    "my_tool"
  ]
}
```

### Adding a New Workflow

1. **Create Workflow Definition** (`registries/workflows/my_workflow.json`)

```json
{
  "workflow_id": "my_workflow",
  "name": "My Custom Workflow",
  "mode": "advisory",
  "goal": "High-level workflow objective",

  "suggested_sequence": [
    "agent1",
    "agent2",
    "agent3"
  ],

  "required_agents": ["agent1"],
  "optional_agents": ["agent2", "agent3"],

  "completion_criteria": {
    "required_outputs": ["output1", "output2"],
    "required_agents_executed": ["agent1"],
    "min_agents_executed": 2,
    "evidence_map_required": true
  },

  "constraints": {
    "max_total_duration_seconds": 300,
    "max_orchestrator_iterations": 10,
    "max_agent_invocations": 20
  }
}
```

2. **Workflow automatically available via API**:

```bash
POST /runs
{
  "workflow_id": "my_workflow",
  "input_data": { ... }
}
```

### Customizing LLM Models

1. **Add Model Profile** (`registries/model_profiles.json`)

```json
{
  "profile_id": "my_custom_model",
  "name": "My Custom Model",
  "description": "Custom model for specific use case",
  "provider": "openai",
  "model_name": "gpt-4-turbo",
  "intended_usage": "complex_reasoning",
  "parameters": {
    "temperature": 0.2,
    "max_tokens": 3000
  },
  "json_mode": true,
  "constraints": {
    "max_context_tokens": 128000,
    "max_output_tokens": 4096
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_multiplier": 2,
    "initial_delay_ms": 1000
  },
  "timeout_seconds": 60
}
```

2. **Assign to Agent**

In `agent_registry.json`, set agent's `model_profile_id`:

```json
{
  "agent_id": "my_agent",
  "model_profile_id": "my_custom_model"
}
```

### Testing

#### Schema Validation Test

Validate all agent output schemas:

```bash
cd backend/orchestrator
python test_schemas.py
```

**What it tests**:
- Agent output schemas match registry definitions
- Pydantic models are correctly defined
- Required fields are present
- Field types are correct

**Example output**:
```
Testing agent output schemas...
✓ orchestrator_agent schema valid
✓ intake_agent schema valid
✓ coverage_agent schema valid
✓ fraud_agent schema valid
✓ severity_agent schema valid
✓ recommendation_agent schema valid
✓ explainability_agent schema valid

All schemas validated successfully!
```

#### Integration Testing

**Health Check**:
```bash
# Test orchestrator health
curl http://localhost:8016/health

# Expected response
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0",
  "registries_loaded": true
}
```

**End-to-End Test**:
```bash
# Submit a test claim
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_claim_clean.json

# Get session ID from response
# Monitor via SSE
curl -N http://localhost:8016/runs/{session_id}/stream

# Verify completion
curl http://localhost:8016/sessions/{session_id}
```

#### Test Claims

Pre-built test cases in `sample_data/`:

1. **sample_claim_clean.json**: Normal claim, should complete successfully
2. **sample_claim_fraud.json**: High fraud signals, triggers fraud agent
3. **sample_claim_edge_case.json**: Complex scenario with missing data

**Testing workflow**:
```bash
# Test clean claim
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_claim_clean.json

# Test fraud detection
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_claim_fraud.json

# Test edge cases
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_claim_edge_case.json
```

#### Debugging Tests

**View logs**:
```bash
# Orchestrator logs
docker compose logs -f orchestrator

# Filter for errors
docker compose logs orchestrator | grep -i error

# View specific session
cat storage/sessions/{session_id}.jsonl | jq
```

**Common test scenarios**:
```bash
# Test registry loading
curl http://localhost:8016/stats | jq '.registries'

# Test agent invocation
curl http://localhost:8016/sessions/{session_id} | \
  jq '.events[] | select(.event_type == "agent_invocation_started")'

# Test tool calls
curl http://localhost:8016/sessions/{session_id} | \
  jq '.events[] | select(.event_type == "tool_invocation")'
```

### Local Development (Without Docker)

1. **Install Dependencies**

```bash
# Backend
cd backend/orchestrator
pip install -r requirements.txt

# Tools
cd tools/tools_gateway
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

2. **Run Services Locally**

```bash
# Terminal 1: Orchestrator
cd backend/orchestrator
STORAGE_PATH=../../storage \
TOOLS_BASE_URL=http://localhost:8010 \
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Tools
cd tools/tools_gateway
python -m uvicorn app.main:app --reload --port 8010

# Terminal 3: Frontend
cd frontend
npm run dev
```

3. **Access**:
- Frontend: http://localhost:3000
- Orchestrator: http://localhost:8000
- Tools: http://localhost:8010

---

## API Documentation

### 📚 Complete API Reference

**For complete API documentation, see [API_REFERENCE.md](API_REFERENCE.md)**

The API Reference includes:
- All Orchestrator API endpoints (workflow execution, sessions, checkpoints, context engineering)
- All Integration Fabric API endpoints (integration runs, DLQ, registries)
- Request/response examples
- Error handling
- Authentication (for production)
- Rate limiting guidelines

### Interactive API Docs

FastAPI provides auto-generated interactive API documentation:

- **Orchestrator Swagger UI**: http://localhost:8016/docs
- **Orchestrator ReDoc**: http://localhost:8016/redoc
- **Integration Fabric Swagger UI**: http://localhost:8020/docs
- **Integration Fabric ReDoc**: http://localhost:8020/redoc

### Core Endpoints

#### Create Workflow Run

```http
POST /runs
Content-Type: application/json

{
  "workflow_id": "claims_triage",
  "input_data": { ... },
  "session_id": "optional-custom-id",
  "options": { }
}

Response 200:
{
  "session_id": "session_20240315_abc123",
  "workflow_id": "claims_triage",
  "status": "running",
  "created_at": "2024-03-15T10:30:00Z",
  "stream_url": "/runs/session_20240315_abc123/stream",
  "session_url": "/sessions/session_20240315_abc123"
}
```

#### Stream Workflow Events

```http
GET /runs/{session_id}/stream
Accept: text/event-stream

Response: SSE stream
event: workflow_started
data: {"workflow_id": "claims_triage", ...}

event: agent_invocation_started
data: {"agent_id": "intake_agent", ...}

event: workflow_completed
data: {"status": "completed", ...}
```

#### Get Run Status

```http
GET /runs/{session_id}/status

Response 200:
{
  "session_id": "session_20240315_abc123",
  "status": "running" | "completed" | "failed"
}
```

#### List Sessions

```http
GET /sessions?limit=20&offset=0

Response 200:
[
  {
    "session_id": "session_...",
    "workflow_id": "claims_triage",
    "status": "completed",
    "created_at": "...",
    "event_count": 42,
    "agents_executed": ["intake_agent", "coverage_agent", ...]
  }
]
```

#### Get Session Details

```http
GET /sessions/{session_id}?event_type=agent_reasoning

Response 200:
{
  "session_id": "...",
  "workflow_id": "claims_triage",
  "status": "completed",
  "input_data": { ... },
  "output_data": { ... },
  "agents_executed": [...],
  "total_iterations": 5,
  "events": [ ... ],
  "warnings": [],
  "errors": []
}
```

#### Get Evidence Map

```http
GET /sessions/{session_id}/evidence

Response 200:
{
  "session_id": "...",
  "evidence_map": {
    "decision": { ... },
    "supporting_evidence": [ ... ],
    "assumptions": [ ... ],
    "limitations": [ ... ],
    "agent_chain": [ ... ]
  },
  "generated_at": "..."
}
```

#### Observability & Context Engineering

**Session Management**:
```http
GET /sessions?limit=20&offset=0
# List all sessions with pagination

DELETE /sessions/{session_id}
# Delete a session and its associated data
```

**Context Engineering (Session)**:
```http
GET /sessions/{session_id}/context-lineage
# Get complete context compilation history

GET /sessions/{session_id}/context-stats
# Get context compilation statistics (for Token Analytics tab)

GET /sessions/{session_id}/token-budget-timeline
# Get token usage timeline data

POST /sessions/{session_id}/trigger-compaction
# Manually trigger session compaction/summarization
```

**Evidence & Explainability**:
```http
GET /sessions/{session_id}/evidence
# Get complete evidence map for Explainability tab
# Returns 6-section decision explanation
```

#### Health Check

```http
GET /health

Response 200:
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0",
  "registries_loaded": true
}
```

#### System Stats

```http
GET /stats

Response 200:
{
  "registries": {
    "agents_count": 7,
    "tools_count": 6,
    ...
  },
  "executor": {
    "running_sessions": 2,
    ...
  },
  "broadcaster": {
    "active_connections": 3,
    ...
  }
}
```

#### Get Active Checkpoints

```http
GET /checkpoints?status=active&limit=20

Response 200:
[
  {
    "checkpoint_id": "cp_abc123",
    "session_id": "session_20240315_xyz",
    "workflow_id": "claims_triage",
    "intervention_type": "approval",
    "status": "active",
    "created_at": "...",
    "timeout_at": "...",
    "required_roles": ["fraud_investigator"],
    "metadata": { ... }
  }
]
```

#### Get Checkpoint Details

```http
GET /checkpoints/{checkpoint_id}

Response 200:
{
  "checkpoint_id": "cp_abc123",
  "session_id": "...",
  "intervention_type": "decision",
  "status": "active",
  "context": {
    "agent_outputs": { ... },
    "current_state": { ... }
  },
  "options": [
    {"value": "auto_process", "label": "Auto Process"},
    {"value": "manual_review", "label": "Manual Review"}
  ],
  "metadata": { ... }
}
```

#### Respond to Checkpoint

```http
POST /checkpoints/{checkpoint_id}/respond
Content-Type: application/json

{
  "decision": "approved",
  "comments": "Verified claim details",
  "data": { ... },
  "responder_id": "user@example.com",
  "responder_role": "claims_adjuster"
}

Response 200:
{
  "checkpoint_id": "cp_abc123",
  "status": "resolved",
  "resolution": "approved",
  "resolved_at": "..."
}
```

#### Get Registry

```http
GET /registries/{registry_name}
# registry_name: agents, tools, models, workflows, governance, system_config

Response 200:
{
  "version": "1.0.0",
  "last_updated": "...",
  ...
}
```

#### Update Registry

```http
PUT /registries/{registry_name}
Content-Type: application/json

{
  "version": "1.0.0",
  ...
}

Response 200:
{
  "status": "updated",
  "validation_result": {
    "valid": true,
    "warnings": []
  }
}
```

---

## Deployment Considerations

### Production Checklist

#### Security

- [ ] **API Authentication**: Implement JWT or OAuth2
- [ ] **CORS**: Restrict allowed origins to specific domains
- [ ] **HTTPS**: Use TLS certificates (Let's Encrypt)
- [ ] **API Keys**: Secure storage (use secrets management)
- [ ] **Rate Limiting**: Implement rate limits per user/IP
- [ ] **Input Validation**: Strict validation on all inputs
- [ ] **SQL Injection**: Not applicable (no SQL database)
- [ ] **XSS Prevention**: Frontend sanitization

#### Scalability

- [ ] **Database**: Replace flat files with PostgreSQL/MongoDB
- [ ] **Caching**: Add Redis for policy lookups, tool results
- [ ] **Load Balancer**: NGINX or AWS ALB
- [ ] **Horizontal Scaling**: Run multiple orchestrator instances
- [ ] **Message Queue**: Use RabbitMQ/Kafka for async workflows
- [ ] **CDN**: CloudFront/Cloudflare for frontend assets
- [ ] **Auto-scaling**: ECS/Kubernetes with HPA

#### Observability

- [ ] **Distributed Tracing**: OpenTelemetry + Jaeger
- [ ] **Metrics**: Prometheus + Grafana
- [ ] **Logging**: Structured logging (JSON) to ELK/CloudWatch
- [ ] **Alerting**: PagerDuty/Opsgenie for failures
- [ ] **APM**: New Relic/Datadog
- [ ] **Uptime Monitoring**: Pingdom/UptimeRobot

#### Reliability

- [ ] **Health Checks**: Implement comprehensive checks
- [ ] **Graceful Shutdown**: Handle SIGTERM properly
- [ ] **Circuit Breakers**: Prevent cascading failures
- [ ] **Retries with Backoff**: Exponential backoff for LLM calls
- [ ] **Timeouts**: Enforce all timeout configurations
- [ ] **Dead Letter Queue**: For failed workflows

#### Cost Optimization

- [ ] **LLM Model Selection**: Use cheaper models where possible
- [ ] **Token Budgets**: Strict enforcement
- [ ] **Caching**: Cache LLM responses for similar queries
- [ ] **Batch Processing**: Batch similar claims
- [ ] **Reserved Capacity**: For predictable workloads

### Docker Production Build

```dockerfile
# Orchestrator production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Environment-Specific Configurations

```bash
# Development
ORCHESTRATOR_MAX_ITERATIONS=10
LLM_TIMEOUT_SECONDS=30

# Staging
ORCHESTRATOR_MAX_ITERATIONS=8
LLM_TIMEOUT_SECONDS=45

# Production
ORCHESTRATOR_MAX_ITERATIONS=5
LLM_TIMEOUT_SECONDS=60
WORKFLOW_MAX_DURATION_SECONDS=180
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: agentmesh/orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Database Migration (Production)

Replace flat-file storage with database:

```python
# Example: PostgreSQL for sessions
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'

    session_id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    events = Column(JSON, nullable=False)

# In storage.py, replace file operations with DB operations
```

---

## Troubleshooting

### Services Won't Start

**Issue**: `docker compose up` fails

**Solutions**:
1. Check port availability:
   ```bash
   lsof -i :3016  # Frontend
   lsof -i :8016  # Orchestrator
   lsof -i :8010  # Tools
   ```

2. Check Docker resources:
   ```bash
   docker system df
   docker system prune  # Free up space
   ```

3. View service logs:
   ```bash
   docker compose logs orchestrator
   docker compose logs tools_gateway
   docker compose logs frontend
   ```

### Orchestrator Health Check Fails

**Issue**: `curl http://localhost:8016/health` returns unhealthy

**Possible Causes**:
1. Registries not loading
2. Invalid JSON in registry files
3. Missing API keys

**Debug**:
```bash
# Check logs
docker compose logs orchestrator | grep -i error

# Validate registry JSON
cat registries/agent_registry.json | jq .

# Test registry loading
docker compose exec orchestrator python -c "
from app.services.registry_manager import RegistryManager
rm = RegistryManager('/registries')
rm.load_all()
print(rm.get_stats())
"
```

### LLM Calls Failing

**Issue**: Agent execution fails with LLM errors

**Possible Causes**:
1. Invalid API key
2. Rate limiting
3. Model not available
4. Token limit exceeded

**Debug**:
```bash
# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check LLM call logs
docker compose logs orchestrator | grep -i "llm_call"

# Verify model profile
cat registries/model_profiles.json | jq '.model_profiles[] | select(.profile_id == "default_gpt35")'
```

### SSE Stream Not Working

**Issue**: Frontend not receiving live updates

**Possible Causes**:
1. CORS blocking SSE
2. Browser EventSource not supported
3. Proxy buffering responses

**Debug**:
```bash
# Test SSE directly
curl -N http://localhost:8016/runs/{session_id}/stream

# Check CORS headers
curl -I http://localhost:8016/runs -H "Origin: http://localhost:3016"

# Disable proxy buffering (if using nginx)
# Add to nginx.conf:
proxy_buffering off;
proxy_cache off;
```

### Session Files Not Created

**Issue**: No JSONL files in `storage/sessions/`

**Possible Causes**:
1. Permission issues
2. Storage path misconfigured
3. Volume mount not working

**Debug**:
```bash
# Check storage permissions
ls -la storage/sessions/

# Fix permissions
chmod 777 storage/sessions/

# Verify volume mount
docker compose exec orchestrator ls -la /storage/sessions/

# Check storage path config
docker compose exec orchestrator env | grep STORAGE_PATH
```

### Agent Execution Timeout

**Issue**: Agents reach max iterations without completing

**Possible Causes**:
1. Iteration limits too low
2. LLM not producing valid actions
3. Tool calls failing
4. Context too large

**Debug**:
```bash
# Check session events for failures
curl http://localhost:8016/sessions/{session_id} | jq '.events[] | select(.event_type | contains("error"))'

# Increase iteration limits in .env
AGENT_DEFAULT_MAX_ITERATIONS=10

# Check tool execution
curl http://localhost:8016/sessions/{session_id} | jq '.events[] | select(.event_type == "tool_invocation")'
```

### High Memory Usage

**Issue**: Services consuming too much RAM

**Solutions**:
1. Reduce context token limits in `.env`:
   ```bash
   LLM_MAX_TOKENS_PER_SESSION=25000
   ```

2. Limit concurrent workflows:
   ```bash
   WORKFLOW_MAX_CONCURRENT=5
   ```

3. Increase Docker memory limit:
   ```bash
   # Docker Desktop → Settings → Resources → Memory
   ```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Registry not initialized` | Startup failed | Check registry JSON syntax |
| `Agent not found` | Invalid agent_id | Verify agent_registry.json |
| `Tool access denied` | Governance policy | Check governance_policies.json |
| `Max iterations reached` | Iteration limit | Increase in .env or agent config |
| `LLM timeout` | Slow response | Increase LLM_TIMEOUT_SECONDS |
| `Invalid output schema` | Schema mismatch | Check agent output vs schema |
| `Session not found` | JSONL not created | Check storage/ permissions |

---

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test locally
4. Run tests: `pytest backend/orchestrator/tests/`
5. Commit with descriptive messages
6. Push to your fork: `git push origin feature/my-feature`
7. Create a Pull Request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow project ESLint config
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend with [Next.js](https://nextjs.org/)
- LLM support: [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/)
- Inspired by production multi-agent systems in regulated industries

---

## Support

### Documentation

Comprehensive documentation is available in the project:

**Core Documentation:**
- **[README.md](README.md)** (this file) - Complete user guide and quick start
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API endpoint documentation (NEW)
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines for Claude Code
- **[DECISIONS.md](DECISIONS.md)** - Architectural decisions and rationale
- **[IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md)** - Detailed implementation status

**Integration Fabric Documentation:**
- **[AIF.md](AIF.md)** - Integration Fabric quick reference (NEW)
- **[INTEGRATION_SCALABILITY.md](INTEGRATION_SCALABILITY.md)** - Integration Scalability UI guide (NEW)
- **[INTEGRATION_SCALABILITY_CONFIG.md](INTEGRATION_SCALABILITY_CONFIG.md)** - Registry schema reference (NEW)
- **[agent_mesh_integration_fabric_detailed_specifications.md](agent_mesh_integration_fabric_detailed_specifications.md)** - Complete AIF specifications (NEW)

**Feature-Specific Guides:**
- **[EXPLAINABILITY_TAB_DOCUMENTATION.md](EXPLAINABILITY_TAB_DOCUMENTATION.md)** - Explainability interface user guide
- **[HUMAN_IN_THE_LOOP.md](HUMAN_IN_THE_LOOP.md)** - HITL feature design and usage
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration management guide
- **[AGENTS.md](AGENTS.md)** - Agent design patterns and best practices
- **[REGISTRY_MANAGEMENT_PLAN.md](REGISTRY_MANAGEMENT_PLAN.md)** - Registry architecture
- **[TIKTOKEN_USAGE.md](TIKTOKEN_USAGE.md)** - Token counting implementation
- **[ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md)** - Known issues and solutions

### Getting Help

- **API Documentation**:
  - Orchestrator API: http://localhost:8016/docs (when running)
  - Integration Fabric API: http://localhost:8020/docs (when running)
  - Complete Reference: [API_REFERENCE.md](API_REFERENCE.md)
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join the community discussions
- **Email**: contact@agentmesh.io

### Learning Resources

**Key Concepts**:
1. Start with [DECISIONS.md](DECISIONS.md) to understand architectural choices
2. Read [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) for system overview
3. Review [AGENTS.md](AGENTS.md) to understand agent patterns
4. Explore [HUMAN_IN_THE_LOOP.md](HUMAN_IN_THE_LOOP.md) for HITL features
5. Study [EXPLAINABILITY_TAB_DOCUMENTATION.md](EXPLAINABILITY_TAB_DOCUMENTATION.md) for evidence-based decision transparency

**Development**:
1. Check [CLAUDE.md](CLAUDE.md) for development workflows
2. Review [CONFIGURATION.md](CONFIGURATION.md) for config management
3. See [REGISTRY_MANAGEMENT_PLAN.md](REGISTRY_MANAGEMENT_PLAN.md) for registry patterns

**User Interface**:
1. Refer to [EXPLAINABILITY_TAB_DOCUMENTATION.md](EXPLAINABILITY_TAB_DOCUMENTATION.md) for complete UI guide
2. All field-level explanations available via InfoTooltip components (ℹ️ icons)
3. Context Engineering documentation in `docs/` folder

---

**Built with ❤️ for scalable multi-agent systems**
