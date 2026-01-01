import { CheckpointConfig, ApprovalUISchema, DecisionUISchema, InputUISchema, EscalationUISchema } from '@/lib/api-client';

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
    } as ApprovalUISchema
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
    } as DecisionUISchema
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
    } as InputUISchema
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
    } as EscalationUISchema
  }
};

export function getCheckpointTemplate(
  type: 'approval' | 'decision' | 'input' | 'escalation'
): Partial<CheckpointConfig> {
  // Deep clone to avoid mutation
  return JSON.parse(JSON.stringify(CHECKPOINT_TEMPLATES[type]));
}

export function createEmptyCheckpoint(
  type: 'approval' | 'decision' | 'input' | 'escalation'
): CheckpointConfig {
  const template = getCheckpointTemplate(type);

  return {
    checkpoint_id: '',
    checkpoint_type: type,
    trigger_point: 'after_agent',
    checkpoint_name: '',
    description: '',
    required_role: '',
    ...template
  } as CheckpointConfig;
}
