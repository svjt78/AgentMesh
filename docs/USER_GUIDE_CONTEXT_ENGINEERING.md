# Context Engineering User Guide

**Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** System Administrators, Operations Teams

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Feature Guides](#feature-guides)
   - [Context Compaction](#context-compaction)
   - [Memory Layer](#memory-layer)
   - [Artifact Versioning](#artifact-versioning)
   - [Governance Controls](#governance-controls)
4. [Configuration Reference](#configuration-reference)
5. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
6. [Best Practices](#best-practices)
7. [FAQ](#faq)

---

## Introduction

### What is Context Engineering?

Context engineering in AgentMesh provides advanced control over how information is compiled, stored, and delivered to AI agents. Think of it as a smart memory management system that:

- **Summarizes** long conversation histories to save costs
- **Remembers** important information across multiple sessions
- **Organizes** large data structures efficiently
- **Protects** sensitive information automatically
- **Optimizes** API usage to reduce expenses

### Why Use Context Engineering?

Without context engineering, long-running workflows can:
- Consume excessive tokens (increasing costs)
- Hit context window limits (causing failures)
- Lose important information from earlier steps
- Repeatedly process the same large data structures

Context engineering solves these problems automatically.

### Key Benefits

| Feature | Benefit | Cost Impact |
|---------|---------|-------------|
| **Context Compaction** | Reduces token usage by 50-80% | 💰💰💰 High savings |
| **Memory Layer** | Maintains knowledge across sessions | 💰 Low cost |
| **Artifact Versioning** | Tracks changes efficiently | 💰 Low cost |
| **Prefix Caching** | Caches stable context components | 💰💰 Medium savings |

---

## Quick Start

### 1. Accessing Configuration

1. Navigate to the AgentMesh frontend at `http://localhost:3016`
2. Click **Configuration** in the top navigation
3. Select the **Context Re-engineering** tab

### 2. Enabling Context Engineering

**First time setup:**

1. Enable the **master toggle**: "Enable Context Engineering Pipeline"
2. Choose features to enable (recommended starter configuration):
   - ✅ **Context Compaction** (rule-based method)
   - ✅ **Memory Layer** (reactive mode)
   - ❌ Artifact Versioning (enable if needed)
   - ❌ Prefix Caching (advanced feature)

3. Click **Save Changes**

### 3. Your First Compaction

To see compaction in action:

1. Enable compaction with default settings:
   - Token Threshold: 8000
   - Event Count Threshold: 100
   - Method: Rule-Based

2. Run a test workflow with many events:
   ```bash
   curl -X POST http://localhost:8016/runs \
     -H "Content-Type: application/json" \
     -d @sample_data/sample_claim_clean.json
   ```

3. View compaction events in the Replay page:
   - Navigate to **Replay** → Select your session
   - Check the **Context Engineering** tab
   - Look for "Compaction Triggered" events

---

## Feature Guides

### Context Compaction

#### What is Context Compaction?

Context compaction automatically summarizes old events to reduce the total amount of information sent to agents. Instead of including every single event from a 200-event workflow, compaction might reduce it to 50 events + a summary.

#### When to Use Compaction

Enable compaction if you have:
- ✅ Workflows with >100 events
- ✅ Long-running sessions (>30 minutes)
- ✅ High token costs
- ✅ Agents that don't need complete history

Don't enable compaction if you have:
- ❌ Short workflows (<50 events)
- ❌ Workflows requiring complete audit trails
- ❌ Real-time critical applications where latency matters

#### Configuration Options

**1. Compaction Method**

| Method | How it Works | Pros | Cons | Cost |
|--------|--------------|------|------|------|
| **Rule-Based** | Removes old events by age/type | Fast, predictable | Less intelligent | Free |
| **LLM-Based** | AI summarizes events | Semantic, accurate | Slower, costs tokens | $$ |

**2. Trigger Thresholds**

- **Token Threshold** (default: 8000)
  - Compaction triggers when token count exceeds this value
  - Recommended: 60-80% of your model's context window
  - Example: For GPT-4 (8K context), set to 6000-6500

- **Event Count Threshold** (default: 100)
  - Compaction triggers when event count exceeds this value
  - Recommended: 100-200 for most workflows

**3. Sliding Window**

When enabled, compaction preserves recent events and compacts only older ones.

- ✅ **Enable** for workflows where recent context is most important
- ❌ **Disable** for workflows where all history is equally important

#### Example: Enabling LLM-Based Compaction

1. Go to **Configuration** → **Context Re-engineering**
2. Enable **Context Compaction**
3. Select **Compaction Method**: LLM-Based
4. Configure LLM Summarization:
   - ✅ Enable LLM Summarization
   - **Model Profile**: Select `summarization_gpt35` (cost-effective)
   - **Quality Level**: Standard
   - ✅ Preserve Critical Events (recommended)

5. **Save Changes**

> **⚠️ Cost Warning:** LLM-based compaction requires API calls. Each compaction may use 500-2000 tokens depending on session size. Monitor costs in your LLM provider dashboard.

#### Monitoring Compaction

View compaction activity:

1. **Real-time (during workflow):**
   - Watch the SSE stream for `compaction_triggered` events

2. **Post-workflow (replay):**
   - Navigate to **Replay** → Select session → **Context Engineering** tab
   - View compaction timeline
   - See events before/after count
   - Check token savings

**Example Compaction Event:**
```json
{
  "event_type": "compaction_triggered",
  "events_before_count": 150,
  "events_after_count": 35,
  "tokens_before": 12000,
  "tokens_after": 3500,
  "method": "rule_based",
  "compression_ratio": 0.71
}
```

### Memory Layer

#### What is the Memory Layer?

The memory layer stores long-term knowledge that persists **across multiple sessions**. Unlike session context (which is forgotten after each workflow), memories can be recalled days or weeks later.

#### Use Cases

| Use Case | Example |
|----------|---------|
| **Learning from past decisions** | "Remember that claims from this merchant are high-risk" |
| **User preferences** | "This customer prefers email communication" |
| **Cross-session continuity** | "Last session concluded that fraud detection needs review" |
| **Knowledge accumulation** | "We've seen 5 similar fraud patterns this month" |

#### Configuration Options

**1. Retrieval Mode**

| Mode | Behavior | When to Use | Cost |
|------|----------|-------------|------|
| **Reactive** | Agents explicitly request memories | Default, predictable | Free |
| **Proactive** | System auto-retrieves similar memories | Advanced, automatic | $ (if embeddings enabled) |

**Reactive Mode (Recommended for Starters):**
- Agent decides when to retrieve memories
- No unexpected API calls
- Full control over what's included in context

**Proactive Mode (Advanced):**
- System automatically finds relevant memories
- Uses similarity search (keyword or embedding-based)
- Higher convenience, lower control

**2. Retention Policy**

- **Retention Days** (default: 90)
  - Memories older than this are automatically deleted
  - Recommended: 30-180 days depending on use case

**3. Proactive Settings** (system_config.json)

If using proactive mode:

```json
{
  "memory": {
    "proactive_settings": {
      "enabled": true,
      "max_memories_to_preload": 5,
      "similarity_threshold": 0.7,
      "use_keyword_similarity": true,
      "use_embeddings": false
    }
  }
}
```

- **use_keyword_similarity**: Fast, free, less accurate
- **use_embeddings**: Slower, costs API calls (OpenAI), more accurate

#### Creating Memories

**Option 1: Via API**

```bash
curl -X POST http://localhost:8016/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "fraud_pattern",
    "content": "Merchant XYZ has 80% fraud rate on claims >$5000",
    "tags": ["fraud", "merchant_xyz"],
    "expires_at": "2026-04-01T00:00:00Z"
  }'
```

**Option 2: Via Frontend**

1. Navigate to **Memory Browser** (link in Context Re-engineering tab)
2. Click **Add Memory**
3. Fill in:
   - **Type**: fraud_pattern, user_preference, etc.
   - **Content**: The actual information to remember
   - **Tags**: Keywords for search
   - **Expiration**: When to auto-delete

4. Click **Save**

#### Retrieving Memories (Reactive Mode)

Agents can request memories during execution:

```python
# Agent includes in context
memory_query = {
    "query": "fraud patterns for merchant XYZ",
    "type": "fraud_pattern",
    "tags": ["merchant_xyz"],
    "limit": 5
}
```

The system retrieves matching memories and adds them to the agent's context.

#### Viewing Memories

**Memory Browser Features:**
- Search by keyword
- Filter by type
- Sort by date
- View full content
- Delete expired/unwanted memories
- Batch operations

Access: **Configuration** → **Context Re-engineering** → **View Memories**

### Artifact Versioning

#### What are Artifacts?

Artifacts are large data structures that are too big to embed directly in context:
- Evidence maps (claims processing results)
- Complex documents
- Large JSON structures
- Binary data (PDFs, images)

Instead of including the full content, AgentMesh uses **handles** like:
```
artifact://evidence_map_session_abc/v3
```

#### Why Version Artifacts?

- **Track Changes**: See how evidence evolved over time
- **Rollback**: Revert to previous version if needed
- **Lineage**: Understand parent-child relationships
- **Audit**: Full history for compliance

#### Configuration Options

**1. Enable Versioning**

When enabled, each artifact modification creates a new version.

**2. Max Versions Per Artifact** (default: 10)

- Oldest versions are pruned when limit exceeded
- Recommended: 5-20 depending on storage capacity

**3. Auto-Externalize Threshold** (default: 100 KB)

- Artifacts larger than this are automatically stored externally
- Only handles are included in context
- Recommended: 50-200 KB

#### Example: Viewing Artifact Versions

1. Navigate to **Artifact Version Browser**
2. Select an artifact (e.g., "evidence_map_session_abc")
3. View version timeline:
   - v1 (created: 2026-01-01 10:00)
   - v2 (created: 2026-01-01 10:15, parent: v1)
   - v3 (created: 2026-01-01 10:30, parent: v2)

4. Click version to view:
   - Full content
   - Metadata (size, creation time, tags)
   - Handle string

5. Download or compare versions

### Governance Controls

#### Content Filtering

Automatically removes or masks sensitive information **before** it reaches agents.

**Built-in Rules:**

| Rule | Action | Example |
|------|--------|---------|
| **SSN Masking** | Masks social security numbers | 123-45-6789 → ***-**-**** |
| **Credit Card Masking** | Masks card numbers | 4111-1111-1111-1111 → ****-****-****-**** |
| **Age Filtering** | Removes old observations | Events >30 days old → removed |
| **Debug Log Removal** | Filters debug-level logs | log_level="debug" → excluded |

**Configuration:** Managed in `governance_policies.json` (backend)

#### Governance Limits

Hard limits to prevent runaway resource usage:

| Limit | Default | Purpose |
|-------|---------|---------|
| **Max Memories Per Invocation** | 10 | Prevents memory overload |
| **Max Artifacts Per Invocation** | 5 | Controls artifact loading |
| **Max Context Tokens** | 10,000 | Enforces token budget |

When limits are exceeded:
- System truncates to limit
- Logs governance violation event
- Workflow continues (degraded mode)

#### Governance Audit Trail

All context decisions are logged:
- What was included/excluded
- Why (rationale)
- Token impact
- Governance limits enforced

View in: **Replay** → **Context Engineering** → **Governance Audit** tab

---

## Configuration Reference

### Quick Reference Table

| Setting | Location | Default | Range | Impact |
|---------|----------|---------|-------|--------|
| Context Engineering Enabled | System Config | false | - | Master toggle |
| Compaction Enabled | System Config | false | - | Enables compaction |
| Token Threshold | Context Strategies | 8000 | 100-50000 | Compaction trigger |
| Event Threshold | Context Strategies | 100 | 10-1000 | Compaction trigger |
| Compaction Method | Context Strategies | rule_based | rule_based/llm_based | Summarization approach |
| Memory Enabled | System Config | false | - | Enables memory layer |
| Memory Retention Days | Context Strategies | 90 | 1-365 | Auto-deletion policy |
| Memory Retrieval Mode | Context Strategies | reactive | reactive/proactive | Retrieval behavior |
| Artifact Versioning | System Config | false | - | Enables versioning |
| Max Versions | Context Strategies | 10 | 1-100 | Version limit |
| Externalize Threshold | Context Strategies | 100 | 1-10000 | Auto-externalize (KB) |
| Prefix Caching | Context Strategies | false | - | Cache optimization |

### Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `registries/system_config.json` | Master toggles | JSON |
| `registries/context_strategies.json` | Detailed configuration | JSON |
| `registries/governance_policies.json` | Filtering rules, limits | JSON |

### Export/Import Configuration

**Export:**
1. Go to **Context Re-engineering** tab
2. Click **Export Configuration**
3. Save JSON file

**Import:**
1. Click **Import Configuration**
2. Select previously exported JSON file
3. Review changes
4. Save

**Use Cases:**
- Backup configurations
- Migrate between environments (dev → staging → prod)
- Share configurations with team
- Version control (commit to git)

---

## Monitoring & Troubleshooting

### Monitoring Tools

#### 1. Context Compilation Events

View in real-time SSE stream or replay:
- `context_compiled` - Every context build
- `context_truncated` - When token limits exceeded
- `compaction_triggered` - When compaction runs
- `memory_retrieved` - When memories loaded
- `artifact_version_created` - When artifact saved

#### 2. Token Usage Dashboard

Track token consumption:
- Tokens before/after compilation
- Compaction savings (%)
- Truncation frequency
- Budget allocation breakdown

Access: **Replay** → **Context Engineering** → **Token Usage**

#### 3. Memory Browser

Monitor memory layer:
- Total memories stored
- Expiring soon (within 7 days)
- Retrieval frequency
- Storage size

Access: **Configuration** → **View Memories**

### Common Issues

#### Issue 1: Compaction Not Triggering

**Symptoms:** Events grow unbounded, no compaction events

**Causes:**
- Compaction disabled in system_config
- Thresholds too high
- Processor pipeline disabled

**Fix:**
1. Check system_config.json: `compaction.enabled = true`
2. Lower thresholds (token: 6000, events: 80)
3. Check context_engineering.enabled = true

#### Issue 2: LLM Summarization Costs Too High

**Symptoms:** Unexpected API bills

**Causes:**
- LLM-based compaction on high-volume workflows
- Quality level set to "high"
- Model profile uses expensive model (GPT-4)

**Fix:**
1. Switch to **rule-based** compaction
2. If LLM needed, use quality level: **fast**
3. Select cheaper model profile (GPT-3.5)
4. Increase thresholds (compact less frequently)

#### Issue 3: Proactive Memory Too Many API Calls

**Symptoms:** High OpenAI bills for embeddings

**Causes:**
- Proactive mode with embeddings enabled
- High workflow volume

**Fix:**
1. Switch to **reactive** mode (agent-controlled)
2. Or disable embeddings: `use_embeddings: false`
3. Use keyword similarity instead

#### Issue 4: Validation Errors on Save

**Symptoms:** Red validation errors, can't save

**Common Errors:**
- Budget allocation doesn't sum to 100%
  - Fix: Adjust percentages (e.g., 30 + 50 + 20 = 100)
- Token threshold out of range
  - Fix: Use value between 100-50,000
- LLM model profile not selected
  - Fix: Choose a model profile from dropdown

---

## Best Practices

### 1. Start Small

**Recommended First Steps:**
1. Enable only compaction (rule-based)
2. Monitor token savings for 1 week
3. Gradually enable memory layer (reactive mode)
4. Only enable advanced features after understanding basics

### 2. Right-Size Thresholds

**Compaction Thresholds:**
- For short workflows (<50 events): Don't enable compaction
- For medium workflows (50-150 events): Token: 5000, Events: 100
- For long workflows (>150 events): Token: 8000, Events: 150

**Memory Retention:**
- Short-term insights: 7-30 days
- Seasonal patterns: 90-180 days
- Long-term knowledge: 365 days

### 3. Monitor Costs

**Weekly Checks:**
- Review compaction frequency (too often = thresholds too low)
- Check LLM summarization token usage
- Monitor proactive memory API calls
- Validate token savings justify feature costs

**Budget Allocation:**
- Development: Rule-based compaction only
- Staging: LLM-based compaction (fast quality)
- Production: LLM-based (standard quality) with monitoring

### 4. Governance Best Practices

**Content Filtering:**
- Enable PII masking for production environments
- Disable debug log removal in development
- Age filtering: Match to compliance retention requirements

**Governance Limits:**
- Start with defaults (10 memories, 5 artifacts)
- Increase only if workflows legitimately need more
- Monitor limit violations in audit logs

### 5. Documentation Discipline

**Record Changes:**
- Export configuration before making changes
- Document rationale (why threshold changed)
- Version control configuration files
- Test in dev before applying to prod

### 6. Testing Strategy

**Before Production:**
1. Test with sample data
2. Verify compaction summaries are accurate
3. Check memory retrieval relevance
4. Measure token savings
5. Validate costs are acceptable

---

## FAQ

### General

**Q: Do I need to enable all features?**
A: No. Start with compaction only. Add memory layer when needed. Most users don't need artifact versioning or prefix caching.

**Q: Will context engineering slow down my workflows?**
A: Minimal impact. Rule-based compaction adds <100ms. LLM-based adds 1-3 seconds per compaction. Proactive memory adds <500ms.

**Q: Can I disable context engineering after enabling?**
A: Yes. Set `context_engineering.enabled: false` in system config. Workflows revert to legacy context compilation.

### Compaction

**Q: Will compaction lose important information?**
A: Rule-based: Only removes old, low-priority events. LLM-based: Creates semantic summaries preserving critical info. Enable "Preserve Critical Events" for extra safety.

**Q: How often does compaction run?**
A: Only when thresholds exceeded. Not every workflow. Monitor via events.

**Q: Can I manually trigger compaction?**
A: Yes. Use API: `POST /api/sessions/{session_id}/trigger-compaction`

### Memory Layer

**Q: How much does memory storage cost?**
A: Storage is file-based (free). API costs only if using proactive mode with embeddings (~$0.0001/memory with OpenAI).

**Q: Can memories be shared across workflows?**
A: Yes! That's the purpose. Memories persist beyond sessions and can be retrieved by any agent.

**Q: How do I delete unwanted memories?**
A: Use Memory Browser → Select memory → Delete. Or set expiration date for auto-deletion.

### Artifacts

**Q: Do I need artifact versioning?**
A: Only if you need:
  - Audit trails (compliance)
  - Change tracking
  - Rollback capability

Most simple use cases don't need it.

**Q: What happens if I exceed max versions?**
A: Oldest version is automatically deleted when new version created.

### Costs

**Q: What are the cost drivers?**
A: Ranked by impact:
  1. **LLM-based compaction** (high if frequent)
  2. **Proactive memory with embeddings** (medium)
  3. **Prefix caching** (negative cost - saves money!)
  4. Rule-based compaction (free)
  5. Reactive memory (free)
  6. Artifact versioning (storage only)

**Q: How can I minimize costs?**
A:
  - Use rule-based compaction
  - Use reactive memory mode
  - Disable embeddings
  - Increase compaction thresholds (compact less often)
  - Use fast quality LLM summarization

---

## Getting Help

**Documentation:**
- Developer Guide: `DEVELOPER_GUIDE_CONTEXT_PROCESSORS.md`
- API Reference: `API_CONTEXT_ENGINEERING.md`
- Configuration Reference: `CONFIGURATION_REFERENCE.md`

**Support:**
- GitHub Issues: https://github.com/your-org/agentmesh/issues
- Internal Slack: #agentmesh-support

**Debugging:**
- Enable debug logging: Set `LOG_LEVEL=DEBUG` in .env
- Review session JSONL: `storage/sessions/{session_id}.jsonl`
- Check governance audit events: Filter for `event_type: governance_audit`

---

**End of User Guide**
*Last updated: January 2026*
