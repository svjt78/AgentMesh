# Context Processor Developer Guide

**Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** Backend Developers, Contributors

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Processor Pipeline](#processor-pipeline)
3. [Creating a Custom Processor](#creating-a-custom-processor)
4. [Testing Processors](#testing-processors)
5. [Advanced Topics](#advanced-topics)
6. [Reference](#reference)

---

## Architecture Overview

### Context Engineering System

The context engineering system uses a **processor pipeline architecture** where context compilation happens through ordered, composable stages.

```
Raw Context → Processor 1 → Processor 2 → ... → Processor N → Final Context
```

**Key Components:**

```
backend/orchestrator/app/services/
├── context_processor_pipeline.py     # Orchestrates processor execution
├── processors/
│   ├── base_processor.py             # Abstract base class
│   ├── content_selector.py           # Filters noisy events
│   ├── compaction_checker.py         # Triggers compaction
│   ├── memory_retriever.py           # Loads memories
│   ├── artifact_resolver.py          # Resolves artifact handles
│   ├── content_filter.py             # PII masking, age filtering
│   ├── transformer.py                # Converts to LLM format
│   ├── token_budget_enforcer.py      # Enforces limits
│   └── injector.py                   # Final LLM formatting
├── compaction_manager.py             # Compaction logic
├── memory_manager.py                 # Memory storage/retrieval
├── artifact_version_store.py         # Artifact versioning
└── governance_auditor.py             # Audit logging
```

**Registries:**

```
registries/
├── context_processor_pipeline.json   # Processor order/config
├── context_strategies.json           # Feature settings
├── governance_policies.json          # Filtering rules, limits
└── system_config.json                # Master toggles
```

### Design Principles

1. **Single Responsibility**: Each processor does one thing well
2. **Composability**: Processors can be reordered or disabled
3. **Observability**: All actions logged as events
4. **Fail-Safe**: Processor failures don't crash workflows
5. **Governance-First**: All decisions auditable

---

## Processor Pipeline

### Pipeline Execution Flow

```python
# Simplified pipeline execution
class ContextProcessorPipeline:
    def execute(self, context: Dict, agent_id: str, session_id: str) -> Dict:
        # 1. Load processor configuration
        processors = self._get_enabled_processors()

        # 2. Execute processors in order
        for processor_config in processors:
            processor = self._instantiate_processor(processor_config)
            result = processor.process(context, agent_id, session_id)

            if not result.success:
                logger.warning(f"Processor {processor_config['processor_id']} failed")
                # Continue with next processor (fail-safe)

            context = result.context
            self._log_processor_executed(processor_config, result)

        return context
```

### Default Processor Order

| Order | Processor | Purpose | Can Fail? |
|-------|-----------|---------|-----------|
| 1 | ContentSelector | Filter noisy/irrelevant events | No |
| 2 | CompactionChecker | Check if compaction needed | No |
| 3 | MemoryRetriever | Load relevant memories | Yes |
| 4 | ArtifactResolver | Resolve artifact handles | Yes |
| 5 | ContentFilter | Mask PII, filter age | No |
| 6 | Transformer | Convert to LLM messages | No |
| 7 | TokenBudgetEnforcer | Truncate if over budget | No |
| 8 | Injector | Final LLM formatting | No |

**Why this order?**
- Filter/select content first (reduce work)
- Retrieve external data (memories, artifacts)
- Apply governance (filtering, masking)
- Transform to target format
- Enforce limits last (catch overflows)

---

## Creating a Custom Processor

### Step 1: Create Processor File

**Location:** `backend/orchestrator/app/services/processors/my_processor.py`

```python
"""
My Custom Processor (Phase X Implementation)

Description of what this processor does and why it exists.
"""

import time
import logging
from typing import Dict, Any

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.config import get_config
from app.services.storage import write_event

logger = logging.getLogger(__name__)


class MyProcessor(BaseProcessor):
    """
    Brief description of processor purpose.

    Features:
    - Feature 1
    - Feature 2
    """

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            # Your processor logic here
            modified_context = self._do_work(context, agent_id, session_id)

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=modified_context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made={
                    "items_processed": 10,
                    "changes_made": "description of changes",
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"MyProcessor failed: {e}", exc_info=True)

            return self._create_result(
                context=context,  # Return unmodified on failure
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _do_work(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Implementation of processor logic.

        Args:
            context: Current context dict
            agent_id: ID of agent being invoked
            session_id: Current session ID

        Returns:
            Modified context dict
        """
        # Example: Add metadata
        if "metadata" not in context:
            context["metadata"] = {}

        context["metadata"]["my_processor_ran"] = True

        return context
```

### Step 2: Understand BaseProcessor

**Base Class API:**

```python
class BaseProcessor(ABC):
    """
    Abstract base class for all context processors.
    """

    @abstractmethod
    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        """
        Process context and return result.

        Args:
            context: Current context dictionary containing:
                - original_input: User's input
                - prior_outputs: Previous agent outputs
                - observations: Agent observations
                - memories: Retrieved memories (if any)
                - artifacts: Loaded artifacts (if any)
                - metadata: Additional metadata
            agent_id: ID of agent being invoked
            session_id: Session ID for event logging

        Returns:
            ProcessorResult with:
                - context: Modified context (or original if failed)
                - success: True if processor succeeded
                - execution_time_ms: How long processing took
                - modifications_made: Dict describing changes
                - error: Error message if failed
        """
        pass

    def _create_result(
        self,
        context: Dict[str, Any],
        success: bool,
        execution_time_ms: float,
        modifications_made: Dict[str, Any] = None,
        error: str = None,
    ) -> ProcessorResult:
        """
        Helper to create ProcessorResult.

        Always use this method to ensure consistent result format.
        """
        return ProcessorResult(
            context=context,
            success=success,
            execution_time_ms=execution_time_ms,
            modifications_made=modifications_made or {},
            error=error,
        )
```

**ProcessorResult Schema:**

```python
@dataclass
class ProcessorResult:
    context: Dict[str, Any]           # Modified context
    success: bool                      # Did processor succeed?
    execution_time_ms: float           # Execution time
    modifications_made: Dict[str, Any] # What changed?
    error: Optional[str] = None        # Error message if failed
```

### Step 3: Register Processor in Pipeline

**Edit:** `registries/context_processor_pipeline.json`

```json
{
  "processors": [
    {"processor_id": "content_selector", "enabled": true, "order": 1},
    {"processor_id": "my_processor", "enabled": true, "order": 2},
    {"processor_id": "compaction_checker", "enabled": true, "order": 3},
    ...
  ]
}
```

**Configuration Options:**

- `processor_id` (required): Unique identifier (snake_case)
- `enabled` (required): true/false
- `order` (required): Execution order (lower = earlier)
- `config` (optional): Processor-specific config dict

### Step 4: Import in Pipeline

**Edit:** `backend/orchestrator/app/services/context_processor_pipeline.py`

Add import at top:

```python
from app.services.processors.my_processor import MyProcessor
```

Add to `_instantiate_processor`:

```python
def _instantiate_processor(self, processor_config: Dict) -> BaseProcessor:
    processor_id = processor_config["processor_id"]

    processors = {
        "content_selector": ContentSelector,
        "my_processor": MyProcessor,  # ADD THIS
        "compaction_checker": CompactionChecker,
        # ... rest
    }

    processor_class = processors.get(processor_id)
    if not processor_class:
        raise ValueError(f"Unknown processor: {processor_id}")

    return processor_class()
```

### Step 5: Test Your Processor

See [Testing Processors](#testing-processors) section.

---

## Real-World Example: Sentiment Analyzer Processor

Let's build a complete processor that analyzes sentiment of observations.

### Use Case

You want to filter out negative feedback observations before they reach agents, to maintain positive framing.

### Implementation

**File:** `backend/orchestrator/app/services/processors/sentiment_filter.py`

```python
"""
Sentiment Filter Processor

Filters observations based on sentiment analysis.
Removes observations with negative sentiment below threshold.
"""

import time
import logging
from typing import Dict, Any, List

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.services.governance_auditor import get_governance_auditor

logger = logging.getLogger(__name__)


class SentimentFilter(BaseProcessor):
    """
    Filters observations based on sentiment score.

    Features:
    - Analyzes sentiment of each observation
    - Removes observations below sentiment threshold
    - Logs filtering decisions for audit
    """

    def __init__(self, sentiment_threshold: float = -0.5):
        """
        Initialize sentiment filter.

        Args:
            sentiment_threshold: Minimum sentiment score (-1 to 1)
                                -1: very negative, 0: neutral, 1: very positive
        """
        self.sentiment_threshold = sentiment_threshold

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            observations = context.get("observations", [])

            if not observations:
                # No observations to filter
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    modifications_made={"status": "no_observations"},
                )

            # Filter observations
            filtered_observations = []
            filtered_count = 0

            for obs in observations:
                sentiment_score = self._analyze_sentiment(obs)

                if sentiment_score >= self.sentiment_threshold:
                    filtered_observations.append(obs)
                else:
                    filtered_count += 1
                    logger.info(
                        f"Filtered observation (sentiment={sentiment_score:.2f}): "
                        f"{obs.get('text', '')[:50]}"
                    )

            # Update context
            context["observations"] = filtered_observations

            # Log governance decision
            if filtered_count > 0:
                auditor = get_governance_auditor(session_id)
                auditor.log_filtering_decision(
                    rule_id="sentiment_filter",
                    field="observations",
                    items_filtered=filtered_count,
                    items_masked=0,
                    description=f"Filtered observations with sentiment < {self.sentiment_threshold}",
                )

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made={
                    "observations_before": len(observations),
                    "observations_after": len(filtered_observations),
                    "filtered_count": filtered_count,
                    "threshold": self.sentiment_threshold,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"SentimentFilter failed: {e}", exc_info=True)

            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _analyze_sentiment(self, observation: Dict[str, Any]) -> float:
        """
        Analyze sentiment of observation.

        This is a simplified example. In production, you might use:
        - TextBlob
        - VADER sentiment analyzer
        - LLM-based sentiment analysis
        - Custom ML model

        Args:
            observation: Observation dict with 'text' field

        Returns:
            Sentiment score from -1 (negative) to 1 (positive)
        """
        text = observation.get("text", "")

        # Simplified keyword-based sentiment (example only!)
        positive_words = ["good", "great", "excellent", "positive", "success"]
        negative_words = ["bad", "poor", "fail", "error", "problem"]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return 0.0  # Neutral

        # Normalize to -1 to 1 range
        score = (positive_count - negative_count) / total
        return score
```

### Configuration

**Add to pipeline** (`context_processor_pipeline.json`):

```json
{
  "processors": [
    {
      "processor_id": "sentiment_filter",
      "enabled": true,
      "order": 5,
      "config": {
        "sentiment_threshold": -0.3
      }
    }
  ]
}
```

**Import and instantiate** (`context_processor_pipeline.py`):

```python
from app.services.processors.sentiment_filter import SentimentFilter

def _instantiate_processor(self, processor_config: Dict) -> BaseProcessor:
    processor_id = processor_config["processor_id"]
    config = processor_config.get("config", {})

    if processor_id == "sentiment_filter":
        return SentimentFilter(
            sentiment_threshold=config.get("sentiment_threshold", -0.5)
        )
    # ... rest of processors
```

### Testing

```python
# tests/test_sentiment_filter.py
import pytest
from app.services.processors.sentiment_filter import SentimentFilter


def test_sentiment_filter_removes_negative():
    processor = SentimentFilter(sentiment_threshold=-0.3)

    context = {
        "observations": [
            {"text": "This is great and excellent!"},
            {"text": "This is bad and terrible!"},
            {"text": "Neutral observation here."},
        ]
    }

    result = processor.process(context, "test_agent", "test_session")

    assert result.success
    assert len(result.context["observations"]) == 2  # Negative filtered
    assert result.modifications_made["filtered_count"] == 1
```

---

## Testing Processors

### Unit Tests

**File:** `backend/orchestrator/tests/processors/test_my_processor.py`

```python
import pytest
from app.services.processors.my_processor import MyProcessor


class TestMyProcessor:
    def test_processor_success(self):
        """Test processor succeeds with valid input."""
        processor = MyProcessor()

        context = {
            "original_input": {"query": "test"},
            "prior_outputs": [],
            "observations": [],
        }

        result = processor.process(context, "test_agent", "test_session")

        assert result.success
        assert result.execution_time_ms > 0
        assert result.context is not None

    def test_processor_modifies_context(self):
        """Test processor actually modifies context."""
        processor = MyProcessor()

        context = {"original_input": {}}
        result = processor.process(context, "test_agent", "test_session")

        # Check your specific modifications
        assert "metadata" in result.context
        assert result.context["metadata"]["my_processor_ran"] is True

    def test_processor_handles_empty_context(self):
        """Test processor handles edge case."""
        processor = MyProcessor()

        context = {}  # Empty context
        result = processor.process(context, "test_agent", "test_session")

        assert result.success  # Should not crash

    def test_processor_error_handling(self):
        """Test processor handles errors gracefully."""
        processor = MyProcessor()

        context = {"invalid": object()}  # Intentionally invalid
        result = processor.process(context, "test_agent", "test_session")

        # Should return failure, not raise exception
        if not result.success:
            assert result.error is not None
```

### Integration Tests

**File:** `backend/orchestrator/tests/integration/test_processor_pipeline.py`

```python
import pytest
from app.services.context_processor_pipeline import ContextProcessorPipeline


def test_pipeline_with_my_processor():
    """Test processor works in full pipeline."""
    pipeline = ContextProcessorPipeline(session_id="test_session")

    raw_context = {
        "original_input": {"query": "test claim"},
        "prior_outputs": [],
        "observations": [{"text": "observation 1"}],
    }

    # Execute full pipeline
    compiled_context = pipeline.execute(raw_context, "test_agent")

    # Verify your processor's effects
    assert "metadata" in compiled_context
    assert compiled_context["metadata"]["my_processor_ran"] is True
```

### Running Tests

```bash
cd backend/orchestrator

# Run specific test
pytest tests/processors/test_my_processor.py -v

# Run all processor tests
pytest tests/processors/ -v

# Run with coverage
pytest tests/processors/ --cov=app.services.processors --cov-report=html
```

---

## Advanced Topics

### Processor Configuration from Registry

If your processor needs user-configurable settings:

**1. Add to context_strategies.json:**

```json
{
  "my_processor_settings": {
    "enabled": true,
    "threshold": 0.5,
    "max_items": 10
  }
}
```

**2. Load in processor:**

```python
from app.config import get_config

class MyProcessor(BaseProcessor):
    def __init__(self):
        config = get_config()
        self.settings = config.context_strategies.get("my_processor_settings", {})
        self.threshold = self.settings.get("threshold", 0.5)
        self.max_items = self.settings.get("max_items", 10)
```

### Accessing Other Services

Processors can interact with other services:

```python
from app.services.memory_manager import get_memory_manager
from app.services.governance_auditor import get_governance_auditor
from app.services.llm_client import get_llm_client
from app.services.storage import write_event

class MyProcessor(BaseProcessor):
    def process(self, context, agent_id, session_id):
        # Access memory layer
        memory_manager = get_memory_manager()
        memories = memory_manager.retrieve_memories(query="test")

        # Log governance decision
        auditor = get_governance_auditor(session_id)
        auditor.log_context_decision(
            decision_type="filtering",
            component="observations",
            action="filtered",
            rationale="Custom filtering logic",
        )

        # Make LLM call (use sparingly!)
        llm_client = get_llm_client()
        response = llm_client.complete(...)

        # Write custom event
        write_event(session_id, {
            "event_type": "my_processor_action",
            "data": {"key": "value"},
        })
```

### Conditional Processing

Skip processing based on conditions:

```python
class MyProcessor(BaseProcessor):
    def process(self, context, agent_id, session_id):
        # Only process for specific agents
        if agent_id not in ["fraud_agent", "coverage_agent"]:
            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=0,
                modifications_made={"status": "skipped_agent_not_eligible"},
            )

        # Only process if feature enabled
        config = get_config()
        if not config.my_processor_settings.get("enabled", False):
            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=0,
                modifications_made={"status": "skipped_feature_disabled"},
            )

        # Proceed with processing
        ...
```

### Performance Optimization

**Caching:**

```python
from functools import lru_cache

class MyProcessor(BaseProcessor):
    @lru_cache(maxsize=128)
    def _expensive_lookup(self, key: str) -> Any:
        """Cache expensive operations."""
        # Heavy computation here
        return result
```

**Batch Processing:**

```python
def process(self, context, agent_id, session_id):
    observations = context.get("observations", [])

    # Process in batches for efficiency
    batch_size = 50
    for i in range(0, len(observations), batch_size):
        batch = observations[i:i + batch_size]
        self._process_batch(batch)
```

**Async Operations (Advanced):**

```python
import asyncio

class MyProcessor(BaseProcessor):
    def process(self, context, agent_id, session_id):
        # Run async operations
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._async_process(context))
        return result

    async def _async_process(self, context):
        # Concurrent API calls, I/O operations
        tasks = [self._fetch_data(item) for item in context["items"]]
        results = await asyncio.gather(*tasks)
        return results
```

---

## Reference

### Context Dictionary Structure

```python
{
    # User's original input
    "original_input": {
        "claim_id": "CLM-12345",
        "description": "Flooded basement",
        # ... user-provided fields
    },

    # Previous agent outputs
    "prior_outputs": [
        {
            "agent_id": "intake",
            "output": {"validation_status": "approved", ...},
            "timestamp": "2026-01-01T10:00:00Z"
        }
    ],

    # Agent observations (tool calls, intermediate results)
    "observations": [
        {
            "observation_type": "tool_result",
            "tool_name": "policy_snapshot",
            "result": {...},
            "timestamp": "2026-01-01T10:05:00Z"
        }
    ],

    # Retrieved memories (if memory layer enabled)
    "memories": [
        {
            "memory_id": "mem_001",
            "content": "Similar claim pattern observed",
            "similarity_score": 0.85,
            "created_at": "2025-12-15T00:00:00Z"
        }
    ],

    # Loaded artifacts (if artifact versioning enabled)
    "artifacts": [
        {
            "artifact_id": "evidence_map",
            "version": 2,
            "handle": "artifact://evidence_map/v2",
            "content": {...}
        }
    ],

    # Metadata added by processors
    "metadata": {
        "filtering_applied": true,
        "compaction_triggered": false,
        "token_count": 5000,
        # ... processor-specific metadata
    }
}
```

### Processor Best Practices

1. **Idempotency**: Running processor twice should produce same result
2. **No Side Effects**: Don't modify external state (except logging)
3. **Fail Safe**: Return original context if processing fails
4. **Performance**: Aim for <100ms execution time
5. **Logging**: Log important decisions at INFO level
6. **Errors**: Log errors at ERROR level with full traceback
7. **Governance**: Use GovernanceAuditor for all filtering/limiting decisions
8. **Testing**: Achieve >80% code coverage

### Common Patterns

**Pattern: Filter List Field**

```python
def process(self, context, agent_id, session_id):
    items = context.get("observations", [])
    filtered = [item for item in items if self._should_keep(item)]
    context["observations"] = filtered
    return self._create_result(...)
```

**Pattern: Enrich with External Data**

```python
def process(self, context, agent_id, session_id):
    observations = context.get("observations", [])

    for obs in observations:
        enriched_data = self._fetch_enrichment(obs)
        obs["enrichment"] = enriched_data

    return self._create_result(...)
```

**Pattern: Aggregate and Summarize**

```python
def process(self, context, agent_id, session_id):
    observations = context.get("observations", [])

    summary = {
        "total_count": len(observations),
        "by_type": {},
        "key_insights": []
    }

    for obs in observations:
        obs_type = obs.get("type")
        summary["by_type"][obs_type] = summary["by_type"].get(obs_type, 0) + 1

    context["observation_summary"] = summary
    return self._create_result(...)
```

### Debugging Tips

**Enable Debug Logging:**

```bash
# .env
LOG_LEVEL=DEBUG
```

**Add Debug Prints:**

```python
logger.debug(f"Processing context keys: {context.keys()}")
logger.debug(f"Observation count: {len(context.get('observations', []))}")
```

**Inspect Pipeline Execution:**

```bash
# View processor execution events
cat storage/sessions/{session_id}.jsonl | jq 'select(.event_type == "processor_executed")'
```

**Test Processor in Isolation:**

```python
# Python REPL
from app.services.processors.my_processor import MyProcessor

processor = MyProcessor()
context = {...}  # Your test context
result = processor.process(context, "test_agent", "test_session")
print(result)
```

---

## Example: Complete Custom Processor Workflow

Let's walk through creating a processor from scratch to finish.

### Requirement

"I want to automatically redact email addresses from all observations before they reach agents."

### Step 1: Create Processor

**File:** `backend/orchestrator/app/services/processors/email_redactor.py`

```python
"""
Email Redactor Processor

Automatically redacts email addresses from observations.
"""

import re
import time
import logging
from typing import Dict, Any

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.services.governance_auditor import get_governance_auditor

logger = logging.getLogger(__name__)


class EmailRedactor(BaseProcessor):
    """Redacts email addresses from observations."""

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def process(self, context: Dict[str, Any], agent_id: str, session_id: str) -> ProcessorResult:
        start_time = time.time()

        try:
            observations = context.get("observations", [])
            redacted_count = 0

            for obs in observations:
                if "text" in obs:
                    original = obs["text"]
                    redacted = re.sub(self.EMAIL_PATTERN, "[EMAIL_REDACTED]", original)

                    if original != redacted:
                        obs["text"] = redacted
                        redacted_count += 1

            # Log governance decision
            if redacted_count > 0:
                auditor = get_governance_auditor(session_id)
                auditor.log_filtering_decision(
                    rule_id="email_redaction",
                    field="observations",
                    items_filtered=0,
                    items_masked=redacted_count,
                    description="Redacted email addresses from observation text",
                )

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made={"emails_redacted": redacted_count},
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"EmailRedactor failed: {e}", exc_info=True)

            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
```

### Step 2: Write Tests

**File:** `backend/orchestrator/tests/processors/test_email_redactor.py`

```python
import pytest
from app.services.processors.email_redactor import EmailRedactor


def test_email_redactor_redacts_email():
    processor = EmailRedactor()

    context = {
        "observations": [
            {"text": "Contact me at john.doe@example.com for details"},
            {"text": "No email here"},
        ]
    }

    result = processor.process(context, "test_agent", "test_session")

    assert result.success
    assert "john.doe@example.com" not in result.context["observations"][0]["text"]
    assert "[EMAIL_REDACTED]" in result.context["observations"][0]["text"]
    assert result.modifications_made["emails_redacted"] == 1


def test_email_redactor_handles_multiple_emails():
    processor = EmailRedactor()

    context = {
        "observations": [
            {"text": "Email alice@test.com or bob@test.org"},
        ]
    }

    result = processor.process(context, "test_agent", "test_session")

    assert "alice@test.com" not in result.context["observations"][0]["text"]
    assert "bob@test.org" not in result.context["observations"][0]["text"]
    assert result.context["observations"][0]["text"].count("[EMAIL_REDACTED]") == 2
```

### Step 3: Register in Pipeline

**Edit:** `registries/context_processor_pipeline.json`

```json
{
  "processors": [
    {"processor_id": "content_selector", "enabled": true, "order": 1},
    {"processor_id": "email_redactor", "enabled": true, "order": 5},
    {"processor_id": "transformer", "enabled": true, "order": 6},
    ...
  ]
}
```

### Step 4: Import in Pipeline

**Edit:** `backend/orchestrator/app/services/context_processor_pipeline.py`

```python
from app.services.processors.email_redactor import EmailRedactor

# In _instantiate_processor method
def _instantiate_processor(self, processor_config: Dict) -> BaseProcessor:
    processors = {
        "content_selector": ContentSelector,
        "email_redactor": EmailRedactor,  # ADD THIS
        # ... rest
    }
    # ...
```

### Step 5: Test Integration

```bash
# Run tests
pytest tests/processors/test_email_redactor.py -v

# Start services
docker compose up

# Submit test claim with email
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "TEST-001",
    "description": "Contact adjuster@insurance.com"
  }'

# Check logs
docker compose logs -f orchestrator | grep "EmailRedactor"

# View session JSONL
cat storage/sessions/{session_id}.jsonl | jq 'select(.event_type == "processor_executed" and .processor_id == "email_redactor")'
```

### Done!

Your processor is now:
- ✅ Implemented
- ✅ Tested
- ✅ Registered
- ✅ Running in production

---

## Getting Help

**Documentation:**
- User Guide: `USER_GUIDE_CONTEXT_ENGINEERING.md`
- API Reference: `API_CONTEXT_ENGINEERING.md`
- Testing Guide: `TESTING_CONTEXT_ENGINEERING.md`

**Code Examples:**
- `app/services/processors/content_filter.py` - Complex filtering logic
- `app/services/processors/memory_retriever.py` - External service integration
- `app/services/processors/token_budget_enforcer.py` - Budget enforcement pattern

**Support:**
- GitHub Issues: Create issue with "processor" label
- Internal Docs: Confluence/Wiki for architecture decisions

---

**End of Developer Guide**
*Last updated: January 2026*
