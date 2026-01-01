import { useState } from 'react';
import { UISchema, ApprovalUISchema, DecisionUISchema, InputUISchema, EscalationUISchema } from '@/lib/api-client';

interface UISchemaBuilderProps {
  checkpointType: 'approval' | 'decision' | 'input' | 'escalation';
  value: UISchema;
  onChange: (schema: UISchema) => void;
  availableRoles?: string[];
}

export default function UISchemaBuilder({
  checkpointType,
  value,
  onChange,
  availableRoles = []
}: UISchemaBuilderProps) {
  if (checkpointType === 'approval') {
    return <ApprovalSchemaEditor value={value as ApprovalUISchema} onChange={onChange} />;
  } else if (checkpointType === 'decision') {
    return <DecisionSchemaEditor value={value as DecisionUISchema} onChange={onChange} />;
  } else if (checkpointType === 'input') {
    return <InputSchemaEditor value={value as InputUISchema} onChange={onChange} />;
  } else if (checkpointType === 'escalation') {
    return <EscalationSchemaEditor value={value as EscalationUISchema} onChange={onChange} availableRoles={availableRoles} />;
  }

  return null;
}

// Approval Schema Editor
function ApprovalSchemaEditor({ value, onChange }: { value: ApprovalUISchema; onChange: (schema: any) => void }) {
  const allActions = ['approve', 'reject', 'request_revision', 'escalate'];

  const toggleAction = (action: string) => {
    const currentActions = value.actions || [];
    const newActions = currentActions.includes(action as any)
      ? currentActions.filter(a => a !== action)
      : [...currentActions, action as any];

    onChange({ ...value, actions: newActions });
  };

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-gray-700">Approval UI Configuration</h4>

      <div className="space-y-2">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="display-evidence-map"
            checked={value.display_evidence_map || false}
            onChange={(e) => onChange({ ...value, display_evidence_map: e.target.checked })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="display-evidence-map" className="ml-2 text-sm text-gray-700">
            Display Evidence Map
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="display-agent-chain"
            checked={value.display_agent_chain || false}
            onChange={(e) => onChange({ ...value, display_agent_chain: e.target.checked })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="display-agent-chain" className="ml-2 text-sm text-gray-700">
            Display Agent Chain
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Available Actions (select at least one)
        </label>
        <div className="space-y-2">
          {allActions.map(action => (
            <div key={action} className="flex items-center">
              <input
                type="checkbox"
                id={`action-${action}`}
                checked={(value.actions || []).includes(action as any)}
                onChange={() => toggleAction(action)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
              <label htmlFor={`action-${action}`} className="ml-2 text-sm text-gray-700 capitalize">
                {action.replace('_', ' ')}
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Decision Schema Editor
function DecisionSchemaEditor({ value, onChange }: { value: DecisionUISchema; onChange: (schema: any) => void }) {
  const [newOptionValue, setNewOptionValue] = useState('');
  const [newOptionLabel, setNewOptionLabel] = useState('');
  const [newOptionDescription, setNewOptionDescription] = useState('');

  const displayFields = value.display_fields || [];
  const options = value.decision_options || [];

  const handleDisplayFieldsChange = (fieldsStr: string) => {
    const fields = fieldsStr.split(',').map(f => f.trim()).filter(Boolean);
    onChange({ ...value, display_fields: fields });
  };

  const addOption = () => {
    if (!newOptionValue || !newOptionLabel) return;

    const newOption = {
      value: newOptionValue,
      label: newOptionLabel,
      description: newOptionDescription
    };

    onChange({
      ...value,
      decision_options: [...options, newOption]
    });

    setNewOptionValue('');
    setNewOptionLabel('');
    setNewOptionDescription('');
  };

  const removeOption = (index: number) => {
    const newOptions = options.filter((_, i) => i !== index);
    onChange({ ...value, decision_options: newOptions });
  };

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-gray-700">Decision UI Configuration</h4>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Fields to Display (comma-separated)
        </label>
        <input
          type="text"
          value={displayFields.join(', ')}
          onChange={(e) => handleDisplayFieldsChange(e.target.value)}
          placeholder="fraud_score, fraud_signals, similar_claims"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
        <p className="mt-1 text-xs text-gray-500">
          Agent output fields to show in the checkpoint UI
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Decision Options (at least one required)
        </label>

        {options.length > 0 && (
          <div className="space-y-2 mb-3">
            {options.map((option, index) => (
              <div key={index} className="flex items-start gap-2 p-3 bg-gray-50 rounded-md">
                <div className="flex-1">
                  <div className="font-medium text-sm">{option.label}</div>
                  <div className="text-xs text-gray-600">Value: {option.value}</div>
                  {option.description && (
                    <div className="text-xs text-gray-500 mt-1">{option.description}</div>
                  )}
                </div>
                <button
                  onClick={() => removeOption(index)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="border border-gray-300 rounded-md p-3 space-y-2">
          <input
            type="text"
            value={newOptionValue}
            onChange={(e) => setNewOptionValue(e.target.value)}
            placeholder="Option value (e.g., confirm_fraud)"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <input
            type="text"
            value={newOptionLabel}
            onChange={(e) => setNewOptionLabel(e.target.value)}
            placeholder="Option label (e.g., Confirm Fraud - Escalate)"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <textarea
            value={newOptionDescription}
            onChange={(e) => setNewOptionDescription(e.target.value)}
            placeholder="Option description (optional)"
            rows={2}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={addOption}
            disabled={!newOptionValue || !newOptionLabel}
            className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-300"
          >
            + Add Option
          </button>
        </div>
      </div>
    </div>
  );
}

// Input Schema Editor
function InputSchemaEditor({ value, onChange }: { value: InputUISchema; onChange: (schema: any) => void }) {
  const editableFields = value.editable_fields || [];

  const handleEditableFieldsChange = (fieldsStr: string) => {
    const fields = fieldsStr.split(',').map(f => f.trim()).filter(Boolean);
    onChange({ ...value, editable_fields: fields });
  };

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-gray-700">Input UI Configuration</h4>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Editable Fields (comma-separated, at least one required)
        </label>
        <input
          type="text"
          value={editableFields.join(', ')}
          onChange={(e) => handleEditableFieldsChange(e.target.value)}
          placeholder="claim_amount, incident_date, description"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
        <p className="mt-1 text-xs text-gray-500">
          Fields that users can edit or supplement during the checkpoint
        </p>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="display-prior-output"
          checked={value.display_prior_output !== false} // default to true
          onChange={(e) => onChange({ ...value, display_prior_output: e.target.checked })}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
        />
        <label htmlFor="display-prior-output" className="ml-2 text-sm text-gray-700">
          Display Prior Agent Output
        </label>
      </div>
    </div>
  );
}

// Escalation Schema Editor
function EscalationSchemaEditor({
  value,
  onChange,
  availableRoles
}: {
  value: EscalationUISchema;
  onChange: (schema: any) => void;
  availableRoles: string[];
}) {
  const escalationTargets = value.escalation_targets || [];

  const toggleRole = (roleId: string) => {
    const newTargets = escalationTargets.includes(roleId)
      ? escalationTargets.filter(r => r !== roleId)
      : [...escalationTargets, roleId];

    onChange({ ...value, escalation_targets: newTargets });
  };

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-gray-700">Escalation UI Configuration</h4>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Escalation Target Roles (select at least one)
        </label>
        <div className="space-y-2">
          {availableRoles.length > 0 ? (
            availableRoles.map(role => (
              <div key={role} className="flex items-center">
                <input
                  type="checkbox"
                  id={`escalation-role-${role}`}
                  checked={escalationTargets.includes(role)}
                  onChange={() => toggleRole(role)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <label htmlFor={`escalation-role-${role}`} className="ml-2 text-sm text-gray-700">
                  {role}
                </label>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500">No roles available</p>
          )}
        </div>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="escalation-reason-required"
          checked={value.escalation_reason_required !== false} // default to true
          onChange={(e) => onChange({ ...value, escalation_reason_required: e.target.checked })}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
        />
        <label htmlFor="escalation-reason-required" className="ml-2 text-sm text-gray-700">
          Require Escalation Reason
        </label>
      </div>
    </div>
  );
}
