"""
Agent Output Schemas - Pydantic models for structured output validation.

Demonstrates scalability patterns:
- Schema-driven validation
- Type safety
- Documentation via models
- Reusable components
- Configurable validation
"""

from pydantic import BaseModel, Field, field_validator
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


# ============= Intake Agent =============

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

    @field_validator('data_quality_score')
    @classmethod
    def score_range_check(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('data_quality_score must be between 0 and 1')
        return v


# ============= Coverage Agent =============

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


# ============= Fraud Agent =============

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


# ============= Severity Agent =============

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


# ============= Recommendation Agent =============

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
        min_length=1,
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


# ============= Explainability Agent =============

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
        min_length=1,
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
        min_length=1,
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


# ============= Orchestrator Output =============

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

    evidence_map: Dict[str, Any] = Field(
        ...,
        description="Final evidence map (can be complete ExplainabilityAgentOutput or partial auto-generated)"
    )

    agents_executed: List[str] = Field(
        ...,
        min_length=1,
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
