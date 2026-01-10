import json
import os
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional

from pydantic import ValidationError

from ..models.schemas import (
    AuthProfile,
    ConnectorMetadata,
    SecurityPolicy,
    SystemConfig,
    WorkflowDefinition,
)


class RegistryManager:
    def __init__(self, registries_path: str | None = None) -> None:
        base_path = os.getenv("REGISTRIES_PATH", "/registries")
        resolved_path = registries_path or f"{base_path}/integration"
        self.registries_path = Path(resolved_path)
        self._lock = RLock()
        self._connectors: Dict[str, ConnectorMetadata] = {}
        self._auth_profiles: Dict[str, AuthProfile] = {}
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._security_policies: Dict[str, SecurityPolicy] = {}
        self._system_config: Optional[SystemConfig] = None
        self._loaded_at: Optional[datetime] = None

    def load_all(self) -> None:
        with self._lock:
            self._load_connectors()
            self._load_auth_profiles()
            self._load_workflows()
            self._load_security_policies()
            self._load_system_config()
            self._loaded_at = datetime.utcnow()

    def _load_connectors(self) -> None:
        registry_file = self.registries_path / "connectors.json"
        with open(registry_file, "r") as f:
            data = json.load(f)
        self._connectors.clear()
        for connector_data in data.get("connectors", []):
            try:
                connector = ConnectorMetadata(**connector_data)
                self._connectors[connector.connector_id] = connector
            except ValidationError:
                continue

    def _load_auth_profiles(self) -> None:
        registry_file = self.registries_path / "auth_profiles.json"
        with open(registry_file, "r") as f:
            data = json.load(f)
        self._auth_profiles.clear()
        for profile_data in data.get("profiles", []):
            try:
                profile = AuthProfile(**profile_data)
                self._auth_profiles[profile.profile_id] = profile
            except ValidationError:
                continue

    def _load_workflows(self) -> None:
        workflows_dir = self.registries_path / "workflows"
        self._workflows.clear()
        for workflow_file in workflows_dir.glob("*.json"):
            with open(workflow_file, "r") as f:
                data = json.load(f)
            try:
                workflow = WorkflowDefinition(**data)
                self._workflows[workflow.workflow_id] = workflow
            except ValidationError:
                continue

    def _load_security_policies(self) -> None:
        registry_file = self.registries_path / "security_policies.json"
        with open(registry_file, "r") as f:
            data = json.load(f)
        self._security_policies.clear()
        for policy_data in data.get("policies", []):
            try:
                policy = SecurityPolicy(**policy_data)
                self._security_policies[policy.policy_id] = policy
            except ValidationError:
                continue

    def _load_system_config(self) -> None:
        registry_file = self.registries_path / "system_config.json"
        with open(registry_file, "r") as f:
            data = json.load(f)
        try:
            self._system_config = SystemConfig(**data)
        except ValidationError:
            self._system_config = SystemConfig(version="0.0", retry_policies=[], features={})

    def _write_json(self, path: Path, payload: Dict) -> None:
        path.write_text(json.dumps(payload, indent=2))

    def list_connectors(self) -> List[ConnectorMetadata]:
        return list(self._connectors.values())

    def get_connector(self, connector_id: str) -> Optional[ConnectorMetadata]:
        return self._connectors.get(connector_id)

    def list_auth_profiles(self) -> List[AuthProfile]:
        return list(self._auth_profiles.values())

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_security_policies(self) -> List[SecurityPolicy]:
        return list(self._security_policies.values())

    def get_security_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        return self._security_policies.get(policy_id)

    def get_system_config(self) -> SystemConfig:
        if not self._system_config:
            self._load_system_config()
        return self._system_config

    def update_system_config(self, config: SystemConfig) -> None:
        registry_file = self.registries_path / "system_config.json"
        with self._lock:
            payload = config.model_dump(exclude_none=True)
            self._write_json(registry_file, payload)
            self._system_config = config

    def update_connectors(self, connectors: List[ConnectorMetadata]) -> None:
        registry_file = self.registries_path / "connectors.json"
        with self._lock:
            payload = {"connectors": [connector.model_dump(exclude_none=True) for connector in connectors]}
            self._write_json(registry_file, payload)
            self._connectors = {connector.connector_id: connector for connector in connectors}

    def update_auth_profiles(self, profiles: List[AuthProfile]) -> None:
        registry_file = self.registries_path / "auth_profiles.json"
        with self._lock:
            payload = {"profiles": [profile.model_dump(exclude_none=True) for profile in profiles]}
            self._write_json(registry_file, payload)
            self._auth_profiles = {profile.profile_id: profile for profile in profiles}

    def update_workflow(self, workflow_id: str, workflow: WorkflowDefinition) -> None:
        workflows_dir = self.registries_path / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflows_dir / f"{workflow_id}.json"
        with self._lock:
            payload = workflow.model_dump(exclude_none=True)
            self._write_json(workflow_file, payload)
            self._workflows[workflow_id] = workflow


_registry_manager: Optional[RegistryManager] = None


def get_registry_manager() -> RegistryManager:
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = RegistryManager()
        _registry_manager.load_all()
    return _registry_manager


def reload_registry_manager() -> None:
    global _registry_manager
    if _registry_manager is not None:
        _registry_manager.load_all()
