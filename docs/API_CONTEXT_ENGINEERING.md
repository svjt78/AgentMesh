# Context Engineering API Reference

**Version:** 1.0
**Last Updated:** January 2026
**Base URL:** `http://localhost:8016/api`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Configuration Endpoints](#configuration-endpoints)
3. [Memory Management Endpoints](#memory-management-endpoints)
4. [Artifact Versioning Endpoints](#artifact-versioning-endpoints)
5. [Context Lineage & Debugging](#context-lineage--debugging)
6. [Error Handling](#error-handling)
7. [Rate Limits](#rate-limits)

---

## Authentication

Currently, the API does not require authentication. In production deployments, implement API key or OAuth2 authentication.

**Future Headers:**
```http
Authorization: Bearer <your_api_key>
```

---

## Configuration Endpoints

### Get Context Strategies

Retrieve current context engineering configuration.

**Endpoint:** `GET /api/context/strategies`

**Response:**
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
      "quality_level": "standard"
    }
  },
  "memory_layer": {
    "enabled": false,
    "retention_days": 90,
    "retrieval_mode": "reactive"
  },
  "artifact_management": {
    "versioning_enabled": false,
    "max_versions_per_artifact": 10,
    "auto_externalize_threshold_kb": 100
  },
  "prefix_caching": {
    "enabled": false
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Configuration file not found

---

### Update Context Strategies

Update context engineering configuration.

**Endpoint:** `PUT /api/context/strategies`

**Request Body:**
```json
{
  "compaction": {
    "enabled": true,
    "token_threshold": 6000,
    "compaction_method": "llm_based"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Context strategies updated successfully"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid configuration
- `500 Internal Server Error` - Failed to write configuration

**Validation Errors:**
```json
{
  "error": "Validation failed",
  "details": [
    "Token threshold must be between 100 and 50,000",
    "Budget allocation must sum to 100%"
  ]
}
```

---

### Get System Config

Retrieve system-wide toggles.

**Endpoint:** `GET /api/context/system-config`

**Response:**
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
      "use_embeddings": false
    }
  },
  "artifacts": {
    "versioning_enabled": false
  }
}
```

---

### Update System Config

Update system-wide toggles.

**Endpoint:** `PUT /api/context/system-config`

**Request Body:**
```json
{
  "context_engineering": {
    "enabled": true
  },
  "compaction": {
    "enabled": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "System config updated successfully"
}
```

---

### List Processors

Get configured context processors.

**Endpoint:** `GET /api/context/processors`

**Response:**
```json
{
  "processors": [
    {
      "processor_id": "content_selector",
      "enabled": true,
      "order": 1
    },
    {
      "processor_id": "compaction_checker",
      "enabled": true,
      "order": 2
    },
    {
      "processor_id": "memory_retriever",
      "enabled": false,
      "order": 3
    }
  ]
}
```

---

## Memory Management Endpoints

### List Memories

Retrieve all stored memories with optional filtering.

**Endpoint:** `GET /api/memory`

**Query Parameters:**
- `limit` (optional, default: 50) - Max memories to return
- `offset` (optional, default: 0) - Pagination offset
- `type` (optional) - Filter by memory type
- `tags` (optional) - Comma-separated tags to filter

**Example Request:**
```http
GET /api/memory?limit=10&offset=0&type=fraud_pattern&tags=high_risk,merchant_xyz
```

**Response:**
```json
{
  "memories": [
    {
      "memory_id": "mem_20250101_abc123",
      "memory_type": "fraud_pattern",
      "content": "Merchant XYZ shows 80% fraud rate on claims >$5000",
      "tags": ["high_risk", "merchant_xyz"],
      "created_at": "2025-01-01T12:00:00Z",
      "expires_at": "2025-04-01T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters

---

### Create Memory

Store a new memory.

**Endpoint:** `POST /api/memory`

**Request Body:**
```json
{
  "memory_type": "fraud_pattern",
  "content": "Merchant ABC has suspicious claim patterns",
  "tags": ["fraud", "merchant_abc"],
  "expires_at": "2026-03-01T00:00:00Z"
}
```

**Required Fields:**
- `memory_type` (string) - Type classification
- `content` (string) - Memory content (1-10,000 chars)

**Optional Fields:**
- `tags` (array of strings) - Searchable tags
- `expires_at` (ISO 8601 datetime) - Auto-deletion time

**Response:**
```json
{
  "memory_id": "mem_20260102_xyz789",
  "created_at": "2026-01-02T14:30:00Z",
  "message": "Memory created successfully"
}
```

**Status Codes:**
- `201 Created` - Success
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - Failed to write memory

---

### Get Memory

Retrieve a specific memory by ID.

**Endpoint:** `GET /api/memory/{memory_id}`

**Response:**
```json
{
  "memory_id": "mem_20250101_abc123",
  "memory_type": "fraud_pattern",
  "content": "Merchant XYZ shows 80% fraud rate on claims >$5000",
  "tags": ["high_risk", "merchant_xyz"],
  "metadata": {
    "session_id": "session_xyz",
    "created_by": "fraud_agent"
  },
  "created_at": "2025-01-01T12:00:00Z",
  "expires_at": "2025-04-01T12:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Memory not found

---

### Delete Memory

Delete a memory by ID.

**Endpoint:** `DELETE /api/memory/{memory_id}`

**Response:**
```json
{
  "success": true,
  "message": "Memory deleted successfully"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Memory not found

---

### Search Memories (Reactive Retrieval)

Search memories using query, type, and tags.

**Endpoint:** `POST /api/memory/retrieve`

**Request Body:**
```json
{
  "query": "fraud patterns for merchant XYZ",
  "memory_type": "fraud_pattern",
  "tags": ["merchant_xyz"],
  "limit": 5,
  "mode": "reactive"
}
```

**Parameters:**
- `query` (string) - Search query
- `memory_type` (optional) - Filter by type
- `tags` (optional, array) - Filter by tags
- `limit` (optional, default: 5) - Max results
- `mode` (optional, default: "reactive") - "reactive" or "proactive"

**Response:**
```json
{
  "memories": [
    {
      "memory_id": "mem_20250101_abc123",
      "memory_type": "fraud_pattern",
      "content": "Merchant XYZ shows 80% fraud rate",
      "similarity_score": 0.92,
      "created_at": "2025-01-01T12:00:00Z"
    }
  ],
  "query": "fraud patterns for merchant XYZ",
  "retrieval_mode": "reactive",
  "total_found": 1
}
```

---

## Artifact Versioning Endpoints

### List Artifact Versions

Get all versions of an artifact.

**Endpoint:** `GET /api/artifacts/{artifact_id}/versions`

**Response:**
```json
{
  "artifact_id": "evidence_map_xyz",
  "current_version": 3,
  "versions": [
    {
      "version": 1,
      "created_at": "2025-12-01T10:00:00Z",
      "parent_version": null,
      "handle": "artifact://evidence_map_xyz/v1",
      "size_bytes": 12345
    },
    {
      "version": 2,
      "created_at": "2025-12-01T11:00:00Z",
      "parent_version": 1,
      "handle": "artifact://evidence_map_xyz/v2",
      "size_bytes": 15678
    },
    {
      "version": 3,
      "created_at": "2025-12-01T12:00:00Z",
      "parent_version": 2,
      "handle": "artifact://evidence_map_xyz/v3",
      "size_bytes": 18901
    }
  ]
}
```

---

### Get Artifact Version

Retrieve a specific artifact version.

**Endpoint:** `GET /api/artifacts/{artifact_id}/versions/{version}`

**Response:**
```json
{
  "artifact_id": "evidence_map_xyz",
  "version": 2,
  "handle": "artifact://evidence_map_xyz/v2",
  "created_at": "2025-12-01T11:00:00Z",
  "parent_version": 1,
  "size_bytes": 15678,
  "metadata": {
    "session_id": "session_abc",
    "created_by": "evidence_compiler"
  },
  "content": {
    "claim_id": "CLM-12345",
    "fraud_score": 0.15,
    "evidence_items": [...]
  }
}
```

---

### Create Artifact Version

Create a new version of an artifact.

**Endpoint:** `POST /api/artifacts/{artifact_id}/versions`

**Request Body:**
```json
{
  "content": {
    "claim_id": "CLM-12345",
    "fraud_score": 0.18,
    "evidence_items": [...]
  },
  "parent_version": 2,
  "metadata": {
    "session_id": "session_def",
    "tags": ["updated", "fraud_review"]
  }
}
```

**Response:**
```json
{
  "artifact_id": "evidence_map_xyz",
  "version": 3,
  "handle": "artifact://evidence_map_xyz/v3",
  "created_at": "2026-01-02T14:30:00Z",
  "parent_version": 2
}
```

---

## Context Lineage & Debugging

### Get Session Context Lineage

Retrieve all context compilations for a session.

**Endpoint:** `GET /api/sessions/{session_id}/context-lineage`

**Response:**
```json
{
  "session_id": "session_abc123",
  "compilations": [
    {
      "compilation_id": "ctx_compile_001",
      "timestamp": "2025-12-01T10:05:00Z",
      "agent_id": "fraud_agent",
      "processors_executed": [
        "content_selector",
        "memory_retriever",
        "transformer"
      ],
      "tokens_before": 12000,
      "tokens_after": 5000,
      "truncation_applied": true,
      "memories_retrieved": 2,
      "artifacts_resolved": 1
    }
  ],
  "total_compilations": 1
}
```

---

### Get Specific Compilation

Get details of a specific context compilation.

**Endpoint:** `GET /api/sessions/{session_id}/context-lineage/{compilation_id}`

**Response:**
```json
{
  "compilation_id": "ctx_compile_001",
  "session_id": "session_abc123",
  "agent_id": "fraud_agent",
  "timestamp": "2025-12-01T10:05:00Z",
  "processors_executed": [
    {
      "processor_id": "content_selector",
      "execution_time_ms": 12,
      "success": true,
      "modifications": {"events_filtered": 5}
    },
    {
      "processor_id": "memory_retriever",
      "execution_time_ms": 45,
      "success": true,
      "modifications": {"memories_retrieved": 2}
    }
  ],
  "context_before": {
    "original_input": {...},
    "prior_outputs": [...],
    "observations": [...]
  },
  "context_after": {
    "original_input": {...},
    "prior_outputs": [...],
    "observations": [...],
    "memories": [...]
  },
  "token_usage": {
    "before": 12000,
    "after": 5000,
    "budget": 10000,
    "truncated": true
  }
}
```

---

### Trigger Manual Compaction

Manually trigger context compaction for a session.

**Endpoint:** `POST /api/sessions/{session_id}/trigger-compaction`

**Request Body:**
```json
{
  "method": "llm_based",
  "force": false
}
```

**Parameters:**
- `method` (optional) - "rule_based" or "llm_based"
- `force` (optional, default: false) - Force compaction even if thresholds not met

**Response:**
```json
{
  "success": true,
  "compaction_id": "compact_001",
  "events_before_count": 150,
  "events_after_count": 35,
  "tokens_before": 15000,
  "tokens_after": 4000,
  "compression_ratio": 0.77,
  "method": "llm_based"
}
```

**Status Codes:**
- `200 OK` - Compaction successful
- `400 Bad Request` - Invalid request or thresholds not met (when force=false)
- `404 Not Found` - Session not found

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_field",
    "reason": "validation failed"
  },
  "timestamp": "2026-01-02T14:30:00Z"
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid input or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Validation Errors

```json
{
  "error": "Validation Error",
  "message": "Invalid configuration",
  "details": [
    {
      "field": "compaction.token_threshold",
      "value": 99,
      "error": "Must be between 100 and 50,000"
    },
    {
      "field": "memory_layer.retention_days",
      "value": 400,
      "error": "Must be between 1 and 365"
    }
  ]
}
```

---

## Rate Limits

**Current Limits:**
- No rate limiting currently implemented

**Planned Production Limits:**
- **Configuration Updates:** 10 requests per minute
- **Memory Operations:** 100 requests per minute
- **Context Lineage Queries:** 50 requests per minute

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

**Rate Limit Exceeded Response:**
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

---

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8016/api"

# Get context strategies
response = requests.get(f"{BASE_URL}/context/strategies")
strategies = response.json()

# Update compaction settings
update = {
    "compaction": {
        "enabled": True,
        "token_threshold": 6000
    }
}
response = requests.put(f"{BASE_URL}/context/strategies", json=update)
print(response.json())

# Create memory
memory = {
    "memory_type": "fraud_pattern",
    "content": "New fraud pattern detected",
    "tags": ["fraud", "high_risk"]
}
response = requests.post(f"{BASE_URL}/memory", json=memory)
memory_id = response.json()["memory_id"]

# Search memories
search = {
    "query": "fraud pattern",
    "limit": 5
}
response = requests.post(f"{BASE_URL}/memory/retrieve", json=search)
memories = response.json()["memories"]
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8016/api";

// Get context strategies
async function getStrategies() {
  const response = await fetch(`${BASE_URL}/context/strategies`);
  const strategies = await response.json();
  return strategies;
}

// Create memory
async function createMemory(memory) {
  const response = await fetch(`${BASE_URL}/memory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(memory),
  });
  return await response.json();
}

// Usage
const memory = {
  memory_type: "fraud_pattern",
  content: "New fraud pattern detected",
  tags: ["fraud", "high_risk"],
};
createMemory(memory).then(console.log);
```

### cURL

```bash
# Get context strategies
curl http://localhost:8016/api/context/strategies

# Update system config
curl -X PUT http://localhost:8016/api/context/system-config \
  -H "Content-Type: application/json" \
  -d '{
    "context_engineering": {"enabled": true},
    "compaction": {"enabled": true}
  }'

# Create memory
curl -X POST http://localhost:8016/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "fraud_pattern",
    "content": "New fraud pattern",
    "tags": ["fraud"]
  }'

# List memories
curl "http://localhost:8016/api/memory?limit=10&type=fraud_pattern"

# Trigger compaction
curl -X POST http://localhost:8016/api/sessions/session_abc/trigger-compaction \
  -H "Content-Type: application/json" \
  -d '{"method": "llm_based", "force": false}'
```

---

## Webhooks (Planned)

**Future Feature:** Subscribe to context engineering events.

**Planned Events:**
- `compaction.triggered`
- `memory.created`
- `memory.retrieved`
- `artifact.version_created`
- `governance.limit_exceeded`

**Webhook Payload Example:**
```json
{
  "event": "compaction.triggered",
  "timestamp": "2026-01-02T14:30:00Z",
  "session_id": "session_abc",
  "data": {
    "events_before": 150,
    "events_after": 35,
    "compression_ratio": 0.77
  }
}
```

---

**End of API Reference**
*Last updated: January 2026*
