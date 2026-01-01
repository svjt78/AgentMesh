import { CheckpointConfig, WorkflowDefinition, TimeoutLimits } from '@/lib/api-client';

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings?: string[];
}

export function validateCheckpoint(
  checkpoint: CheckpointConfig,
  workflow: WorkflowDefinition,
  roles: string[],
  timeoutLimits: TimeoutLimits
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Required field validation
  if (!checkpoint.checkpoint_id) {
    errors.push("Checkpoint ID is required");
  } else {
    // Validate format (alphanumeric + underscore)
    if (!/^[a-zA-Z0-9_]+$/.test(checkpoint.checkpoint_id)) {
      errors.push("Checkpoint ID must contain only letters, numbers, and underscores");
    }
  }

  if (!checkpoint.checkpoint_name) {
    errors.push("Checkpoint name is required");
  } else if (checkpoint.checkpoint_name.length > 100) {
    errors.push("Checkpoint name must be 100 characters or less");
  }

  if (!checkpoint.description) {
    errors.push("Description is required");
  }

  if (!checkpoint.checkpoint_type) {
    errors.push("Checkpoint type is required");
  }

  if (!checkpoint.trigger_point) {
    errors.push("Trigger point is required");
  }

  if (!checkpoint.required_role) {
    errors.push("Required role is required");
  }

  // Trigger point validation
  if (checkpoint.trigger_point === "after_agent" && !checkpoint.agent_id) {
    errors.push("Agent ID is required when trigger point is 'after_agent'");
  }

  // Agent existence validation
  if (checkpoint.agent_id) {
    const agentExists = workflow.steps?.some(s => s.agent_id === checkpoint.agent_id);
    if (!agentExists) {
      errors.push(`Agent '${checkpoint.agent_id}' not found in workflow`);
    }
  }

  // Role validation
  if (checkpoint.required_role && !roles.includes(checkpoint.required_role)) {
    errors.push(`Invalid role: '${checkpoint.required_role}'. Must be one of: ${roles.join(', ')}`);
  }

  // Timeout validation
  if (checkpoint.timeout_config?.enabled) {
    const timeout = checkpoint.timeout_config.timeout_seconds;
    if (!timeout) {
      errors.push("Timeout seconds required when timeout enabled");
    } else {
      if (timeout < timeoutLimits.min_timeout_seconds) {
        errors.push(`Timeout must be at least ${timeoutLimits.min_timeout_seconds} seconds (${Math.floor(timeoutLimits.min_timeout_seconds / 60)} minutes)`);
      }
      if (timeout > timeoutLimits.max_timeout_seconds) {
        errors.push(`Timeout must not exceed ${timeoutLimits.max_timeout_seconds} seconds (${Math.floor(timeoutLimits.max_timeout_seconds / 3600)} hours)`);
      }
    }

    if (!checkpoint.timeout_config.on_timeout) {
      errors.push("Timeout action required when timeout enabled");
    }
  }

  // UI schema validation (type-specific)
  if (checkpoint.checkpoint_type === "decision") {
    const schema = checkpoint.ui_schema as any;
    const options = schema?.decision_options;
    if (!options || !Array.isArray(options) || options.length === 0) {
      errors.push("Decision checkpoints require at least one decision option");
    } else {
      options.forEach((opt, idx) => {
        if (!opt.value) errors.push(`Decision option ${idx + 1} missing value`);
        if (!opt.label) errors.push(`Decision option ${idx + 1} missing label`);
        if (!opt.description) warnings.push(`Decision option ${idx + 1} missing description`);
      });

      // Check for duplicate values
      const values = options.map(o => o.value).filter(Boolean);
      const duplicates = values.filter((v, i) => values.indexOf(v) !== i);
      if (duplicates.length > 0) {
        errors.push(`Duplicate decision option values: ${duplicates.join(', ')}`);
      }
    }
  }

  if (checkpoint.checkpoint_type === "input") {
    const schema = checkpoint.ui_schema as any;
    const fields = schema?.editable_fields;
    if (!fields || !Array.isArray(fields) || fields.length === 0) {
      errors.push("Input checkpoints require at least one editable field");
    }
  }

  if (checkpoint.checkpoint_type === "approval") {
    const schema = checkpoint.ui_schema as any;
    const actions = schema?.actions;
    if (!actions || !Array.isArray(actions) || actions.length === 0) {
      errors.push("Approval checkpoints require at least one action");
    }
  }

  if (checkpoint.checkpoint_type === "escalation") {
    const schema = checkpoint.ui_schema as any;
    const targets = schema?.escalation_targets;
    if (!targets || !Array.isArray(targets) || targets.length === 0) {
      errors.push("Escalation checkpoints require at least one escalation target");
    } else {
      // Validate escalation target roles exist
      targets.forEach(target => {
        if (!roles.includes(target)) {
          errors.push(`Invalid escalation target role: '${target}'`);
        }
      });
    }
  }

  // Uniqueness validation
  const existingCheckpoints = workflow.hitl_checkpoints || [];
  const duplicates = existingCheckpoints.filter(
    cp => cp.checkpoint_id === checkpoint.checkpoint_id
  );

  if (duplicates.length > 0) {
    warnings.push("Checkpoint ID already exists in this workflow. Saving will replace the existing checkpoint.");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings: warnings.length > 0 ? warnings : undefined
  };
}

export function validateTriggerCondition(condition: string): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!condition || condition.trim().length === 0) {
    return { valid: true, errors: [] }; // Empty condition is valid (always trigger)
  }

  // Basic expression validation (Phase 1)
  // Allowed patterns:
  // - field > value
  // - field < value
  // - field == value
  // - field != value
  // - field >= value
  // - field <= value
  // - nested.field operator value
  // - field operator "string value"
  const validPattern = /^[\w.]+\s*([><=!]+)\s*([\d.]+|"[^"]*")$/;

  if (!validPattern.test(condition.trim())) {
    errors.push(
      "Invalid condition syntax. Expected format: field operator value (e.g., 'fraud_score > 0.7' or 'status == \"pending\"')"
    );
  }

  // Additional validation: check for dangerous patterns
  if (condition.includes(';') || condition.includes('--') || condition.toLowerCase().includes('drop')) {
    errors.push("Potentially unsafe condition detected");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings: warnings.length > 0 ? warnings : undefined
  };
}

export function generateCheckpointId(name: string): string {
  // Convert name to snake_case
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 50); // Limit length
}
