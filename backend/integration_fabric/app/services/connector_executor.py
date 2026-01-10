from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from ..models.schemas import AuthProfile, ConnectorMetadata


class ConnectorExecutor:
    def __init__(self) -> None:
        pass

    def execute(
        self,
        connector: ConnectorMetadata,
        auth_profile: Optional[AuthProfile],
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        start = time.time()
        simulator_payload = {
            "connector_id": connector.connector_id,
            "operation": operation,
            "request": {
                "base_url": self._resolve_base_url(connector.base_url),
                "payload": payload,
            },
            "auth_profile": auth_profile.profile_id if auth_profile else None,
            "simulated": True,
        }

        response = self._simulate_response(connector, operation, payload)
        duration_ms = int((time.time() - start) * 1000)
        return {
            "status": "success",
            "duration_ms": duration_ms,
            "request": simulator_payload["request"],
            "response": response,
            "auth_profile": simulator_payload["auth_profile"],
            "simulated": True,
        }

    def _resolve_base_url(self, base_url: str) -> str:
        if base_url.startswith("${") and base_url.endswith("}"):
            env_key = base_url[2:-1]
            return os.getenv(env_key, "")
        return base_url

    def _simulate_response(
        self,
        connector: ConnectorMetadata,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "message": "Simulated response",
            "connector": connector.name,
            "operation": operation,
            "payload_echo": payload,
            "correlation_id": f"sim-{connector.connector_id}-{int(time.time())}",
        }
