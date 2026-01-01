"""
API Models - Request and response schemas for orchestrator API.

Demonstrates:
- API contract definition
- Input validation
- Type safety
- OpenAPI documentation
"""

from pydantic import BaseModel, Field
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
        json_schema_extra = {
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
        json_schema_extra = {
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


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(default="1.0.0", description="API version")
    registries_loaded: bool = Field(..., description="Whether registries are loaded")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error detail message")
    error_type: Optional[str] = Field(None, description="Error type classification")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


# ============= Registry Management Models =============

# ----- Agent Models -----

class AgentResponse(BaseModel):
    """Agent response model."""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    allowed_tools: List[str]
    allowed_agents: Optional[List[str]] = None
    model_profile_id: str
    max_iterations: int
    iteration_timeout_seconds: int
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Dict[str, Any]
    context_requirements: Dict[str, Any]


class AgentCreateRequest(BaseModel):
    """Request model for creating/updating agents."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent purpose and capabilities")
    capabilities: List[str] = Field(..., description="List of agent capabilities for discovery")
    allowed_tools: List[str] = Field(default=[], description="Tools this agent can use")
    allowed_agents: Optional[List[str]] = Field(None, description="Agents this agent can invoke (orchestrator only)")
    model_profile_id: str = Field(..., description="LLM model profile to use")
    max_iterations: int = Field(default=10, ge=1, le=50, description="Maximum ReAct iterations")
    iteration_timeout_seconds: int = Field(default=60, ge=10, le=300, description="Timeout per iteration")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for expected input")
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for agent output")
    context_requirements: Dict[str, Any] = Field(default={}, description="Context compilation requirements")


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    agents: List[AgentResponse]
    total_count: int
    timestamp: str


# ----- Tool Models -----

class ToolResponse(BaseModel):
    """Tool response model."""
    tool_id: str
    name: str
    description: str
    endpoint: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    lineage_tags: List[str]


class ToolCreateRequest(BaseModel):
    """Request model for creating/updating tools."""
    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Detailed tool description for LLM context")
    endpoint: str = Field(..., description="API endpoint path (e.g., /invoke/fraud_rules)")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for tool input")
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for tool output")
    lineage_tags: List[str] = Field(default=[], description="Tags for tool categorization")


class ToolListResponse(BaseModel):
    """Response model for listing tools."""
    tools: List[ToolResponse]
    total_count: int
    timestamp: str


# ----- Model Profile Models -----

class ModelProfileResponse(BaseModel):
    """Model profile response model."""
    profile_id: str
    name: str
    description: str
    provider: str
    model_name: str
    intended_usage: str
    parameters: Dict[str, Any]
    json_mode: bool
    constraints: Dict[str, Any]
    retry_policy: Dict[str, Any]
    timeout_seconds: int


class ModelProfileCreateRequest(BaseModel):
    """Request model for creating/updating model profiles."""
    profile_id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., description="Human-readable profile name")
    description: str = Field(..., description="Profile purpose and characteristics")
    provider: str = Field(..., description="LLM provider (openai or anthropic)")
    model_name: str = Field(..., description="Specific model name")
    intended_usage: str = Field(..., description="Recommended use case")
    parameters: Dict[str, Any] = Field(default={}, description="Model parameters (temperature, max_tokens, etc.)")
    json_mode: bool = Field(default=False, description="Enable JSON mode")
    constraints: Dict[str, Any] = Field(default={}, description="Token limits and constraints")
    retry_policy: Dict[str, Any] = Field(default={}, description="Retry configuration")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Request timeout")


class ModelProfileListResponse(BaseModel):
    """Response model for listing model profiles."""
    profiles: List[ModelProfileResponse]
    total_count: int
    timestamp: str


# ----- Workflow Models -----

class WorkflowResponse(BaseModel):
    """Workflow response model."""
    workflow_id: str
    name: str
    description: str
    version: str
    mode: str
    goal: Optional[str] = None
    steps: List[Dict[str, Any]]
    suggested_sequence: Optional[List[str]] = []
    required_agents: Optional[List[str]] = []
    optional_agents: Optional[List[str]] = []
    completion_criteria: Optional[Dict[str, Any]] = {}
    constraints: Optional[Dict[str, Any]] = {}
    metadata: Dict[str, Any]
    hitl_checkpoints: Optional[List[Dict[str, Any]]] = []


class WorkflowCreateRequest(BaseModel):
    """Request model for creating/updating workflows."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(..., description="Workflow purpose and scope")
    version: str = Field(default="1.0.0", description="Workflow version")
    mode: str = Field(default="advisory", description="Execution mode (advisory or strict)")
    goal: Optional[str] = Field(None, description="Workflow goal statement")
    steps: List[Dict[str, Any]] = Field(default=[], description="Workflow step definitions")
    suggested_sequence: Optional[List[str]] = Field(default=[], description="Suggested agent sequence")
    required_agents: Optional[List[str]] = Field(default=[], description="Required agents")
    optional_agents: Optional[List[str]] = Field(default=[], description="Optional agents")
    completion_criteria: Optional[Dict[str, Any]] = Field(default={}, description="Completion criteria")
    constraints: Optional[Dict[str, Any]] = Field(default={}, description="Workflow constraints")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    hitl_checkpoints: Optional[List[Dict[str, Any]]] = Field(default=[], description="HITL checkpoint configurations")


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[WorkflowResponse]
    total_count: int
    timestamp: str


# ----- Governance Models -----

class GovernancePoliciesResponse(BaseModel):
    """Governance policies response model."""
    version: str
    policies: Dict[str, Any]


class GovernancePoliciesUpdateRequest(BaseModel):
    """Request model for updating governance policies."""
    version: str = Field(..., description="Policy version")
    policies: Dict[str, Any] = Field(..., description="Complete policy document")


# ----- System Configuration Models -----

class SystemConfigResponse(BaseModel):
    """System configuration response model."""
    version: str
    orchestrator: Dict[str, Any]
    workflow: Dict[str, Any]
    agent: Dict[str, Any]
    llm: Dict[str, Any]
    governance: Dict[str, Any]
    safety: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = {}


class SystemConfigUpdateRequest(BaseModel):
    """Request model for updating system configuration."""
    version: str = Field(..., description="Configuration version")
    orchestrator: Dict[str, Any] = Field(..., description="Orchestrator limits")
    workflow: Dict[str, Any] = Field(..., description="Workflow execution limits")
    agent: Dict[str, Any] = Field(..., description="Agent default limits")
    llm: Dict[str, Any] = Field(..., description="LLM interaction limits")
    governance: Dict[str, Any] = Field(..., description="Governance session limits")
    safety: Dict[str, Any] = Field(..., description="Safety thresholds")
    schema: Optional[Dict[str, Any]] = Field(default={}, description="Schema validation settings")


# ----- Generic Operation Response -----

class RegistryOperationResponse(BaseModel):
    """Generic response for registry operations."""
    success: bool
    message: str
    timestamp: str
