"""
Schema Validators - Validation utilities for agent outputs.

Demonstrates:
- Runtime validation
- Schema version checking
- Custom validation rules
- Detailed error reporting
- Context engineering support
"""

from typing import Dict, Any, Type, Optional
from pydantic import ValidationError
from datetime import datetime
from .agent_outputs import (
    AgentOutputBase,
    IntakeAgentOutput,
    CoverageAgentOutput,
    FraudAgentOutput,
    SeverityAgentOutput,
    RecommendationAgentOutput,
    ExplainabilityAgentOutput,
    OrchestratorOutput
)


# Schema registry - maps agent_id to output schema class
AGENT_OUTPUT_SCHEMAS: Dict[str, Type[AgentOutputBase]] = {
    "intake_agent": IntakeAgentOutput,
    "coverage_agent": CoverageAgentOutput,
    "fraud_agent": FraudAgentOutput,
    "severity_agent": SeverityAgentOutput,
    "recommendation_agent": RecommendationAgentOutput,
    "explainability_agent": ExplainabilityAgentOutput,
    "orchestrator_agent": OrchestratorOutput
}


class SchemaValidationError(Exception):
    """
    Exception raised when schema validation fails.

    Includes detailed error information for observability and debugging.
    """

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.errors = errors or []
        self.timestamp = datetime.utcnow().isoformat() + "Z"


def validate_agent_output(
    agent_id: str,
    output_data: Dict[str, Any],
    version: Optional[str] = None
) -> AgentOutputBase:
    """
    Validate agent output against its schema.

    Demonstrates: Production-grade validation with detailed error reporting.

    Args:
        agent_id: Agent ID to look up schema
        output_data: Raw output data from agent
        version: Optional schema version override

    Returns:
        Validated output model

    Raises:
        SchemaValidationError: If validation fails with detailed error list

    Example:
        >>> output = validate_agent_output("fraud_agent", {
        ...     "fraud_score": 0.75,
        ...     "risk_band": "high",
        ...     "siu_referral_required": True,
        ...     "rationale": "Multiple fraud indicators detected"
        ... })
    """
    # Get schema for agent
    schema_class = AGENT_OUTPUT_SCHEMAS.get(agent_id)

    if not schema_class:
        raise SchemaValidationError(
            f"No output schema defined for agent '{agent_id}'. "
            f"Available agents: {', '.join(AGENT_OUTPUT_SCHEMAS.keys())}"
        )

    try:
        # Ensure required metadata fields are present
        if "agent_id" not in output_data:
            output_data["agent_id"] = agent_id

        if "timestamp" not in output_data:
            output_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Apply version override if provided
        if version and "version" not in output_data:
            output_data["version"] = version

        # Validate and parse
        validated_output = schema_class(**output_data)

        return validated_output

    except ValidationError as e:
        # Format validation errors for observability
        formatted_errors = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = error["msg"]
            error_type = error["type"]

            formatted_errors.append({
                "field": field_path,
                "message": error_msg,
                "type": error_type,
                "input": error.get("input")
            })

        # Create detailed error message
        error_summary = "\n".join(
            f"  • {err['field']}: {err['message']}"
            for err in formatted_errors
        )

        raise SchemaValidationError(
            f"Output validation failed for agent '{agent_id}':\n{error_summary}",
            errors=formatted_errors
        )

    except Exception as e:
        # Catch any other validation errors
        raise SchemaValidationError(
            f"Unexpected validation error for agent '{agent_id}': {str(e)}"
        )


def get_schema_for_agent(agent_id: str) -> Optional[Type[AgentOutputBase]]:
    """
    Get output schema class for agent.

    Args:
        agent_id: Agent ID

    Returns:
        Schema class or None if not found

    Example:
        >>> schema = get_schema_for_agent("fraud_agent")
        >>> print(schema.__name__)
        'FraudAgentOutput'
    """
    return AGENT_OUTPUT_SCHEMAS.get(agent_id)


def get_schema_json(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get JSON schema for agent output.

    Useful for API documentation and client code generation.

    Args:
        agent_id: Agent ID

    Returns:
        JSON schema dict or None if agent not found

    Example:
        >>> schema_json = get_schema_json("fraud_agent")
        >>> print(schema_json["properties"]["fraud_score"])
        {'type': 'number', 'minimum': 0.0, 'maximum': 1.0, ...}
    """
    schema_class = AGENT_OUTPUT_SCHEMAS.get(agent_id)
    if schema_class:
        return schema_class.model_json_schema()
    return None


def list_available_schemas() -> Dict[str, str]:
    """
    List all available agent output schemas.

    Returns:
        Dict mapping agent_id to schema class name

    Example:
        >>> schemas = list_available_schemas()
        >>> for agent_id, schema_name in schemas.items():
        ...     print(f"{agent_id}: {schema_name}")
    """
    return {
        agent_id: schema_class.__name__
        for agent_id, schema_class in AGENT_OUTPUT_SCHEMAS.items()
    }


def validate_partial_output(
    agent_id: str,
    output_data: Dict[str, Any],
    required_fields: Optional[list] = None
) -> tuple[bool, list]:
    """
    Validate partial output (for incomplete agent executions).

    Less strict than full validation - only checks specified required fields.

    Args:
        agent_id: Agent ID
        output_data: Partial output data
        required_fields: List of field names that must be present

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        >>> valid, errors = validate_partial_output(
        ...     "fraud_agent",
        ...     {"fraud_score": 0.5},
        ...     required_fields=["fraud_score", "risk_band"]
        ... )
        >>> print(valid, errors)
        False ['Missing required field: risk_band']
    """
    errors = []

    # Check if schema exists
    if agent_id not in AGENT_OUTPUT_SCHEMAS:
        errors.append(f"Unknown agent_id: {agent_id}")
        return False, errors

    # Check required fields if specified
    if required_fields:
        for field in required_fields:
            if field not in output_data:
                errors.append(f"Missing required field: {field}")

    # Check if output_data is a dict
    if not isinstance(output_data, dict):
        errors.append(f"Output must be a dict, got {type(output_data).__name__}")

    return len(errors) == 0, errors


def get_schema_version(agent_id: str, output_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract schema version from output data.

    Args:
        agent_id: Agent ID
        output_data: Output data dict

    Returns:
        Schema version string or None

    Example:
        >>> version = get_schema_version("fraud_agent", {"version": "1.0", ...})
        >>> print(version)
        '1.0'
    """
    return output_data.get("version")


def validate_schema_version(
    agent_id: str,
    output_version: str,
    expected_version: str = "1.0"
) -> bool:
    """
    Validate that output schema version matches expected version.

    Args:
        agent_id: Agent ID
        output_version: Version from output data
        expected_version: Expected schema version

    Returns:
        True if versions match

    Example:
        >>> is_valid = validate_schema_version("fraud_agent", "1.0", "1.0")
        >>> print(is_valid)
        True
    """
    return output_version == expected_version
