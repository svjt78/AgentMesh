from typing import Any, Dict

from ..models.schemas import SecurityPolicy


class SecurityEngine:
    def apply_policy(self, policy: SecurityPolicy, payload: Dict[str, Any]) -> Dict[str, Any]:
        applied = []
        for rule in policy.rules:
            applied.append({"field": rule.field, "action": rule.action})
        return {
            "policy_id": policy.policy_id,
            "applied_rules": applied,
            "note": "Simulated masking - payload not modified",
        }
