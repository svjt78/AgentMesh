"""
Registry Manager - Production-grade dynamic discovery system.

Demonstrates scalability patterns:
- Dynamic discovery (not hardcoded dependencies)
- Hot-reload capability (update without restart)
- Caching for performance
- Validation for safety
- Versioning support
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
from pydantic import BaseModel, ValidationError


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
    input_schema: Optional[Dict[str, Any]] = None  # NEW: Optional for backward compatibility
    output_schema: Dict[str, Any]
    context_requirements: Dict[str, Any]


class ToolMetadata(BaseModel):
    """Tool registry entry."""
    tool_id: str
    name: str
    description: str
    endpoint: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    lineage_tags: List[str]


class ModelProfile(BaseModel):
    """Model profile configuration."""
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


class WorkflowDefinition(BaseModel):
    """Workflow definition (advisory mode)."""
    workflow_id: str
    name: str
    description: str
    version: str
    mode: str  # "advisory" or "strict"
    goal: Optional[str] = None
    steps: List[Dict[str, Any]]
    suggested_sequence: Optional[List[str]] = []
    required_agents: Optional[List[str]] = []
    optional_agents: Optional[List[str]] = []
    completion_criteria: Optional[Dict[str, Any]] = {}
    constraints: Optional[Dict[str, Any]] = {}
    metadata: Dict[str, Any]
    hitl_checkpoints: Optional[List[Dict[str, Any]]] = []  # HITL checkpoint configurations


class GovernancePolicies(BaseModel):
    """Governance policies."""
    version: str
    policies: Dict[str, Any]


class RegistryManager:
    """
    Production-grade registry manager.

    Demonstrates scalability patterns:
    - Lazy loading with caching
    - Thread-safe operations
    - Hot-reload support
    - Validation on load
    - Lookup optimization (O(1) by ID)
    """

    def __init__(self, registries_path: str = "/registries"):
        self.registries_path = Path(registries_path)
        self._lock = threading.RLock()

        # Caches (indexed by ID for O(1) lookup)
        self._agents: Dict[str, AgentMetadata] = {}
        self._tools: Dict[str, ToolMetadata] = {}
        self._models: Dict[str, ModelProfile] = {}
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._governance: Optional[GovernancePolicies] = None

        # Metadata
        self._loaded_at: Optional[datetime] = None
        self._load_count = 0

    def load_all(self) -> None:
        """
        Load all registries from disk.

        Thread-safe, can be called multiple times for hot-reload.
        Validates all entries on load.
        """
        with self._lock:
            self._load_agents()
            self._load_tools()
            self._load_models()
            self._load_workflows()
            self._load_governance()

            self._loaded_at = datetime.utcnow()
            self._load_count += 1

            print(f"[RegistryManager] Loaded all registries (count: {self._load_count})")
            print(f"  - Agents: {len(self._agents)}")
            print(f"  - Tools: {len(self._tools)}")
            print(f"  - Models: {len(self._models)}")
            print(f"  - Workflows: {len(self._workflows)}")

    def _load_agents(self) -> None:
        """Load agent registry with validation."""
        registry_file = self.registries_path / "agent_registry.json"

        with open(registry_file, "r") as f:
            data = json.load(f)

        self._agents.clear()
        for agent_data in data["agents"]:
            try:
                agent = AgentMetadata(**agent_data)
                self._agents[agent.agent_id] = agent
            except ValidationError as e:
                print(f"[RegistryManager] WARNING: Invalid agent entry: {agent_data.get('agent_id')}")
                print(f"  Error: {e}")
                # In production: log error, skip entry, continue

    def _load_tools(self) -> None:
        """Load tool registry with validation."""
        registry_file = self.registries_path / "tool_registry.json"

        with open(registry_file, "r") as f:
            data = json.load(f)

        self._tools.clear()
        for tool_data in data["tools"]:
            try:
                tool = ToolMetadata(**tool_data)
                self._tools[tool.tool_id] = tool
            except ValidationError as e:
                print(f"[RegistryManager] WARNING: Invalid tool entry: {tool_data.get('tool_id')}")

    def _load_models(self) -> None:
        """Load model profiles."""
        registry_file = self.registries_path / "model_profiles.json"

        with open(registry_file, "r") as f:
            data = json.load(f)

        self._models.clear()
        for model_data in data["profiles"]:
            try:
                model = ModelProfile(**model_data)
                self._models[model.profile_id] = model
            except ValidationError as e:
                print(f"[RegistryManager] WARNING: Invalid model profile: {model_data.get('profile_id')}")

    def _load_workflows(self) -> None:
        """Load workflow definitions."""
        workflows_dir = self.registries_path / "workflows"

        self._workflows.clear()
        for workflow_file in workflows_dir.glob("*.json"):
            with open(workflow_file, "r") as f:
                data = json.load(f)

            try:
                workflow = WorkflowDefinition(**data)
                self._workflows[workflow.workflow_id] = workflow
            except ValidationError as e:
                print(f"[RegistryManager] WARNING: Invalid workflow: {workflow_file.name}")

    def _load_governance(self) -> None:
        """Load governance policies."""
        governance_file = self.registries_path / "governance_policies.json"

        with open(governance_file, "r") as f:
            data = json.load(f)

        try:
            self._governance = GovernancePolicies(**data)
        except ValidationError as e:
            print(f"[RegistryManager] WARNING: Invalid governance policies")
            self._governance = None

    # ============= Agent Queries =============

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID (O(1) lookup)."""
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self, capability: Optional[str] = None) -> List[AgentMetadata]:
        """
        List all agents, optionally filtered by capability.

        Demonstrates: Dynamic discovery for agent selection.
        """
        with self._lock:
            agents = list(self._agents.values())

            if capability:
                agents = [a for a in agents if capability in a.capabilities]

            return agents

    def get_agents_for_orchestrator(self) -> List[AgentMetadata]:
        """
        Get all agents that orchestrator can invoke.

        Demonstrates: Governance-aware discovery.
        """
        orchestrator = self.get_agent("orchestrator_agent")
        if not orchestrator or not orchestrator.allowed_agents:
            return []

        with self._lock:
            return [
                self._agents[agent_id]
                for agent_id in orchestrator.allowed_agents
                if agent_id in self._agents
            ]

    # ============= Tool Queries =============

    def get_tool(self, tool_id: str) -> Optional[ToolMetadata]:
        """Get tool metadata by ID (O(1) lookup)."""
        with self._lock:
            return self._tools.get(tool_id)

    def get_tools_for_agent(self, agent_id: str) -> List[ToolMetadata]:
        """
        Get all tools an agent is allowed to use.

        Demonstrates: Governance-aware tool discovery.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        with self._lock:
            return [
                self._tools[tool_id]
                for tool_id in agent.allowed_tools
                if tool_id in self._tools
            ]

    def list_tools(self, tag: Optional[str] = None) -> List[ToolMetadata]:
        """List all tools, optionally filtered by lineage tag."""
        with self._lock:
            tools = list(self._tools.values())

            if tag:
                tools = [t for t in tools if tag in t.lineage_tags]

            return tools

    # ============= Model Queries =============

    def get_model_profile(self, profile_id: str) -> Optional[ModelProfile]:
        """Get model profile by ID."""
        with self._lock:
            return self._models.get(profile_id)

    # ============= Workflow Queries =============

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID."""
        with self._lock:
            return self._workflows.get(workflow_id)

    # ============= Governance Queries =============

    def get_governance_policies(self) -> Optional[GovernancePolicies]:
        """Get governance policies."""
        with self._lock:
            return self._governance

    def is_agent_invocation_allowed(self, invoker_agent_id: str, target_agent_id: str) -> bool:
        """
        Check if invoker agent can invoke target agent.

        Demonstrates: Runtime governance enforcement.
        """
        if not self._governance:
            return True  # Permissive if no policies loaded

        policy = self._governance.policies.get("agent_invocation_access", {})
        rules = policy.get("rules", [])

        for rule in rules:
            if rule.get("agent_id") == invoker_agent_id:
                allowed = rule.get("allowed_agents", [])
                denied = rule.get("denied_agents", [])

                if target_agent_id in denied:
                    return False
                if target_agent_id in allowed:
                    return True

        return False  # Deny by default if not explicitly allowed

    def is_tool_access_allowed(self, agent_id: str, tool_id: str) -> bool:
        """
        Check if agent can use tool.

        Demonstrates: Runtime governance enforcement.
        """
        if not self._governance:
            return True

        policy = self._governance.policies.get("agent_tool_access", {})
        rules = policy.get("rules", [])

        for rule in rules:
            if rule.get("agent_id") == agent_id:
                allowed = rule.get("allowed_tools", [])
                denied = rule.get("denied_tools", [])

                if tool_id in denied:
                    return False
                if tool_id in allowed:
                    return True

        return False

    # ============= Agent CRUD Operations =============

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

            if agent.agent_id != agent_id:
                raise ValueError(f"Agent ID mismatch: '{agent_id}' != '{agent.agent_id}'")

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

    # ============= Tool CRUD Operations =============

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

            print(f"[RegistryManager] Created tool: {tool.tool_id}")

    def update_tool(self, tool_id: str, tool: ToolMetadata) -> None:
        """Update existing tool."""
        with self._lock:
            if tool_id not in self._tools:
                raise ValueError(f"Tool '{tool_id}' not found")

            if tool.tool_id != tool_id:
                raise ValueError(f"Tool ID mismatch: '{tool_id}' != '{tool.tool_id}'")

            self._validate_json_schema(tool.input_schema)
            self._validate_json_schema(tool.output_schema)

            self._tools[tool_id] = tool
            self._write_tool_registry()
            self.load_all()

            print(f"[RegistryManager] Updated tool: {tool_id}")

    def delete_tool(self, tool_id: str) -> None:
        """Delete tool after usage checks."""
        with self._lock:
            if tool_id not in self._tools:
                raise ValueError(f"Tool '{tool_id}' not found")

            self._check_tool_usage(tool_id)

            del self._tools[tool_id]
            self._write_tool_registry()
            self.load_all()

            print(f"[RegistryManager] Deleted tool: {tool_id}")

    # ============= Model Profile CRUD Operations =============

    def create_model_profile(self, profile: ModelProfile) -> None:
        """Create new model profile."""
        with self._lock:
            if profile.profile_id in self._models:
                raise ValueError(f"Model profile '{profile.profile_id}' already exists")

            self._models[profile.profile_id] = profile
            self._write_model_registry()
            self.load_all()

            print(f"[RegistryManager] Created model profile: {profile.profile_id}")

    def update_model_profile(self, profile_id: str, profile: ModelProfile) -> None:
        """Update existing model profile."""
        with self._lock:
            if profile_id not in self._models:
                raise ValueError(f"Model profile '{profile_id}' not found")

            if profile.profile_id != profile_id:
                raise ValueError(f"Profile ID mismatch: '{profile_id}' != '{profile.profile_id}'")

            self._models[profile_id] = profile
            self._write_model_registry()
            self.load_all()

            print(f"[RegistryManager] Updated model profile: {profile_id}")

    def delete_model_profile(self, profile_id: str) -> None:
        """Delete model profile after usage checks."""
        with self._lock:
            if profile_id not in self._models:
                raise ValueError(f"Model profile '{profile_id}' not found")

            self._check_model_usage(profile_id)

            del self._models[profile_id]
            self._write_model_registry()
            self.load_all()

            print(f"[RegistryManager] Deleted model profile: {profile_id}")

    # ============= Workflow CRUD Operations =============

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

            print(f"[RegistryManager] Created workflow: {workflow.workflow_id}")

    def update_workflow(self, workflow_id: str, workflow: WorkflowDefinition) -> None:
        """Update existing workflow."""
        with self._lock:
            if workflow_id not in self._workflows:
                raise ValueError(f"Workflow '{workflow_id}' not found")

            if workflow.workflow_id != workflow_id:
                raise ValueError(f"Workflow ID mismatch: '{workflow_id}' != '{workflow.workflow_id}'")

            for agent_id in workflow.required_agents or []:
                if agent_id not in self._agents:
                    raise ValueError(f"Required agent '{agent_id}' not found")

            self._workflows[workflow_id] = workflow
            self._write_workflow_registry(workflow)
            self.load_all()

            print(f"[RegistryManager] Updated workflow: {workflow_id}")

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

            print(f"[RegistryManager] Deleted workflow: {workflow_id}")

    # ============= Governance Update Operations =============

    def update_governance_policies(self, policies: GovernancePolicies) -> None:
        """Update governance policies (no create/delete - single document)."""
        with self._lock:
            self._governance = policies
            self._write_governance_policies()
            self.load_all()

            print("[RegistryManager] Updated governance policies")

    def get_system_config(self) -> Dict[str, Any]:
        """Get current system configuration."""
        config_file = self.registries_path / "system_config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"System config not found at {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def update_system_config(self, config: Dict[str, Any]) -> None:
        """Update system configuration."""
        with self._lock:
            self._write_system_config(config)
            print("[RegistryManager] Updated system configuration")

    def list_model_profiles(self) -> List[ModelProfile]:
        """List all model profiles."""
        with self._lock:
            return list(self._models.values())

    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all workflows."""
        with self._lock:
            return list(self._workflows.values())

    # ============= Validation Helper Methods =============

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
        for tool_id in agent.allowed_tools or []:
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
            if tool_id in (agent.allowed_tools or []):
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

    # ============= Atomic File Writing Methods =============

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

    def _write_system_config(self, config: Dict[str, Any]):
        """Write system configuration atomically."""
        import tempfile
        import os
        from datetime import datetime

        config_file = self.registries_path / "system_config.json"

        # Update last_updated timestamp
        config["last_updated"] = datetime.utcnow().isoformat() + "Z"

        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=config_file.parent,
            delete=False,
            suffix='.json'
        ) as tmp:
            json.dump(config, tmp, indent=2)
            tmp_path = tmp.name

        os.rename(tmp_path, config_file)

    # ============= Metadata =============

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics (for observability)."""
        with self._lock:
            return {
                "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
                "load_count": self._load_count,
                "counts": {
                    "agents": len(self._agents),
                    "tools": len(self._tools),
                    "models": len(self._models),
                    "workflows": len(self._workflows)
                }
            }


# Singleton instance
_registry_manager: Optional[RegistryManager] = None


def init_registry_manager(registries_path: str = "/registries"):
    """Initialize registry manager singleton."""
    global _registry_manager
    _registry_manager = RegistryManager(registries_path)
    _registry_manager.load_all()


def get_registry_manager() -> RegistryManager:
    """Get singleton RegistryManager instance."""
    if _registry_manager is None:
        raise RuntimeError("RegistryManager not initialized. Call init_registry_manager() first.")
    return _registry_manager


def reload_registries():
    """Hot-reload all registries without restart."""
    manager = get_registry_manager()
    manager.load_all()
    return manager.get_stats()
