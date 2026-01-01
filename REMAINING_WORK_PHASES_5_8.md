# Remaining Work: Phases 5-8

**AgentMesh - Production-Scale Multi-Agentic Insurance Framework**

This document provides comprehensive implementation details for all remaining phases (5-8) to enable seamless continuation of work at any time.

---

## Table of Contents

1. [Phase 5: Agent Output Schemas](#phase-5-agent-output-schemas)
2. [Phase 6: Orchestrator API & SSE](#phase-6-orchestrator-api--sse)
3. [Phase 7: Frontend UI](#phase-7-frontend-ui)
4. [Phase 8: Documentation & Polish](#phase-8-documentation--polish)
5. [Integration Checklist](#integration-checklist)
6. [Testing Strategy](#testing-strategy)

---

## Phase 5: Agent Output Schemas

**Goal**: Implement Pydantic models for structured agent output validation.

**Why Needed**: Ensures agents produce consistent, validated outputs that can be reliably consumed by subsequent agents and the orchestrator.

**Dependencies**:
- Phase 2 (RegistryManager, AgentReActLoopController)
- Phase 3 (ResponseParser)
- Tool outputs from Phase 4

**Estimated Lines of Code**: ~400 lines

---

### 5.1 Agent Output Schema Models

**File**: `backend/orchestrator/app/schemas/agent_outputs.py`

**Purpose**: Define Pydantic models for each agent's output structure, matching the `output_schema` in `agent_registry.json`.

#### 5.1.1 Base Models

```python
"""
Agent Output Schemas - Pydantic models for structured output validation.

Demonstrates scalability patterns:
- Schema-driven validation
- Type safety
- Documentation via models
- Reusable components
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentOutputBase(BaseModel):
    """Base class for all agent outputs."""
    agent_id: str = Field(..., description="Agent that produced this output")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(default="1.0", description="Schema version")

    class Config:
        extra = "forbid"  # Strict mode - no extra fields allowed
```

#### 5.1.2 Intake Agent Output

```python
class DataQualityIssue(BaseModel):
    """Data quality issue detected during intake."""
    field: str = Field(..., description="Field with issue")
    issue_type: str = Field(..., description="Type of issue (missing, invalid, inconsistent)")
    severity: str = Field(..., description="Severity: low, medium, high")
    message: str = Field(..., description="Human-readable description")


class IntakeAgentOutput(AgentOutputBase):
    """Output schema for intake_agent."""

    normalized_claim: Dict[str, Any] = Field(
        ...,
        description="Normalized and validated claim data"
    )

    data_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall data quality score (0-1)"
    )

    data_quality_issues: List[DataQualityIssue] = Field(
        default_factory=list,
        description="List of data quality issues found"
    )

    validation_passed: bool = Field(
        ...,
        description="Whether claim passed basic validation"
    )

    normalization_changes: List[str] = Field(
        default_factory=list,
        description="List of normalization changes applied"
    )

    @validator('data_quality_score')
    def score_range_check(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('data_quality_score must be between 0 and 1')
        return v
```

#### 5.1.3 Coverage Agent Output

```python
class CoverageDeterminationType(str, Enum):
    """Coverage determination outcomes."""
    APPROVED = "approved"
    PARTIAL = "partial"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"


class CoverageAgentOutput(AgentOutputBase):
    """Output schema for coverage_agent."""

    coverage_determination: CoverageDeterminationType = Field(
        ...,
        description="Coverage determination result"
    )

    coverage_amount: float = Field(
        ...,
        ge=0.0,
        description="Amount covered by policy (after deductibles)"
    )

    deductible_amount: float = Field(
        ...,
        ge=0.0,
        description="Applicable deductible amount"
    )

    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of claim covered"
    )

    exclusions_triggered: List[str] = Field(
        default_factory=list,
        description="List of policy exclusions that apply"
    )

    coverage_limits_applied: Dict[str, float] = Field(
        default_factory=dict,
        description="Coverage limits that were applied"
    )

    reasoning: str = Field(
        ...,
        description="Detailed explanation of coverage determination"
    )
```

#### 5.1.4 Fraud Agent Output

```python
class RiskBand(str, Enum):
    """Fraud risk classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudIndicator(BaseModel):
    """Individual fraud indicator."""
    indicator_id: str = Field(..., description="Unique indicator ID")
    indicator_name: str = Field(..., description="Human-readable name")
    severity: str = Field(..., description="Severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    description: str = Field(..., description="Why this indicator was triggered")


class FraudAgentOutput(AgentOutputBase):
    """Output schema for fraud_agent."""

    fraud_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall fraud risk score (0-1)"
    )

    risk_band: RiskBand = Field(
        ...,
        description="Risk classification"
    )

    triggered_indicators: List[FraudIndicator] = Field(
        default_factory=list,
        description="All fraud indicators that were triggered"
    )

    siu_referral_required: bool = Field(
        ...,
        description="Whether SIU referral is required"
    )

    similar_claims_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Analysis of similar historical claims"
    )

    rationale: str = Field(
        ...,
        description="Detailed fraud assessment rationale"
    )
```

#### 5.1.5 Severity Agent Output

```python
class ComplexityLevel(str, Enum):
    """Claim complexity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityAgentOutput(AgentOutputBase):
    """Output schema for severity_agent."""

    complexity_level: ComplexityLevel = Field(
        ...,
        description="Overall complexity classification"
    )

    complexity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numerical complexity score (0-1)"
    )

    complexity_factors: List[str] = Field(
        default_factory=list,
        description="Factors contributing to complexity"
    )

    estimated_processing_days: int = Field(
        ...,
        ge=1,
        description="Estimated processing time in days"
    )

    required_expertise_level: str = Field(
        ...,
        description="Required adjuster expertise level"
    )

    special_handling_required: bool = Field(
        ...,
        description="Whether special handling is needed"
    )

    assessment_rationale: str = Field(
        ...,
        description="Detailed complexity assessment"
    )
```

#### 5.1.6 Recommendation Agent Output

```python
class ProcessingTrack(str, Enum):
    """Processing track classification."""
    FAST_TRACK = "fast_track"
    STANDARD = "standard"
    STANDARD_ENHANCED = "standard_enhanced"
    COMPLEX = "complex"
    INVESTIGATION = "investigation"
    EXPEDITED = "expedited"


class RecommendationAgentOutput(AgentOutputBase):
    """Output schema for recommendation_agent."""

    recommended_action: str = Field(
        ...,
        description="Primary recommended action"
    )

    action_priority: str = Field(
        ...,
        description="Priority level: low, medium, high, urgent"
    )

    processing_track: ProcessingTrack = Field(
        ...,
        description="Recommended processing track"
    )

    required_approvals: List[str] = Field(
        default_factory=list,
        description="List of required approvals"
    )

    next_steps: List[str] = Field(
        ...,
        min_items=1,
        description="Ordered list of next steps"
    )

    estimated_timeline_days: int = Field(
        ...,
        ge=1,
        description="Estimated timeline for resolution"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in recommendation"
    )

    rationale: str = Field(
        ...,
        description="Detailed recommendation rationale"
    )
```

#### 5.1.7 Explainability Agent Output (Evidence Map)

```python
class Evidence(BaseModel):
    """Individual piece of evidence."""
    source: str = Field(..., description="Source agent or data source")
    evidence_type: str = Field(..., description="Type of evidence")
    summary: str = Field(..., description="Evidence summary")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight/importance")


class Decision(BaseModel):
    """Final decision structure."""
    outcome: str = Field(..., description="Decision outcome")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    basis: str = Field(..., description="Primary basis for decision")


class ExplainabilityAgentOutput(AgentOutputBase):
    """Output schema for explainability_agent (Evidence Map)."""

    decision: Decision = Field(
        ...,
        description="Final decision with confidence"
    )

    supporting_evidence: List[Evidence] = Field(
        ...,
        min_items=1,
        description="All supporting evidence"
    )

    assumptions: List[str] = Field(
        default_factory=list,
        description="Key assumptions made"
    )

    limitations: List[str] = Field(
        default_factory=list,
        description="Limitations of the analysis"
    )

    agent_chain: List[str] = Field(
        ...,
        min_items=1,
        description="Ordered list of agents executed"
    )

    alternative_outcomes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Alternative outcomes considered"
    )

    explanation: str = Field(
        ...,
        description="Human-readable explanation of entire analysis"
    )
```

#### 5.1.8 Orchestrator Output

```python
class CompletionReason(str, Enum):
    """Workflow completion reasons."""
    ALL_OBJECTIVES_ACHIEVED = "all_objectives_achieved"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    TIMEOUT = "timeout"
    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"
    ERROR = "error"


class OrchestratorOutput(AgentOutputBase):
    """Output schema for orchestrator_agent."""

    status: str = Field(
        ...,
        description="Completion status: completed, completed_with_warning, failed"
    )

    completion_reason: CompletionReason = Field(
        ...,
        description="Reason for completion"
    )

    evidence_map: ExplainabilityAgentOutput = Field(
        ...,
        description="Final evidence map"
    )

    agents_executed: List[str] = Field(
        ...,
        min_items=1,
        description="List of agents executed in order"
    )

    total_iterations: int = Field(
        ...,
        ge=1,
        description="Total orchestrator iterations"
    )

    total_agent_invocations: int = Field(
        ...,
        ge=1,
        description="Total number of agent invocations"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings encountered"
    )

    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered"
    )
```

---

### 5.2 Schema Validator Utility

**File**: `backend/orchestrator/app/schemas/validators.py`

**Purpose**: Validation utilities for agent outputs.

```python
"""
Schema Validators - Validation utilities for agent outputs.

Demonstrates:
- Runtime validation
- Schema version checking
- Custom validation rules
"""

from typing import Dict, Any, Type, Optional
from pydantic import ValidationError
from .agent_outputs import (
    AgentOutputBase,
    IntakeAgentOutput,
    CoverageAgentOutput,
    FraudAgentOutput,
    SeverityAgentOutput,
    RecommendationAgentOutput,
    ExplainabilityAgentOutput
)


# Schema registry - maps agent_id to output schema class
AGENT_OUTPUT_SCHEMAS: Dict[str, Type[AgentOutputBase]] = {
    "intake_agent": IntakeAgentOutput,
    "coverage_agent": CoverageAgentOutput,
    "fraud_agent": FraudAgentOutput,
    "severity_agent": SeverityAgentOutput,
    "recommendation_agent": RecommendationAgentOutput,
    "explainability_agent": ExplainabilityAgentOutput
}


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


def validate_agent_output(
    agent_id: str,
    output_data: Dict[str, Any]
) -> AgentOutputBase:
    """
    Validate agent output against its schema.

    Args:
        agent_id: Agent ID
        output_data: Raw output data from agent

    Returns:
        Validated output model

    Raises:
        SchemaValidationError: If validation fails
    """
    # Get schema for agent
    schema_class = AGENT_OUTPUT_SCHEMAS.get(agent_id)

    if not schema_class:
        raise SchemaValidationError(
            f"No output schema defined for agent '{agent_id}'"
        )

    try:
        # Add agent_id and timestamp if not present
        if "agent_id" not in output_data:
            output_data["agent_id"] = agent_id

        if "timestamp" not in output_data:
            from datetime import datetime
            output_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Validate and parse
        validated_output = schema_class(**output_data)
        return validated_output

    except ValidationError as e:
        # Format validation errors
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")

        raise SchemaValidationError(
            f"Output validation failed for {agent_id}:\n" + "\n".join(errors)
        )


def get_schema_for_agent(agent_id: str) -> Optional[Type[AgentOutputBase]]:
    """Get output schema class for agent."""
    return AGENT_OUTPUT_SCHEMAS.get(agent_id)


def get_schema_json(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get JSON schema for agent output."""
    schema_class = AGENT_OUTPUT_SCHEMAS.get(agent_id)
    if schema_class:
        return schema_class.schema()
    return None
```

---

### 5.3 Integration into AgentReActLoopController

**File**: `backend/orchestrator/app/services/agent_react_loop.py`

**Changes Needed**: Update `_validate_output()` method to use schema validation.

**Location in file**: Around line 1447 (in `execute()` method)

**Current Code**:
```python
def _validate_output(self, output: Dict[str, Any]) -> bool:
    """Validate agent output against schema."""
    # TODO: Implement schema validation
    return True
```

**Updated Code**:
```python
def _validate_output(self, output: Dict[str, Any]) -> bool:
    """
    Validate agent output against schema.

    Demonstrates: Runtime schema validation with detailed error reporting.
    """
    from ..schemas.validators import validate_agent_output, SchemaValidationError

    try:
        # Validate output against agent's schema
        validated_output = validate_agent_output(self.agent_id, output)

        # Log successful validation
        self._log_event("output_validated", {
            "agent_id": self.agent_id,
            "schema_version": validated_output.version
        })

        return True

    except SchemaValidationError as e:
        # Log validation failure
        self._log_event("output_validation_failed", {
            "agent_id": self.agent_id,
            "error": str(e)
        })

        logger.error(
            f"Output validation failed for {self.agent_id}: {str(e)}"
        )

        return False
```

---

### 5.4 Testing Schema Validation

**File**: `backend/orchestrator/tests/test_agent_schemas.py` (Optional but recommended)

**Purpose**: Unit tests for schema validation.

```python
"""Tests for agent output schemas."""

import pytest
from datetime import datetime
from app.schemas.agent_outputs import (
    IntakeAgentOutput,
    CoverageAgentOutput,
    FraudAgentOutput
)
from app.schemas.validators import validate_agent_output, SchemaValidationError


def test_intake_agent_output_valid():
    """Test valid intake agent output."""
    output_data = {
        "agent_id": "intake_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "normalized_claim": {"claim_id": "CLM-001"},
        "data_quality_score": 0.95,
        "validation_passed": True,
        "normalization_changes": ["standardized_date_format"]
    }

    output = IntakeAgentOutput(**output_data)
    assert output.data_quality_score == 0.95
    assert output.validation_passed is True


def test_fraud_agent_output_invalid_score():
    """Test fraud agent output with invalid score."""
    output_data = {
        "agent_id": "fraud_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fraud_score": 1.5,  # Invalid - should be 0-1
        "risk_band": "high",
        "siu_referral_required": True,
        "rationale": "Test"
    }

    with pytest.raises(ValidationError):
        FraudAgentOutput(**output_data)


def test_validate_agent_output():
    """Test validation utility."""
    output_data = {
        "coverage_determination": "approved",
        "coverage_amount": 10000.0,
        "deductible_amount": 500.0,
        "coverage_percentage": 95.0,
        "reasoning": "Full coverage approved"
    }

    validated = validate_agent_output("coverage_agent", output_data)
    assert validated.agent_id == "coverage_agent"
    assert validated.coverage_amount == 10000.0
```

---

### 5.5 Phase 5 Completion Checklist

- [ ] Create `backend/orchestrator/app/schemas/__init__.py`
- [ ] Implement all 7 agent output schema models in `agent_outputs.py`
- [ ] Implement schema validator utility in `validators.py`
- [ ] Update `AgentReActLoopController._validate_output()` to use schemas
- [ ] Update `OrchestratorRunner._validate_completion_criteria()` to use schemas
- [ ] Test schema validation with sample data
- [ ] Update IMPLEMENTATION_PROGRESS.md with Phase 5 documentation

**Success Criteria**:
- All agent outputs have Pydantic schema models
- Schema validation integrated into ReAct loops
- Validation errors provide detailed feedback
- Schemas match `output_schema` in agent_registry.json

---

## Phase 6: Orchestrator API & SSE

**Goal**: Implement REST API with Server-Sent Events for live workflow streaming.

**Why Needed**: Enables external clients (frontend) to trigger workflows and monitor execution in real-time.

**Dependencies**:
- All previous phases (1-5)
- Schemas for request/response validation

**Estimated Lines of Code**: ~800 lines

---

### 6.1 API Models

**File**: `backend/orchestrator/app/api/models.py`

**Purpose**: Pydantic models for API requests and responses.

```python
"""
API Models - Request and response schemas for orchestrator API.

Demonstrates:
- API contract definition
- Input validation
- Type safety
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime


class RunWorkflowRequest(BaseModel):
    """Request to run a workflow."""

    workflow_id: str = Field(
        ...,
        description="Workflow ID to execute"
    )

    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data for workflow (e.g., claim data)"
    )

    session_id: Optional[str] = Field(
        None,
        description="Optional session ID (generated if not provided)"
    )

    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional execution options"
    )

    class Config:
        schema_extra = {
            "example": {
                "workflow_id": "claims_triage",
                "input_data": {
                    "claim_id": "CLM-2024-001",
                    "policy_id": "POL-001",
                    "claim_amount": 15000.0,
                    "loss_type": "collision"
                }
            }
        }


class RunWorkflowResponse(BaseModel):
    """Response from workflow run request."""

    session_id: str = Field(..., description="Unique session ID")
    workflow_id: str = Field(..., description="Workflow being executed")
    status: str = Field(..., description="Initial status: running")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    stream_url: str = Field(..., description="SSE stream URL")
    session_url: str = Field(..., description="Session details URL")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_20240315_abc123",
                "workflow_id": "claims_triage",
                "status": "running",
                "created_at": "2024-03-15T10:30:00Z",
                "stream_url": "/runs/session_20240315_abc123/stream",
                "session_url": "/sessions/session_20240315_abc123"
            }
        }


class SessionSummary(BaseModel):
    """Summary of a session."""

    session_id: str
    workflow_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    event_count: int
    agents_executed: List[str]


class SessionDetails(BaseModel):
    """Detailed session information."""

    session_id: str
    workflow_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None

    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None

    agents_executed: List[str]
    total_iterations: int
    total_agent_invocations: int

    events: List[Dict[str, Any]]

    warnings: List[str] = []
    errors: List[str] = []


class EvidenceMapResponse(BaseModel):
    """Evidence map response."""

    session_id: str
    evidence_map: Dict[str, Any]
    generated_at: str
```

---

### 6.2 SSE Broadcaster

**File**: `backend/orchestrator/app/services/sse_broadcaster.py`

**Purpose**: Server-Sent Events broadcaster for live event streaming.

```python
"""
SSE Broadcaster - Real-time event streaming for workflow execution.

Demonstrates scalability patterns:
- Non-blocking event streaming
- Client connection management
- Event buffering for reconnections
- Clean resource cleanup
"""

import asyncio
import json
from typing import Dict, List, AsyncGenerator, Optional
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """
    Server-Sent Events broadcaster for real-time workflow updates.

    Manages multiple client connections per session and broadcasts events
    to all connected clients.
    """

    def __init__(self, max_buffer_size: int = 100):
        """
        Initialize SSE broadcaster.

        Args:
            max_buffer_size: Maximum events to buffer per session
        """
        self.max_buffer_size = max_buffer_size

        # Session-level event queues
        # Structure: {session_id: deque of events}
        self._session_buffers: Dict[str, deque] = {}

        # Active client queues
        # Structure: {session_id: [asyncio.Queue, ...]}
        self._client_queues: Dict[str, List[asyncio.Queue]] = {}

        # Session completion flags
        self._completed_sessions: Dict[str, bool] = {}

        logger.info("SSE Broadcaster initialized")

    async def subscribe(
        self,
        session_id: str,
        last_event_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to session events.

        Args:
            session_id: Session to subscribe to
            last_event_id: Last received event ID (for reconnection)

        Yields:
            SSE-formatted event strings
        """
        logger.info(f"New SSE subscription: session_id={session_id}")

        # Create client queue
        client_queue: asyncio.Queue = asyncio.Queue()

        # Register client
        if session_id not in self._client_queues:
            self._client_queues[session_id] = []
        self._client_queues[session_id].append(client_queue)

        try:
            # Send buffered events if reconnecting
            if last_event_id and session_id in self._session_buffers:
                for buffered_event in self._session_buffers[session_id]:
                    if buffered_event.get("id", "") > last_event_id:
                        yield self._format_sse_event(buffered_event)

            # Stream new events
            while True:
                # Wait for next event
                event = await client_queue.get()

                # Check for completion signal
                if event is None:
                    logger.info(f"Stream complete for session {session_id}")
                    break

                # Send event
                yield self._format_sse_event(event)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        finally:
            # Unregister client
            if session_id in self._client_queues:
                try:
                    self._client_queues[session_id].remove(client_queue)
                    if not self._client_queues[session_id]:
                        del self._client_queues[session_id]
                except ValueError:
                    pass

    async def broadcast_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict,
        event_id: Optional[str] = None
    ) -> None:
        """
        Broadcast event to all subscribers of a session.

        Args:
            session_id: Target session
            event_type: Event type
            event_data: Event data
            event_id: Optional event ID
        """
        # Create event
        event = {
            "id": event_id or self._generate_event_id(),
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Buffer event
        if session_id not in self._session_buffers:
            self._session_buffers[session_id] = deque(maxlen=self.max_buffer_size)
        self._session_buffers[session_id].append(event)

        # Broadcast to all connected clients
        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(event)
                except Exception as e:
                    logger.error(f"Failed to send event to client: {e}")

    async def complete_session(self, session_id: str) -> None:
        """
        Signal session completion to all clients.

        Args:
            session_id: Session that completed
        """
        logger.info(f"Completing session {session_id}")

        # Mark as completed
        self._completed_sessions[session_id] = True

        # Send completion signal (None) to all clients
        if session_id in self._client_queues:
            for client_queue in self._client_queues[session_id]:
                try:
                    await client_queue.put(None)
                except Exception as e:
                    logger.error(f"Failed to send completion signal: {e}")

    def _format_sse_event(self, event: Dict) -> str:
        """
        Format event as SSE string.

        SSE format:
        id: <event_id>
        event: <event_type>
        data: <json_data>

        """
        lines = []

        if "id" in event:
            lines.append(f"id: {event['id']}")

        if "event" in event:
            lines.append(f"event: {event['event']}")

        if "data" in event:
            data_json = json.dumps(event["data"])
            lines.append(f"data: {data_json}")

        lines.append("")  # Empty line signals end of event

        return "\n".join(lines) + "\n"

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        from datetime import datetime
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}"

    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up session resources.

        Call this after sufficient time has passed to allow clients to reconnect.
        """
        if session_id in self._session_buffers:
            del self._session_buffers[session_id]

        if session_id in self._completed_sessions:
            del self._completed_sessions[session_id]

        logger.info(f"Cleaned up session {session_id}")


# Global broadcaster instance
_broadcaster: Optional[SSEBroadcaster] = None


def get_broadcaster() -> SSEBroadcaster:
    """Get singleton SSE broadcaster."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = SSEBroadcaster()
    return _broadcaster
```

---

### 6.3 Background Workflow Executor

**File**: `backend/orchestrator/app/services/workflow_executor.py`

**Purpose**: Execute workflows in background with SSE broadcasting.

```python
"""
Workflow Executor - Background workflow execution with SSE streaming.

Demonstrates:
- Async workflow execution
- Event broadcasting
- Error handling
- Resource cleanup
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from .orchestrator_runner import OrchestratorRunner, create_orchestrator_runner
from .sse_broadcaster import get_broadcaster
from .storage import get_session_writer, get_artifact_writer

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Execute workflows in background with SSE broadcasting.
    """

    def __init__(self):
        self.broadcaster = get_broadcaster()
        self.session_writer = get_session_writer()
        self.artifact_writer = get_artifact_writer()

        # Track running workflows
        self._running_workflows: Dict[str, asyncio.Task] = {}

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Execute workflow in background.

        Args:
            workflow_id: Workflow to execute
            input_data: Input data for workflow
            session_id: Optional session ID

        Returns:
            Session ID
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id()

        # Log workflow start
        await self.broadcaster.broadcast_event(
            session_id=session_id,
            event_type="workflow_started",
            event_data={
                "workflow_id": workflow_id,
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat() + "Z"
            }
        )

        # Create background task
        task = asyncio.create_task(
            self._run_workflow_task(session_id, workflow_id, input_data)
        )

        self._running_workflows[session_id] = task

        return session_id

    async def _run_workflow_task(
        self,
        session_id: str,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Background task to run workflow.
        """
        try:
            logger.info(f"Starting workflow execution: session={session_id}")

            # Create orchestrator runner
            orchestrator = create_orchestrator_runner(
                session_id=session_id,
                workflow_id=workflow_id
            )

            # Execute workflow (this is synchronous, wrap in executor)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                orchestrator.execute,
                input_data
            )

            # Broadcast completion
            await self.broadcaster.broadcast_event(
                session_id=session_id,
                event_type="workflow_completed",
                event_data={
                    "status": result.status,
                    "completion_reason": result.completion_reason,
                    "agents_executed": result.agents_executed,
                    "completed_at": datetime.utcnow().isoformat() + "Z"
                }
            )

            # Save evidence map as artifact
            if result.evidence_map:
                artifact_id = f"{session_id}_evidence_map"
                self.artifact_writer.write_artifact(
                    artifact_id=artifact_id,
                    artifact_type="evidence_map",
                    data=result.evidence_map
                )

            # Complete session
            await self.broadcaster.complete_session(session_id)

            logger.info(f"Workflow completed: session={session_id}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Broadcast error
            await self.broadcaster.broadcast_event(
                session_id=session_id,
                event_type="workflow_error",
                event_data={
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat() + "Z"
                }
            )

            # Complete session even on error
            await self.broadcaster.complete_session(session_id)

        finally:
            # Remove from running workflows
            if session_id in self._running_workflows:
                del self._running_workflows[session_id]

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"session_{timestamp}_{unique_id}"

    def get_running_sessions(self) -> list:
        """Get list of currently running session IDs."""
        return list(self._running_workflows.keys())


# Global executor instance
_executor: Optional[WorkflowExecutor] = None


def get_workflow_executor() -> WorkflowExecutor:
    """Get singleton workflow executor."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor()
    return _executor
```

---

### 6.4 API Endpoints - Runs

**File**: `backend/orchestrator/app/api/runs.py`

**Purpose**: Workflow execution endpoints.

```python
"""
Runs API - Endpoints for workflow execution and streaming.

Demonstrates:
- Async API endpoints
- SSE streaming
- Background task management
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import logging

from .models import RunWorkflowRequest, RunWorkflowResponse
from ..services.workflow_executor import get_workflow_executor
from ..services.sse_broadcaster import get_broadcaster
from ..services.registry_manager import get_registry_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunWorkflowResponse)
async def create_run(request: RunWorkflowRequest):
    """
    Create new workflow run.

    Starts workflow execution in background and returns session info with stream URL.
    """
    logger.info(f"Creating workflow run: workflow_id={request.workflow_id}")

    # Validate workflow exists
    registry = get_registry_manager()
    workflow = registry.get_workflow(request.workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request.workflow_id}' not found"
        )

    # Execute workflow in background
    executor = get_workflow_executor()
    session_id = await executor.execute_workflow(
        workflow_id=request.workflow_id,
        input_data=request.input_data,
        session_id=request.session_id
    )

    # Return response with URLs
    return RunWorkflowResponse(
        session_id=session_id,
        workflow_id=request.workflow_id,
        status="running",
        created_at=datetime.utcnow().isoformat() + "Z",
        stream_url=f"/runs/{session_id}/stream",
        session_url=f"/sessions/{session_id}"
    )


@router.get("/{session_id}/stream")
async def stream_run(
    session_id: str,
    request: Request,
    last_event_id: Optional[str] = None
):
    """
    Stream workflow execution events via Server-Sent Events.

    Args:
        session_id: Session to stream
        last_event_id: Last received event ID (for reconnection)
    """
    logger.info(f"Starting SSE stream: session_id={session_id}")

    broadcaster = get_broadcaster()

    async def event_generator():
        """Generate SSE events."""
        try:
            async for event in broadcaster.subscribe(session_id, last_event_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: session_id={session_id}")
                    break

                yield event

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/{session_id}/status")
async def get_run_status(session_id: str):
    """
    Get current status of a workflow run.

    Returns quick status without full session details.
    """
    executor = get_workflow_executor()

    is_running = session_id in executor.get_running_sessions()

    # TODO: Check if completed by reading session file

    return {
        "session_id": session_id,
        "status": "running" if is_running else "completed"
    }
```

---

### 6.5 API Endpoints - Sessions

**File**: `backend/orchestrator/app/api/sessions.py`

**Purpose**: Session replay and evidence map endpoints.

```python
"""
Sessions API - Endpoints for session replay and evidence maps.

Demonstrates:
- Session retrieval
- Event filtering
- Artifact access
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
from pathlib import Path

from .models import SessionSummary, SessionDetails, EvidenceMapResponse
from ..services.storage import get_session_reader, get_artifact_reader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionSummary])
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    List recent sessions.

    Returns paginated list of session summaries.
    """
    reader = get_session_reader()

    # Get all session files
    storage_path = Path("/storage/sessions")
    if not storage_path.exists():
        return []

    session_files = sorted(
        storage_path.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    # Apply pagination
    session_files = session_files[offset:offset + limit]

    # Build summaries
    summaries = []
    for session_file in session_files:
        session_id = session_file.stem

        try:
            events = reader.read_session(session_id)

            # Extract summary info
            first_event = events[0] if events else {}
            last_event = events[-1] if events else {}

            # Get agents executed
            agents_executed = []
            for event in events:
                if event.get("event_type") == "agent_invocation_completed":
                    agent_id = event.get("event_data", {}).get("agent_id")
                    if agent_id and agent_id not in agents_executed:
                        agents_executed.append(agent_id)

            summary = SessionSummary(
                session_id=session_id,
                workflow_id=first_event.get("event_data", {}).get("workflow_id", "unknown"),
                status=last_event.get("event_type", "unknown"),
                created_at=first_event.get("timestamp", ""),
                completed_at=last_event.get("timestamp"),
                event_count=len(events),
                agents_executed=agents_executed
            )

            summaries.append(summary)

        except Exception as e:
            logger.error(f"Failed to read session {session_id}: {e}")
            continue

    return summaries


@router.get("/{session_id}", response_model=SessionDetails)
async def get_session(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter events by type")
):
    """
    Get complete session details with events.

    Args:
        session_id: Session ID
        event_type: Optional event type filter
    """
    reader = get_session_reader()

    try:
        # Read events
        if event_type:
            events = reader.filter_events(session_id, event_type)
        else:
            events = reader.read_session(session_id)

        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        # Extract session metadata
        first_event = events[0]
        last_event = events[-1]

        # Extract input/output
        input_data = {}
        output_data = None

        for event in events:
            if event.get("event_type") == "workflow_started":
                input_data = event.get("event_data", {}).get("input_data", {})
            elif event.get("event_type") == "workflow_completed":
                output_data = event.get("event_data", {})

        # Get agents executed
        agents_executed = []
        for event in events:
            if event.get("event_type") == "agent_invocation_completed":
                agent_id = event.get("event_data", {}).get("agent_id")
                if agent_id and agent_id not in agents_executed:
                    agents_executed.append(agent_id)

        # Build details
        details = SessionDetails(
            session_id=session_id,
            workflow_id=first_event.get("event_data", {}).get("workflow_id", "unknown"),
            status=last_event.get("event_type", "unknown"),
            created_at=first_event.get("timestamp", ""),
            completed_at=last_event.get("timestamp"),
            input_data=input_data,
            output_data=output_data,
            agents_executed=agents_executed,
            total_iterations=len([e for e in events if "iteration" in e.get("event_type", "")]),
            total_agent_invocations=len(agents_executed),
            events=events
        )

        return details

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )


@router.get("/{session_id}/evidence", response_model=EvidenceMapResponse)
async def get_evidence_map(session_id: str):
    """
    Get evidence map for session.

    Returns final evidence map artifact.
    """
    artifact_reader = get_artifact_reader()
    artifact_id = f"{session_id}_evidence_map"

    try:
        artifact = artifact_reader.read_artifact(artifact_id)

        return EvidenceMapResponse(
            session_id=session_id,
            evidence_map=artifact["data"],
            generated_at=artifact["created_at"]
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Evidence map not found for session '{session_id}'"
        )
```

---

### 6.6 Main Application Integration

**File**: `backend/orchestrator/app/main.py`

**Purpose**: FastAPI application with all routers.

```python
"""
Orchestrator API - Main FastAPI application.

Production-grade API for multi-agent orchestration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .api import runs, sessions
from .services.registry_manager import init_registry_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AgentMesh Orchestrator",
    description="Production-scale multi-agent orchestration platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3016"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs.router)
app.include_router(sessions.router)


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    logger.info("Starting AgentMesh Orchestrator")

    # Initialize registries
    init_registry_manager()

    logger.info("Orchestrator ready")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down Orchestrator")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AgentMesh Orchestrator",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

---

### 6.7 Phase 6 Completion Checklist

- [ ] Create `backend/orchestrator/app/api/__init__.py`
- [ ] Implement API models in `api/models.py`
- [ ] Implement SSE broadcaster in `services/sse_broadcaster.py`
- [ ] Implement workflow executor in `services/workflow_executor.py`
- [ ] Implement runs endpoints in `api/runs.py`
- [ ] Implement sessions endpoints in `api/sessions.py`
- [ ] Update `main.py` with routers and startup logic
- [ ] Update Dockerfile to expose port 8000
- [ ] Test SSE streaming with curl or browser
- [ ] Test API endpoints with sample requests
- [ ] Update IMPLEMENTATION_PROGRESS.md with Phase 6 documentation

**Success Criteria**:
- `POST /runs` creates workflow and returns session_id
- `GET /runs/{session_id}/stream` streams events via SSE
- `GET /sessions/{session_id}` returns complete session timeline
- `GET /sessions/{session_id}/evidence` returns evidence map
- SSE reconnection works with `last_event_id`
- All endpoints have proper error handling

---

## Phase 7: Frontend UI

**Goal**: Build Next.js frontend with live progress streaming and replay capabilities.

**Why Needed**: Provides executive-grade UI for submitting claims and monitoring workflow execution.

**Dependencies**:
- Phase 6 (Orchestrator API)
- SSE support in browser

**Estimated Lines of Code**: ~1,200 lines

---

### 7.1 Next.js Initialization

**Directory**: `frontend/`

**Steps**:

```bash
# Navigate to frontend directory
cd frontend

# Initialize Next.js with TypeScript
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# Install additional dependencies
npm install @heroicons/react date-fns clsx
```

**Dependencies to install**:
- `@heroicons/react` - Icon library
- `date-fns` - Date formatting
- `clsx` - Conditional className utility

---

### 7.2 Environment Configuration

**File**: `frontend/.env.local`

```bash
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:8016
```

---

### 7.3 API Client Utility

**File**: `frontend/lib/api-client.ts`

**Purpose**: HTTP client for orchestrator API.

```typescript
/**
 * API Client for Orchestrator
 */

const ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:8016';

export interface RunWorkflowRequest {
  workflow_id: string;
  input_data: Record<string, any>;
  session_id?: string;
}

export interface RunWorkflowResponse {
  session_id: string;
  workflow_id: string;
  status: string;
  created_at: string;
  stream_url: string;
  session_url: string;
}

export interface SessionDetails {
  session_id: string;
  workflow_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  agents_executed: string[];
  total_iterations: number;
  total_agent_invocations: number;
  events: Array<Record<string, any>>;
  warnings: string[];
  errors: string[];
}

export interface EvidenceMap {
  session_id: string;
  evidence_map: Record<string, any>;
  generated_at: string;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = ORCHESTRATOR_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Create new workflow run
   */
  async createRun(request: RunWorkflowRequest): Promise<RunWorkflowResponse> {
    const response = await fetch(`${this.baseUrl}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create run');
    }

    return response.json();
  }

  /**
   * Get session details
   */
  async getSession(sessionId: string): Promise<SessionDetails> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch session');
    }

    return response.json();
  }

  /**
   * Get evidence map
   */
  async getEvidenceMap(sessionId: string): Promise<EvidenceMap> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/evidence`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch evidence map');
    }

    return response.json();
  }

  /**
   * Get SSE stream URL
   */
  getStreamUrl(sessionId: string): string {
    return `${this.baseUrl}/runs/${sessionId}/stream`;
  }
}

export const apiClient = new APIClient();
```

---

### 7.4 SSE Hook

**File**: `frontend/hooks/use-sse.ts`

**Purpose**: React hook for SSE event streaming.

```typescript
/**
 * useSSE Hook - Server-Sent Events subscription
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface SSEEvent {
  id?: string;
  event?: string;
  data: any;
  timestamp: string;
}

export interface UseSSEOptions {
  onEvent?: (event: SSEEvent) => void;
  onError?: (error: Event) => void;
  onComplete?: () => void;
  reconnect?: boolean;
}

export function useSSE(url: string | null, options: UseSSEOptions = {}) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastEventIdRef = useRef<string | null>(null);

  const connect = useCallback(() => {
    if (!url) return;

    // Build URL with last event ID for reconnection
    let streamUrl = url;
    if (options.reconnect && lastEventIdRef.current) {
      streamUrl += `?last_event_id=${lastEventIdRef.current}`;
    }

    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('SSE connection opened');
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const event: SSEEvent = {
          id: e.lastEventId,
          data,
          timestamp: new Date().toISOString(),
        };

        // Store last event ID
        if (e.lastEventId) {
          lastEventIdRef.current = e.lastEventId;
        }

        setEvents((prev) => [...prev, event]);
        options.onEvent?.(event);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };

    // Handle custom event types
    eventSource.addEventListener('workflow_completed', (e: MessageEvent) => {
      console.log('Workflow completed');
      options.onComplete?.();
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.addEventListener('workflow_error', (e: MessageEvent) => {
      console.error('Workflow error:', e.data);
      options.onComplete?.();
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.onerror = (e) => {
      console.error('SSE error:', e);
      setError('Connection error');
      setIsConnected(false);
      options.onError?.(e);

      // Reconnect if enabled
      if (options.reconnect) {
        setTimeout(() => {
          console.log('Reconnecting...');
          connect();
        }, 3000);
      }
    };
  }, [url, options]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  return {
    events,
    isConnected,
    error,
    disconnect,
  };
}
```

---

### 7.5 Run Claim Page

**File**: `frontend/app/run-claim/page.tsx`

**Purpose**: Submit claim and watch live progress.

```typescript
/**
 * Run Claim Page - Submit claim and watch live execution
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, RunWorkflowResponse } from '@/lib/api-client';
import { useSSE } from '@/hooks/use-sse';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

export default function RunClaimPage() {
  const router = useRouter();
  const [claimData, setClaimData] = useState({
    claim_id: '',
    policy_id: 'POL-001',
    claim_date: new Date().toISOString().split('T')[0],
    loss_type: 'collision',
    claim_amount: '',
    incident_date: '',
    description: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runResponse, setRunResponse] = useState<RunWorkflowResponse | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  const { events, isConnected } = useSSE(streamUrl, {
    onComplete: () => {
      console.log('Workflow complete');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await apiClient.createRun({
        workflow_id: 'claims_triage',
        input_data: {
          ...claimData,
          claim_amount: parseFloat(claimData.claim_amount),
        },
      });

      setRunResponse(response);
      setStreamUrl(apiClient.getStreamUrl(response.session_id));
    } catch (error) {
      console.error('Failed to submit claim:', error);
      alert('Failed to submit claim');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewEvidence = () => {
    if (runResponse) {
      router.push(`/evidence/${runResponse.session_id}`);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Run Claim Triage</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Claim Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Claim Information</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Claim ID</label>
              <input
                type="text"
                value={claimData.claim_id}
                onChange={(e) => setClaimData({ ...claimData, claim_id: e.target.value })}
                className="w-full border rounded px-3 py-2"
                placeholder="CLM-2024-001"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Policy ID</label>
              <select
                value={claimData.policy_id}
                onChange={(e) => setClaimData({ ...claimData, policy_id: e.target.value })}
                className="w-full border rounded px-3 py-2"
              >
                <option value="POL-001">POL-001 (Auto - John Doe)</option>
                <option value="POL-002">POL-002 (Home - Jane Smith)</option>
                <option value="POL-003">POL-003 (Auto - Bob Johnson)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Loss Type</label>
              <select
                value={claimData.loss_type}
                onChange={(e) => setClaimData({ ...claimData, loss_type: e.target.value })}
                className="w-full border rounded px-3 py-2"
              >
                <option value="collision">Collision</option>
                <option value="comprehensive">Comprehensive</option>
                <option value="theft">Theft</option>
                <option value="fire">Fire</option>
                <option value="water_damage">Water Damage</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Claim Amount ($)</label>
              <input
                type="number"
                step="0.01"
                value={claimData.claim_amount}
                onChange={(e) => setClaimData({ ...claimData, claim_amount: e.target.value })}
                className="w-full border rounded px-3 py-2"
                placeholder="15000.00"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Incident Date</label>
              <input
                type="date"
                value={claimData.incident_date}
                onChange={(e) => setClaimData({ ...claimData, incident_date: e.target.value })}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={claimData.description}
                onChange={(e) => setClaimData({ ...claimData, description: e.target.value })}
                className="w-full border rounded px-3 py-2"
                rows={3}
                placeholder="Brief description of the incident..."
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !!runResponse}
              className="w-full bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : runResponse ? 'Submitted' : 'Submit Claim'}
            </button>
          </form>
        </div>

        {/* Right: Live Progress */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Live Progress</h2>
            {isConnected && (
              <span className="flex items-center text-green-600 text-sm">
                <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse" />
                Connected
              </span>
            )}
          </div>

          {!runResponse ? (
            <p className="text-gray-500 text-center py-8">Submit a claim to see live progress</p>
          ) : (
            <div className="space-y-4">
              {/* Session Info */}
              <div className="bg-gray-50 rounded p-3 text-sm">
                <div>
                  <span className="font-medium">Session ID:</span>{' '}
                  <code className="text-xs">{runResponse.session_id}</code>
                </div>
                <div>
                  <span className="font-medium">Workflow:</span> {runResponse.workflow_id}
                </div>
              </div>

              {/* Event Timeline */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.map((event, index) => (
                  <EventCard key={index} event={event} />
                ))}
              </div>

              {/* View Evidence Button */}
              {events.some((e) => e.data.status === 'completed') && (
                <button
                  onClick={handleViewEvidence}
                  className="w-full bg-green-600 text-white py-2 rounded font-medium hover:bg-green-700"
                >
                  View Evidence Map
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EventCard({ event }: { event: any }) {
  const eventType = event.data.event || 'unknown';
  const timestamp = new Date(event.timestamp);

  const getEventIcon = () => {
    if (eventType.includes('completed')) {
      return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
    } else if (eventType.includes('error')) {
      return <ExclamationCircleIcon className="w-5 h-5 text-red-600" />;
    }
    return <div className="w-5 h-5 border-2 border-blue-600 rounded-full" />;
  };

  return (
    <div className="flex gap-3 p-3 bg-gray-50 rounded">
      {getEventIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="font-medium text-sm">{eventType.replace(/_/g, ' ')}</span>
          <span className="text-xs text-gray-500">
            {formatDistanceToNow(timestamp, { addSuffix: true })}
          </span>
        </div>
        <pre className="text-xs text-gray-600 mt-1 overflow-x-auto">
          {JSON.stringify(event.data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

---

### 7.6 Session Replay Page

**File**: `frontend/app/replay/[sessionId]/page.tsx`

**Purpose**: Replay session timeline.

```typescript
/**
 * Session Replay Page - View complete session timeline
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, SessionDetails } from '@/lib/api-client';
import { format } from 'date-fns';

export default function ReplayPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterEventType, setFilterEventType] = useState<string>('all');

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  const loadSession = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSession(sessionId);
      setSession(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-8 text-red-600">Error: {error}</div>;
  }

  if (!session) {
    return <div className="container mx-auto px-4 py-8">Session not found</div>;
  }

  const eventTypes = Array.from(
    new Set(session.events.map((e) => e.event_type))
  );

  const filteredEvents =
    filterEventType === 'all'
      ? session.events
      : session.events.filter((e) => e.event_type === filterEventType);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Session Replay</h1>

      {/* Session Summary */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Session Summary</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Session ID:</span>
            <br />
            <code className="text-xs">{session.session_id}</code>
          </div>
          <div>
            <span className="font-medium">Workflow:</span>
            <br />
            {session.workflow_id}
          </div>
          <div>
            <span className="font-medium">Status:</span>
            <br />
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
              {session.status}
            </span>
          </div>
          <div>
            <span className="font-medium">Created:</span>
            <br />
            {format(new Date(session.created_at), 'PPpp')}
          </div>
          <div>
            <span className="font-medium">Agents Executed:</span>
            <br />
            {session.agents_executed.join(', ')}
          </div>
          <div>
            <span className="font-medium">Total Events:</span>
            <br />
            {session.events.length}
          </div>
        </div>
      </div>

      {/* Event Filter */}
      <div className="mb-4">
        <label className="font-medium mr-2">Filter by event type:</label>
        <select
          value={filterEventType}
          onChange={(e) => setFilterEventType(e.target.value)}
          className="border rounded px-3 py-1"
        >
          <option value="all">All Events</option>
          {eventTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {/* Event Timeline */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Event Timeline ({filteredEvents.length})</h2>
        <div className="space-y-3">
          {filteredEvents.map((event, index) => (
            <EventDetail key={index} event={event} />
          ))}
        </div>
      </div>
    </div>
  );
}

function EventDetail({ event }: { event: any }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded p-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <span className="font-medium">{event.event_type}</span>
          <span className="text-sm text-gray-500 ml-3">
            {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
          </span>
        </div>
        <button className="text-blue-600 text-sm">
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {expanded && (
        <pre className="mt-3 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
          {JSON.stringify(event, null, 2)}
        </pre>
      )}
    </div>
  );
}
```

---

### 7.7 Evidence Map Page

**File**: `frontend/app/evidence/[sessionId]/page.tsx`

**Purpose**: Display evidence map visualization.

```typescript
/**
 * Evidence Map Page - Display final evidence map
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, EvidenceMap } from '@/lib/api-client';
import { format } from 'date-fns';

export default function EvidenceMapPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [evidenceMap, setEvidenceMap] = useState<EvidenceMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEvidenceMap();
  }, [sessionId]);

  const loadEvidenceMap = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getEvidenceMap(sessionId);
      setEvidenceMap(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading evidence map...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-8 text-red-600">Error: {error}</div>;
  }

  if (!evidenceMap) {
    return <div className="container mx-auto px-4 py-8">Evidence map not found</div>;
  }

  const map = evidenceMap.evidence_map;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Evidence Map</h1>

      {/* Session Info */}
      <div className="bg-gray-50 rounded-lg p-4 mb-8 text-sm">
        <div>
          <span className="font-medium">Session:</span> <code>{sessionId}</code>
        </div>
        <div>
          <span className="font-medium">Generated:</span>{' '}
          {format(new Date(evidenceMap.generated_at), 'PPpp')}
        </div>
      </div>

      {/* Decision */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4">Decision</h2>
        <div className="space-y-3">
          <div>
            <span className="font-medium">Outcome:</span>
            <br />
            <span className="text-xl">{map.decision?.outcome || 'N/A'}</span>
          </div>
          {map.decision?.confidence && (
            <div>
              <span className="font-medium">Confidence:</span>
              <br />
              <div className="w-full bg-gray-200 rounded-full h-4 mt-1">
                <div
                  className="bg-blue-600 h-4 rounded-full"
                  style={{ width: `${(map.decision.confidence || 0) * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">
                {((map.decision.confidence || 0) * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {map.decision?.basis && (
            <div>
              <span className="font-medium">Basis:</span>
              <br />
              <p className="text-gray-700">{map.decision.basis}</p>
            </div>
          )}
        </div>
      </div>

      {/* Supporting Evidence */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Supporting Evidence</h2>
        <div className="space-y-4">
          {map.supporting_evidence?.map((evidence: any, index: number) => (
            <div key={index} className="border-l-4 border-blue-600 pl-4 py-2">
              <div className="font-medium">{evidence.source || `Evidence ${index + 1}`}</div>
              <div className="text-sm text-gray-600">{evidence.evidence_type}</div>
              <p className="text-gray-700 mt-1">{evidence.summary}</p>
              {evidence.weight && (
                <div className="text-sm text-gray-500 mt-1">
                  Weight: {(evidence.weight * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Agent Chain */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Agent Execution Chain</h2>
        <div className="flex flex-wrap gap-2">
          {map.agent_chain?.map((agent: string, index: number) => (
            <div key={index} className="flex items-center">
              <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded">
                {agent}
              </div>
              {index < (map.agent_chain?.length || 0) - 1 && (
                <span className="mx-2 text-gray-400">→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Assumptions & Limitations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Assumptions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Assumptions</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {map.assumptions?.map((assumption: string, index: number) => (
              <li key={index}>{assumption}</li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Limitations</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {map.limitations?.map((limitation: string, index: number) => (
              <li key={index}>{limitation}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
```

---

### 7.8 Phase 7 Completion Checklist

- [ ] Initialize Next.js with TypeScript and Tailwind
- [ ] Install dependencies (@heroicons/react, date-fns, clsx)
- [ ] Create API client utility (`lib/api-client.ts`)
- [ ] Create SSE hook (`hooks/use-sse.ts`)
- [ ] Implement Run Claim page (`app/run-claim/page.tsx`)
- [ ] Implement Session Replay page (`app/replay/[sessionId]/page.tsx`)
- [ ] Implement Evidence Map page (`app/evidence/[sessionId]/page.tsx`)
- [ ] Test live streaming with real workflow execution
- [ ] Test replay functionality
- [ ] Test evidence map visualization
- [ ] Update IMPLEMENTATION_PROGRESS.md with Phase 7 documentation

**Success Criteria**:
- User can submit claim via form
- Live progress streams in real-time
- Timeline shows all events with expandable details
- Evidence map displays with proper formatting
- SSE reconnection works properly
- UI is responsive and polished

---

## Phase 8: Documentation & Polish

**Goal**: Comprehensive documentation, sample data, and end-to-end testing.

**Why Needed**: Enables new users to run the demo and understand architectural decisions.

**Dependencies**: All previous phases

**Estimated Lines of Code**: ~1,500 lines (documentation)

---

### 8.1 Sample Claim Data

**File**: `sample_data/sample_claim.json`

**Purpose**: Realistic sample claim for testing.

```json
{
  "claim_id": "CLM-2024-DEMO-001",
  "policy_id": "POL-001",
  "claim_date": "2024-03-15",
  "incident_date": "2024-03-14",
  "loss_type": "collision",
  "claim_amount": 12500.00,
  "claimant": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "(555) 123-4567"
  },
  "incident_details": {
    "location": "Los Angeles, CA",
    "description": "Rear-ended at traffic light on I-405. Other driver admitted fault. Front bumper and hood damaged, airbags deployed.",
    "police_report": "LA-2024-031401",
    "weather_conditions": "clear",
    "time_of_day": "17:30"
  },
  "vehicle_details": {
    "make": "Toyota",
    "model": "Camry",
    "year": 2022,
    "vin": "4T1B11HK0NU123456",
    "mileage": 15234
  },
  "injuries": {
    "reported": true,
    "severity": "minor",
    "description": "Minor whiplash, seeking medical evaluation"
  },
  "witnesses": [
    {
      "name": "Jane Smith",
      "contact": "(555) 987-6543"
    }
  ]
}
```

---

### 8.2 Comprehensive README

**File**: `README.md`

**Structure**:

```markdown
# AgentMesh - Production-Scale Multi-Agentic Insurance Framework

**Flagship demonstration of scalable multi-agent solutions using Bounded ReAct Agents**

## Overview

AgentMesh is a fully working, dockerized prototype demonstrating production-grade patterns for building scalable multi-agent systems. Built specifically for insurance claims processing, it showcases how to:

- **Orchestrate multiple specialized agents** dynamically via a meta-agent ReAct loop
- **Discover and invoke tools** at runtime from registries (no hardcoding)
- **Enforce governance policies** across agent and tool access
- **Stream execution events** in real-time via Server-Sent Events
- **Compile evidence maps** for complete explainability
- **Scale horizontally** with stateless, containerized services

## Key Features

- ✅ **7 Agents**: 1 orchestrator + 6 specialized workers (intake, coverage, fraud, severity, recommendation, explainability)
- ✅ **6 Mock Tools**: Policy snapshot, fraud rules, similarity search, schema validator, coverage rules, decision rules
- ✅ **Multi-Provider LLM**: OpenAI (GPT-3.5, GPT-4) + Anthropic (Claude 3 Sonnet/Opus/Haiku)
- ✅ **Dynamic Discovery**: Agents and tools discovered from JSON registries
- ✅ **Bounded Execution**: Iteration limits, timeouts, token budgets
- ✅ **Complete Observability**: JSONL event streams for full replay
- ✅ **Live Streaming**: SSE for real-time progress monitoring
- ✅ **Executive UI**: Next.js frontend with live updates and evidence map visualization

## Architecture

[Include architecture diagram]

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or Anthropic API key)
- 8GB RAM minimum
- Ports available: 3016 (frontend), 8016 (orchestrator), 8001 (tools)

### Installation

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd AgentMesh
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start services**
   ```bash
   docker compose up
   ```

4. **Access UI**
   ```
   Frontend: http://localhost:3016
   API Docs: http://localhost:8016/docs
   ```

### Run Demo

1. Open http://localhost:3016/run-claim
2. Fill in claim details (or use sample data)
3. Click "Submit Claim"
4. Watch live progress as agents execute
5. View final Evidence Map

## Project Structure

[Include file tree]

## Scalability Patterns Demonstrated

[List all 20+ patterns with brief descriptions]

## API Documentation

[Document all API endpoints]

## Configuration

[Explain all environment variables and registry files]

## Development

[How to add new agents, tools, workflows]

## Testing

[How to run tests]

## Troubleshooting

[Common issues and solutions]

## License

[License info]
```

---

### 8.3 Architectural Decisions Document

**File**: `DECISIONS.md`

**Structure**:

```markdown
# Architectural Decisions

This document explains key architectural decisions made in AgentMesh and the reasoning behind them.

## Table of Contents

1. [Orchestrator as ReAct Agent](#orchestrator-as-react-agent)
2. [Centralized LLM Control](#centralized-llm-control)
3. [Registry-Driven Architecture](#registry-driven-architecture)
4. [Flat-File Storage](#flat-file-storage)
5. [Mock Tools](#mock-tools)
6. [Advisory Workflow Mode](#advisory-workflow-mode)
7. [SSE for Live Streaming](#sse-for-live-streaming)
8. [Multi-Provider LLM](#multi-provider-llm)
9. [Bounded Execution](#bounded-execution)
10. [Simplifications for Prototype](#simplifications-for-prototype)

---

## Orchestrator as ReAct Agent

**Decision**: The orchestrator is itself a ReAct agent that discovers and invokes other agents dynamically.

**Alternatives Considered**:
- Hardcoded workflow execution
- Simple workflow manager without ReAct loop
- Event-driven orchestration

**Reasoning**:
- **Adaptability**: Orchestrator can adapt based on workflow state, not just execute fixed sequence
- **Consistency**: Same ReAct pattern used for both orchestrator and workers
- **Discovery**: Demonstrates dynamic agent discovery from registry
- **Scalability**: New agents can be added without changing orchestrator code

**Trade-offs**:
- More complex than simple workflow manager
- Requires orchestrator to have its own LLM calls
- Additional iteration tracking needed

---

## Centralized LLM Control

**Decision**: Orchestrator manages all LLM calls for both itself and worker agents.

**Alternatives Considered**:
- Each agent as separate service with own LLM client
- Distributed agent services

**Reasoning**:
- **Unified governance**: Single point for prompt engineering, cost tracking, policy enforcement
- **Simplified deployment**: Fewer services to manage
- **Cost control**: Easier to implement token budgets and rate limiting
- **Consistency**: All agents use same LLM calling patterns

**Trade-offs**:
- Orchestrator becomes single point of failure
- Can't scale agents independently
- All agents share orchestrator's resource limits

**Production Evolution**:
In production, agents could be separate services while maintaining centralized governance through API gateway pattern.

---

[Continue with all other decisions...]

## Simplifications for Prototype

**Acceptable Simplifications**:

1. **No Database**: Flat files (JSONL/JSON) instead of PostgreSQL/MongoDB
   - Easy to inspect and debug
   - No setup required
   - Production would use database for querying and scale

2. **Mock Tools**: Realistic but fake data
   - Demonstrates patterns without external dependencies
   - Easy to test deterministically
   - Production would integrate real policy systems, fraud detection APIs, etc.

3. **Single Workflow**: Only claims_triage implemented
   - Sufficient to demonstrate all patterns
   - Production would have multiple workflows

4. **No Authentication**: Open API endpoints
   - Simplifies demo
   - Production would require JWT/OAuth

5. **No Distributed Tracing**: Basic logging only
   - Sufficient for debugging
   - Production would use OpenTelemetry, Jaeger

6. **Single Tenant**: No isolation
   - Simplifies architecture
   - Production would require tenant isolation

7. **No Caching**: All tools execute fresh
   - Simplifies logic
   - Production would cache policy lookups, etc.

8. **Synchronous Tool Calls**: Sequential execution
   - Easier to reason about
   - Production could parallelize tool calls

**Core Patterns Fully Represented**:
- ✅ Loose coupling via registries
- ✅ Dynamic discovery
- ✅ Bounded ReAct loops
- ✅ Governance enforcement
- ✅ Complete observability
- ✅ Multi-provider LLM
- ✅ Event streaming

The simplifications do not compromise the demonstration of scalability patterns.
```

---

### 8.4 Docker Compose Enhancement

**File**: `docker-compose.yml`

**Add health checks**:

```yaml
services:
  orchestrator:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  tools_gateway:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  frontend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

### 8.5 Phase 8 Completion Checklist

- [ ] Create `sample_data/sample_claim.json` with realistic data
- [ ] Write comprehensive README.md (installation, quick start, architecture)
- [ ] Write DECISIONS.md documenting all architectural choices
- [ ] Add health checks to docker-compose.yml
- [ ] Test complete end-to-end workflow with sample data
- [ ] Verify all services start cleanly with `docker compose up`
- [ ] Test SSE reconnection by refreshing browser during execution
- [ ] Verify all API endpoints work correctly
- [ ] Check all registry files load without errors
- [ ] Run sample claim through complete workflow
- [ ] Capture screenshots for README
- [ ] Create demo video (optional)
- [ ] Update IMPLEMENTATION_PROGRESS.md with Phase 8 documentation
- [ ] Final polish: fix any bugs, improve error messages, add tooltips

**Success Criteria**:
- New user can clone repo and run demo in < 5 minutes
- README provides clear instructions
- DECISIONS.md explains all major choices
- Sample data produces realistic workflow execution
- All services pass health checks
- Evidence map shows complete analysis
- UI is polished and professional

---

## Integration Checklist

This checklist ensures all phases integrate correctly:

### Phase 5 → Phase 6 Integration
- [ ] Agent output schemas used in API response models
- [ ] Schema validation integrated into workflow execution
- [ ] Validation errors properly broadcasted via SSE

### Phase 6 → Phase 7 Integration
- [ ] API client correctly formats requests
- [ ] SSE hook properly receives and parses events
- [ ] Frontend displays all event types correctly
- [ ] Evidence map API returns correctly formatted data

### Phase 7 → Phase 8 Integration
- [ ] Sample data works with frontend form
- [ ] README examples match actual UI flow
- [ ] Screenshots reflect current UI design

### Cross-Phase Integration
- [ ] Registries → Orchestrator: All registry files load correctly
- [ ] Orchestrator → Tools: Tool invocation works end-to-end
- [ ] LLM → Parser: All LLM responses parse correctly
- [ ] Storage → API: Session retrieval returns complete data
- [ ] SSE → Frontend: Live updates display in real-time

---

## Testing Strategy

### Unit Testing (Optional but Recommended)

**Backend Tests**:
- `test_agent_schemas.py` - Schema validation
- `test_response_parser.py` - JSON parsing with malformed inputs
- `test_registry_manager.py` - Registry loading and lookups
- `test_governance_enforcer.py` - Policy enforcement
- `test_tools.py` - Each tool with edge cases

**Frontend Tests**:
- API client error handling
- SSE hook reconnection logic
- Component rendering

### Integration Testing

**End-to-End Test**:
1. Start all services with `docker compose up`
2. Submit claim via API: `POST /runs`
3. Verify SSE stream contains expected events
4. Check session file created in `/storage/sessions/`
5. Verify evidence map artifact created
6. Retrieve via API: `GET /sessions/{id}`
7. Verify all agents executed in correct order
8. Check evidence map structure

**Manual UI Test**:
1. Open frontend
2. Submit sample claim
3. Watch live progress
4. Verify all agents show in timeline
5. Click "View Evidence Map"
6. Verify evidence map displays correctly
7. Navigate to replay page
8. Verify all events display
9. Test event filtering

### Performance Testing

**Workflow Execution**:
- Should complete in < 2 minutes for sample claim
- SSE events should stream without noticeable delay
- No memory leaks during execution
- Services should be responsive during workflow

---

## Notes for Continuation

### When Resuming Work:

1. **Check current phase**: Look at todo list or IMPLEMENTATION_PROGRESS.md
2. **Review this document**: Read the relevant phase section completely
3. **Verify dependencies**: Ensure previous phases are complete
4. **Check registry files**: Ensure they match code expectations
5. **Test incrementally**: Test each component as you build it

### Common Gotchas:

1. **Port conflicts**: Ensure 3016, 8016, 8001 are available
2. **API keys**: Remember to set in .env
3. **CORS**: Frontend needs CORS enabled on orchestrator
4. **SSE buffering**: Disable nginx buffering if deploying
5. **Event format**: SSE requires specific format (id, event, data, blank line)
6. **Pydantic versions**: Use Pydantic v2 syntax
7. **Async/Sync mixing**: Orchestrator is sync, API is async - use run_in_executor

### File Naming Conventions:

- Snake_case: Python files (`agent_outputs.py`)
- Kebab-case: TypeScript files (`api-client.ts`)
- PascalCase: React components (`RunClaimPage`)
- Lowercase: Directories (`backend`, `frontend`)

### Import Patterns:

**Python (Backend)**:
```python
from ..services.registry_manager import get_registry_manager
from ..schemas.agent_outputs import IntakeAgentOutput
from .models import RunWorkflowRequest
```

**TypeScript (Frontend)**:
```typescript
import { apiClient } from '@/lib/api-client';
import { useSSE } from '@/hooks/use-sse';
```

---

## End of Remaining Work Document

This document provides complete implementation details for Phases 5-8. Each phase includes:
- Purpose and dependencies
- Detailed file-by-file implementation
- Code examples
- Integration points
- Completion checklists
- Success criteria

Refer to this document when continuing work to ensure seamless continuation with full context.
