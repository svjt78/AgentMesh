# Registry Management System - Implementation Plan

**Version:** 1.0
**Date:** 2025-12-26
**Status:** Ready for Implementation

---

## Executive Summary

This document outlines the complete implementation plan for adding comprehensive CRUD (Create, Read, Update, Delete) operations to the AgentMesh registry management system. The implementation will provide both REST API endpoints and a web-based Configuration Panel, demonstrating production-ready configurability, governance, and observability for multi-agent systems.

### Goals

1. **Full Configurability**: Enable runtime management of all registry types without editing JSON files
2. **Production Governance**: Validate references, prevent invalid configurations, check usage before deletion
3. **Hot Reload**: Automatic registry reload after changes without service restart
4. **Transparency**: Clear UI for viewing and managing system configuration
5. **Scalability**: Thread-safe operations supporting concurrent access

### Key Features

- ✅ REST API with full CRUD operations for agents, tools, model profiles, workflows, and governance policies
- ✅ Web UI Configuration Panel with tabbed interface
- ✅ Input schema support for agents (added to existing output schema)
- ✅ Automatic hot reload after registry modifications
- ✅ Comprehensive validation (reference checking, schema validation, usage prevention)
- ✅ Special handling for orchestrator agent (separate UI/API, cannot be deleted)
- ✅ Thread-safe atomic file operations

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Requirements](#requirements)
3. [Phase 1: Backend Foundation](#phase-1-backend-foundation)
4. [Phase 2: Frontend Development](#phase-2-frontend-development)
5. [Phase 3: Testing & Validation](#phase-3-testing--validation)
6. [Implementation Timeline](#implementation-timeline)
7. [Critical Files](#critical-files)
8. [Design Patterns](#design-patterns)
9. [Security Considerations](#security-considerations)
10. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### Current State

**Registry Structure:**
- JSON files in `/registries/` directory
- RegistryManager singleton loads registries at startup
- Pydantic models for validation
- Thread-safe read operations
- Hot-reload function exists but not exposed via API

**Limitations:**
- Read-only at runtime (requires file editing)
- No validation before file modification
- No UI for configuration management
- No input schema for agents

### Target State

**Enhanced Registry Management:**
- Full CRUD API endpoints (`/registries/*`)
- Web-based Configuration Panel (`/config`)
- Input schema support for agents
- Automatic hot reload after changes
- Comprehensive validation pipeline
- Usage tracking to prevent breaking changes

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Configuration Panel (/config)                           │   │
│  │  ├─ Orchestrator Tab                                     │   │
│  │  ├─ Agents Tab                                           │   │
│  │  ├─ Tools Tab                                            │   │
│  │  ├─ Model Profiles Tab                                   │   │
│  │  ├─ Workflows Tab                                        │   │
│  │  └─ Governance Tab                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓ API Client                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Registries API Router (/registries/*)                   │   │
│  │  ├─ GET/POST/PUT/DELETE /agents                          │   │
│  │  ├─ GET/PUT /orchestrator                                │   │
│  │  ├─ GET/POST/PUT/DELETE /tools                           │   │
│  │  ├─ GET/POST/PUT/DELETE /model-profiles                  │   │
│  │  ├─ GET/POST/PUT/DELETE /workflows                       │   │
│  │  ├─ GET/PUT /governance                                  │   │
│  │  └─ POST /reload                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  RegistryManager (Enhanced)                              │   │
│  │  ├─ Read Operations (existing)                           │   │
│  │  ├─ Write Operations (new)                               │   │
│  │  ├─ Validation Pipeline (new)                            │   │
│  │  ├─ Atomic File Writes (new)                             │   │
│  │  └─ Hot Reload (enhanced)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Registry Files (JSON)                         │
│  ├─ agent_registry.json                                          │
│  ├─ tool_registry.json                                           │
│  ├─ model_profiles.json                                          │
│  ├─ governance_policies.json                                     │
│  └─ workflows/*.json                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requirements

### Functional Requirements

1. **CRUD Operations**
   - Create new registry entries with validation
   - Read individual entries or list all entries
   - Update existing entries with reference checking
   - Delete entries with usage validation

2. **Input Schema Support**
   - Add optional `input_schema` field to agents
   - Maintain existing `input_schema` for tools
   - Support JSON Schema validation

3. **Hot Reload**
   - Automatic registry reload after modifications
   - No service restart required
   - Thread-safe reload operations

4. **Validation**
   - Reference validation (tools exist, models exist)
   - JSON Schema structure validation
   - Usage checking (prevent deletion of in-use items)
   - Orchestrator protection (cannot be deleted)

5. **User Interface**
   - Tabbed configuration panel
   - Separate tabs for each registry type
   - Create/Edit modals with forms
   - Delete confirmations
   - JSON schema editors

6. **Orchestrator Management**
   - Separate UI tab for orchestrator
   - Separate API endpoints
   - Update only (no create/delete)
   - Manage `allowed_agents` list

### Non-Functional Requirements

1. **Performance**
   - O(1) registry lookups (existing)
   - Fast hot reload (< 100ms)
   - Non-blocking UI operations

2. **Reliability**
   - Atomic file writes (no corruption)
   - Thread-safe operations
   - Graceful error handling

3. **Usability**
   - Intuitive UI design
   - Clear error messages
   - Immediate feedback on operations

4. **Maintainability**
   - Follow existing code patterns
   - Comprehensive error logging
   - Clear separation of concerns

---

## Phase 1: Backend Foundation

### 1.1 Update Pydantic Models

**File:** `backend/orchestrator/app/services/registry_manager.py`

**Changes Required:**

Add `input_schema` field to `AgentMetadata` class (lines 20-33):

```python
class AgentMetadata(BaseModel):
    """Agent registry entry with full metadata."""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    allowed_tools: Optional[List[str]] = []
    allowed_agents: Optional[List[str]] = []  # For orchestrator agent
    model_profile_id: str
    max_iterations: int
    iteration_timeout_seconds: int
    input_schema: Optional[Dict[str, Any]] = None  # NEW FIELD - optional for backward compatibility
    output_schema: Dict[str, Any]
    context_requirements: Dict[str, Any]
```

**Rationale:**
- Optional field ensures backward compatibility
- Allows agents to specify expected input structure
- Mirrors existing `input_schema` pattern in `ToolMetadata`

---

### 1.2 Add Write Operations to RegistryManager

**File:** `backend/orchestrator/app/services/registry_manager.py`

**New Methods to Add:**

#### Agent CRUD

```python
def create_agent(self, agent: AgentMetadata) -> None:
    """
    Create new agent with validation.

    Validates:
    - Agent ID doesn't already exist
    - Model profile exists
    - All allowed tools exist

    Raises:
        ValueError: If validation fails
    """
    with self._lock:
        # Check for duplicate ID
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent '{agent.agent_id}' already exists")

        # Validate references
        self._validate_agent_references(agent)

        # Update in-memory cache
        self._agents[agent.agent_id] = agent

        # Write to disk atomically
        self._write_agent_registry()

        # Hot reload to ensure consistency
        self.load_all()

        print(f"[RegistryManager] Created agent: {agent.agent_id}")

def update_agent(self, agent_id: str, agent: AgentMetadata) -> None:
    """
    Update existing agent.

    Args:
        agent_id: Current agent ID
        agent: New agent data (agent.agent_id must match agent_id)

    Raises:
        ValueError: If agent not found or validation fails
    """
    with self._lock:
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")

        # Validate new data
        self._validate_agent_references(agent)

        # Update cache
        self._agents[agent_id] = agent

        # Write to disk
        self._write_agent_registry()

        # Hot reload
        self.load_all()

        print(f"[RegistryManager] Updated agent: {agent_id}")

def delete_agent(self, agent_id: str) -> None:
    """
    Delete agent after usage checks.

    Prevents deletion if:
    - Agent is the orchestrator
    - Agent is in orchestrator's allowed_agents
    - Agent is required by any workflow

    Raises:
        ValueError: If agent not found or in use
    """
    with self._lock:
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")

        # Prevent deletion of orchestrator
        if agent_id == "orchestrator_agent":
            raise ValueError("Cannot delete orchestrator agent")

        # Check if agent is in use
        self._check_agent_usage(agent_id)

        # Delete from cache
        del self._agents[agent_id]

        # Write to disk
        self._write_agent_registry()

        # Hot reload
        self.load_all()

        print(f"[RegistryManager] Deleted agent: {agent_id}")
```

#### Tool CRUD

```python
def create_tool(self, tool: ToolMetadata) -> None:
    """Create new tool with validation."""
    with self._lock:
        if tool.tool_id in self._tools:
            raise ValueError(f"Tool '{tool.tool_id}' already exists")

        # Validate JSON schemas
        self._validate_json_schema(tool.input_schema)
        self._validate_json_schema(tool.output_schema)

        self._tools[tool.tool_id] = tool
        self._write_tool_registry()
        self.load_all()

def update_tool(self, tool_id: str, tool: ToolMetadata) -> None:
    """Update existing tool."""
    with self._lock:
        if tool_id not in self._tools:
            raise ValueError(f"Tool '{tool_id}' not found")

        self._validate_json_schema(tool.input_schema)
        self._validate_json_schema(tool.output_schema)

        self._tools[tool_id] = tool
        self._write_tool_registry()
        self.load_all()

def delete_tool(self, tool_id: str) -> None:
    """Delete tool after usage checks."""
    with self._lock:
        if tool_id not in self._tools:
            raise ValueError(f"Tool '{tool_id}' not found")

        self._check_tool_usage(tool_id)

        del self._tools[tool_id]
        self._write_tool_registry()
        self.load_all()
```

#### Model Profile CRUD

```python
def create_model_profile(self, profile: ModelProfile) -> None:
    """Create new model profile."""
    with self._lock:
        if profile.profile_id in self._models:
            raise ValueError(f"Model profile '{profile.profile_id}' already exists")

        self._models[profile.profile_id] = profile
        self._write_model_registry()
        self.load_all()

def update_model_profile(self, profile_id: str, profile: ModelProfile) -> None:
    """Update existing model profile."""
    with self._lock:
        if profile_id not in self._models:
            raise ValueError(f"Model profile '{profile_id}' not found")

        self._models[profile_id] = profile
        self._write_model_registry()
        self.load_all()

def delete_model_profile(self, profile_id: str) -> None:
    """Delete model profile after usage checks."""
    with self._lock:
        if profile_id not in self._models:
            raise ValueError(f"Model profile '{profile_id}' not found")

        self._check_model_usage(profile_id)

        del self._models[profile_id]
        self._write_model_registry()
        self.load_all()
```

#### Workflow CRUD

```python
def create_workflow(self, workflow: WorkflowDefinition) -> None:
    """Create new workflow."""
    with self._lock:
        if workflow.workflow_id in self._workflows:
            raise ValueError(f"Workflow '{workflow.workflow_id}' already exists")

        # Validate referenced agents exist
        for agent_id in workflow.required_agents or []:
            if agent_id not in self._agents:
                raise ValueError(f"Required agent '{agent_id}' not found")

        self._workflows[workflow.workflow_id] = workflow
        self._write_workflow_registry(workflow)
        self.load_all()

def update_workflow(self, workflow_id: str, workflow: WorkflowDefinition) -> None:
    """Update existing workflow."""
    with self._lock:
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        for agent_id in workflow.required_agents or []:
            if agent_id not in self._agents:
                raise ValueError(f"Required agent '{agent_id}' not found")

        self._workflows[workflow_id] = workflow
        self._write_workflow_registry(workflow)
        self.load_all()

def delete_workflow(self, workflow_id: str) -> None:
    """Delete workflow."""
    with self._lock:
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        workflow = self._workflows[workflow_id]
        del self._workflows[workflow_id]

        # Delete file
        workflow_file = self.registries_path / "workflows" / f"{workflow_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()

        self.load_all()
```

#### Governance Update

```python
def update_governance_policies(self, policies: GovernancePolicies) -> None:
    """Update governance policies (no create/delete - single document)."""
    with self._lock:
        self._governance = policies
        self._write_governance_policies()
        self.load_all()
```

---

### 1.3 Validation Helper Methods

**Add after CRUD methods:**

```python
def _validate_agent_references(self, agent: AgentMetadata):
    """
    Validate agent references to other registries.

    Checks:
    - Model profile exists
    - All allowed tools exist

    Raises:
        ValueError: If any reference is invalid
    """
    # Validate model profile
    if agent.model_profile_id not in self._models:
        raise ValueError(
            f"Model profile '{agent.model_profile_id}' not found. "
            f"Available profiles: {list(self._models.keys())}"
        )

    # Validate allowed tools
    for tool_id in agent.allowed_tools:
        if tool_id not in self._tools:
            raise ValueError(
                f"Tool '{tool_id}' not found. "
                f"Available tools: {list(self._tools.keys())}"
            )

def _validate_json_schema(self, schema: Dict[str, Any]):
    """
    Validate that a dictionary is a well-formed JSON Schema.

    Uses jsonschema library's Draft7Validator.

    Raises:
        ValueError: If schema is malformed
    """
    try:
        import jsonschema
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as e:
        raise ValueError(f"Invalid JSON schema: {str(e)}")
    except ImportError:
        # jsonschema not installed - skip validation
        print("[RegistryManager] WARNING: jsonschema not installed, skipping schema validation")

def _check_agent_usage(self, agent_id: str):
    """
    Check if agent is used by orchestrator or workflows.

    Prevents deletion of agents that are:
    - In orchestrator's allowed_agents list
    - Required by any workflow

    Raises:
        ValueError: If agent is in use
    """
    # Check orchestrator
    orchestrator = self.get_agent("orchestrator_agent")
    if orchestrator and agent_id in (orchestrator.allowed_agents or []):
        raise ValueError(
            f"Cannot delete agent '{agent_id}': "
            f"used by orchestrator. Remove from orchestrator's allowed_agents first."
        )

    # Check workflows
    for workflow in self._workflows.values():
        if agent_id in (workflow.required_agents or []):
            raise ValueError(
                f"Cannot delete agent '{agent_id}': "
                f"required by workflow '{workflow.workflow_id}'"
            )

def _check_tool_usage(self, tool_id: str):
    """
    Check if tool is used by any agent.

    Raises:
        ValueError: If tool is in use
    """
    using_agents = []
    for agent in self._agents.values():
        if tool_id in agent.allowed_tools:
            using_agents.append(agent.agent_id)

    if using_agents:
        raise ValueError(
            f"Cannot delete tool '{tool_id}': "
            f"used by agents: {', '.join(using_agents)}"
        )

def _check_model_usage(self, profile_id: str):
    """
    Check if model profile is used by any agent.

    Raises:
        ValueError: If model is in use
    """
    using_agents = []
    for agent in self._agents.values():
        if agent.model_profile_id == profile_id:
            using_agents.append(agent.agent_id)

    if using_agents:
        raise ValueError(
            f"Cannot delete model profile '{profile_id}': "
            f"used by agents: {', '.join(using_agents)}"
        )
```

---

### 1.4 Atomic File Writing Methods

**Add after validation methods:**

```python
def _write_agent_registry(self):
    """
    Write agent registry to disk atomically.

    Uses temp file + rename pattern for atomicity.
    Prevents corruption if process crashes during write.
    """
    import tempfile
    import os

    registry_file = self.registries_path / "agent_registry.json"

    data = {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "agents": [agent.model_dump() for agent in self._agents.values()]
    }

    # Write to temporary file first
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=registry_file.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic rename (POSIX systems)
    os.rename(tmp_path, registry_file)

def _write_tool_registry(self):
    """Write tool registry atomically."""
    import tempfile
    import os

    registry_file = self.registries_path / "tool_registry.json"

    data = {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "tools": [tool.model_dump() for tool in self._tools.values()]
    }

    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=registry_file.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    os.rename(tmp_path, registry_file)

def _write_model_registry(self):
    """Write model profiles registry atomically."""
    import tempfile
    import os

    registry_file = self.registries_path / "model_profiles.json"

    data = {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "profiles": [model.model_dump() for model in self._models.values()]
    }

    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=registry_file.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    os.rename(tmp_path, registry_file)

def _write_workflow_registry(self, workflow: WorkflowDefinition):
    """
    Write individual workflow file atomically.

    Note: Workflows are stored as individual files in workflows/ directory.
    """
    import tempfile
    import os

    workflows_dir = self.registries_path / "workflows"
    workflows_dir.mkdir(exist_ok=True)

    workflow_file = workflows_dir / f"{workflow.workflow_id}.json"

    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=workflows_dir,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(workflow.model_dump(), tmp, indent=2)
        tmp_path = tmp.name

    os.rename(tmp_path, workflow_file)

def _write_governance_policies(self):
    """Write governance policies atomically."""
    import tempfile
    import os

    governance_file = self.registries_path / "governance_policies.json"

    if not self._governance:
        return

    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=governance_file.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(self._governance.model_dump(), tmp, indent=2)
        tmp_path = tmp.name

    os.rename(tmp_path, governance_file)
```

---

### 1.5 Create API Request/Response Models

**File:** `backend/orchestrator/app/api/models.py`

**Add at the end of file:**

```python
# ============= Registry Management Models =============

from typing import List, Dict, Any, Optional

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

# ----- Generic Operation Response -----

class RegistryOperationResponse(BaseModel):
    """Generic response for registry operations."""
    success: bool
    message: str
    timestamp: str
```

---

### 1.6 Create Registries API Router

**File:** `backend/orchestrator/app/api/registries.py` (NEW FILE)

Create complete CRUD API with all endpoints. See the plan file for full implementation details. Key endpoints:

```python
"""
Registries API - Endpoints for registry management.

Demonstrates:
- Production-ready CRUD operations
- Validation and error handling
- Hot-reload capability
- Governance enforcement
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from .models import (
    AgentResponse, AgentCreateRequest, AgentListResponse,
    ToolResponse, ToolCreateRequest, ToolListResponse,
    ModelProfileResponse, ModelProfileCreateRequest, ModelProfileListResponse,
    WorkflowResponse, WorkflowCreateRequest, WorkflowListResponse,
    GovernancePoliciesResponse, GovernancePoliciesUpdateRequest,
    RegistryOperationResponse
)
from ..services.registry_manager import (
    get_registry_manager,
    AgentMetadata,
    ToolMetadata,
    ModelProfile,
    WorkflowDefinition,
    GovernancePolicies
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registries", tags=["registries"])

# ========== AGENTS ==========

@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    exclude_orchestrator: bool = Query(False, description="Exclude orchestrator from results")
):
    """List all agents with optional filtering."""
    # Implementation...

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get detailed agent configuration."""
    # Implementation...

@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(request: AgentCreateRequest):
    """Create new agent."""
    # Implementation...

@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: AgentCreateRequest):
    """Update existing agent."""
    # Implementation...

@router.delete("/agents/{agent_id}", response_model=RegistryOperationResponse)
async def delete_agent(agent_id: str):
    """Delete agent."""
    # Implementation...

# ========== ORCHESTRATOR ==========

@router.get("/orchestrator", response_model=AgentResponse)
async def get_orchestrator():
    """Get orchestrator configuration."""
    # Implementation...

@router.put("/orchestrator", response_model=AgentResponse)
async def update_orchestrator(request: AgentCreateRequest):
    """Update orchestrator configuration."""
    # Implementation...

# Similar patterns for tools, models, workflows, governance...

@router.post("/reload", response_model=RegistryOperationResponse)
async def reload_registries():
    """Manually trigger registry reload."""
    # Implementation...
```

See plan file section 1.4 for complete endpoint implementations.

---

### 1.7 Register Router in Main App

**File:** `backend/orchestrator/app/main.py`

**Changes:**

1. Add import (around line 12):
```python
from .api import runs, sessions, registries  # Add registries
```

2. Register router (around line 50):
```python
app.include_router(runs.router)
app.include_router(sessions.router)
app.include_router(registries.router)  # NEW
```

---

## Phase 2: Frontend Development

### 2.1 Extend API Client

**File:** `frontend/lib/api-client.ts`

**Add TypeScript interfaces and methods for all registry types.**

Key interfaces:
- `AgentMetadata`
- `ToolMetadata`
- `ModelProfile`
- `WorkflowDefinition`
- `GovernancePolicies`

Key methods:
- `listAgents()`, `getAgent()`, `createAgent()`, `updateAgent()`, `deleteAgent()`
- `getOrchestrator()`, `updateOrchestrator()`
- Similar methods for tools, models, workflows, governance

See plan file section 2.1 for complete implementation.

---

### 2.2 Create Navigation Component

**File:** `frontend/components/Navigation.tsx` (NEW FILE)

Responsive navigation bar with links to:
- Home
- Run Claim
- Replay
- Evidence
- Configuration (new)

Highlights active page using Next.js `usePathname()`.

---

### 2.3 Update Root Layout

**File:** `frontend/app/layout.tsx`

Add Navigation component above `{children}`:

```typescript
import Navigation from '@/components/Navigation';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Navigation />
        {children}
      </body>
    </html>
  );
}
```

---

### 2.4 Create Configuration Page

**File:** `frontend/app/config/page.tsx` (NEW FILE)

Tabbed interface with six tabs:
1. Orchestrator
2. Agents
3. Tools
4. Model Profiles
5. Workflows
6. Governance

Each tab renders its corresponding component.

---

### 2.5 Create Tab Components

Create six tab components in `frontend/components/config/`:

1. **OrchestratorTab.tsx** - Manage orchestrator, emphasize allowed_agents
2. **AgentsTab.tsx** - List agents with create/edit/delete
3. **ToolsTab.tsx** - List tools with CRUD
4. **ModelProfilesTab.tsx** - Manage LLM model profiles
5. **WorkflowsTab.tsx** - Workflow management
6. **GovernanceTab.tsx** - Edit governance policies (single document)

Each tab follows similar pattern:
- Table/list view
- Add button (except Orchestrator and Governance)
- Edit/Delete buttons per row
- Modal for create/edit
- Delete confirmation dialog

See plan file section 2.5 for AgentsTab example implementation.

---

### 2.6 Create Modal Components

Create modal components for create/edit forms:

1. **AgentModal.tsx** - Full agent form
2. **ToolModal.tsx** - Tool form
3. **ModelProfileModal.tsx** - Model profile form
4. **WorkflowModal.tsx** - Workflow form

Each modal includes:
- Form fields for all properties
- JSON editors for schemas
- Validation feedback
- Save/Cancel buttons
- Loading states

---

### 2.7 Create JSON Schema Editor Component

**File:** `frontend/components/config/JsonSchemaEditor.tsx` (NEW FILE)

Features:
- Textarea for JSON input
- Syntax validation
- Error display
- Optional formatting
- Copy/paste friendly

---

## Phase 3: Testing & Validation

### Backend Testing Checklist

**Agent Operations:**
- ✅ Create agent with valid data → Success (201)
- ✅ Create agent with duplicate ID → Fail (400)
- ✅ Create agent with non-existent model_profile_id → Fail (400)
- ✅ Create agent with non-existent tool in allowed_tools → Fail (400)
- ✅ Update agent successfully → Success (200)
- ✅ Update agent with invalid references → Fail (400)
- ✅ Delete unused agent → Success (200)
- ✅ Delete agent used by orchestrator → Fail (400)
- ✅ Delete agent required by workflow → Fail (400)
- ✅ Delete orchestrator_agent → Fail (400)

**Tool Operations:**
- ✅ Create tool with valid schemas → Success
- ✅ Create tool with invalid JSON schema → Fail (400)
- ✅ Delete tool used by agent → Fail (400)

**Model Operations:**
- ✅ Create model profile → Success
- ✅ Delete model used by agent → Fail (400)

**Workflow Operations:**
- ✅ Create workflow with valid agents → Success
- ✅ Create workflow with non-existent required agent → Fail (400)
- ✅ Delete workflow → Success

**Governance Operations:**
- ✅ Update governance policies → Success

**System Tests:**
- ✅ Verify hot reload after each operation
- ✅ Verify atomic file writes (no corruption on crash simulation)
- ✅ Test concurrent modifications (thread safety)
- ✅ Verify registry stats updated after operations

### Frontend Testing Checklist

**Navigation:**
- ✅ Navigate to /config page → Loads successfully
- ✅ Switch between tabs → All tabs render correctly
- ✅ Navigation bar highlights active page

**Agents Tab:**
- ✅ List agents loads correctly
- ✅ Create new agent via modal → Appears in list
- ✅ Edit existing agent → Pre-populated form, saves changes
- ✅ Delete agent → Confirmation dialog, removes from list
- ✅ Delete in-use agent → Shows error message
- ✅ Form validation → Required fields enforced
- ✅ JSON schema editor → Validates JSON syntax

**Orchestrator Tab:**
- ✅ Loads orchestrator config
- ✅ Shows allowed_agents list
- ✅ Update orchestrator → Saves successfully
- ✅ No delete button present

**Tools/Models/Workflows Tabs:**
- ✅ CRUD operations work correctly
- ✅ Validation errors display clearly

**Governance Tab:**
- ✅ Loads current policies
- ✅ Update policies → Saves successfully
- ✅ JSON validation works

**Error Handling:**
- ✅ API errors display user-friendly messages
- ✅ Loading states show during operations
- ✅ Success feedback after save
- ✅ Network errors handled gracefully

---

## Implementation Timeline

### Week 1: Backend Foundation
**Day 1-2**: Update Pydantic models, implement write operations in RegistryManager
**Day 3**: Add validation helpers, atomic file writing
**Day 4**: Create API models and registries router
**Day 5**: Register router, test all endpoints with curl/Postman

### Week 2: Frontend Core
**Day 1**: Extend API client with all registry methods
**Day 2**: Create Navigation component, update layout
**Day 3**: Build config page with tabbed interface
**Day 4**: Create AgentsTab and AgentModal
**Day 5**: Build JsonSchemaEditor component

### Week 3: Remaining Tabs
**Day 1**: OrchestratorTab (special UI)
**Day 2**: ToolsTab and ToolModal
**Day 3**: ModelProfilesTab and WorkflowsTab
**Day 4**: GovernanceTab
**Day 5**: Polish, refinements, bug fixes

### Week 4: Testing & Documentation
**Day 1-2**: Comprehensive backend testing (API, validation, concurrency)
**Day 3-4**: Frontend testing (UI, edge cases, error handling)
**Day 5**: Update documentation, create usage guide

---

## Critical Files

### Backend Files (7 files)
1. `backend/orchestrator/app/services/registry_manager.py` - Core logic (~500 new lines)
2. `backend/orchestrator/app/api/registries.py` - NEW - CRUD endpoints (~800 lines)
3. `backend/orchestrator/app/api/models.py` - Add registry models (~300 new lines)
4. `backend/orchestrator/app/main.py` - Register router (2 lines changed)
5. `backend/orchestrator/requirements.txt` - Add jsonschema dependency

### Frontend Files (12 files)
6. `frontend/lib/api-client.ts` - Add registry methods (~400 new lines)
7. `frontend/app/config/page.tsx` - NEW - Configuration page (~100 lines)
8. `frontend/components/Navigation.tsx` - NEW - Navigation bar (~50 lines)
9. `frontend/app/layout.tsx` - Add navigation (2 lines changed)
10. `frontend/components/config/AgentsTab.tsx` - NEW (~200 lines)
11. `frontend/components/config/OrchestratorTab.tsx` - NEW (~150 lines)
12. `frontend/components/config/ToolsTab.tsx` - NEW (~200 lines)
13. `frontend/components/config/ModelProfilesTab.tsx` - NEW (~200 lines)
14. `frontend/components/config/WorkflowsTab.tsx` - NEW (~200 lines)
15. `frontend/components/config/GovernanceTab.tsx` - NEW (~150 lines)
16. `frontend/components/config/AgentModal.tsx` - NEW (~300 lines)
17. `frontend/components/config/JsonSchemaEditor.tsx` - NEW (~100 lines)

### Registry Data Files (1 file)
18. `registries/agent_registry.json` - Add input_schema field (optional, backward compatible)

---

## Design Patterns

### Thread Safety Pattern

**All write operations use locking:**
```python
with self._lock:
    # Validate
    # Update cache
    # Write to disk
    # Reload
```

The `RLock` (reentrant lock) allows the same thread to acquire the lock multiple times, which is important since `load_all()` also acquires the lock.

### Atomic File Write Pattern

**Prevents corruption on crash:**
```python
# Write to temp file
with tempfile.NamedTemporaryFile(...) as tmp:
    json.dump(data, tmp, indent=2)
    tmp_path = tmp.name

# Atomic rename (POSIX)
os.rename(tmp_path, registry_file)
```

On POSIX systems (Linux, macOS), `os.rename()` is atomic. If the process crashes during `json.dump()`, the original file is untouched. If the crash happens during rename, either the old or new file exists (never corrupted).

### Validation Pipeline Pattern

**Fail fast, fail clearly:**
```python
def create_agent(self, agent: AgentMetadata):
    with self._lock:
        # 1. Check duplicates
        if agent.agent_id in self._agents:
            raise ValueError("Already exists")

        # 2. Validate references
        self._validate_agent_references(agent)

        # 3. Update cache
        self._agents[agent.agent_id] = agent

        # 4. Write to disk
        self._write_agent_registry()

        # 5. Hot reload
        self.load_all()
```

Order matters: validate before modifying state.

### Error Message Pattern

**Specific, contextual, actionable:**
```python
# Bad
raise ValueError("Invalid model")

# Good
raise ValueError(
    f"Model profile '{agent.model_profile_id}' not found. "
    f"Available profiles: {list(self._models.keys())}"
)
```

### Frontend State Management Pattern

**Simple, predictable:**
```typescript
const [items, setItems] = useState([]);
const [loading, setLoading] = useState(true);
const [modalOpen, setModalOpen] = useState(false);
const [editingItem, setEditingItem] = useState(null);

// Load on mount
useEffect(() => { loadItems(); }, []);

// Reload after mutations
const handleSave = async () => {
    setModalOpen(false);
    await loadItems();  // Reload from server
};
```

No optimistic updates - simple refresh after changes ensures consistency.

---

## Security Considerations

### Input Validation

**Backend validates all inputs:**
- Pydantic models enforce types and required fields
- Custom validation checks references
- JSON Schema validation ensures well-formed schemas
- Agent IDs checked against orchestrator protection

### No Cascading Deletes

**Explicit dependency management:**
- System prevents deletion of in-use resources
- User must manually remove references before deletion
- Clear error messages guide remediation

Example: "Cannot delete tool 'fraud_rules': used by agents: fraud_agent, coverage_agent"

### Thread Safety

**Prevents race conditions:**
- All operations acquire lock before modifying state
- Atomic file writes prevent partial updates
- Hot reload ensures consistency

### API Error Handling

**Never leak internal details:**
```python
try:
    registry.create_agent(agent)
except ValueError as e:
    # User-facing validation error
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Internal error - log but don't expose details
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Registry Versioning**
   - Track registry changes over time
   - Rollback to previous versions
   - Diff visualization

2. **Export/Import**
   - Export registries as ZIP
   - Import registries from file
   - Bulk operations

3. **Audit Logging**
   - Track who changed what and when
   - Change history per registry
   - Compliance reporting

4. **Advanced Validation**
   - Circular dependency detection
   - Resource usage analytics
   - Performance impact analysis

5. **Database Migration**
   - Move from JSON files to PostgreSQL
   - Better concurrency support
   - Query optimization

6. **Schema Migration Tools**
   - Automated schema version upgrades
   - Backward compatibility checks
   - Migration scripts

7. **Access Control**
   - Role-based permissions
   - Read-only vs admin users
   - Approval workflows for changes

8. **Testing Tools**
   - Registry dry-run mode
   - Validation sandbox
   - Impact analysis before changes

---

## Appendix A: API Endpoint Reference

### Agents

```
GET    /registries/agents              - List all agents
GET    /registries/agents/{id}         - Get agent details
POST   /registries/agents              - Create new agent
PUT    /registries/agents/{id}         - Update agent
DELETE /registries/agents/{id}         - Delete agent
```

### Orchestrator

```
GET    /registries/orchestrator        - Get orchestrator config
PUT    /registries/orchestrator        - Update orchestrator
```

### Tools

```
GET    /registries/tools               - List all tools
GET    /registries/tools/{id}          - Get tool details
POST   /registries/tools               - Create new tool
PUT    /registries/tools/{id}          - Update tool
DELETE /registries/tools/{id}          - Delete tool
```

### Model Profiles

```
GET    /registries/model-profiles      - List all profiles
GET    /registries/model-profiles/{id} - Get profile details
POST   /registries/model-profiles      - Create new profile
PUT    /registries/model-profiles/{id} - Update profile
DELETE /registries/model-profiles/{id} - Delete profile
```

### Workflows

```
GET    /registries/workflows           - List all workflows
GET    /registries/workflows/{id}      - Get workflow details
POST   /registries/workflows           - Create new workflow
PUT    /registries/workflows/{id}      - Update workflow
DELETE /registries/workflows/{id}      - Delete workflow
```

### Governance

```
GET    /registries/governance          - Get governance policies
PUT    /registries/governance          - Update policies
```

### Utility

```
POST   /registries/reload              - Trigger manual reload
```

---

## Appendix B: Example API Usage

### Create Agent

```bash
curl -X POST http://localhost:8016/registries/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "name": "Test Agent",
    "description": "Agent for testing",
    "capabilities": ["testing", "validation"],
    "allowed_tools": ["fraud_rules"],
    "model_profile_id": "default_gpt35",
    "max_iterations": 5,
    "iteration_timeout_seconds": 30,
    "output_schema": {
      "type": "object",
      "properties": {
        "result": {"type": "string"}
      }
    },
    "context_requirements": {}
  }'
```

### Update Orchestrator

```bash
curl -X PUT http://localhost:8016/registries/orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "orchestrator_agent",
    "name": "Orchestrator Agent",
    "allowed_agents": ["intake_agent", "fraud_agent", "coverage_agent"],
    ...
  }'
```

### Delete Agent

```bash
curl -X DELETE http://localhost:8016/registries/agents/test_agent
```

---

## Appendix C: Registry File Format Examples

### Agent Registry (agent_registry.json)

```json
{
  "version": "1.0.0",
  "last_updated": "2025-12-26T10:30:00Z",
  "agents": [
    {
      "agent_id": "fraud_agent",
      "name": "Fraud Signal Agent",
      "description": "Evaluates fraud indicators",
      "capabilities": ["fraud_detection", "risk_scoring"],
      "allowed_tools": ["fraud_rules", "similarity"],
      "model_profile_id": "default_gpt35",
      "max_iterations": 5,
      "iteration_timeout_seconds": 45,
      "input_schema": {
        "type": "object",
        "required": ["claim_data"],
        "properties": {
          "claim_data": {
            "type": "object",
            "description": "Claim information"
          }
        }
      },
      "output_schema": {
        "type": "object",
        "required": ["fraud_score"],
        "properties": {
          "fraud_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100
          }
        }
      },
      "context_requirements": {
        "requires_prior_outputs": ["intake"],
        "max_context_tokens": 6000
      }
    }
  ]
}
```

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding production-ready registry management to AgentMesh. The system will demonstrate:

- **Scalability**: Thread-safe operations, efficient lookups
- **Transparency**: Clear UI for all configuration
- **Governance**: Validation, usage tracking, safe deletions
- **Observability**: Hot reload, logging, error tracking
- **Maintainability**: Clean patterns, clear separation of concerns

The plan follows existing AgentMesh patterns and can be implemented incrementally over 3-4 weeks.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-26
**Status:** Ready for Implementation
