# Context Engineering Testing Guide

**Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** QA Engineers, Developers

---

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [End-to-End Tests](#end-to-end-tests)
5. [Performance Tests](#performance-tests)
6. [Regression Tests](#regression-tests)
7. [CI/CD Integration](#cicd-integration)

---

## Testing Strategy

### Test Pyramid

```
       /\
      /E2E\        10% - End-to-End Tests
     /------\
    /  Integ \     30% - Integration Tests
   /----------\
  /   Unit     \   60% - Unit Tests
 /--------------\
```

**Coverage Targets:**
- **Unit Tests:** 80% code coverage
- **Integration Tests:** All major workflows
- **E2E Tests:** Critical user journeys
- **Performance:** Baseline benchmarks

### Test Environments

| Environment | Purpose | Data | Configuration |
|-------------|---------|------|---------------|
| **Local** | Development | Mock data | All features enabled |
| **CI** | Automated testing | Fixtures | Minimal config |
| **Staging** | Pre-production | Sanitized prod data | Production-like |
| **Production** | Monitoring | Real data | Production config |

---

## Unit Tests

### Processor Tests

**Location:** `backend/orchestrator/tests/processors/`

#### Template: Test Processor

```python
# tests/processors/test_my_processor.py
import pytest
from app.services.processors.my_processor import MyProcessor


class TestMyProcessor:
    """Unit tests for MyProcessor"""

    def test_process_success(self):
        """Test processor succeeds with valid input"""
        processor = MyProcessor()
        context = {
            "original_input": {"query": "test"},
            "prior_outputs": [],
            "observations": [],
        }

        result = processor.process(context, "test_agent", "test_session")

        assert result.success
        assert result.execution_time_ms > 0
        assert result.error is None

    def test_process_modifies_context(self):
        """Test processor modifies context as expected"""
        processor = MyProcessor()
        context = {"observations": [{"text": "test"}]}

        result = processor.process(context, "test_agent", "test_session")

        # Verify your specific modifications
        assert "metadata" in result.context
        assert len(result.modifications_made) > 0

    def test_process_empty_context(self):
        """Test processor handles empty context gracefully"""
        processor = MyProcessor()
        context = {}

        result = processor.process(context, "test_agent", "test_session")

        assert result.success  # Should not crash

    def test_process_error_handling(self):
        """Test processor handles errors without crashing"""
        processor = MyProcessor()
        # Intentionally invalid input
        context = {"observations": "invalid_type"}

        result = processor.process(context, "test_agent", "test_session")

        # Should return failure, not raise exception
        if not result.success:
            assert result.error is not None
            assert isinstance(result.error, str)
```

#### Example: Content Filter Tests

```python
# tests/processors/test_content_filter.py
import pytest
from datetime import datetime, timedelta
from app.services.processors.content_filter import ContentFilterProcessor


class TestContentFilterProcessor:
    def test_age_filtering(self):
        """Test age-based filtering removes old observations"""
        processor = ContentFilterProcessor()

        # Create observations with different ages
        old_date = (datetime.utcnow() - timedelta(days=40)).isoformat() + "Z"
        recent_date = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"

        context = {
            "observations": [
                {"text": "Old observation", "timestamp": old_date},
                {"text": "Recent observation", "timestamp": recent_date},
            ]
        }

        # Mock filtering rule: max age 30 days
        # (In real test, load from governance_policies.json)

        result = processor.process(context, "test_agent", "test_session")

        assert result.success
        assert len(result.context["observations"]) == 1
        assert result.context["observations"][0]["text"] == "Recent observation"

    def test_pii_masking(self):
        """Test PII masking redacts sensitive information"""
        processor = ContentFilterProcessor()

        context = {
            "original_input": {
                "description": "SSN is 123-45-6789 and card is 4111-1111-1111-1111"
            }
        }

        result = processor.process(context, "test_agent", "test_session")

        assert result.success
        description = result.context["original_input"]["description"]
        assert "123-45-6789" not in description
        assert "4111-1111-1111-1111" not in description
        assert "***-**-****" in description
        assert "****-****-****-****" in description
```

#### Running Unit Tests

```bash
cd backend/orchestrator

# Run all processor tests
pytest tests/processors/ -v

# Run specific test file
pytest tests/processors/test_content_filter.py -v

# Run with coverage
pytest tests/processors/ --cov=app.services.processors --cov-report=html

# Run tests matching pattern
pytest tests/ -k "test_age_filtering" -v
```

---

## Integration Tests

### Pipeline Integration Tests

**Location:** `backend/orchestrator/tests/integration/`

#### Template: Test Processor Pipeline

```python
# tests/integration/test_context_processor_pipeline.py
import pytest
from app.services.context_processor_pipeline import ContextProcessorPipeline


class TestContextProcessorPipeline:
    """Integration tests for full processor pipeline"""

    def test_pipeline_executes_all_processors(self):
        """Test pipeline executes processors in order"""
        pipeline = ContextProcessorPipeline(session_id="test_session")

        raw_context = {
            "original_input": {"claim_id": "TEST-001"},
            "prior_outputs": [],
            "observations": [{"text": "obs1"}, {"text": "obs2"}],
        }

        compiled_context = pipeline.execute(raw_context, "test_agent")

        # Verify pipeline executed
        assert compiled_context is not None
        assert "metadata" in compiled_context

    def test_pipeline_with_compaction(self):
        """Test pipeline triggers compaction when threshold exceeded"""
        # This test requires mock session with >100 events
        # (Implementation depends on your mocking strategy)
        pass

    def test_pipeline_with_memory_retrieval(self):
        """Test pipeline retrieves memories in proactive mode"""
        # Setup: Create test memories
        # Enable proactive mode in config
        # Execute pipeline
        # Verify memories added to context
        pass
```

### Service Integration Tests

```python
# tests/integration/test_memory_service.py
import pytest
from app.services.memory_manager import MemoryManager
from app.models.memory import Memory


class TestMemoryServiceIntegration:
    @pytest.fixture
    def memory_manager(self, tmp_path):
        """Create MemoryManager with temp storage"""
        manager = MemoryManager()
        manager.storage_path = tmp_path
        return manager

    def test_create_and_retrieve_memory(self, memory_manager):
        """Test full lifecycle: create, retrieve, delete"""
        # Create memory
        memory_id = memory_manager.store_memory(
            memory_type="test",
            content="Test memory content",
            tags=["test"],
        )

        assert memory_id is not None

        # Retrieve by ID
        memory = memory_manager.get_memory(memory_id)
        assert memory is not None
        assert memory.content == "Test memory content"

        # Search by query
        results = memory_manager.retrieve_memories(
            query="test memory", mode="reactive"
        )
        assert len(results) > 0

        # Delete
        success = memory_manager.delete_memory(memory_id)
        assert success

        # Verify deleted
        memory = memory_manager.get_memory(memory_id)
        assert memory is None

    def test_similarity_search(self, memory_manager):
        """Test similarity-based retrieval"""
        # Create test memories
        memory_manager.store_memory(
            memory_type="fraud",
            content="High fraud risk for merchant ABC",
            tags=["fraud", "high_risk"],
        )
        memory_manager.store_memory(
            memory_type="fraud",
            content="Low fraud risk for merchant XYZ",
            tags=["fraud", "low_risk"],
        )

        # Search by similarity
        results = memory_manager.retrieve_memories_by_similarity(
            query_text="fraud risk merchant ABC",
            limit=5,
            threshold=0.3,
            use_embeddings=False,
        )

        assert len(results) > 0
        # First result should be high similarity
        assert results[0][1] > 0.5  # similarity score
```

---

## End-to-End Tests

### E2E Test Scenarios

#### Scenario 1: Compaction Workflow

```python
# tests/e2e/test_compaction_e2e.py
import pytest
import requests
import time

BASE_URL = "http://localhost:8016"


class TestCompactionE2E:
    """End-to-end tests for context compaction"""

    def test_automatic_compaction_trigger(self):
        """Test compaction triggers automatically when threshold exceeded"""

        # 1. Enable compaction via API
        config = {
            "compaction": {
                "enabled": True,
                "token_threshold": 5000,
                "event_count_threshold": 50,
                "compaction_method": "rule_based",
            }
        }
        response = requests.put(
            f"{BASE_URL}/api/context/strategies", json=config
        )
        assert response.status_code == 200

        # 2. Submit workflow that generates >50 events
        claim = {
            "claim_id": "TEST-E2E-001",
            "description": "Test claim for compaction",
        }
        run_response = requests.post(f"{BASE_URL}/runs", json=claim)
        assert run_response.status_code == 200
        session_id = run_response.json()["session_id"]

        # 3. Wait for workflow completion
        time.sleep(10)  # Adjust based on workflow duration

        # 4. Check session events for compaction
        session_response = requests.get(f"{BASE_URL}/sessions/{session_id}")
        session_data = session_response.json()

        # 5. Verify compaction triggered
        events = session_data["events"]
        compaction_events = [
            e for e in events if e["event_type"] == "compaction_triggered"
        ]

        assert len(compaction_events) > 0
        compaction = compaction_events[0]

        # 6. Validate compaction results
        assert compaction["events_before_count"] > 50
        assert compaction["events_after_count"] < compaction["events_before_count"]
        assert compaction["tokens_before"] > compaction["tokens_after"]

        # 7. Verify token savings >50%
        savings_ratio = (
            compaction["tokens_before"] - compaction["tokens_after"]
        ) / compaction["tokens_before"]
        assert savings_ratio > 0.5

    def test_manual_compaction_trigger(self):
        """Test manual compaction via API"""
        # Create session with events
        # Manually trigger compaction
        # Verify results
        pass
```

#### Scenario 2: Proactive Memory Retrieval

```python
# tests/e2e/test_proactive_memory_e2e.py
class TestProactiveMemoryE2E:
    def test_proactive_memory_auto_retrieval(self):
        """Test proactive mode automatically retrieves relevant memories"""

        # 1. Create test memories
        memory1 = {
            "memory_type": "fraud_pattern",
            "content": "Merchant ABC shows high fraud on claims >$5000",
            "tags": ["fraud", "merchant_abc"],
        }
        response = requests.post(f"{BASE_URL}/api/memory", json=memory1)
        assert response.status_code == 201

        # 2. Enable proactive memory mode
        config = {
            "memory": {"enabled": True, "retrieval_mode": "proactive"}
        }
        requests.put(f"{BASE_URL}/api/context/system-config", json=config)

        # 3. Submit workflow with similar input
        claim = {
            "claim_id": "TEST-MEMORY-001",
            "description": "Claim from merchant ABC for $6000",
        }
        run_response = requests.post(f"{BASE_URL}/runs", json=claim)
        session_id = run_response.json()["session_id"]

        # 4. Wait for completion
        time.sleep(5)

        # 5. Check context lineage for memory retrieval
        lineage_response = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}/context-lineage"
        )
        lineage = lineage_response.json()

        # 6. Verify memories were auto-retrieved
        compilations = lineage["compilations"]
        assert len(compilations) > 0

        first_compilation = compilations[0]
        assert first_compilation["memories_retrieved"] > 0

        # 7. Check similarity scores
        # (Would require detailed compilation data)
```

---

## Performance Tests

### Benchmarks

**Location:** `backend/orchestrator/tests/performance/`

#### Benchmark: Context Compilation Time

```python
# tests/performance/test_compilation_performance.py
import time
import pytest
from app.services.context_processor_pipeline import ContextProcessorPipeline


class TestCompilationPerformance:
    """Performance benchmarks for context compilation"""

    def test_compilation_time_under_500ms(self):
        """Test context compilation completes in <500ms"""
        pipeline = ContextProcessorPipeline(session_id="perf_test")

        # Large context (worst case)
        context = {
            "original_input": {"description": "test" * 100},
            "prior_outputs": [{"output": f"output_{i}"} for i in range(10)],
            "observations": [{"text": f"obs_{i}"} for i in range(100)],
        }

        # Warm up
        pipeline.execute(context, "test_agent")

        # Benchmark
        start = time.time()
        for _ in range(10):
            pipeline.execute(context, "test_agent")
        elapsed = (time.time() - start) / 10

        # Assert <500ms average
        assert elapsed < 0.5, f"Compilation took {elapsed*1000:.0f}ms (target: <500ms)"

    def test_memory_retrieval_time(self):
        """Test memory retrieval completes in <200ms"""
        from app.services.memory_manager import get_memory_manager

        manager = get_memory_manager()

        # Create 100 test memories
        for i in range(100):
            manager.store_memory(
                memory_type="test",
                content=f"Test memory content {i}",
                tags=["test"],
            )

        # Benchmark retrieval
        start = time.time()
        results = manager.retrieve_memories_by_similarity(
            query_text="test memory",
            limit=10,
            threshold=0.5,
            use_embeddings=False,
        )
        elapsed = time.time() - start

        assert elapsed < 0.2, f"Retrieval took {elapsed*1000:.0f}ms (target: <200ms)"
        assert len(results) > 0
```

#### Load Test: Concurrent Workflows

```python
# tests/performance/test_concurrent_load.py
import concurrent.futures
import requests


class TestConcurrentLoad:
    """Load tests for concurrent workflow execution"""

    def test_100_concurrent_workflows(self):
        """Test system handles 100 concurrent workflow submissions"""

        def submit_workflow(i):
            claim = {
                "claim_id": f"LOAD-TEST-{i:04d}",
                "description": f"Load test claim {i}",
            }
            response = requests.post(f"{BASE_URL}/runs", json=claim)
            return response.status_code == 200

        # Submit 100 concurrent workflows
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(submit_workflow, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Verify all succeeded
        success_count = sum(results)
        assert success_count >= 95, f"Only {success_count}/100 workflows succeeded"
```

---

## Regression Tests

### Regression Test Checklist

Use this checklist before each release:

```markdown
## Context Engineering Regression Tests

### Configuration
- [ ] Can enable/disable context engineering master toggle
- [ ] Can export/import configuration successfully
- [ ] Validation prevents invalid configurations
- [ ] Reset to defaults works

### Compaction
- [ ] Rule-based compaction triggers at threshold
- [ ] LLM-based compaction produces valid summaries
- [ ] Compaction events logged correctly
- [ ] Token savings measured accurately

### Memory Layer
- [ ] Can create memories via API
- [ ] Reactive retrieval works with queries
- [ ] Proactive retrieval auto-triggers
- [ ] Memory expiration works (retention policy)
- [ ] Memory deletion works

### Artifacts
- [ ] Artifact versioning creates new versions
- [ ] Version lineage tracks parent-child relationships
- [ ] Artifact handles resolve correctly
- [ ] Max version limit enforced

### Governance
- [ ] PII masking redacts SSNs and credit cards
- [ ] Age filtering removes old observations
- [ ] Governance limits enforced (memories, artifacts)
- [ ] All decisions logged in audit trail

### Performance
- [ ] Context compilation <500ms
- [ ] Memory retrieval <200ms
- [ ] No memory leaks in long-running sessions
- [ ] Token budget enforced correctly
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-context-engineering.yml
name: Context Engineering Tests

on:
  push:
    branches: [main, develop]
    paths:
      - "backend/orchestrator/app/services/processors/**"
      - "backend/orchestrator/app/services/memory_manager.py"
      - "backend/orchestrator/app/services/context_processor_pipeline.py"
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd backend/orchestrator
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: |
          cd backend/orchestrator
          pytest tests/processors/ --cov=app.services.processors --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/orchestrator/coverage.xml

  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd backend/orchestrator
          pip install -r requirements.txt
          pip install pytest

      - name: Run integration tests
        run: |
          cd backend/orchestrator
          pytest tests/integration/ -v

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker compose up -d

      - name: Wait for services
        run: sleep 10

      - name: Run E2E tests
        run: |
          cd backend/orchestrator
          pytest tests/e2e/ -v

      - name: Stop services
        run: docker compose down
```

### Local Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running context engineering tests..."

cd backend/orchestrator

# Run unit tests
pytest tests/processors/ -q
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit aborted."
    exit 1
fi

# Run integration tests
pytest tests/integration/ -q
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed. Commit aborted."
    exit 1
fi

echo "✅ All tests passed!"
exit 0
```

---

## Test Data Fixtures

### Sample Fixtures

```python
# tests/fixtures/contexts.py
import pytest


@pytest.fixture
def minimal_context():
    """Minimal valid context"""
    return {
        "original_input": {"claim_id": "TEST-001"},
        "prior_outputs": [],
        "observations": [],
    }


@pytest.fixture
def large_context():
    """Large context for performance testing"""
    return {
        "original_input": {"description": "test" * 1000},
        "prior_outputs": [{"output": f"output_{i}"} for i in range(50)],
        "observations": [{"text": f"obs_{i}"} for i in range(200)],
    }


@pytest.fixture
def context_with_pii():
    """Context containing PII for filtering tests"""
    return {
        "original_input": {
            "description": "SSN: 123-45-6789, Card: 4111-1111-1111-1111"
        }
    }
```

---

## Debugging Failed Tests

### Common Test Failures

**1. Test fails intermittently**
- **Cause:** Race condition, timing issues
- **Fix:** Add proper synchronization, increase timeouts

**2. Test fails in CI but passes locally**
- **Cause:** Environment differences
- **Fix:** Use docker for consistent environment

**3. Performance test fails**
- **Cause:** Resource constraints in CI
- **Fix:** Relax thresholds for CI environment

### Debug Commands

```bash
# Run test with verbose output
pytest tests/processors/test_my_processor.py -v -s

# Run test with debugging
pytest tests/processors/test_my_processor.py --pdb

# Run only failed tests
pytest --lf

# Show print statements
pytest -s

# Generate HTML coverage report
pytest --cov=app.services.processors --cov-report=html
open htmlcov/index.html
```

---

**End of Testing Guide**
*Last updated: January 2026*
