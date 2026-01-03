"""
Data models for multi-agent context handoffs.

Supports:
- Handoff modes (full, scoped, minimal)
- Governance rules for agent-pair handoffs
- Conversation translation configuration
- Handoff event tracking
"""

from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# ============= Enums =============

class HandoffMode(str, Enum):
    """Mode for context sharing during agent handoffs."""
    FULL = "full"        # Complete context passed
    SCOPED = "scoped"    # Only specified fields passed
    MINIMAL = "minimal"  # Only essential trigger information


class TranslationStrategy(str, Enum):
    """Strategy for translating agent outputs."""
    EXTRACT_FIELDS = "extract_fields"    # Pull specific fields
    SUMMARIZE = "summarize"              # Condense output
    RECAST_ROLE = "recast_role"          # Change message role
    FILTER = "filter"                    # Remove blocked fields


# ============= Configuration Models =============

class ConversationTranslationConfig(BaseModel):
    """Configuration for conversation translation."""
    enabled: bool = False
    strategies: List[TranslationStrategy] = []

    # Summarization settings
    summarize: bool = False
    max_summary_tokens: Optional[int] = 500

    # Field extraction settings
    extract_fields: Optional[List[str]] = None

    # Role recasting settings
    recast_role: Optional[str] = None  # "system", "user", "assistant"

    # Filtering settings
    filter_enabled: bool = True


class HandoffRule(BaseModel):
    """Governance rule for agent-to-agent handoffs."""
    from_agent_id: str = Field(
        ...,
        description="Source agent ID (* for wildcard)"
    )
    to_agent_id: str = Field(
        ...,
        description="Destination agent ID (* for wildcard)"
    )
    handoff_mode: HandoffMode = Field(
        default=HandoffMode.SCOPED,
        description="Context sharing mode"
    )

    # Field-level controls
    allowed_context_fields: Optional[List[str]] = Field(
        default=None,
        description="Whitelist of allowed fields (scoped mode)"
    )
    blocked_context_fields: Optional[List[str]] = Field(
        default=None,
        description="Blacklist of blocked fields"
    )

    # Translation configuration
    conversation_translation: Optional[ConversationTranslationConfig] = None

    # Audit settings
    audit_enabled: bool = True
    rule_id: Optional[str] = None
    description: Optional[str] = None

    def matches(self, from_agent: str, to_agent: str) -> bool:
        """Check if this rule applies to the agent pair."""
        from_match = self.from_agent_id == "*" or self.from_agent_id == from_agent
        to_match = self.to_agent_id == "*" or self.to_agent_id == to_agent
        return from_match and to_match

    def get_specificity_score(self) -> int:
        """Calculate rule specificity for precedence (higher = more specific)."""
        score = 0
        if self.from_agent_id != "*":
            score += 10
        if self.to_agent_id != "*":
            score += 10
        return score


class HandoffPolicyConfig(BaseModel):
    """Overall handoff policy configuration."""
    default_handoff_mode: HandoffMode = HandoffMode.SCOPED
    enable_conversation_translation: bool = True
    audit_all_handoffs: bool = True
    agent_handoff_rules: List[HandoffRule] = []

    def get_rule_for_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str
    ) -> Optional[HandoffRule]:
        """Get the most specific rule for an agent pair."""
        matching_rules = [
            rule for rule in self.agent_handoff_rules
            if rule.matches(from_agent_id, to_agent_id)
        ]

        if not matching_rules:
            return None

        # Sort by specificity (most specific first)
        matching_rules.sort(key=lambda r: r.get_specificity_score(), reverse=True)
        return matching_rules[0]


# ============= Context Models =============

class ContextSummary(BaseModel):
    """Summary of context before/after scoping."""
    prior_outputs_count: int = 0
    observations_count: int = 0
    total_tokens: int = 0
    fields_included: Optional[List[str]] = None
    fields_excluded: Optional[List[str]] = None
    agents_included: Optional[List[str]] = None


class ScopedContext(BaseModel):
    """Context after scoping has been applied."""
    prior_outputs: Dict[str, Any] = {}
    observations: List[Dict[str, Any]] = []
    original_input: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

    # Scoping metadata
    handoff_mode: HandoffMode
    fields_filtered: List[str] = []
    translation_applied: bool = False


# ============= Event Models =============

class ContextHandoffEvent(BaseModel):
    """Event logged when context is handed off between agents."""
    event_type: Literal["context_handoff"] = "context_handoff"
    session_id: str
    from_agent_id: str
    to_agent_id: str
    timestamp: str

    # Handoff configuration
    handoff_mode: HandoffMode
    governance_rule_id: Optional[str] = None

    # Context metrics
    context_before_scoping: ContextSummary
    context_after_scoping: ContextSummary

    # Token savings
    tokens_saved: int = 0
    tokens_saved_percentage: float = 0.0

    # Translation details
    conversation_translation_applied: bool = False
    translation_strategies: List[str] = []

    # Audit trail
    audit_note: Optional[str] = None


# ============= Helper Functions =============

def create_context_summary(
    prior_outputs: Dict[str, Any],
    observations: List[Dict[str, Any]],
    token_count: int
) -> ContextSummary:
    """Create a context summary from context components."""
    return ContextSummary(
        prior_outputs_count=len(prior_outputs),
        observations_count=len(observations),
        total_tokens=token_count,
        agents_included=list(prior_outputs.keys())
    )


def calculate_token_savings(
    before: ContextSummary,
    after: ContextSummary
) -> tuple[int, float]:
    """Calculate token savings from scoping."""
    tokens_saved = before.total_tokens - after.total_tokens
    if before.total_tokens > 0:
        percentage = (tokens_saved / before.total_tokens) * 100
    else:
        percentage = 0.0

    return tokens_saved, percentage
