# HITL Checkpoint Configuration UI - Design & Implementation Plan

## Document Information

**Created**: 2025-12-31
**Status**: Design Phase
**Related Documents**: [HUMAN_IN_THE_LOOP.md](HUMAN_IN_THE_LOOP.md), [CLAUDE.md](CLAUDE.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Architecture Decisions](#architecture-decisions)
4. [System Design](#system-design)
5. [Component Specifications](#component-specifications)
6. [API Design](#api-design)
7. [Data Models](#data-models)
8. [Validation Rules](#validation-rules)
9. [Implementation Phases](#implementation-phases)
10. [Testing Strategy](#testing-strategy)
11. [Future Enhancements](#future-enhancements)

---

## Overview

### Purpose

This document describes the design and implementation plan for adding a user-friendly configuration interface for HITL (Human-in-the-Loop) checkpoints in AgentMesh. The interface will allow administrators to configure human intervention points within workflows without manually editing JSON files.

### Current State

- HITL checkpoints are configured manually in workflow JSON files (`registries/workflows/*.json`)
- Each workflow has an optional `hitl_checkpoints` array containing checkpoint configurations
- The existing `/hitl` page displays **pending checkpoints** for human resolution
- No UI exists for **configuring** checkpoint definitions

### Desired State

- Administrators can configure checkpoints via a UI in the `/config` page
- All checkpoint properties are editable through form fields and dropdowns
- Changes save directly to workflow JSON files
- The existing `/hitl` page remains unchanged (for operational checkpoint resolution)

---

## Requirements

### Functional Requirements

1. **CRUD Operations**: Create, Read, Update, Delete checkpoint configurations
2. **Per-Workflow Configuration**: Configure checkpoints for specific workflows
3. **Role Selection**: Dropdown populated from governance policies (reviewer, fraud_investigator, claims_adjuster, approver, admin)
4. **Trigger Point Selection**: Dropdown with options (pre_workflow, after_agent, before_completion)
5. **Agent Selection**: Conditional dropdown showing agents from workflow (when trigger_point is after_agent)
6. **Checkpoint Type Selection**: Dropdown with options (approval, decision, input, escalation)
7. **Action Configuration**: Type-specific UI for configuring checkpoint behavior
8. **Text Input**: Text areas for name, description, trigger conditions
9. **Timeout Configuration**: Enable/disable with timeout value and action selection
10. **Validation**: Prevent invalid configurations (missing required fields, out-of-range values)
11. **Persistence**: Save to workflow JSON files in `registries/workflows/`

### Non-Functional Requirements

1. **Consistency**: Follow existing config page patterns (WorkflowsTab, AgentsTab)
2. **Registry-Driven**: Leverage existing workflow CRUD APIs
3. **User-Friendly**: Clear labels, helpful tooltips, validation messages
4. **Responsive**: Support different screen sizes
5. **Maintainable**: Modular component structure, reusable utilities

---

## Architecture Decisions

### Decision 1: UI Placement

**Options Considered**:
- A) Add new tab to existing `/config` page
- B) Create new route `/hitl/configure`
- C) Integrate into existing `/hitl` page

**Decision**: **Option A - New tab in `/config` page**

**Rationale**:
- Checkpoints are configuration data (like agents, tools, workflows)
- Config page already has tabs for all registry types
- Maintains separation of concerns:
  - `/config` → Administrative configuration
  - `/hitl` → Operational checkpoint resolution
- Consistent with existing patterns
- Easy navigation for administrators

### Decision 2: Backend API Strategy

**Options Considered**:
- A) Create checkpoint-specific CRUD endpoints
- B) Use existing workflow update endpoints
- C) Hybrid approach (convenience endpoints + workflow update)

**Decision**: **Option C - Hybrid approach**

**Rationale**:
- Existing `PUT /registries/workflows/{workflow_id}` can handle checkpoint updates
- Optional convenience endpoints improve developer experience
- Helper endpoints for dropdown data (roles, agents) simplify frontend
- Maintains flexibility for future enhancements

### Decision 3: Data Storage

**Options Considered**:
- A) Save to workflow JSON files
- B) Create separate checkpoint registry
- C) Store in database

**Decision**: **Option A - Save to workflow JSON files**

**Rationale**:
- Consistent with registry-driven architecture
- Checkpoints are workflow-specific configuration
- No schema changes required
- Matches current HITL implementation
- Version control friendly (Git-trackable)

### Decision 4: UI Schema Editing

**Options Considered**:
- A) Generic JSON editor for all checkpoint types
- B) Type-specific form builders
- C) Hybrid (simple fields + JSON fallback)

**Decision**: **Option B - Type-specific form builders**

**Rationale**:
- Better user experience for non-technical users
- Prevents common JSON syntax errors
- Type-specific validation
- Can add JSON editor later for advanced users

---

