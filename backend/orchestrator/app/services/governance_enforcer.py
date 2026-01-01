"""
Governance Enforcer - Production-grade policy enforcement.

Demonstrates scalability patterns:
- Policy-driven (not hardcoded rules)
- Audit trail generation
- Multiple enforcement layers
- Extensible for new policy types
- Performance tracking
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel

from .registry_manager import get_registry_manager


class ViolationType(str, Enum):
    """Types of policy violations."""
    AGENT_INVOCATION_DENIED = "agent_invocation_denied"
    TOOL_ACCESS_DENIED = "tool_access_denied"
    ITERATION_LIMIT_EXCEEDED = "iteration_limit_exceeded"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"
    MAX_INVOCATIONS_EXCEEDED = "max_invocations_exceeded"


class PolicyViolation(BaseModel):
    """Represents a policy violation."""
    violation_type: ViolationType
    agent_id: str
    target: str  # agent_id or tool_id
    reason: str
    timestamp: str
    session_id: Optional[str] = None


class EnforcementResult(BaseModel):
    """Result of policy enforcement check."""
    allowed: bool
    violation: Optional[PolicyViolation] = None
    warning: Optional[str] = None


class GovernanceEnforcer:
    """
    Production-grade governance enforcer.

    Demonstrates scalability patterns:
    - Stateless enforcement (scales horizontally)
    - Policy-driven decisions
    - Audit trail for compliance
    - Performance metrics
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.registry = get_registry_manager()

        # Session-level tracking (for limits enforcement)
        self._agent_invocation_counts: Dict[str, int] = {}
        self._tool_invocation_count = 0
        self._llm_call_count = 0
        self._policy_violations: List[PolicyViolation] = []

    # ============= Agent Invocation Governance =============

    def check_agent_invocation(
        self,
        invoker_agent_id: str,
        target_agent_id: str
    ) -> EnforcementResult:
        """
        Check if agent invocation is allowed.

        Demonstrates: Runtime governance with audit trail.

        Args:
            invoker_agent_id: Agent requesting the invocation
            target_agent_id: Agent to be invoked

        Returns:
            EnforcementResult with allowed flag and violation details
        """
        # Check 1: Registry-based access control
        if not self.registry.is_agent_invocation_allowed(invoker_agent_id, target_agent_id):
            violation = PolicyViolation(
                violation_type=ViolationType.AGENT_INVOCATION_DENIED,
                agent_id=invoker_agent_id,
                target=target_agent_id,
                reason=f"Agent '{invoker_agent_id}' not permitted to invoke '{target_agent_id}' per governance policy",
                timestamp=datetime.utcnow().isoformat() + "Z",
                session_id=self.session_id
            )
            self._policy_violations.append(violation)

            return EnforcementResult(
                allowed=False,
                violation=violation
            )

        # Check 2: Duplicate invocation detection
        current_count = self._agent_invocation_counts.get(target_agent_id, 0)
        max_duplicates = 2  # Configurable from env or governance

        if current_count >= max_duplicates:
            violation = PolicyViolation(
                violation_type=ViolationType.MAX_INVOCATIONS_EXCEEDED,
                agent_id=invoker_agent_id,
                target=target_agent_id,
                reason=f"Agent '{target_agent_id}' already invoked {current_count} times (max: {max_duplicates})",
                timestamp=datetime.utcnow().isoformat() + "Z",
                session_id=self.session_id
            )
            self._policy_violations.append(violation)

            return EnforcementResult(
                allowed=False,
                violation=violation
            )

        # Passed - increment counter
        self._agent_invocation_counts[target_agent_id] = current_count + 1

        # Warning if approaching limit
        warning = None
        if current_count + 1 == max_duplicates:
            warning = f"Agent '{target_agent_id}' invoked {current_count + 1} times (limit: {max_duplicates}). Further invocations will be blocked."

        return EnforcementResult(
            allowed=True,
            warning=warning
        )

    # ============= Tool Access Governance =============

    def check_tool_access(
        self,
        agent_id: str,
        tool_id: str
    ) -> EnforcementResult:
        """
        Check if agent can use tool.

        Demonstrates: Policy-driven tool access control.
        """
        # Check 1: Registry-based access control
        if not self.registry.is_tool_access_allowed(agent_id, tool_id):
            violation = PolicyViolation(
                violation_type=ViolationType.TOOL_ACCESS_DENIED,
                agent_id=agent_id,
                target=tool_id,
                reason=f"Agent '{agent_id}' not permitted to use tool '{tool_id}' per governance policy",
                timestamp=datetime.utcnow().isoformat() + "Z",
                session_id=self.session_id
            )
            self._policy_violations.append(violation)

            return EnforcementResult(
                allowed=False,
                violation=violation
            )

        # Check 2: Session-level tool invocation limit
        governance = self.registry.get_governance_policies()
        if governance:
            max_invocations = governance.policies.get("execution_constraints", {}).get(
                "max_tool_invocations_per_session", 50
            )

            if self._tool_invocation_count >= max_invocations:
                violation = PolicyViolation(
                    violation_type=ViolationType.MAX_INVOCATIONS_EXCEEDED,
                    agent_id=agent_id,
                    target=tool_id,
                    reason=f"Session tool invocation limit reached ({max_invocations})",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    session_id=self.session_id
                )
                self._policy_violations.append(violation)

                return EnforcementResult(
                    allowed=False,
                    violation=violation
                )

        # Passed - increment counter
        self._tool_invocation_count += 1

        return EnforcementResult(allowed=True)

    # ============= Iteration Limits =============

    def check_iteration_limit(
        self,
        agent_id: str,
        current_iteration: int
    ) -> EnforcementResult:
        """
        Check if agent has exceeded iteration limit.

        Demonstrates: Resource governance at scale.
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return EnforcementResult(allowed=True)  # Unknown agent, allow

        max_iterations = agent.max_iterations

        if current_iteration >= max_iterations:
            violation = PolicyViolation(
                violation_type=ViolationType.ITERATION_LIMIT_EXCEEDED,
                agent_id=agent_id,
                target=agent_id,
                reason=f"Agent '{agent_id}' reached max iterations ({max_iterations})",
                timestamp=datetime.utcnow().isoformat() + "Z",
                session_id=self.session_id
            )
            self._policy_violations.append(violation)

            return EnforcementResult(
                allowed=False,
                violation=violation
            )

        return EnforcementResult(allowed=True)

    # ============= LLM Usage Governance =============

    def record_llm_call(self, tokens_used: int) -> EnforcementResult:
        """
        Record LLM call and check against session limits.

        Demonstrates: Cost governance.
        """
        self._llm_call_count += 1

        governance = self.registry.get_governance_policies()
        if governance:
            max_calls = governance.policies.get("execution_constraints", {}).get(
                "max_llm_calls_per_session", 30
            )

            if self._llm_call_count > max_calls:
                violation = PolicyViolation(
                    violation_type=ViolationType.MAX_INVOCATIONS_EXCEEDED,
                    agent_id="system",
                    target="llm",
                    reason=f"Session LLM call limit exceeded ({max_calls})",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    session_id=self.session_id
                )
                self._policy_violations.append(violation)

                return EnforcementResult(
                    allowed=False,
                    violation=violation
                )

        return EnforcementResult(allowed=True)

    # ============= HITL Checkpoint Governance =============

    def check_hitl_access(self, user_role: str, required_role: str) -> bool:
        """
        Check if user role has permission to resolve checkpoint.

        Validates role authorization for Human-in-the-Loop checkpoints.

        Args:
            user_role: Role of requesting user
            required_role: Role required by checkpoint

        Returns:
            True if authorized, False otherwise
        """
        # Admin override
        if user_role == "admin":
            return True

        # Exact match
        if user_role == required_role:
            return True

        # Check role hierarchy from governance policies
        try:
            policies = self.registry.get_governance_policies()
            hitl_policies = policies.get("policies", {}).get("hitl_access_control", {})
            roles = hitl_policies.get("roles", [])

            # Find user's role definition
            user_role_def = next((r for r in roles if r["role_id"] == user_role), None)
            if not user_role_def:
                return False

            # Check if user can act as required role (future enhancement)
            can_act_as = user_role_def.get("can_act_as", [])
            if required_role in can_act_as:
                return True

        except Exception as e:
            # If governance policies not found or error, fall back to exact match only
            pass

        return False

    # ============= Audit & Reporting =============

    def get_violations(self) -> List[PolicyViolation]:
        """
        Get all policy violations for this session.

        Demonstrates: Audit trail for compliance.
        """
        return self._policy_violations.copy()

    def get_enforcement_stats(self) -> Dict[str, Any]:
        """
        Get enforcement statistics for observability.

        Demonstrates: Metrics for monitoring governance effectiveness.
        """
        return {
            "session_id": self.session_id,
            "total_violations": len(self._policy_violations),
            "violations_by_type": self._count_violations_by_type(),
            "agent_invocation_counts": self._agent_invocation_counts.copy(),
            "tool_invocation_count": self._tool_invocation_count,
            "llm_call_count": self._llm_call_count
        }

    def _count_violations_by_type(self) -> Dict[str, int]:
        """Count violations by type."""
        counts: Dict[str, int] = {}
        for violation in self._policy_violations:
            violation_type = violation.violation_type.value
            counts[violation_type] = counts.get(violation_type, 0) + 1
        return counts

    def has_violations(self) -> bool:
        """Check if any violations occurred."""
        return len(self._policy_violations) > 0

    def clear_violations(self) -> None:
        """Clear violation history (for testing or reset)."""
        self._policy_violations.clear()


def create_governance_enforcer(session_id: str) -> GovernanceEnforcer:
    """Factory function to create enforcer for a session."""
    return GovernanceEnforcer(session_id=session_id)
