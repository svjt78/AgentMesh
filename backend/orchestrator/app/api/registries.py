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
    SystemConfigResponse, SystemConfigUpdateRequest,
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
    try:
        registry = get_registry_manager()
        agents = registry.list_agents(capability=capability)

        if exclude_orchestrator:
            agents = [a for a in agents if a.agent_id != "orchestrator_agent"]

        return AgentListResponse(
            agents=[AgentResponse(**agent.model_dump()) for agent in agents],
            total_count=len(agents),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get detailed agent configuration."""
    try:
        registry = get_registry_manager()
        agent = registry.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        return AgentResponse(**agent.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(request: AgentCreateRequest):
    """Create new agent."""
    try:
        registry = get_registry_manager()

        # Convert request to AgentMetadata
        agent = AgentMetadata(**request.model_dump())

        # Create (will raise ValueError if validation fails)
        registry.create_agent(agent)

        return AgentResponse(**agent.model_dump())
    except ValueError as e:
        # Validation errors - user-facing
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: AgentCreateRequest):
    """Update existing agent."""
    try:
        registry = get_registry_manager()

        # Convert request to AgentMetadata
        agent = AgentMetadata(**request.model_dump())

        # Update (will raise ValueError if validation fails)
        registry.update_agent(agent_id, agent)

        return AgentResponse(**agent.model_dump())
    except ValueError as e:
        # Validation errors - user-facing
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/agents/{agent_id}", response_model=RegistryOperationResponse)
async def delete_agent(agent_id: str):
    """Delete agent."""
    try:
        registry = get_registry_manager()
        registry.delete_agent(agent_id)

        return RegistryOperationResponse(
            success=True,
            message=f"Agent '{agent_id}' deleted successfully",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except ValueError as e:
        # Validation errors (in use, not found, etc.)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== ORCHESTRATOR ==========

@router.get("/orchestrator", response_model=AgentResponse)
async def get_orchestrator():
    """Get orchestrator configuration."""
    try:
        registry = get_registry_manager()
        orchestrator = registry.get_agent("orchestrator_agent")

        if not orchestrator:
            raise HTTPException(status_code=404, detail="Orchestrator not found")

        return AgentResponse(**orchestrator.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orchestrator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orchestrator", response_model=AgentResponse)
async def update_orchestrator(request: AgentCreateRequest):
    """Update orchestrator configuration."""
    try:
        # Ensure agent_id is orchestrator_agent
        if request.agent_id != "orchestrator_agent":
            raise HTTPException(
                status_code=400,
                detail="Orchestrator agent_id must be 'orchestrator_agent'"
            )

        registry = get_registry_manager()

        # Convert request to AgentMetadata
        agent = AgentMetadata(**request.model_dump())

        # Update
        registry.update_agent("orchestrator_agent", agent)

        return AgentResponse(**agent.model_dump())
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating orchestrator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== TOOLS ==========

@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    tag: Optional[str] = Query(None, description="Filter by lineage tag")
):
    """List all tools with optional filtering."""
    try:
        registry = get_registry_manager()
        tools = registry.list_tools(tag=tag)

        return ToolListResponse(
            tools=[ToolResponse(**tool.model_dump()) for tool in tools],
            total_count=len(tools),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str):
    """Get detailed tool configuration."""
    try:
        registry = get_registry_manager()
        tool = registry.get_tool(tool_id)

        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        return ToolResponse(**tool.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools", response_model=ToolResponse, status_code=201)
async def create_tool(request: ToolCreateRequest):
    """Create new tool."""
    try:
        registry = get_registry_manager()

        # Convert request to ToolMetadata
        tool = ToolMetadata(**request.model_dump())

        # Create
        registry.create_tool(tool)

        return ToolResponse(**tool.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tool: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, request: ToolCreateRequest):
    """Update existing tool."""
    try:
        registry = get_registry_manager()

        # Convert request to ToolMetadata
        tool = ToolMetadata(**request.model_dump())

        # Update
        registry.update_tool(tool_id, tool)

        return ToolResponse(**tool.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tools/{tool_id}", response_model=RegistryOperationResponse)
async def delete_tool(tool_id: str):
    """Delete tool."""
    try:
        registry = get_registry_manager()
        registry.delete_tool(tool_id)

        return RegistryOperationResponse(
            success=True,
            message=f"Tool '{tool_id}' deleted successfully",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== MODEL PROFILES ==========

@router.get("/model-profiles", response_model=ModelProfileListResponse)
async def list_model_profiles():
    """List all model profiles."""
    try:
        registry = get_registry_manager()
        profiles = registry.list_model_profiles()

        return ModelProfileListResponse(
            profiles=[ModelProfileResponse(**profile.model_dump()) for profile in profiles],
            total_count=len(profiles),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error listing model profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-profiles/{profile_id}", response_model=ModelProfileResponse)
async def get_model_profile(profile_id: str):
    """Get detailed model profile configuration."""
    try:
        registry = get_registry_manager()
        profile = registry.get_model_profile(profile_id)

        if not profile:
            raise HTTPException(status_code=404, detail=f"Model profile '{profile_id}' not found")

        return ModelProfileResponse(**profile.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model-profiles", response_model=ModelProfileResponse, status_code=201)
async def create_model_profile(request: ModelProfileCreateRequest):
    """Create new model profile."""
    try:
        registry = get_registry_manager()

        # Convert request to ModelProfile
        profile = ModelProfile(**request.model_dump())

        # Create
        registry.create_model_profile(profile)

        return ModelProfileResponse(**profile.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating model profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/model-profiles/{profile_id}", response_model=ModelProfileResponse)
async def update_model_profile(profile_id: str, request: ModelProfileCreateRequest):
    """Update existing model profile."""
    try:
        registry = get_registry_manager()

        # Convert request to ModelProfile
        profile = ModelProfile(**request.model_dump())

        # Update
        registry.update_model_profile(profile_id, profile)

        return ModelProfileResponse(**profile.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating model profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/model-profiles/{profile_id}", response_model=RegistryOperationResponse)
async def delete_model_profile(profile_id: str):
    """Delete model profile."""
    try:
        registry = get_registry_manager()
        registry.delete_model_profile(profile_id)

        return RegistryOperationResponse(
            success=True,
            message=f"Model profile '{profile_id}' deleted successfully",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting model profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== WORKFLOWS ==========

@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    """List all workflows."""
    try:
        registry = get_registry_manager()
        workflows = registry.list_workflows()

        return WorkflowListResponse(
            workflows=[WorkflowResponse(**workflow.model_dump()) for workflow in workflows],
            total_count=len(workflows),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get detailed workflow configuration."""
    try:
        registry = get_registry_manager()
        workflow = registry.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

        return WorkflowResponse(**workflow.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(request: WorkflowCreateRequest):
    """Create new workflow."""
    try:
        registry = get_registry_manager()

        # Convert request to WorkflowDefinition
        workflow = WorkflowDefinition(**request.model_dump())

        # Create
        registry.create_workflow(workflow)

        return WorkflowResponse(**workflow.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, request: WorkflowCreateRequest):
    """Update existing workflow."""
    try:
        registry = get_registry_manager()

        # Convert request to WorkflowDefinition
        workflow = WorkflowDefinition(**request.model_dump())

        # Update
        registry.update_workflow(workflow_id, workflow)

        return WorkflowResponse(**workflow.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/workflows/{workflow_id}", response_model=RegistryOperationResponse)
async def delete_workflow(workflow_id: str):
    """Delete workflow."""
    try:
        registry = get_registry_manager()
        registry.delete_workflow(workflow_id)

        return RegistryOperationResponse(
            success=True,
            message=f"Workflow '{workflow_id}' deleted successfully",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== GOVERNANCE ==========

@router.get("/governance", response_model=GovernancePoliciesResponse)
async def get_governance_policies():
    """Get governance policies."""
    try:
        registry = get_registry_manager()
        policies = registry.get_governance_policies()

        if not policies:
            raise HTTPException(status_code=404, detail="Governance policies not found")

        return GovernancePoliciesResponse(**policies.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting governance policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/governance", response_model=GovernancePoliciesResponse)
async def update_governance_policies(request: GovernancePoliciesUpdateRequest):
    """Update governance policies."""
    try:
        registry = get_registry_manager()

        # Convert request to GovernancePolicies
        policies = GovernancePolicies(**request.model_dump())

        # Update
        registry.update_governance_policies(policies)

        return GovernancePoliciesResponse(**policies.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating governance policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== SYSTEM CONFIGURATION ==========

@router.get("/system-config", response_model=SystemConfigResponse)
async def get_system_config():
    """Get current system configuration."""
    try:
        registry = get_registry_manager()
        config = registry.get_system_config()

        return SystemConfigResponse(**config)
    except Exception as e:
        logger.error(f"Error getting system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/system-config", response_model=SystemConfigResponse)
async def update_system_config(request: SystemConfigUpdateRequest):
    """Update system configuration."""
    try:
        registry = get_registry_manager()

        # Update configuration
        config_dict = request.model_dump()
        registry.update_system_config(config_dict)
        from ..config import reload_config
        reload_config()

        return SystemConfigResponse(**config_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== CONTEXT STRATEGIES ==========

@router.get("/context/strategies")
async def get_context_strategies():
    """Get context engineering strategies configuration."""
    try:
        import json
        from pathlib import Path

        strategies_candidates = [
            Path("/registries/context_strategies.json"),
            Path("registries/context_strategies.json"),
            Path("../../../registries/context_strategies.json"),
        ]
        strategies_path = next((path for path in strategies_candidates if path.exists()), None)

        if strategies_path is None:
            raise HTTPException(status_code=404, detail="Context strategies configuration not found")

        with open(strategies_path, "r") as f:
            strategies = json.load(f)

        return strategies
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/context/strategies")
async def update_context_strategies(strategies: dict):
    """Update context engineering strategies configuration."""
    try:
        import json
        from pathlib import Path

        strategies_candidates = [
            Path("/registries/context_strategies.json"),
            Path("registries/context_strategies.json"),
            Path("../../../registries/context_strategies.json"),
        ]
        strategies_path = next((path for path in strategies_candidates if path.exists()), None)
        if strategies_path is None:
            strategies_path = strategies_candidates[0]
            strategies_path.parent.mkdir(parents=True, exist_ok=True)

        # Validate basic structure
        if "version" not in strategies:
            strategies["version"] = "1.0.0"

        # Write to file
        with open(strategies_path, "w") as f:
            json.dump(strategies, f, indent=2)

        logger.info("Context strategies configuration updated successfully")

        return strategies
    except Exception as e:
        logger.error(f"Error updating context strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== UTILITY ==========

@router.post("/reload", response_model=RegistryOperationResponse)
async def reload_registries():
    """Manually trigger registry reload."""
    try:
        registry = get_registry_manager()
        registry.load_all()
        stats = registry.get_stats()

        return RegistryOperationResponse(
            success=True,
            message=f"Registries reloaded successfully. Loaded {stats['counts']} items.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error reloading registries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
