from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from ..models.schemas import RunStepResult, WorkflowDefinition
from .connector_executor import ConnectorExecutor
from .idempotency_store import get_idempotency_store
from .dlq_store import get_dlq_store
from .registry_manager import get_registry_manager
from .run_store import get_run_store
from .security_engine import SecurityEngine
from .sse_broadcaster import get_broadcaster


class WorkflowRunner:
    def __init__(self) -> None:
        self.registry = get_registry_manager()
        self.idempotency_store = get_idempotency_store()
        self.dlq_store = get_dlq_store()
        self.run_store = get_run_store()
        self.broadcaster = get_broadcaster()
        self.connector_executor = ConnectorExecutor()
        self.security_engine = SecurityEngine()

    async def run(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
        run_id: str,
        run_payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        run_payload = run_payload or self.run_store.create_run(run_id, workflow.workflow_id, input_data)
        await self.broadcaster.broadcast_event(
            session_id=run_id,
            event_type="run_started",
            event_data={
                "workflow_id": workflow.workflow_id,
                "run_id": run_id,
                "started_at": run_payload["created_at"],
            },
        )

        step_results: List[RunStepResult] = []
        errors: List[str] = []
        warnings: List[str] = []

        for step in workflow.steps:
            step_start = time.time()
            attempts = 0
            step_error = None
            idempotency_key = None
            step_output: Dict[str, Any] = {}

            while True:
                attempts += 1
                try:
                    if step.idempotency:
                        idempotency_key = self._make_idempotency_key(run_id, step.id, input_data)
                        cached = self.idempotency_store.get(idempotency_key)
                        if cached:
                            step_output = {"idempotent": True, "cached_result": cached}
                            await self._record_event(run_id, step.id, "idempotent_skip", step_output)
                            break

                    if step.type == "rest_call":
                        connector = self.registry.get_connector(step.connector or "")
                        if not connector:
                            raise ValueError(f"Connector '{step.connector}' not found")
                        auth_profile = None
                        if connector.auth_profile:
                            auth_profile = next(
                                (p for p in self.registry.list_auth_profiles() if p.profile_id == connector.auth_profile),
                                None,
                            )
                        step_output = self.connector_executor.execute(
                            connector=connector,
                            auth_profile=auth_profile,
                            operation=step.operation or "",
                            payload=input_data,
                        )
                    elif step.type == "security_transform":
                        policy = self.registry.get_security_policy(step.policy or "")
                        if not policy:
                            raise ValueError(f"Security policy '{step.policy}' not found")
                        step_output = self.security_engine.apply_policy(policy, input_data)
                    elif step.type == "audit_event":
                        step_output = {
                            "event": "audit",
                            "details": {
                                "workflow_id": workflow.workflow_id,
                                "run_id": run_id,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                            },
                        }
                    elif step.type == "failure_simulation":
                        raise RuntimeError("Simulated integration failure")
                    else:
                        step_output = {
                            "note": "No-op step",
                            "type": step.type,
                        }

                    if idempotency_key:
                        self.idempotency_store.set(idempotency_key, step_output)

                    await self._record_event(run_id, step.id, "step_completed", step_output)
                    break
                except Exception as exc:
                    step_error = str(exc)
                    await self._record_event(run_id, step.id, "step_error", {"error": step_error})
                    retry_policy = self._get_retry_policy(step.retry_policy)
                    if retry_policy and attempts < retry_policy["max_attempts"]:
                        await asyncio.sleep(retry_policy["backoff_seconds"])
                        continue
                    failure_policy = step.failure_policy or "dead_letter"
                    if failure_policy == "skip":
                        warnings.append(f"Step {step.id} skipped after error: {step_error}")
                        break
                    if failure_policy == "pause_for_human":
                        errors.append(f"Step {step.id} paused for human: {step_error}")
                        break
                    dlq_item = self.dlq_store.add_item({
                        "item_id": f"dlq_{uuid.uuid4().hex[:8]}",
                        "run_id": run_id,
                        "step_id": step.id,
                        "workflow_id": workflow.workflow_id,
                        "error": step_error,
                        "payload": input_data,
                    })
                    errors.append(f"Step {step.id} sent to DLQ: {dlq_item['item_id']}")
                    break

            duration_ms = int((time.time() - step_start) * 1000)
            step_result = RunStepResult(
                step_id=step.id,
                status="error" if step_error else "success",
                attempts=attempts,
                idempotency_key=idempotency_key,
                connector=step.connector,
                operation=step.operation,
                error=step_error,
                duration_ms=duration_ms,
                output=step_output,
            )
            step_results.append(step_result)
            self.run_store.append_step(run_id, step_result.model_dump())

            if step_error and (step.failure_policy or "dead_letter") in {"pause_for_human", "dead_letter"}:
                break

        status = "completed" if not errors else "error"
        completed_at = datetime.utcnow().isoformat() + "Z"
        self.run_store.update_run(
            run_id,
            {
                "status": status,
                "completed_at": completed_at,
                "warnings": warnings,
                "errors": errors,
            },
        )
        await self.broadcaster.broadcast_event(
            session_id=run_id,
            event_type="run_completed",
            event_data={
                "status": status,
                "completed_at": completed_at,
                "warnings": warnings,
                "errors": errors,
            },
        )
        await self.broadcaster.complete_session(run_id)
        return self.run_store.get_run(run_id)

    async def _record_event(self, run_id: str, step_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "step_id": step_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.run_store.append_event(run_id, event)
        await self.broadcaster.broadcast_event(
            session_id=run_id,
            event_type=event_type,
            event_data=event,
        )

    def _make_idempotency_key(self, run_id: str, step_id: str, input_data: Dict[str, Any]) -> str:
        business_key = input_data.get("claim_id") or input_data.get("policy_id") or "default"
        return f"{run_id}:{step_id}:{business_key}"

    def _get_retry_policy(self, policy_id: str | None) -> Dict[str, Any] | None:
        system_config = self.registry.get_system_config()
        for policy in system_config.retry_policies:
            if policy.policy_id == (policy_id or ""):
                return {
                    "max_attempts": policy.max_attempts,
                    "backoff_seconds": policy.backoff_seconds,
                }
        return None
