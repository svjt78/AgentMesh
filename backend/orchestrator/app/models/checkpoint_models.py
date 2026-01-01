"""
Checkpoint Models

Pydantic models for Human-in-the-Loop (HITL) checkpoints.
Supports approval, decision, input, and escalation checkpoint types.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CheckpointType(str, Enum):
    """Type of human intervention required"""
    APPROVAL = "approval"        # Simple approve/reject decision
    DECISION = "decision"        # Choose from multiple options
    INPUT = "input"             # Provide or correct data
    ESCALATION = "escalation"   # Escalate to higher authority


class CheckpointStatus(str, Enum):
    """Lifecycle status of checkpoint"""
    PENDING = "pending"         # Awaiting human response
    RESOLVED = "resolved"       # Human has responded
    TIMEOUT = "timeout"         # Timeout threshold reached
    CANCELLED = "cancelled"     # Manually cancelled (admin)


class CheckpointResolution(BaseModel):
    """
    Human decision/input at checkpoint.

    Captures what action the human took and any associated data.
    """
    action: str = Field(..., description="Action taken (approve/reject/escalate/confirm_fraud/etc)")
    user_id: str = Field(..., description="ID of user who resolved checkpoint")
    user_role: str = Field(..., description="Role of user who resolved")
    comments: Optional[str] = Field(None, description="Human reasoning or notes")
    data_updates: Optional[Dict[str, Any]] = Field(None, description="Data corrections or additions")
    resolved_at: str = Field(..., description="ISO timestamp of resolution")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "confirm_fraud",
                "user_id": "john.doe@example.com",
                "user_role": "fraud_investigator",
                "comments": "High confidence fraud - similar pattern to case #1234",
                "data_updates": {"fraud_confirmed": True},
                "resolved_at": "2025-12-30T14:25:00Z"
            }
        }


class CheckpointInstance(BaseModel):
    """
    Active checkpoint instance for a workflow session.

    Represents a paused workflow waiting for human intervention.
    """
    checkpoint_instance_id: str = Field(..., description="Unique checkpoint instance ID (UUID)")
    session_id: str = Field(..., description="Workflow session ID")
    workflow_id: str = Field(..., description="Workflow type")
    checkpoint_id: str = Field(..., description="Checkpoint config ID from registry")
    checkpoint_type: CheckpointType = Field(..., description="Type of checkpoint")
    checkpoint_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed explanation for users")
    status: CheckpointStatus = Field(CheckpointStatus.PENDING, description="Current status")

    # Timestamps
    created_at: str = Field(..., description="ISO timestamp when created")
    timeout_at: Optional[str] = Field(None, description="ISO timestamp when timeout occurs")
    resolved_at: Optional[str] = Field(None, description="ISO timestamp when resolved")

    # Resolution
    resolution: Optional[CheckpointResolution] = Field(None, description="Human decision (when resolved)")

    # Context and configuration
    context_data: Dict[str, Any] = Field(..., description="Data for UI display (input, outputs, etc)")
    required_role: str = Field(..., description="Role required to resolve this checkpoint")
    on_timeout: Optional[str] = Field(None, description="Action on timeout (auto_approve/auto_reject/cancel_workflow)")

    # UI configuration
    ui_schema: Dict[str, Any] = Field(default_factory=dict, description="UI display schema from config")

    class Config:
        json_schema_extra = {
            "example": {
                "checkpoint_instance_id": "cp_abc123xyz",
                "session_id": "sess_xyz789",
                "workflow_id": "claims_triage",
                "checkpoint_id": "fraud_review",
                "checkpoint_type": "decision",
                "checkpoint_name": "Fraud Signal Review",
                "description": "Review fraud detection results when score is high",
                "status": "pending",
                "created_at": "2025-12-30T14:00:00Z",
                "timeout_at": "2025-12-30T15:00:00Z",
                "resolved_at": None,
                "resolution": None,
                "context_data": {
                    "fraud_score": 0.85,
                    "fraud_signals": ["multiple_claims", "suspicious_timing"]
                },
                "required_role": "fraud_investigator",
                "on_timeout": "proceed_with_default",
                "ui_schema": {
                    "display_fields": ["fraud_score", "fraud_signals"],
                    "decision_options": [
                        {"value": "confirm_fraud", "label": "Confirm Fraud"},
                        {"value": "false_positive", "label": "False Positive"}
                    ]
                }
            }
        }


class TriggerCondition(BaseModel):
    """
    Conditional trigger for checkpoints.

    Allows checkpoints to be created only when condition evaluates to true.
    """
    type: str = Field(..., description="Condition type (output_based/input_based/always)")
    condition: str = Field(..., description="Expression to evaluate (e.g., 'fraud_score > 0.7')")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "output_based",
                "condition": "fraud_score > 0.7"
            }
        }


class TimeoutConfig(BaseModel):
    """Timeout configuration for checkpoint"""
    enabled: bool = Field(False, description="Whether timeout is enabled")
    timeout_seconds: Optional[int] = Field(None, description="Seconds until timeout")
    on_timeout: Optional[str] = Field(None, description="Action on timeout")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "timeout_seconds": 3600,
                "on_timeout": "auto_approve"
            }
        }


class NotificationConfig(BaseModel):
    """Notification configuration for checkpoint"""
    enabled: bool = Field(False, description="Whether notifications are enabled")
    channels: List[str] = Field(default_factory=list, description="Notification channels")
    urgency: str = Field("normal", description="Urgency level (low/normal/high)")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "channels": ["dashboard", "email"],
                "urgency": "high"
            }
        }


class CheckpointConfig(BaseModel):
    """
    Checkpoint configuration from workflow registry.

    Defines when and how a checkpoint is created.
    """
    checkpoint_id: str = Field(..., description="Unique checkpoint ID")
    checkpoint_type: CheckpointType = Field(..., description="Type of checkpoint")
    trigger_point: str = Field(..., description="When to trigger (pre_workflow/after_agent/before_completion)")
    agent_id: Optional[str] = Field(None, description="Agent ID (required if trigger_point is after_agent)")
    checkpoint_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed explanation")
    required_role: str = Field(..., description="Role required to resolve")

    # Optional configurations
    trigger_condition: Optional[TriggerCondition] = Field(None, description="Conditional trigger")
    timeout_config: TimeoutConfig = Field(default_factory=TimeoutConfig, description="Timeout settings")
    notification_config: NotificationConfig = Field(default_factory=NotificationConfig, description="Notification settings")
    ui_schema: Dict[str, Any] = Field(default_factory=dict, description="UI display schema")

    class Config:
        json_schema_extra = {
            "example": {
                "checkpoint_id": "fraud_review",
                "checkpoint_type": "decision",
                "trigger_point": "after_agent",
                "agent_id": "fraud_agent",
                "checkpoint_name": "Fraud Signal Review",
                "description": "Review fraud detection results when score is high",
                "required_role": "fraud_investigator",
                "trigger_condition": {
                    "type": "output_based",
                    "condition": "fraud_score > 0.7"
                },
                "timeout_config": {
                    "enabled": True,
                    "timeout_seconds": 3600,
                    "on_timeout": "proceed_with_default"
                },
                "ui_schema": {
                    "display_fields": ["fraud_score", "fraud_signals"]
                }
            }
        }


# Request/Response models for API

class ResolveCheckpointRequest(BaseModel):
    """Request to resolve a checkpoint"""
    action: str = Field(..., description="Action to take")
    user_id: str = Field(..., description="User ID")
    user_role: str = Field(..., description="User role")
    comments: Optional[str] = Field(None, description="Comments or reasoning")
    data_updates: Optional[Dict[str, Any]] = Field(None, description="Data updates")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "approve",
                "user_id": "john.doe@example.com",
                "user_role": "reviewer",
                "comments": "Claim details verified",
                "data_updates": None
            }
        }


class CheckpointListResponse(BaseModel):
    """Response for list of checkpoints"""
    checkpoints: List[CheckpointInstance] = Field(..., description="List of checkpoints")
    total_count: int = Field(..., description="Total count")


class ResolveCheckpointResponse(BaseModel):
    """Response after resolving checkpoint"""
    success: bool = Field(..., description="Whether resolution succeeded")
    message: str = Field(..., description="Success or error message")
    checkpoint_instance_id: str = Field(..., description="Checkpoint instance ID")
