from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    AuthProfileListResponse,
    AuthProfile,
    ConnectorListResponse,
    ConnectorMetadata,
    SecurityPolicyListResponse,
    SystemConfigResponse,
    SystemConfig,
    WorkflowListResponse,
    WorkflowDefinition,
    RegistryOperationResponse,
)
from ..services.registry_manager import get_registry_manager

router = APIRouter(prefix="/registries", tags=["registries"])


@router.get("/connectors", response_model=ConnectorListResponse)
async def list_connectors():
    registry = get_registry_manager()
    connectors = registry.list_connectors()
    return ConnectorListResponse(connectors=connectors, total_count=len(connectors))


@router.get("/auth-profiles", response_model=AuthProfileListResponse)
async def list_auth_profiles():
    registry = get_registry_manager()
    profiles = registry.list_auth_profiles()
    return AuthProfileListResponse(profiles=profiles, total_count=len(profiles))


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    registry = get_registry_manager()
    workflows = registry.list_workflows()
    return WorkflowListResponse(workflows=workflows, total_count=len(workflows))


@router.get("/security-policies", response_model=SecurityPolicyListResponse)
async def list_security_policies():
    registry = get_registry_manager()
    policies = registry.list_security_policies()
    return SecurityPolicyListResponse(policies=policies, total_count=len(policies))


@router.get("/system-config", response_model=SystemConfigResponse)
async def get_system_config():
    registry = get_registry_manager()
    config = registry.get_system_config()
    return SystemConfigResponse(config=config)

@router.put("/system-config", response_model=SystemConfigResponse)
async def update_system_config(config: SystemConfig):
    registry = get_registry_manager()
    registry.update_system_config(config)
    return SystemConfigResponse(config=config)


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return workflow


@router.put("/connectors/{connector_id}", response_model=ConnectorMetadata)
async def update_connector(connector_id: str, connector: ConnectorMetadata):
    if connector.connector_id != connector_id:
        raise HTTPException(status_code=400, detail="connector_id does not match payload")
    registry = get_registry_manager()
    connectors = registry.list_connectors()
    if connector_id not in {item.connector_id for item in connectors}:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    updated = [connector if item.connector_id == connector_id else item for item in connectors]
    registry.update_connectors(updated)
    return connector


@router.put("/auth-profiles/{profile_id}", response_model=AuthProfile)
async def update_auth_profile(profile_id: str, profile: AuthProfile):
    if profile.profile_id != profile_id:
        raise HTTPException(status_code=400, detail="profile_id does not match payload")
    registry = get_registry_manager()
    profiles = registry.list_auth_profiles()
    if profile_id not in {item.profile_id for item in profiles}:
        raise HTTPException(status_code=404, detail=f"Auth profile '{profile_id}' not found")
    updated = [profile if item.profile_id == profile_id else item for item in profiles]
    registry.update_auth_profiles(updated)
    return profile


@router.put("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(workflow_id: str, workflow: WorkflowDefinition):
    if workflow.workflow_id != workflow_id:
        raise HTTPException(status_code=400, detail="workflow_id does not match payload")
    registry = get_registry_manager()
    if not registry.get_workflow(workflow_id):
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    registry.update_workflow(workflow_id, workflow)
    return workflow


@router.post("/reload", response_model=RegistryOperationResponse)
async def reload_registries():
    registry = get_registry_manager()
    registry.load_all()
    return RegistryOperationResponse(success=True, message="Registries reloaded")
