import { useState, useEffect } from 'react';
import { CheckpointConfig, WorkflowDefinition, HITLRole, TimeoutLimits } from '@/lib/api-client';
import TriggerConditionEditor from './TriggerConditionEditor';
import UISchemaBuilder from './UISchemaBuilder';
import { validateCheckpoint, generateCheckpointId } from './validation';
import { getCheckpointTemplate } from './templates';

interface CheckpointFormProps {
  checkpoint: CheckpointConfig | null;
  workflow: WorkflowDefinition;
  roles: HITLRole[];
  timeoutLimits: TimeoutLimits;
  onSave: (checkpoint: CheckpointConfig) => void;
  onCancel: () => void;
}

export default function CheckpointForm({
  checkpoint,
  workflow,
  roles,
  timeoutLimits,
  onSave,
  onCancel
}: CheckpointFormProps) {
  const isEditing = !!checkpoint;

  const [formData, setFormData] = useState<CheckpointConfig>(
    checkpoint || {
      checkpoint_id: '',
      checkpoint_type: 'approval',
      trigger_point: 'after_agent',
      checkpoint_name: '',
      description: '',
      required_role: roles[0]?.role_id || '',
      timeout_config: {
        enabled: false
      },
      notification_config: {
        enabled: true,
        channels: ['dashboard'],
        urgency: 'normal'
      },
      ui_schema: {
        actions: ['approve', 'reject']
      }
    }
  );

  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Reset form state when checkpoint prop changes
  useEffect(() => {
    if (checkpoint) {
      // Editing existing checkpoint
      setFormData(checkpoint);
    } else {
      // Adding new checkpoint - reset to defaults
      const template = getCheckpointTemplate('approval');
      setFormData({
        checkpoint_id: '',
        checkpoint_type: 'approval',
        trigger_point: 'after_agent',
        checkpoint_name: '',
        description: '',
        required_role: roles[0]?.role_id || '',
        timeout_config: template.timeout_config!,
        notification_config: template.notification_config!,
        ui_schema: template.ui_schema!
      });
    }
    setErrors([]);
    setWarnings([]);
  }, [checkpoint, roles]);

  // Auto-generate checkpoint_id from name
  useEffect(() => {
    if (!isEditing && formData.checkpoint_name && !formData.checkpoint_id) {
      const generatedId = generateCheckpointId(formData.checkpoint_name);
      updateField('checkpoint_id', generatedId);
    }
  }, [formData.checkpoint_name, isEditing]);

  // Apply template when checkpoint type changes
  useEffect(() => {
    if (!isEditing) {
      const template = getCheckpointTemplate(formData.checkpoint_type);
      setFormData(prev => ({
        ...prev,
        timeout_config: template.timeout_config!,
        notification_config: template.notification_config!,
        ui_schema: template.ui_schema!
      }));
    }
  }, [formData.checkpoint_type, isEditing]);

  const updateField = (field: keyof CheckpointConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    const validation = validateCheckpoint(
      formData,
      workflow,
      roles.map(r => r.role_id),
      timeoutLimits
    );

    if (!validation.valid) {
      setErrors(validation.errors);
      setWarnings(validation.warnings || []);
      return;
    }

    setErrors([]);
    setWarnings(validation.warnings || []);
    onSave(formData);
  };

  // Get agents from workflow steps
  const workflowAgents = (workflow.steps || [])
    .map(s => s.agent_id)
    .filter(Boolean);

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">
        {isEditing ? 'Edit Checkpoint' : 'Add New Checkpoint'}
      </h3>

      {/* Errors and Warnings */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-red-800 mb-2">Validation Errors:</h4>
          <ul className="list-disc list-inside space-y-1">
            {errors.map((error, idx) => (
              <li key={idx} className="text-sm text-red-700">{error}</li>
            ))}
          </ul>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">Warnings:</h4>
          <ul className="list-disc list-inside space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-sm text-yellow-700">{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Basic Information */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Basic Information</h4>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Checkpoint ID <span className="text-xs text-gray-500">(auto-generated from name, editable)</span>
          </label>
          <input
            type="text"
            value={formData.checkpoint_id}
            onChange={(e) => updateField('checkpoint_id', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            placeholder="fraud_review"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Checkpoint Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.checkpoint_name}
            onChange={(e) => updateField('checkpoint_name', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            placeholder="High Fraud Score Review"
            maxLength={100}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => updateField('description', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            placeholder="Review fraud detection results when fraud score exceeds threshold"
            rows={3}
          />
        </div>
      </div>

      {/* Trigger Configuration */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Trigger Configuration</h4>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trigger Point <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.trigger_point}
              onChange={(e) => updateField('trigger_point', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="pre_workflow">Before Workflow Starts</option>
              <option value="after_agent">After Specific Agent</option>
              <option value="before_completion">Before Workflow Completes</option>
            </select>
          </div>

          {formData.trigger_point === 'after_agent' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.agent_id || ''}
                onChange={(e) => updateField('agent_id', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">Select agent...</option>
                {workflowAgents.map(agentId => (
                  <option key={agentId} value={agentId}>{agentId}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div>
          <TriggerConditionEditor
            value={formData.trigger_condition}
            onChange={(condition) => updateField('trigger_condition', condition)}
          />
        </div>
      </div>

      {/* Access Control */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Access Control</h4>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Required Role <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.required_role}
            onChange={(e) => updateField('required_role', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">Select role...</option>
            {roles.map(role => (
              <option key={role.role_id} value={role.role_id}>
                {role.role_name} ({role.role_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Checkpoint Type & Behavior */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Checkpoint Type & Behavior</h4>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Checkpoint Type <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.checkpoint_type}
            onChange={(e) => updateField('checkpoint_type', e.target.value as any)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="approval">Approval/Rejection</option>
            <option value="decision">Decision Selection</option>
            <option value="input">Data Input/Correction</option>
            <option value="escalation">Escalation</option>
          </select>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <UISchemaBuilder
            checkpointType={formData.checkpoint_type}
            value={formData.ui_schema}
            onChange={(schema) => updateField('ui_schema', schema)}
            availableRoles={roles.map(r => r.role_id)}
          />
        </div>
      </div>

      {/* Timeout Configuration */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Timeout Configuration</h4>

        <div className="flex items-center mb-3">
          <input
            type="checkbox"
            id="timeout-enabled"
            checked={formData.timeout_config?.enabled || false}
            onChange={(e) => updateField('timeout_config', {
              ...formData.timeout_config,
              enabled: e.target.checked
            })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="timeout-enabled" className="ml-2 text-sm font-medium text-gray-700">
            Enable Timeout
          </label>
        </div>

        {formData.timeout_config?.enabled && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (seconds) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.timeout_config.timeout_seconds || 3600}
                onChange={(e) => updateField('timeout_config', {
                  ...formData.timeout_config,
                  timeout_seconds: parseInt(e.target.value)
                })}
                min={timeoutLimits.min_timeout_seconds}
                max={timeoutLimits.max_timeout_seconds}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">
                Min: {timeoutLimits.min_timeout_seconds}s ({Math.floor(timeoutLimits.min_timeout_seconds / 60)}m),
                Max: {timeoutLimits.max_timeout_seconds}s ({Math.floor(timeoutLimits.max_timeout_seconds / 3600)}h)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Action on Timeout <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.timeout_config.on_timeout || 'auto_approve'}
                onChange={(e) => updateField('timeout_config', {
                  ...formData.timeout_config,
                  on_timeout: e.target.value as any
                })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="auto_approve">Auto-approve and continue</option>
                <option value="auto_reject">Auto-reject</option>
                <option value="cancel_workflow">Cancel workflow</option>
                <option value="proceed_with_default">Use default decision</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Notification Configuration */}
      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-800 border-b pb-2">Notification Configuration</h4>

        <div className="flex items-center mb-3">
          <input
            type="checkbox"
            id="notification-enabled"
            checked={formData.notification_config?.enabled !== false}
            onChange={(e) => updateField('notification_config', {
              ...formData.notification_config,
              enabled: e.target.checked
            })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="notification-enabled" className="ml-2 text-sm font-medium text-gray-700">
            Enable Notifications
          </label>
        </div>

        {formData.notification_config?.enabled !== false && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notification Channels
              </label>
              <div className="space-y-2">
                {['dashboard', 'email', 'slack'].map(channel => (
                  <div key={channel} className="flex items-center">
                    <input
                      type="checkbox"
                      id={`channel-${channel}`}
                      checked={(formData.notification_config?.channels || []).includes(channel)}
                      onChange={(e) => {
                        const currentChannels = formData.notification_config?.channels || [];
                        const newChannels = e.target.checked
                          ? [...currentChannels, channel]
                          : currentChannels.filter(c => c !== channel);
                        updateField('notification_config', {
                          ...formData.notification_config,
                          channels: newChannels
                        });
                      }}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor={`channel-${channel}`} className="ml-2 text-sm text-gray-700 capitalize">
                      {channel}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Urgency
              </label>
              <select
                value={formData.notification_config?.urgency || 'normal'}
                onChange={(e) => updateField('notification_config', {
                  ...formData.notification_config,
                  urgency: e.target.value as any
                })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
        >
          {isEditing ? 'Save Changes' : 'Create Checkpoint'}
        </button>
      </div>
    </div>
  );
}
