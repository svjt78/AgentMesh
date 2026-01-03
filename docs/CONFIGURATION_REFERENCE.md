# Context Engineering Configuration Reference

**Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** System Administrators, DevOps Engineers

---

## Table of Contents

1. [Configuration Files Overview](#configuration-files-overview)
2. [context_strategies.json Reference](#context_strategiesjson-reference)
3. [system_config.json Reference](#system_configjson-reference)
4. [governance_policies.json Reference](#governance_policiesjson-reference)
5. [context_processor_pipeline.json Reference](#context_processor_pipelinejson-reference)
6. [Environment Variables](#environment-variables)
7. [Migration Guide](#migration-guide)
8. [Validation Rules](#validation-rules)

---

## Configuration Files Overview

### File Locations

```
registries/
├── context_strategies.json           # Feature configurations and thresholds
├── system_config.json                # Master toggles and system-wide settings
├── governance_policies.json          # Filtering rules and limits
└── context_processor_pipeline.json   # Processor execution order
```

### Configuration Hierarchy

```
System Config (Master Toggles)
    ↓
Context Strategies (Detailed Settings)
    ↓
Governance Policies (Rules & Limits)
    ↓
Processor Pipeline (Execution Order)
```

**Override Priority:**
1. Environment Variables (highest)
2. System Config
3. Context Strategies
4. Registry Defaults (lowest)

---

## context_strategies.json Reference

**Purpose:** Detailed configuration for each context engineering feature.

**Location:** `registries/context_strategies.json`

### Complete Schema

```json
{
  "version": "1.0.0",

  "context_compilation": {
    "default_budget_allocation": {
      "original_input_percentage": 30,
      "prior_outputs_percentage": 50,
      "observations_percentage": 20
    }
  },

  "compaction": {
    "enabled": false,
    "trigger_strategy": "token_threshold",
    "token_threshold": 8000,
    "event_count_threshold": 100,
    "compaction_method": "rule_based",
    "llm_summarization": {
      "enabled": false,
      "model_profile_id": "summarization_gpt35",
      "quality_level": "standard",
      "preserve_critical_events": true,
      "summary_max_tokens": 2000
    },
    "sliding_window": {
      "enabled": true,
      "overlap_percentage": 10
    }
  },

  "memory_layer": {
    "enabled": false,
    "storage_path": "/storage/memory",
    "retention_days": 90,
    "retrieval_mode": "reactive"
  },

  "artifact_management": {
    "versioning_enabled": false,
    "max_versions_per_artifact": 10,
    "auto_externalize_threshold_kb": 100,
    "handle_format": "artifact://{artifact_id}/v{version}"
  },

  "prefix_caching": {
    "enabled": false,
    "stable_prefix_components": [
      "system_instructions",
      "agent_identity"
    ],
    "variable_suffix_components": [
      "recent_observations",
      "current_task"
    ]
  }
}
```

### Field Definitions

#### context_compilation

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `default_budget_allocation.original_input_percentage` | integer | 30 | 0-100 | Percentage of token budget for original input |
| `default_budget_allocation.prior_outputs_percentage` | integer | 50 | 0-100 | Percentage of token budget for prior outputs |
| `default_budget_allocation.observations_percentage` | integer | 20 | 0-100 | Percentage of token budget for observations |

**Validation:** Sum must equal 100

**Example Override:**
```json
{
  "context_compilation": {
    "default_budget_allocation": {
      "original_input_percentage": 40,
      "prior_outputs_percentage": 40,
      "observations_percentage": 20
    }
  }
}
```

#### compaction

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `enabled` | boolean | false | true/false | Enable context compaction |
| `trigger_strategy` | string | "token_threshold" | "token_threshold", "event_threshold", "both" | When to trigger compaction |
| `token_threshold` | integer | 8000 | 100-50000 | Trigger when tokens exceed this |
| `event_count_threshold` | integer | 100 | 10-1000 | Trigger when events exceed this |
| `compaction_method` | string | "rule_based" | "rule_based", "llm_based" | Compaction method |

**LLM Summarization:**

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `llm_summarization.enabled` | boolean | false | true/false | Enable LLM-based summarization |
| `llm_summarization.model_profile_id` | string | "summarization_gpt35" | Any model profile ID | Model to use for summarization |
| `llm_summarization.quality_level` | string | "standard" | "fast", "standard", "high" | Summarization quality/speed tradeoff |
| `llm_summarization.preserve_critical_events` | boolean | true | true/false | Keep critical events untouched |
| `llm_summarization.summary_max_tokens` | integer | 2000 | 100-10000 | Max tokens for summary |

**Sliding Window:**

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `sliding_window.enabled` | boolean | true | true/false | Use sliding window for compaction |
| `sliding_window.overlap_percentage` | integer | 10 | 0-50 | Overlap between windows |

#### memory_layer

| Field | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `enabled` | boolean | false | true/false | Enable memory layer |
| `storage_path` | string | "/storage/memory" | Valid path | Where to store memories |
| `retention_days` | integer | 90 | 1-365 | Auto-delete after N days |
| `retrieval_mode` | string | "reactive" | "reactive", "proactive" | How to retrieve memories |

#### artifact_management

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `versioning_enabled` | boolean | false | true/false | Enable artifact versioning |
| `max_versions_per_artifact` | integer | 10 | 1-100 | Max versions to keep |
| `auto_externalize_threshold_kb` | integer | 100 | 1-10000 | Size threshold for externalization (KB) |
| `handle_format` | string | "artifact://{artifact_id}/v{version}" | Valid format string | Format for artifact handles |

#### prefix_caching

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable prefix caching optimization |
| `stable_prefix_components` | array | ["system_instructions", "agent_identity"] | Components to cache |
| `variable_suffix_components` | array | ["recent_observations", "current_task"] | Components that change |

---

## system_config.json Reference

**Purpose:** System-wide master toggles and high-level settings.

**Location:** `registries/system_config.json`

### Complete Schema

```json
{
  "context_engineering": {
    "enabled": false,
    "processor_pipeline_enabled": true
  },

  "compaction": {
    "enabled": false,
    "method": "rule_based"
  },

  "memory": {
    "enabled": false,
    "retrieval_mode": "reactive",
    "proactive_settings": {
      "enabled": true,
      "max_memories_to_preload": 5,
      "similarity_threshold": 0.7,
      "use_keyword_similarity": true,
      "use_embeddings": false,
      "embedding_model": "text-embedding-ada-002"
    }
  },

  "artifacts": {
    "versioning_enabled": false
  }
}
```

### Field Definitions

#### context_engineering

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Master toggle for all context engineering features |
| `processor_pipeline_enabled` | boolean | true | Enable processor pipeline execution |

**Note:** When `enabled` is false, all context engineering features are bypassed.

#### compaction

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `enabled` | boolean | false | true/false | Enable compaction system-wide |
| `method` | string | "rule_based" | "rule_based", "llm_based" | Default compaction method |

#### memory

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `enabled` | boolean | false | true/false | Enable memory layer |
| `retrieval_mode` | string | "reactive" | "reactive", "proactive" | Default retrieval mode |

**Proactive Settings:**

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `proactive_settings.enabled` | boolean | true | true/false | Enable proactive preloading |
| `proactive_settings.max_memories_to_preload` | integer | 5 | 1-20 | Max memories to auto-retrieve |
| `proactive_settings.similarity_threshold` | float | 0.7 | 0.0-1.0 | Minimum similarity score |
| `proactive_settings.use_keyword_similarity` | boolean | true | true/false | Use keyword-based similarity |
| `proactive_settings.use_embeddings` | boolean | false | true/false | Use embedding-based similarity |
| `proactive_settings.embedding_model` | string | "text-embedding-ada-002" | OpenAI model name | Embedding model to use |

#### artifacts

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `versioning_enabled` | boolean | false | Enable artifact versioning system-wide |

---

## governance_policies.json Reference

**Purpose:** Filtering rules, governance limits, and security policies.

**Location:** `registries/governance_policies.json`

### Complete Schema

```json
{
  "policies": {
    "context_governance": {
      "max_context_tokens_per_agent": 10000,
      "max_memory_retrievals_per_invocation": 10,
      "max_artifact_loads_per_invocation": 5,
      "context_auditing": {
        "log_all_compilations": true,
        "log_truncations": true,
        "log_compactions": true
      }
    },

    "context_filtering": {
      "enabled": false,
      "rules": [
        {
          "rule_id": "mask_ssn",
          "enabled": true,
          "field": "original_input",
          "description": "Mask Social Security Numbers",
          "condition": {
            "type": "regex_mask",
            "patterns": [
              {
                "pattern": "\\d{3}-\\d{2}-\\d{4}",
                "replacement": "***-**-****"
              }
            ]
          }
        },
        {
          "rule_id": "mask_credit_card",
          "enabled": true,
          "field": "original_input",
          "description": "Mask credit card numbers",
          "condition": {
            "type": "regex_mask",
            "patterns": [
              {
                "pattern": "\\d{4}-\\d{4}-\\d{4}-\\d{4}",
                "replacement": "****-****-****-****"
              }
            ]
          }
        },
        {
          "rule_id": "filter_old_observations",
          "enabled": true,
          "field": "observations",
          "description": "Remove observations older than 30 days",
          "condition": {
            "type": "age_threshold",
            "max_age_days": 30
          }
        },
        {
          "rule_id": "remove_debug_logs",
          "enabled": false,
          "field": "observations",
          "description": "Remove debug-level log entries",
          "condition": {
            "type": "field_value_match",
            "match_field": "log_level",
            "match_value": "debug"
          }
        }
      ]
    },

    "multi_agent_handoffs": {
      "default_handoff_mode": "scoped",
      "agent_handoff_rules": []
    }
  }
}
```

### Field Definitions

#### context_governance

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `max_context_tokens_per_agent` | integer | 10000 | 1000-100000 | Max tokens per agent invocation |
| `max_memory_retrievals_per_invocation` | integer | 10 | 1-100 | Max memories to retrieve |
| `max_artifact_loads_per_invocation` | integer | 5 | 1-50 | Max artifacts to load |

**Context Auditing:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `context_auditing.log_all_compilations` | boolean | true | Log every context compilation |
| `context_auditing.log_truncations` | boolean | true | Log when context is truncated |
| `context_auditing.log_compactions` | boolean | true | Log compaction events |

#### context_filtering

**Global Settings:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable content filtering system |

**Rule Structure:**

Each rule in the `rules` array has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | Yes | Unique identifier |
| `enabled` | boolean | Yes | Is this rule active |
| `field` | string | Yes | Field to apply rule to |
| `description` | string | Yes | Human-readable description |
| `condition` | object | Yes | Rule condition (see below) |

**Condition Types:**

**1. regex_mask** - Mask patterns with replacement:
```json
{
  "type": "regex_mask",
  "patterns": [
    {
      "pattern": "\\d{3}-\\d{2}-\\d{4}",
      "replacement": "***-**-****"
    }
  ]
}
```

**2. age_threshold** - Filter by age:
```json
{
  "type": "age_threshold",
  "max_age_days": 30
}
```

**3. field_value_match** - Filter by field value:
```json
{
  "type": "field_value_match",
  "match_field": "log_level",
  "match_value": "debug"
}
```

---

## context_processor_pipeline.json Reference

**Purpose:** Define processor execution order and configuration.

**Location:** `registries/context_processor_pipeline.json`

### Complete Schema

```json
{
  "processors": [
    {
      "processor_id": "content_selector",
      "enabled": true,
      "order": 1,
      "config": {}
    },
    {
      "processor_id": "compaction_checker",
      "enabled": true,
      "order": 2,
      "config": {}
    },
    {
      "processor_id": "memory_retriever",
      "enabled": false,
      "order": 3,
      "config": {}
    },
    {
      "processor_id": "artifact_resolver",
      "enabled": true,
      "order": 4,
      "config": {}
    },
    {
      "processor_id": "content_filter",
      "enabled": false,
      "order": 5,
      "config": {}
    },
    {
      "processor_id": "transformer",
      "enabled": true,
      "order": 6,
      "config": {}
    },
    {
      "processor_id": "token_budget_enforcer",
      "enabled": true,
      "order": 7,
      "config": {}
    },
    {
      "processor_id": "injector",
      "enabled": true,
      "order": 8,
      "config": {}
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `processor_id` | string | Yes | Unique processor identifier |
| `enabled` | boolean | Yes | Is this processor active |
| `order` | integer | Yes | Execution order (lower = earlier) |
| `config` | object | No | Processor-specific configuration |

### Available Processors

| Processor ID | Purpose | Can Disable? |
|--------------|---------|--------------|
| `content_selector` | Filter irrelevant events | Yes |
| `compaction_checker` | Check if compaction needed | Yes |
| `memory_retriever` | Load memories | Yes |
| `artifact_resolver` | Resolve artifact handles | Yes |
| `content_filter` | Apply PII masking, filtering | Yes |
| `transformer` | Convert to LLM message format | No (required) |
| `token_budget_enforcer` | Enforce token limits | No (required) |
| `injector` | Final LLM formatting | No (required) |

**Note:** Disabling required processors may cause compilation failures.

---

## Environment Variables

### Override Hierarchy

Environment variables override registry configuration:

```
ENV VARS (highest priority)
    ↓
System Config
    ↓
Context Strategies
    ↓
Registry Defaults (lowest priority)
```

### Available Variables

#### Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRY_PATH` | `/registries` | Path to registry files |
| `STORAGE_PATH` | `/storage` | Path to storage directory |
| `MEMORY_STORAGE_PATH` | `${STORAGE_PATH}/memory` | Memory storage path |
| `ARTIFACT_STORAGE_PATH` | `${STORAGE_PATH}/artifacts` | Artifact storage path |

#### Feature Toggles

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONTEXT_ENGINEERING_ENABLED` | boolean | false | Master toggle |
| `COMPACTION_ENABLED` | boolean | false | Enable compaction |
| `MEMORY_LAYER_ENABLED` | boolean | false | Enable memory layer |
| `ARTIFACT_VERSIONING_ENABLED` | boolean | false | Enable versioning |

#### Thresholds

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `COMPACTION_TOKEN_THRESHOLD` | integer | 8000 | 100-50000 | Token trigger |
| `COMPACTION_EVENT_THRESHOLD` | integer | 100 | 10-1000 | Event trigger |
| `MEMORY_RETENTION_DAYS` | integer | 90 | 1-365 | Memory retention |
| `MAX_ARTIFACT_VERSIONS` | integer | 10 | 1-100 | Version limit |

#### LLM Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | - | OpenAI API key (required for embeddings) |
| `EMBEDDING_MODEL` | string | text-embedding-ada-002 | Embedding model name |

### Example .env File

```bash
# Context Engineering
CONTEXT_ENGINEERING_ENABLED=true
COMPACTION_ENABLED=true
COMPACTION_TOKEN_THRESHOLD=6000
COMPACTION_EVENT_THRESHOLD=80

# Memory Layer
MEMORY_LAYER_ENABLED=true
MEMORY_RETENTION_DAYS=60

# Paths
REGISTRY_PATH=/app/registries
STORAGE_PATH=/app/storage

# LLM
OPENAI_API_KEY=sk-...
```

---

## Migration Guide

### From Default Configuration

**Step 1: Backup Current Config**
```bash
# Export current configuration
curl http://localhost:8016/api/context/strategies > backup-strategies.json
curl http://localhost:8016/api/context/system-config > backup-system.json
```

**Step 2: Enable Features Incrementally**

```json
// Week 1: Enable compaction only
{
  "context_engineering": {"enabled": true},
  "compaction": {"enabled": true}
}

// Week 2: Add memory layer
{
  "memory": {"enabled": true, "retrieval_mode": "reactive"}
}

// Week 3: Enable proactive memory
{
  "memory": {
    "retrieval_mode": "proactive",
    "proactive_settings": {"enabled": true}
  }
}
```

**Step 3: Monitor & Adjust**
- Monitor token usage (should decrease 50%+)
- Check compaction frequency (events logged)
- Adjust thresholds based on workload

### From Legacy System

**Compatibility Mode:**

Set these to maintain legacy behavior:
```json
{
  "context_engineering": {
    "enabled": false  // Bypass all context engineering
  }
}
```

**Gradual Migration:**

1. **Phase 1: Observation (Week 1)**
   - Enable with all features OFF
   - Monitor baseline metrics

2. **Phase 2: Compaction (Week 2)**
   - Enable rule-based compaction
   - Validate summaries are accurate

3. **Phase 3: Memory (Week 3-4)**
   - Enable reactive memory
   - Create initial memories manually

4. **Phase 4: Full Features (Week 5+)**
   - Enable all features
   - Tune thresholds based on data

---

## Validation Rules

### Cross-Field Validations

**1. Budget Allocation:**
```
original_input_percentage +
prior_outputs_percentage +
observations_percentage = 100
```

**2. LLM Summarization:**
```
IF compaction_method = "llm_based"
AND llm_summarization.enabled = true
THEN llm_summarization.model_profile_id MUST be set
```

**3. Proactive Memory:**
```
IF memory.retrieval_mode = "proactive"
AND proactive_settings.use_embeddings = true
THEN OPENAI_API_KEY MUST be set
```

### Range Validations

| Field | Min | Max | Default |
|-------|-----|-----|---------|
| token_threshold | 100 | 50000 | 8000 |
| event_count_threshold | 10 | 1000 | 100 |
| retention_days | 1 | 365 | 90 |
| max_versions_per_artifact | 1 | 100 | 10 |
| auto_externalize_threshold_kb | 1 | 10000 | 100 |
| similarity_threshold | 0.0 | 1.0 | 0.7 |
| max_memories_to_preload | 1 | 20 | 5 |

### Type Validations

| Field | Type | Example Valid | Example Invalid |
|-------|------|---------------|-----------------|
| enabled | boolean | true, false | "true", 1 |
| token_threshold | integer | 8000 | 8000.5, "8000" |
| retrieval_mode | enum | "reactive", "proactive" | "auto", "manual" |
| compaction_method | enum | "rule_based", "llm_based" | "hybrid" |

---

## Quick Reference

### Minimal Configuration (Starter)

```json
// system_config.json
{
  "context_engineering": {"enabled": true},
  "compaction": {"enabled": true}
}

// context_strategies.json
{
  "compaction": {
    "token_threshold": 8000,
    "compaction_method": "rule_based"
  }
}
```

### Recommended Configuration (Production)

```json
// system_config.json
{
  "context_engineering": {"enabled": true},
  "compaction": {"enabled": true, "method": "llm_based"},
  "memory": {"enabled": true, "retrieval_mode": "reactive"}
}

// context_strategies.json
{
  "compaction": {
    "token_threshold": 6000,
    "compaction_method": "llm_based",
    "llm_summarization": {
      "enabled": true,
      "model_profile_id": "summarization_gpt35",
      "quality_level": "standard"
    }
  },
  "memory_layer": {
    "retention_days": 90,
    "retrieval_mode": "reactive"
  }
}
```

### Advanced Configuration (All Features)

```json
// system_config.json
{
  "context_engineering": {"enabled": true},
  "compaction": {"enabled": true, "method": "llm_based"},
  "memory": {
    "enabled": true,
    "retrieval_mode": "proactive",
    "proactive_settings": {
      "enabled": true,
      "use_embeddings": true
    }
  },
  "artifacts": {"versioning_enabled": true}
}

// governance_policies.json
{
  "policies": {
    "context_filtering": {"enabled": true}
  }
}
```

---

## Troubleshooting Configuration Issues

### Issue: Configuration Not Applied

**Symptoms:** Changes don't take effect

**Solutions:**
1. Check file permissions (must be readable)
2. Validate JSON syntax (use `jq . < file.json`)
3. Restart services after registry changes
4. Check logs for validation errors

### Issue: Validation Errors

**Symptoms:** Save fails with validation error

**Solutions:**
1. Check ranges (see validation rules above)
2. Ensure budget allocation sums to 100%
3. Verify model_profile_id exists in model_profiles.json
4. Check enum values match exactly

### Issue: Features Not Working

**Symptoms:** Features enabled but not functioning

**Checklist:**
- [ ] `context_engineering.enabled = true` in system_config
- [ ] Feature-specific toggle enabled
- [ ] Processor pipeline includes required processors
- [ ] No validation errors in logs
- [ ] Environment variables not overriding

---

**End of Configuration Reference**
*Last updated: January 2026*