## System Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (/config page)                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  HITL Checkpoints Tab                                  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ Workflow Selector                                │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ Checkpoint List                                  │  │  │
│  │  │  ├─ Checkpoint 1 [Edit] [Delete]                │  │  │
│  │  │  ├─ Checkpoint 2 [Edit] [Delete]                │  │  │
│  │  │  └─ [+ Add Checkpoint]                           │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ Checkpoint Form Modal                            │  │  │
│  │  │  ├─ Basic Info (name, description)               │  │  │
│  │  │  ├─ Trigger Config (point, agent, condition)     │  │  │
│  │  │  ├─ Access Control (role dropdown)               │  │  │
│  │  │  ├─ Checkpoint Type (dropdown)                   │  │  │
│  │  │  ├─ Timeout Config                                │  │  │
│  │  │  ├─ Notification Config                           │  │  │
│  │  │  └─ UI Schema Builder (type-specific)            │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Registry API (/registries)                           │  │
│  │  ├─ GET /workflows → List all workflows              │  │
│  │  ├─ GET /workflows/{id} → Get workflow + checkpoints │  │
│  │  ├─ PUT /workflows/{id} → Update workflow            │  │
│  │  ├─ GET /governance/roles → List HITL roles          │  │
│  │  └─ GET /workflows/{id}/agents → List workflow agents│  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│                            ▼                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Registry Manager                                      │  │
│  │  ├─ Load from registries/workflows/*.json             │  │
│  │  ├─ Validate checkpoint schema                        │  │
│  │  └─ Save to registries/workflows/*.json               │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    File System                               │
│  registries/workflows/                                       │
│  ├─ claims_triage.json                                       │
│  │   └─ hitl_checkpoints: [...]  ← Updated via UI           │
│  └─ other_workflow.json                                      │
│                                                               │
│  registries/governance_policies.json                         │
│  └─ roles: [...] ← Read for role dropdown                    │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Flow

```
User Journey: Configuring a Checkpoint

1. Admin navigates to /config page
2. Clicks "HITL Checkpoints" tab
3. Selects workflow from dropdown (e.g., "Claims Triage Workflow")
4. Views list of existing checkpoints for that workflow
5. Clicks "+ Add Checkpoint" button
6. Modal opens with CheckpointForm
7. Fills in form fields:
   - checkpoint_id: "fraud_review"
   - checkpoint_name: "High Fraud Score Review"
   - description: "Review claims with fraud score > 0.7"
   - trigger_point: "after_agent" (dropdown)
   - agent_id: "fraud_agent" (dropdown, conditional)
   - required_role: "fraud_investigator" (dropdown)
   - checkpoint_type: "decision" (dropdown)
   - trigger_condition: { type: "output_based", condition: "fraud_score > 0.7" }
   - timeout: enabled, 3600 seconds, auto_approve on timeout
   - UI schema: decision_options array
8. Clicks "Save"
9. Frontend validates form
10. Frontend updates workflow.hitl_checkpoints array
11. Frontend calls PUT /registries/workflows/claims_triage with updated workflow
12. Backend validates and saves to registries/workflows/claims_triage.json
13. Modal closes, checkpoint list refreshes
14. New checkpoint appears in list
```

---

## Component Specifications

### 1. HITLCheckpointsTab Component

**Location**: `frontend/components/config/HITLCheckpointsTab.tsx`

**Purpose**: Main tab component for managing checkpoints per workflow

**State**:
```typescript
const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowDefinition | null>(null);
const [checkpoints, setCheckpoints] = useState<CheckpointConfig[]>([]);
const [modalOpen, setModalOpen] = useState(false);
const [editingCheckpoint, setEditingCheckpoint] = useState<CheckpointConfig | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```

**Key Methods**:
- `loadWorkflows()` - Fetch all workflows via `apiClient.listWorkflows()`
- `handleWorkflowSelect(workflowId)` - Load selected workflow and extract checkpoints
- `handleAddCheckpoint()` - Open modal with empty checkpoint template
- `handleEditCheckpoint(checkpoint)` - Open modal with existing checkpoint data
- `handleSaveCheckpoint(checkpoint)` - Update workflow.hitl_checkpoints array and save
- `handleDeleteCheckpoint(checkpointId)` - Remove checkpoint and save workflow
- `validateCheckpoint(checkpoint)` - Client-side validation before save

**UI Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ HITL Checkpoints (3 workflows)              [Workflow ▼]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Claims Triage Workflow - 2 checkpoints                  │
│                                        [+ Add Checkpoint]│
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✓ High Fraud Score Review            [decision]     │ │
│ │   After fraud_agent · fraud_investigator            │ │
│ │   Trigger: fraud_score > 0.7                        │ │
│ │                                   [Edit]  [Delete]  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✓ Final Approval                     [approval]     │ │
│ │   Before completion · approver                      │ │
│ │                                   [Edit]  [Delete]  │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2. CheckpointForm Component

**Location**: `frontend/components/config/checkpoint-config/CheckpointForm.tsx`

**Purpose**: Form for creating/editing checkpoint configurations

**Props**:
```typescript
interface CheckpointFormProps {
  checkpoint: CheckpointConfig | null;  // null for new, populated for edit
  workflow: WorkflowDefinition;
  roles: string[];                      // Available roles from governance
  onSave: (checkpoint: CheckpointConfig) => void;
  onCancel: () => void;
}
```

**Form Sections**:

#### Section 1: Basic Information
```typescript
- checkpoint_id: string (text input, auto-generated or manual)
  - Read-only when editing existing
  - Auto-suggest: snake_case from checkpoint_name

- checkpoint_name: string (text input, required)
  - Label: "Checkpoint Name"
  - Placeholder: "e.g., High Fraud Score Review"
  - Max length: 100 characters

- description: string (textarea, required)
  - Label: "Description"
  - Placeholder: "Explain when and why this checkpoint is triggered..."
  - Rows: 3
```

#### Section 2: Trigger Configuration
```typescript
- trigger_point: enum (dropdown, required)
  - Options:
    * "pre_workflow" → "Before Workflow Starts"
    * "after_agent" → "After Specific Agent"
    * "before_completion" → "Before Workflow Completes"

- agent_id: string (dropdown, conditional)
  - Shown only if trigger_point === "after_agent"
  - Options: workflow.steps.map(s => s.agent_id)
  - Label: "Agent"
  - Required when visible

- trigger_condition: object (optional)
  - Component: TriggerConditionEditor
  - Fields:
    * type: enum ("output_based", "input_based", "always")
    * condition: string (expression, e.g., "fraud_score > 0.7")
```

#### Section 3: Access Control
```typescript
- required_role: string (dropdown, required)
  - Label: "Required Role"
  - Options: roles array from governance policies
  - Options: ["reviewer", "fraud_investigator", "claims_adjuster", "approver", "admin"]
  - Displays role_name from governance, stores role_id
```

#### Section 4: Checkpoint Type & Behavior
```typescript
- checkpoint_type: enum (dropdown, required)
  - Options:
    * "approval" → "Approval/Rejection"
    * "decision" → "Decision Selection"
    * "input" → "Data Input/Correction"
    * "escalation" → "Escalation"
  - Triggers UISchemaBuilder update
```

#### Section 5: Timeout Configuration
```typescript
- timeout_config.enabled: boolean (checkbox)
  - Label: "Enable Timeout"
  - Default: false for input/escalation, true for approval/decision

- timeout_config.timeout_seconds: number (number input)
  - Shown only if enabled
  - Label: "Timeout (seconds)"
  - Min: 300 (from governance policies)
  - Max: 86400 (from governance policies)
  - Default: 3600
  - Helper text: "Min: 5 minutes, Max: 24 hours"

- timeout_config.on_timeout: enum (dropdown)
  - Shown only if enabled
  - Label: "Action on Timeout"
  - Options:
    * "auto_approve" → "Auto-approve and continue"
    * "auto_reject" → "Auto-reject"
    * "cancel_workflow" → "Cancel workflow"
    * "proceed_with_default" → "Use default decision"
```

#### Section 6: Notification Configuration
```typescript
- notification_config.enabled: boolean (checkbox)
  - Label: "Enable Notifications"
  - Default: true

- notification_config.channels: string[] (multi-select checkboxes)
  - Shown only if enabled
  - Options: ["dashboard", "email", "slack"]
  - Default: ["dashboard"]

- notification_config.urgency: enum (dropdown)
  - Shown only if enabled
  - Options: ["low", "normal", "high", "critical"]
  - Default: "normal"
```

#### Section 7: UI Schema Configuration
```typescript
- ui_schema: object (dynamic component)
  - Component: UISchemaBuilder
  - Props: { checkpoint_type, value, onChange }
  - Renders type-specific editor (see UISchemaBuilder spec)
```

**Validation on Save**:
- All required fields present
- agent_id required if trigger_point is "after_agent"
- Timeout within limits if enabled
- UI schema valid for checkpoint type
- Role exists in governance policies
- Checkpoint_id unique within workflow

### 3. UISchemaBuilder Component

**Location**: `frontend/components/config/checkpoint-config/UISchemaBuilder.tsx`

**Purpose**: Type-specific editor for checkpoint UI schema

**Props**:
```typescript
interface UISchemaBuilderProps {
  checkpointType: 'approval' | 'decision' | 'input' | 'escalation';
  value: Record<string, any>;
  onChange: (schema: Record<string, any>) => void;
  agentOutputSchema?: object;  // For field suggestions
}
```

**Type-Specific Editors**:

#### For checkpoint_type === "approval":
```typescript
UI Fields:
- display_evidence_map: boolean (checkbox)
  - Label: "Display Evidence Map"
  - Default: true

- display_agent_chain: boolean (checkbox)
  - Label: "Display Agent Chain"
  - Default: true

- actions: string[] (multi-select checkboxes)
  - Label: "Available Actions"
  - Options: ["approve", "reject", "request_revision", "escalate"]
  - Default: ["approve", "reject", "request_revision"]
  - At least one required
```

#### For checkpoint_type === "decision":
```typescript
UI Fields:
- display_fields: string[] (text input array)
  - Label: "Fields to Display"
  - Placeholder: "fraud_score, fraud_signals, etc."
  - Helper: "Comma-separated field names from agent output"
  - Optional field name suggestions from agentOutputSchema

- decision_options: array (dynamic array builder)
  - Label: "Decision Options"
  - Array item fields:
    * value: string (unique ID)
    * label: string (display text)
    * description: string (help text)
  - [+ Add Option] button
  - [Remove] button per option
  - Drag to reorder
  - At least one option required
```

#### For checkpoint_type === "input":
```typescript
UI Fields:
- editable_fields: string[] (text input array)
  - Label: "Editable Fields"
  - Placeholder: "claim_amount, incident_date, etc."
  - Helper: "Comma-separated field names"
  - At least one required

- display_prior_output: boolean (checkbox)
  - Label: "Display Prior Agent Output"
  - Default: true

- validation_rules: object (JSON editor, optional)
  - Label: "Validation Rules"
  - Component: JsonSchemaEditor
  - Placeholder: { "claim_amount": { "type": "number", "min": 0 } }
```

#### For checkpoint_type === "escalation":
```typescript
UI Fields:
- escalation_targets: string[] (multi-select)
  - Label: "Escalation Target Roles"
  - Options: roles from governance policies
  - At least one required

- escalation_reason_required: boolean (checkbox)
  - Label: "Require Escalation Reason"
  - Default: true
```

### 4. TriggerConditionEditor Component

**Location**: `frontend/components/config/checkpoint-config/TriggerConditionEditor.tsx`

**Purpose**: Edit trigger condition expressions

**Props**:
```typescript
interface TriggerConditionEditorProps {
  value: { type: string; condition: string } | null;
  onChange: (condition: { type: string; condition: string } | null) => void;
  agentOutputSchema?: object;  // For field suggestions
}
```

**Phase 1 Implementation** (Simple):
```typescript
UI:
- enabled: boolean (checkbox)
  - Label: "Enable Conditional Trigger"
  - If unchecked, always triggers

- type: enum (dropdown)
  - Shown only if enabled
  - Options: ["output_based", "input_based"]
  - Default: "output_based"

- condition: string (textarea)
  - Shown only if enabled
  - Label: "Condition Expression"
  - Placeholder: "fraud_score > 0.7"
  - Rows: 2
  - Helper text: "Examples: field > value, field == 'value', nested.field < 100"
  - Syntax validation on blur (basic regex check)
```

**Phase 2 Enhancement** (Visual Builder):
```typescript
UI:
- Visual expression builder:
  - Field dropdown (from agentOutputSchema)
  - Operator dropdown (>, <, ==, !=, >=, <=, contains)
  - Value input (text/number based on field type)
  - [+ Add Condition] for compound expressions (AND/OR)
  - Auto-generates condition string
  - Show generated expression below builder
```

### 5. Validation Utilities

**Location**: `frontend/components/config/checkpoint-config/validation.ts`

**Functions**:

```typescript
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings?: string[];
}

export function validateCheckpoint(
  checkpoint: CheckpointConfig,
  workflow: WorkflowDefinition,
  roles: string[],
  timeoutLimits: { min: number; max: number }
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Required field validation
  if (!checkpoint.checkpoint_id) errors.push("Checkpoint ID is required");
  if (!checkpoint.checkpoint_name) errors.push("Checkpoint name is required");
  if (!checkpoint.description) errors.push("Description is required");
  if (!checkpoint.checkpoint_type) errors.push("Checkpoint type is required");
  if (!checkpoint.trigger_point) errors.push("Trigger point is required");
  if (!checkpoint.required_role) errors.push("Required role is required");

  // Trigger point validation
  if (checkpoint.trigger_point === "after_agent" && !checkpoint.agent_id) {
    errors.push("Agent ID is required when trigger point is 'after_agent'");
  }

  // Agent existence validation
  if (checkpoint.agent_id) {
    const agentExists = workflow.steps.some(s => s.agent_id === checkpoint.agent_id);
    if (!agentExists) {
      errors.push(`Agent '${checkpoint.agent_id}' not found in workflow`);
    }
  }

  // Role validation
  if (!roles.includes(checkpoint.required_role)) {
    errors.push(`Invalid role: '${checkpoint.required_role}'`);
  }

  // Timeout validation
  if (checkpoint.timeout_config?.enabled) {
    const timeout = checkpoint.timeout_config.timeout_seconds;
    if (!timeout) {
      errors.push("Timeout seconds required when timeout enabled");
    } else if (timeout < timeoutLimits.min) {
      errors.push(`Timeout must be at least ${timeoutLimits.min} seconds`);
    } else if (timeout > timeoutLimits.max) {
      errors.push(`Timeout must not exceed ${timeoutLimits.max} seconds`);
    }

    if (!checkpoint.timeout_config.on_timeout) {
      errors.push("Timeout action required when timeout enabled");
    }
  }

  // UI schema validation (type-specific)
  if (checkpoint.checkpoint_type === "decision") {
    const options = checkpoint.ui_schema?.decision_options;
    if (!options || options.length === 0) {
      errors.push("Decision checkpoints require at least one decision option");
    } else {
      options.forEach((opt, idx) => {
        if (!opt.value) errors.push(`Decision option ${idx + 1} missing value`);
        if (!opt.label) errors.push(`Decision option ${idx + 1} missing label`);
      });
    }
  }

  if (checkpoint.checkpoint_type === "input") {
    const fields = checkpoint.ui_schema?.editable_fields;
    if (!fields || fields.length === 0) {
      errors.push("Input checkpoints require at least one editable field");
    }
  }

  if (checkpoint.checkpoint_type === "approval") {
    const actions = checkpoint.ui_schema?.actions;
    if (!actions || actions.length === 0) {
      errors.push("Approval checkpoints require at least one action");
    }
  }

  if (checkpoint.checkpoint_type === "escalation") {
    const targets = checkpoint.ui_schema?.escalation_targets;
    if (!targets || targets.length === 0) {
      errors.push("Escalation checkpoints require at least one escalation target");
    }
  }

  // Uniqueness validation
  const duplicates = workflow.hitl_checkpoints?.filter(
    cp => cp.checkpoint_id === checkpoint.checkpoint_id
  );
  if (duplicates && duplicates.length > 0) {
    // Allow if editing existing
    warnings.push("Checkpoint ID already exists in this workflow");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

export function validateTriggerCondition(condition: string): ValidationResult {
  const errors: string[] = [];

  // Basic expression validation (Phase 1)
  const validPattern = /^[\w.]+\s*[><=!]+\s*[\d.]+$|^[\w.]+\s*[><=!]+\s*"[^"]*"$/;
  if (!validPattern.test(condition.trim())) {
    errors.push("Invalid condition syntax. Expected: field operator value");
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
```

### 6. Default Templates

**Location**: `frontend/components/config/checkpoint-config/templates.ts`

**Templates**:

```typescript
export const CHECKPOINT_TEMPLATES: Record<string, Partial<CheckpointConfig>> = {
  approval: {
    timeout_config: {
      enabled: false
    },
    notification_config: {
      enabled: true,
      channels: ["dashboard"],
      urgency: "normal"
    },
    ui_schema: {
      display_evidence_map: true,
      display_agent_chain: true,
      actions: ["approve", "reject", "request_revision"]
    }
  },

  decision: {
    timeout_config: {
      enabled: true,
      timeout_seconds: 3600,
      on_timeout: "auto_approve"
    },
    notification_config: {
      enabled: true,
      channels: ["dashboard"],
      urgency: "high"
    },
    ui_schema: {
      display_fields: [],
      decision_options: []
    }
  },

  input: {
    timeout_config: {
      enabled: false
    },
    notification_config: {
      enabled: true,
      channels: ["dashboard"],
      urgency: "normal"
    },
    ui_schema: {
      editable_fields: [],
      display_prior_output: true
    }
  },

  escalation: {
    timeout_config: {
      enabled: false
    },
    notification_config: {
      enabled: true,
      channels: ["dashboard", "email"],
      urgency: "critical"
    },
    ui_schema: {
      escalation_targets: [],
      escalation_reason_required: true
    }
  }
};

export function getCheckpointTemplate(
  type: 'approval' | 'decision' | 'input' | 'escalation'
): Partial<CheckpointConfig> {
  return JSON.parse(JSON.stringify(CHECKPOINT_TEMPLATES[type]));
}

export function createEmptyCheckpoint(
  type: 'approval' | 'decision' | 'input' | 'escalation',
  workflowId: string
): CheckpointConfig {
  const template = getCheckpointTemplate(type);

  return {
    checkpoint_id: `${type}_checkpoint_${Date.now()}`,
    checkpoint_type: type,
    trigger_point: 'after_agent',
    checkpoint_name: '',
    description: '',
    required_role: '',
    ...template
  } as CheckpointConfig;
}
```

---

## API Design

### Existing Endpoints (Already Available)

```typescript
GET    /registries/workflows
Response: {
  workflows: WorkflowDefinition[]
}

GET    /registries/workflows/{workflow_id}
Response: WorkflowDefinition (includes hitl_checkpoints array)

PUT    /registries/workflows/{workflow_id}
Body: WorkflowDefinition
Response: { success: boolean, workflow_id: string }

DELETE /registries/workflows/{workflow_id}
Response: { success: boolean }
```

### Optional Convenience Endpoints (Backend Enhancement)

**Add to**: `backend/orchestrator/app/api/registries.py`

```python
@router.get("/workflows/{workflow_id}/checkpoints")
async def get_workflow_checkpoints(workflow_id: str):
    """Get all checkpoint configurations for a specific workflow."""
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "workflow_id": workflow_id,
        "checkpoints": workflow.get("hitl_checkpoints", []),
        "total_count": len(workflow.get("hitl_checkpoints", []))
    }

@router.post("/workflows/{workflow_id}/checkpoints")
async def add_workflow_checkpoint(
    workflow_id: str,
    checkpoint: CheckpointConfigRequest
):
    """Add new checkpoint to workflow."""
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Validate checkpoint
    if "hitl_checkpoints" not in workflow:
        workflow["hitl_checkpoints"] = []

    # Check for duplicate checkpoint_id
    existing = next(
        (cp for cp in workflow["hitl_checkpoints"]
         if cp["checkpoint_id"] == checkpoint.checkpoint_id),
        None
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Checkpoint ID '{checkpoint.checkpoint_id}' already exists"
        )

    # Add checkpoint
    workflow["hitl_checkpoints"].append(checkpoint.dict())

    # Save workflow
    registry.save_workflow(workflow_id, workflow)

    return {
        "success": True,
        "checkpoint_id": checkpoint.checkpoint_id
    }

@router.put("/workflows/{workflow_id}/checkpoints/{checkpoint_id}")
async def update_workflow_checkpoint(
    workflow_id: str,
    checkpoint_id: str,
    checkpoint: CheckpointConfigRequest
):
    """Update existing checkpoint in workflow."""
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    checkpoints = workflow.get("hitl_checkpoints", [])

    # Find and update checkpoint
    for i, cp in enumerate(checkpoints):
        if cp["checkpoint_id"] == checkpoint_id:
            checkpoints[i] = checkpoint.dict()
            workflow["hitl_checkpoints"] = checkpoints
            registry.save_workflow(workflow_id, workflow)
            return {"success": True, "checkpoint_id": checkpoint_id}

    raise HTTPException(status_code=404, detail="Checkpoint not found")

@router.delete("/workflows/{workflow_id}/checkpoints/{checkpoint_id}")
async def delete_workflow_checkpoint(
    workflow_id: str,
    checkpoint_id: str
):
    """Remove checkpoint from workflow."""
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    checkpoints = workflow.get("hitl_checkpoints", [])
    original_count = len(checkpoints)

    # Filter out checkpoint
    workflow["hitl_checkpoints"] = [
        cp for cp in checkpoints if cp["checkpoint_id"] != checkpoint_id
    ]

    if len(workflow["hitl_checkpoints"]) == original_count:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    registry.save_workflow(workflow_id, workflow)
    return {"success": True}

@router.get("/governance/roles")
async def get_hitl_roles():
    """Get all available HITL roles from governance policies."""
    registry = get_registry_manager()
    policies = registry.get_governance_policies()

    hitl_config = policies.get("policies", {}).get("hitl_access_control", {})
    roles = hitl_config.get("roles", [])

    return {
        "roles": [
            {
                "role_id": role["role_id"],
                "role_name": role["role_name"],
                "allowed_checkpoint_types": role.get("allowed_checkpoint_types", []),
                "permissions": role.get("permissions", [])
            }
            for role in roles
        ],
        "timeout_limits": hitl_config.get("checkpoint_timeout_limits", {})
    }

@router.get("/workflows/{workflow_id}/agents")
async def get_workflow_agents(workflow_id: str):
    """Get all agents available in a workflow."""
    registry = get_registry_manager()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    agent_ids = list(set([
        step.get("agent_id")
        for step in workflow.get("steps", [])
        if step.get("agent_id")
    ]))

    # Get agent details
    agents = []
    for agent_id in agent_ids:
        agent = registry.get_agent(agent_id)
        if agent:
            agents.append({
                "agent_id": agent["agent_id"],
                "name": agent.get("name", agent_id),
                "description": agent.get("description", "")
            })

    return {
        "workflow_id": workflow_id,
        "agents": agents
    }
```

**Backend Models** (Add to `backend/orchestrator/app/api/models.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TriggerCondition(BaseModel):
    type: str = Field(..., description="Condition type: output_based, input_based, always")
    condition: Optional[str] = Field(None, description="Expression to evaluate")

class TimeoutConfig(BaseModel):
    enabled: bool = Field(default=False)
    timeout_seconds: Optional[int] = Field(None, ge=300, le=86400)
    on_timeout: Optional[str] = Field(None)

class NotificationConfig(BaseModel):
    enabled: bool = Field(default=True)
    channels: List[str] = Field(default=["dashboard"])
    urgency: str = Field(default="normal")

class CheckpointConfigRequest(BaseModel):
    checkpoint_id: str
    checkpoint_type: str  # approval, decision, input, escalation
    trigger_point: str    # pre_workflow, after_agent, before_completion
    agent_id: Optional[str] = None
    checkpoint_name: str
    description: str
    required_role: str
    trigger_condition: Optional[TriggerCondition] = None
    timeout_config: TimeoutConfig
    notification_config: NotificationConfig
    ui_schema: Dict[str, Any]
```

---

## Data Models

### TypeScript Types (Frontend)

**Location**: `frontend/lib/api-client.ts`

```typescript
export interface CheckpointConfig {
  checkpoint_id: string;
  checkpoint_type: 'approval' | 'decision' | 'input' | 'escalation';
  trigger_point: 'pre_workflow' | 'after_agent' | 'before_completion';
  agent_id?: string;
  checkpoint_name: string;
  description: string;
  required_role: string;
  trigger_condition?: {
    type: 'output_based' | 'input_based' | 'always';
    condition?: string;
  };
  timeout_config: {
    enabled: boolean;
    timeout_seconds?: number;
    on_timeout?: 'auto_approve' | 'auto_reject' | 'cancel_workflow' | 'proceed_with_default';
  };
  notification_config: {
    enabled: boolean;
    channels: string[];
    urgency: 'low' | 'normal' | 'high' | 'critical';
  };
  ui_schema: UISchema;
}

// Discriminated union for type-safe ui_schema
export type UISchema =
  | ApprovalUISchema
  | DecisionUISchema
  | InputUISchema
  | EscalationUISchema;

export interface ApprovalUISchema {
  display_evidence_map?: boolean;
  display_agent_chain?: boolean;
  actions: ('approve' | 'reject' | 'request_revision' | 'escalate')[];
}

export interface DecisionUISchema {
  display_fields: string[];
  decision_options: {
    value: string;
    label: string;
    description: string;
  }[];
}

export interface InputUISchema {
  editable_fields: string[];
  display_prior_output?: boolean;
  validation_rules?: Record<string, any>;
}

export interface EscalationUISchema {
  escalation_targets: string[];
  escalation_reason_required?: boolean;
}

export interface HITLRole {
  role_id: string;
  role_name: string;
  allowed_checkpoint_types: string[];
  permissions: string[];
}

export interface TimeoutLimits {
  min_timeout_seconds: number;
  max_timeout_seconds: number;
  default_timeout_seconds: number;
}
```

### JSON Schema (Workflow Registry)

**Example checkpoint in** `registries/workflows/claims_triage.json`:

```json
{
  "workflow_id": "claims_triage",
  "name": "Claims Triage Workflow",
  "hitl_checkpoints": [
    {
      "checkpoint_id": "fraud_review",
      "checkpoint_type": "decision",
      "trigger_point": "after_agent",
      "agent_id": "fraud_agent",
      "checkpoint_name": "High Fraud Score Review",
      "description": "Review fraud detection results when fraud score exceeds threshold",
      "required_role": "fraud_investigator",
      "trigger_condition": {
        "type": "output_based",
        "condition": "fraud_score > 0.7"
      },
      "timeout_config": {
        "enabled": true,
        "timeout_seconds": 3600,
        "on_timeout": "auto_approve"
      },
      "notification_config": {
        "enabled": true,
        "channels": ["dashboard", "email"],
        "urgency": "high"
      },
      "ui_schema": {
        "display_fields": ["fraud_score", "fraud_signals", "similar_claims"],
        "decision_options": [
          {
            "value": "confirm_fraud",
            "label": "Confirm Fraud - Escalate",
            "description": "High confidence fraud detected - escalate for investigation"
          },
          {
            "value": "false_positive",
            "label": "False Positive - Continue",
            "description": "Legitimate claim, proceed with normal processing"
          },
          {
            "value": "needs_investigation",
            "label": "Requires Further Investigation",
            "description": "Inconclusive - assign to investigator for manual review"
          }
        ]
      }
    }
  ]
}
```

---

## Validation Rules

### Client-Side Validation (Frontend)

**Required Fields**:
- `checkpoint_id`: Must be non-empty, alphanumeric + underscore, unique within workflow
- `checkpoint_name`: Must be non-empty, max 100 characters
- `description`: Must be non-empty
- `checkpoint_type`: Must be valid enum value
- `trigger_point`: Must be valid enum value
- `required_role`: Must exist in governance roles list

**Conditional Required**:
- `agent_id`: Required if `trigger_point === 'after_agent'`
- `timeout_seconds`: Required if `timeout_config.enabled === true`
- `on_timeout`: Required if `timeout_config.enabled === true`

**Range Validation**:
- `timeout_seconds`: Must be between `min_timeout_seconds` and `max_timeout_seconds` from governance policies (default: 300-86400)

**Type-Specific Validation**:
- **approval**: `actions` array must have at least 1 item
- **decision**: `decision_options` array must have at least 1 item; each option must have `value`, `label`, `description`
- **input**: `editable_fields` array must have at least 1 item
- **escalation**: `escalation_targets` array must have at least 1 item

**Reference Validation**:
- `agent_id`: Must exist in `workflow.steps[].agent_id`
- `required_role`: Must exist in governance `roles[].role_id`
- `escalation_targets`: Each role must exist in governance roles

### Server-Side Validation (Backend)

**Additional Backend Checks**:
- Workflow exists
- JSON schema validation for checkpoint structure
- File system permissions for saving workflow JSON
- Prevent duplicate `checkpoint_id` within same workflow
- Validate trigger condition syntax (prevent code injection)

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Basic CRUD functionality working end-to-end

**Tasks**:
1. Update `/config` page to add HITL Checkpoints tab
2. Create `HITLCheckpointsTab` component skeleton
3. Implement workflow selection and checkpoint list display
4. Create `CheckpointForm` with basic fields (no UI schema yet)
5. Implement validation utilities
6. Wire up save/delete operations using existing workflow API
7. Test basic create/edit/delete flow

**Deliverables**:
- ✅ Users can view existing checkpoints for a workflow
- ✅ Users can add new checkpoints with basic fields
- ✅ Users can edit/delete checkpoints
- ✅ Changes save to workflow JSON files

### Phase 2: Type-Specific UI (Week 2)

**Goal**: Complete checkpoint configuration with all field types

**Tasks**:
8. Create `UISchemaBuilder` component
9. Implement type-specific editors (approval, decision, input, escalation)
10. Create `TriggerConditionEditor` (simple textarea version)
11. Create default templates
12. Integrate templates into form (auto-populate on type selection)
13. Enhance validation for UI schema fields
14. Add helpful tooltips and field descriptions

**Deliverables**:
- ✅ All checkpoint types fully configurable
- ✅ UI schema builder working for each type
- ✅ Templates speed up checkpoint creation
- ✅ Comprehensive validation prevents errors

### Phase 3: UX Polish (Week 3)

**Goal**: Production-ready user experience

**Tasks**:
15. Add loading states for all async operations
16. Add error handling and user-friendly error messages
17. Add confirmation dialogs for destructive actions (delete)
18. Add success toast notifications
19. Add inline field validation with real-time feedback
20. Add keyboard shortcuts (Ctrl+S to save, Esc to cancel)
21. Improve layout and styling
22. Add "Clone Checkpoint" feature
23. Add search/filter for checkpoint list

**Deliverables**:
- ✅ Professional, polished UI
- ✅ Clear feedback for all actions
- ✅ Error prevention and recovery
- ✅ Productivity features (clone, keyboard shortcuts)

### Phase 4: Backend Enhancements (Optional)

**Goal**: Optional backend conveniences (if desired)

**Tasks**:
24. Add checkpoint-specific CRUD endpoints to `registries.py`
25. Add `/governance/roles` helper endpoint
26. Add `/workflows/{id}/agents` helper endpoint
27. Add Pydantic models for checkpoint validation
28. Add comprehensive backend validation
29. Add audit logging for checkpoint changes

**Deliverables**:
- ✅ Cleaner frontend code (less data transformation)
- ✅ Backend validation catches errors
- ✅ Audit trail for configuration changes

### Phase 5: Advanced Features (Future)

**Goal**: Enhanced capabilities for power users

**Future Tasks**:
- Visual expression builder for trigger conditions
- Checkpoint testing/preview (simulate trigger without workflow)
- Bulk operations (enable/disable multiple checkpoints)
- Import/export checkpoint configurations
- Checkpoint usage analytics dashboard
- Version control integration (Git diff view)
- Role-based access for checkpoint configuration

---

## Testing Strategy

### Unit Tests

**Frontend Components**:
```typescript
// CheckpointForm.test.tsx
- Renders all fields correctly
- Shows/hides conditional fields based on selections
- Validates required fields on submit
- Calls onSave with correct data structure
- Applies templates when checkpoint type changes
- Validates timeout ranges

// UISchemaBuilder.test.tsx
- Renders correct editor for each checkpoint type
- Updates parent form state on changes
- Validates type-specific requirements
- Handles array operations (add/remove decision options)

// validation.test.ts
- Validates all required fields
- Enforces timeout limits
- Validates agent_id references
- Validates role references
- Checks UI schema completeness
```

**Backend Endpoints**:
```python
# test_checkpoint_endpoints.py
- GET /workflows/{id}/checkpoints returns correct data
- POST adds checkpoint to workflow
- PUT updates existing checkpoint
- DELETE removes checkpoint
- Validates checkpoint schema
- Prevents duplicate checkpoint_id
- Returns 404 for missing workflow
```

### Integration Tests

**End-to-End Flows**:
1. **Create Checkpoint Flow**:
   - Navigate to /config → HITL Checkpoints tab
   - Select workflow
   - Click "Add Checkpoint"
   - Fill in all fields
   - Save
   - Verify checkpoint appears in list
   - Verify JSON file updated on disk

2. **Edit Checkpoint Flow**:
   - Select existing checkpoint
   - Click Edit
   - Modify fields
   - Save
   - Verify changes reflected in list and JSON

3. **Delete Checkpoint Flow**:
   - Click Delete on checkpoint
   - Confirm deletion
   - Verify removed from list and JSON

4. **Validation Flow**:
   - Try to save checkpoint with missing required field
   - Verify error message displayed
   - Correct error
   - Save successfully

### Manual Testing Checklist

- [ ] All dropdown options populated correctly
- [ ] Agent dropdown only shows when trigger_point is "after_agent"
- [ ] Agent dropdown shows agents from selected workflow
- [ ] Role dropdown shows all governance roles
- [ ] Timeout fields hidden when disabled
- [ ] UI schema builder changes when checkpoint type changes
- [ ] Decision options can be added/removed/reordered
- [ ] Validation prevents saving invalid checkpoints
- [ ] Error messages are clear and actionable
- [ ] Success feedback shown after save
- [ ] Checkpoint list updates immediately after changes
- [ ] Can switch between workflows without losing unsaved changes warning
- [ ] Templates auto-populate correctly
- [ ] Timeout validation enforces min/max from governance
- [ ] Trigger condition syntax validation works
- [ ] JSON files saved correctly to registries/workflows/
- [ ] Existing checkpoints loaded and displayed correctly
- [ ] Can edit checkpoints created via UI
- [ ] Can edit checkpoints created manually in JSON
- [ ] No console errors during normal operation
- [ ] Responsive layout works on different screen sizes

---

## Future Enhancements

### Short-Term (3-6 months)

1. **Visual Expression Builder**
   - Drag-and-drop condition builder
   - Field type-aware input controls
   - Compound conditions (AND/OR)
   - Validation against agent output schemas

2. **Checkpoint Testing**
   - "Preview" mode to test checkpoint without workflow
   - Mock agent output injection
   - Validate trigger condition evaluation
   - Test UI rendering

3. **Enhanced UX**
   - Checkpoint templates library (import from gallery)
   - Clone checkpoint to different workflow
   - Checkpoint search and filtering
   - Bulk enable/disable

4. **Analytics**
   - Checkpoint trigger frequency dashboard
   - Average resolution time per checkpoint
   - Timeout rate analysis
   - User performance metrics

### Long-Term (6-12 months)

5. **Advanced Governance**
   - Role-based access to checkpoint configuration
   - Approval workflow for checkpoint changes
   - Checkpoint change history and rollback
   - Configuration drift detection

6. **Integration Features**
   - Export checkpoints to Terraform/IaC
   - Import checkpoints from other systems
   - Sync checkpoints across environments (dev/staging/prod)
   - Webhook notifications for checkpoint events

7. **AI-Assisted Configuration**
   - Suggest checkpoints based on workflow analysis
   - Auto-generate trigger conditions from agent schemas
   - Recommend timeout values based on historical data
   - Anomaly detection (unusual checkpoint patterns)

8. **Mobile Support**
   - Responsive checkpoint configuration UI
   - Mobile-optimized checkpoint resolution
   - Push notifications for pending checkpoints

---

## Appendix

### File Structure

```
AgentMesh/
├── frontend/
│   ├── app/
│   │   └── config/
│   │       └── page.tsx                          # MODIFY: Add HITL Checkpoints tab
│   ├── components/
│   │   └── config/
│   │       ├── HITLCheckpointsTab.tsx           # NEW: Main tab component
│   │       └── checkpoint-config/                # NEW: Checkpoint-specific components
│   │           ├── CheckpointForm.tsx            # NEW: Form for add/edit
│   │           ├── UISchemaBuilder.tsx           # NEW: Type-specific schema editor
│   │           ├── TriggerConditionEditor.tsx    # NEW: Condition expression editor
│   │           ├── validation.ts                 # NEW: Validation utilities
│   │           └── templates.ts                  # NEW: Default templates
│   └── lib/
│       └── api-client.ts                         # MODIFY: Add CheckpointConfig types
│
├── backend/orchestrator/app/
│   ├── api/
│   │   ├── registries.py                         # MODIFY: Add checkpoint endpoints (optional)
│   │   └── models.py                             # MODIFY: Add CheckpointConfig models (optional)
│   └── services/
│       └── registry_manager.py                   # (No changes - already supports workflow save)
│
└── registries/
    ├── workflows/
    │   └── *.json                                # MODIFY: hitl_checkpoints array via UI
    └── governance_policies.json                  # READ: Roles and timeout limits
```

### Key Dependencies

**Frontend**:
- React (already installed)
- TypeScript (already installed)
- Tailwind CSS (already installed)
- No new dependencies required

**Backend**:
- FastAPI (already installed)
- Pydantic (already installed)
- No new dependencies required

### Configuration Files

No new configuration files needed. All data stored in existing registry files:
- `registries/workflows/{workflow_id}.json` - Checkpoint configurations
- `registries/governance_policies.json` - Roles and timeout limits

### Backwards Compatibility

- ✅ Existing workflows without `hitl_checkpoints` continue to work
- ✅ Manually created checkpoints can be edited via UI
- ✅ UI-created checkpoints can be edited manually in JSON
- ✅ Existing `/hitl` page (pending resolution) unchanged
- ✅ No database migrations or schema changes required

---

## Conclusion

This design provides a comprehensive, user-friendly interface for configuring HITL checkpoints in AgentMesh. The implementation follows existing patterns, integrates seamlessly with the registry-driven architecture, and provides a solid foundation for future enhancements.

**Next Steps**:
1. Review and approve this design document
2. Create GitHub issues/tasks for Phase 1
3. Begin implementation with HITLCheckpointsTab component
4. Iterate based on user feedback

**Questions or Feedback**: Please direct to the AgentMesh development team.
