"""
Central configuration module.

Loads configuration with the following priority:
1. system_config.json (if exists)
2. Environment variables (.env file)
3. Hardcoded defaults

All limits and timeouts are configurable via UI (writes to system_config.json) or .env file.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class OrchestratorLimits(BaseModel):
    """Orchestrator agent execution limits."""
    max_iterations: int = Field(default=10)
    iteration_timeout_seconds: int = Field(default=30)


class WorkflowLimits(BaseModel):
    """Workflow execution limits."""
    max_duration_seconds: int = Field(default=300)
    max_agent_invocations: int = Field(default=20)


class AgentLimits(BaseModel):
    """Default agent execution limits."""
    default_max_iterations: int = Field(default=5)
    default_iteration_timeout_seconds: int = Field(default=30)
    max_duplicate_invocations: int = Field(default=2)


class LLMLimits(BaseModel):
    """LLM API constraints."""
    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    max_tokens_per_request: int = Field(default=2000)
    max_tokens_per_session: int = Field(default=50000)


class GovernanceLimits(BaseModel):
    """Governance and safety limits."""
    max_tool_invocations_per_session: int = Field(default=50)
    max_llm_calls_per_session: int = Field(default=30)


class SafetyThresholds(BaseModel):
    """Safety mechanism thresholds."""
    consecutive_no_progress_limit: int = Field(default=2)
    malformed_response_limit: int = Field(default=3)


class SchemaSettings(BaseModel):
    """Schema validation settings for agent outputs."""
    default_version: str = Field(default="1.0", description="Default schema version")
    strict_validation: bool = Field(default=True, description="Enforce strict schema validation")
    validation_failure_limit: int = Field(default=3, description="Max validation failures before agent errors")
    log_validation_sample: bool = Field(default=True, description="Log output sample on validation failure")
    max_validation_sample_chars: int = Field(default=500, description="Max chars to log in validation samples")


class Config(BaseModel):
    """Complete system configuration."""

    # LLM Provider API Keys
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")

    # Service URLs
    tools_base_url: str = Field(default="http://tools_gateway:8010")

    # Storage
    storage_path: str = Field(default="/storage")

    # Limits
    orchestrator: OrchestratorLimits = Field(default_factory=OrchestratorLimits)
    workflow: WorkflowLimits = Field(default_factory=WorkflowLimits)
    agent: AgentLimits = Field(default_factory=AgentLimits)
    llm: LLMLimits = Field(default_factory=LLMLimits)
    governance: GovernanceLimits = Field(default_factory=GovernanceLimits)
    safety: SafetyThresholds = Field(default_factory=SafetyThresholds)
    schema: SchemaSettings = Field(default_factory=SchemaSettings)


def _load_system_config() -> Optional[Dict[str, Any]]:
    """
    Load system configuration from JSON file if it exists.

    Returns:
        Dict with config values, or None if file doesn't exist
    """
    # Try to find system_config.json in registries/
    config_paths = [
        Path("/app/registries/system_config.json"),  # Docker path
        Path("registries/system_config.json"),  # Relative path
        Path("../../../registries/system_config.json"),  # From backend/orchestrator/app
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load system_config.json: {e}")
                return None

    return None


def load_config() -> Config:
    """
    Load configuration with fallback chain:
    1. system_config.json (if exists) - UI-edited values
    2. Environment variables (.env file) - deployment overrides
    3. Hardcoded defaults - fallback

    Returns:
        Config object with all settings loaded
    """
    # Try to load from system_config.json first
    sys_config = _load_system_config()

    # Helper function to get value with fallback chain
    def get_value(sys_key: str, field_key: str, env_var: str, default: str) -> str:
        """Get config value with fallback: JSON -> env -> default"""
        if sys_config and sys_key in sys_config and field_key in sys_config[sys_key]:
            return str(sys_config[sys_key][field_key])
        return os.getenv(env_var, default)

    return Config(
        # LLM Provider API Keys (always from env, never from JSON for security)
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),

        # Service URLs (always from env, never from JSON for security)
        tools_base_url=os.getenv("TOOLS_BASE_URL", "http://tools_gateway:8010"),

        # Storage (always from env)
        storage_path=os.getenv("STORAGE_PATH", "/storage"),

        # Orchestrator limits
        orchestrator=OrchestratorLimits(
            max_iterations=int(get_value("orchestrator", "max_iterations", "ORCHESTRATOR_MAX_ITERATIONS", "10")),
            iteration_timeout_seconds=int(get_value("orchestrator", "iteration_timeout_seconds", "ORCHESTRATOR_ITERATION_TIMEOUT_SECONDS", "30"))
        ),

        # Workflow limits
        workflow=WorkflowLimits(
            max_duration_seconds=int(get_value("workflow", "max_duration_seconds", "WORKFLOW_MAX_DURATION_SECONDS", "300")),
            max_agent_invocations=int(get_value("workflow", "max_agent_invocations", "WORKFLOW_MAX_AGENT_INVOCATIONS", "20"))
        ),

        # Agent limits
        agent=AgentLimits(
            default_max_iterations=int(get_value("agent", "default_max_iterations", "AGENT_DEFAULT_MAX_ITERATIONS", "5")),
            default_iteration_timeout_seconds=int(get_value("agent", "default_iteration_timeout_seconds", "AGENT_DEFAULT_ITERATION_TIMEOUT_SECONDS", "30")),
            max_duplicate_invocations=int(get_value("agent", "max_duplicate_invocations", "AGENT_MAX_DUPLICATE_INVOCATIONS", "2"))
        ),

        # LLM limits
        llm=LLMLimits(
            timeout_seconds=int(get_value("llm", "timeout_seconds", "LLM_TIMEOUT_SECONDS", "30")),
            max_retries=int(get_value("llm", "max_retries", "LLM_MAX_RETRIES", "3")),
            max_tokens_per_request=int(get_value("llm", "max_tokens_per_request", "LLM_MAX_TOKENS_PER_REQUEST", "2000")),
            max_tokens_per_session=int(get_value("llm", "max_tokens_per_session", "LLM_MAX_TOKENS_PER_SESSION", "50000"))
        ),

        # Governance limits
        governance=GovernanceLimits(
            max_tool_invocations_per_session=int(get_value("governance", "max_tool_invocations_per_session", "MAX_TOOL_INVOCATIONS_PER_SESSION", "50")),
            max_llm_calls_per_session=int(get_value("governance", "max_llm_calls_per_session", "MAX_LLM_CALLS_PER_SESSION", "30"))
        ),

        # Safety thresholds
        safety=SafetyThresholds(
            consecutive_no_progress_limit=int(get_value("safety", "consecutive_no_progress_limit", "CONSECUTIVE_NO_PROGRESS_LIMIT", "2")),
            malformed_response_limit=int(get_value("safety", "malformed_response_limit", "MALFORMED_RESPONSE_LIMIT", "3"))
        ),

        # Schema validation settings
        schema=SchemaSettings(
            default_version=get_value("schema", "default_version", "SCHEMA_DEFAULT_VERSION", "1.0"),
            strict_validation=get_value("schema", "strict_validation", "SCHEMA_STRICT_VALIDATION", "true").lower() == "true",
            validation_failure_limit=int(get_value("schema", "validation_failure_limit", "SCHEMA_VALIDATION_FAILURE_LIMIT", "3")),
            log_validation_sample=get_value("schema", "log_validation_sample", "SCHEMA_LOG_VALIDATION_SAMPLE", "true").lower() == "true",
            max_validation_sample_chars=int(get_value("schema", "max_validation_sample_chars", "SCHEMA_MAX_VALIDATION_SAMPLE_CHARS", "500"))
        )
    )


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get singleton Config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Force reload configuration from environment."""
    global _config
    _config = load_config()
    return _config
