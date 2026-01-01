
# Production-Scale Multi‑Agentic Insurance Framework  
## Technical Design Specification (Prototype)

---

## 1. Purpose of This Document

This document describes the **technical design** for a production‑shaped prototype that demonstrates how to scale **multi‑agentic insurance solutions** using modern, modular architecture patterns.

This design:
- Implements the previously defined **functional specification**
- Focuses on **architecture, components, and interactions**
- Avoids low‑level implementation or code details
- Is suitable for architects, senior engineers, and platform leaders

---

## 2. Technology Stack (Fixed for Prototype)

### Frontend
- **Next.js**
- **Tailwind CSS**
- Server‑Sent Events (SSE) for live progress

### Backend
- **Python**
- **FastAPI**
- Async HTTP communication between services

### LLM
- **OpenAI – gpt‑3.5‑turbo**
- Centralized LLM access via orchestrator

### Storage
- Flat files only (JSON / JSONL)
- No databases

### Deployment
- Fully Dockerized
- Single `docker-compose.yml`
- One `.env` file at repository root
- Hot reload enabled for development

---

## 3. High‑Level System Architecture

The system is composed of **loosely coupled microservices** coordinated by a central orchestrator.

### Core Runtime Components
1. Orchestrator Service
2. Agent Services (one per agent)
3. Tool Services
4. Frontend UI
5. Flat‑file storage layer

All communication is **HTTP‑based**.  
Agents and tools never communicate directly with each other.

---

## 4. Orchestrator Service

### Responsibilities
The Orchestrator is the **control plane** of the system.

It is responsible for:
- Loading workflow definitions
- Discovering agents, tools, and models from registries
- Executing workflow steps
- Compiling scoped context per agent
- Invoking agent services
- Invoking tool services
- Enforcing governance rules
- Recording execution events
- Streaming live progress to the UI

### Key Characteristics
- Stateless execution logic
- All state persisted via flat files
- Single source of truth for orchestration

---

## 5. Agent Services

### Design Principles
- Each agent is its own **independent microservice**
- Each agent represents **one business capability**
- Agents do not retain state between calls
- Agents do not call tools or other agents directly

### Standard Agent Contract
Each agent exposes a single endpoint:

- `POST /run`

The orchestrator supplies:
- Scoped working context
- Model profile identifier
- Guardrails and constraints

The agent returns:
- Structured output
- Optional tool requests
- Optional explanation notes

### Agents in the Prototype
- Intake & Normalization Agent
- Coverage & Policy Agent
- Fraud Signal Agent
- Severity & Complexity Agent
- Action Recommendation Agent
- Explainability Agent

---

## 6. Tool Services

### Purpose
Tools represent **external or internal capabilities** used by agents.

### Tool Types
- Internal HTTP tools (rules, similarity, heuristics)
- External integrations (mocked for prototype)

### Invocation Model
- Orchestrator invokes tools on behalf of agents
- Tool access is governed by registry and policy rules
- Tool results are recorded as session events

### Tool Gateway
For simplicity, tools may be grouped into a single **tools gateway service** for the prototype.

---

## 7. Registry‑Driven Configuration

All dynamic behavior is driven by **flat‑file registries**.

### 7.1 Agent Registry
Defines:
- Agent identity
- Capabilities
- Endpoint location
- Context requirements
- Allowed tools
- Guardrails

### 7.2 Tool Registry
Defines:
- Tool identity
- Business purpose
- Interface contract
- Data lineage classification
- Access constraints

### 7.3 Model Profiles
Defines:
- Model provider
- Model name (gpt‑3.5‑turbo)
- Intended usage pattern
- Behavioral constraints
- Cost and token limits

Agents request **model profiles**, never raw model names.

### 7.4 Workflow Definitions
Defines:
- Ordered workflow steps
- Agent selection per step
- Conditional routing logic
- Failure and retry behavior

---

## 8. Context Engineering Design

### Session Context
- Each run produces a unique session
- Session data is recorded as an append‑only event stream

### Working Context Compilation
Before invoking an agent, the orchestrator:
- Selects only relevant prior outputs
- References large artifacts by ID
- Applies compaction summaries when needed

### Context Compaction
- Older events are summarized into durable context
- Prevents prompt bloat
- Preserves decision continuity

---

## 9. LLM Access Pattern

### Centralized LLM Proxy
- Only the orchestrator interacts with OpenAI APIs
- Agents request inference indirectly via orchestration

### Benefits
- Unified logging and cost tracking
- Centralized retry and error handling
- Governance enforcement
- Output schema validation

---

## 10. Governance & Guardrails

### Policy Enforcement
Policies control:
- Which workflows may execute
- Which agents may be used
- Which tools an agent may request
- Which model profiles are allowed

### Audit Trail
- Every action is recorded as a session event
- Events are immutable
- Registry versions are captured per run

### Safety Controls
- Output constraints
- Basic redaction rules
- Kill switches for agents or tools

---

## 11. Observability & Monitoring

### Captured Signals
- Agent execution duration
- Tool latency
- LLM usage and estimated cost
- Errors and retries

### Session Replay
- Full timeline reconstruction from JSONL events
- Supports audit, debugging, and executive review

---

## 12. Frontend Architecture

### UI Goals
- Executive‑friendly visualization
- Clear demonstration of orchestration
- Transparent decision traceability

### Core Screens
1. Claim Submission & Run Initiation
2. Live Execution Progress (SSE)
3. Session Timeline Replay
4. Evidence Map & Explanation
5. Operational Metrics Summary
6. Registry Explorer

### Design Characteristics
- Responsive layout
- Clear separation of business vs technical detail
- Minimal but expressive UI

---

## 13. Docker & Deployment Design

### Containerized Services
- Frontend (Next.js)
- Orchestrator
- Individual Agent Services
- Tool Services

### docker‑compose
- Orchestrates all services
- Shared volume for flat‑file storage
- Hot reload enabled for development

### Environment Configuration
- Single `.env` file at repo root
- Shared across all services

---

## 14. Claims Triage Workflow (End‑to‑End)

1. Claim submitted via UI
2. Orchestrator creates session
3. Intake agent normalizes claim
4. Coverage agent evaluates policy
5. Fraud agent evaluates risk
6. Severity agent classifies complexity
7. Recommendation agent determines action
8. Explainability agent produces evidence map
9. Session completes and is replayable

---

## 15. Design Outcomes

This technical design demonstrates:
- True agent decoupling
- Registry‑driven extensibility
- Production‑grade observability
- Explainable AI decisioning
- Governance‑ready architecture

---

**End of Technical Design Specification**
