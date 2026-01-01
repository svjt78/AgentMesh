"""
Agent Output Schemas - Pydantic models for structured output validation.

Provides type-safe, validated schemas for all agent outputs enabling:
- Runtime validation
- Type safety
- Documentation
- Observability
- Context engineering

Demonstrates scalability patterns:
- Schema-driven validation
- Configurable validation behavior
- Detailed error reporting
- Version tracking
"""

from .agent_outputs import (
    AgentOutputBase,
    DataQualityIssue,
    IntakeAgentOutput,
    CoverageDeterminationType,
    CoverageAgentOutput,
    RiskBand,
    FraudIndicator,
    FraudAgentOutput,
    ComplexityLevel,
    SeverityAgentOutput,
    ProcessingTrack,
    RecommendationAgentOutput,
    Evidence,
    Decision,
    ExplainabilityAgentOutput,
    CompletionReason,
    OrchestratorOutput
)

from .validators import (
    validate_agent_output,
    get_schema_for_agent,
    get_schema_json,
    list_available_schemas,
    SchemaValidationError,
    AGENT_OUTPUT_SCHEMAS
)

__all__ = [
    # Base models
    "AgentOutputBase",

    # Intake agent
    "DataQualityIssue",
    "IntakeAgentOutput",

    # Coverage agent
    "CoverageDeterminationType",
    "CoverageAgentOutput",

    # Fraud agent
    "RiskBand",
    "FraudIndicator",
    "FraudAgentOutput",

    # Severity agent
    "ComplexityLevel",
    "SeverityAgentOutput",

    # Recommendation agent
    "ProcessingTrack",
    "RecommendationAgentOutput",

    # Explainability agent
    "Evidence",
    "Decision",
    "ExplainabilityAgentOutput",

    # Orchestrator
    "CompletionReason",
    "OrchestratorOutput",

    # Validators
    "validate_agent_output",
    "get_schema_for_agent",
    "get_schema_json",
    "list_available_schemas",
    "SchemaValidationError",
    "AGENT_OUTPUT_SCHEMAS"
]
