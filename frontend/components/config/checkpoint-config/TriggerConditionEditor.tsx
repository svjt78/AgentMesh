import { useState, useEffect } from 'react';
import { validateTriggerCondition } from './validation';

interface TriggerConditionEditorProps {
  value: { type: string; condition?: string } | null | undefined;
  onChange: (condition: { type: string; condition?: string } | null) => void;
}

export default function TriggerConditionEditor({ value, onChange }: TriggerConditionEditorProps) {
  const [enabled, setEnabled] = useState(!!value && value.type !== 'always');
  const [conditionType, setConditionType] = useState(value?.type || 'output_based');
  const [conditionExpr, setConditionExpr] = useState(value?.condition || '');
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (enabled && conditionExpr) {
      const result = validateTriggerCondition(conditionExpr);
      if (!result.valid && result.errors.length > 0) {
        setValidationError(result.errors[0]);
      } else {
        setValidationError(null);
      }
    } else {
      setValidationError(null);
    }
  }, [enabled, conditionExpr]);

  const handleEnabledChange = (checked: boolean) => {
    setEnabled(checked);
    if (!checked) {
      onChange(null);
    } else {
      onChange({
        type: conditionType,
        condition: conditionExpr
      });
    }
  };

  const handleTypeChange = (type: string) => {
    setConditionType(type);
    onChange({
      type,
      condition: conditionExpr
    });
  };

  const handleConditionChange = (expr: string) => {
    setConditionExpr(expr);
    if (enabled) {
      onChange({
        type: conditionType,
        condition: expr
      });
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center">
        <input
          type="checkbox"
          id="trigger-condition-enabled"
          checked={enabled}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <label htmlFor="trigger-condition-enabled" className="ml-2 text-sm font-medium text-gray-700">
          Enable Conditional Trigger
        </label>
      </div>

      {enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Condition Type
            </label>
            <select
              value={conditionType}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="output_based">Output-Based (evaluate against agent output)</option>
              <option value="input_based">Input-Based (evaluate against workflow input)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Condition Expression
            </label>
            <textarea
              value={conditionExpr}
              onChange={(e) => handleConditionChange(e.target.value)}
              placeholder="e.g., fraud_score > 0.7 or claim_amount > 50000"
              rows={2}
              className={`w-full border rounded-md px-3 py-2 text-sm font-mono focus:ring-blue-500 focus:border-blue-500 ${
                validationError ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {validationError && (
              <p className="mt-1 text-xs text-red-600">{validationError}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Examples: <code className="bg-gray-100 px-1 py-0.5 rounded">field &gt; value</code>,{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">field == &quot;value&quot;</code>,{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">nested.field &lt; 100</code>
            </p>
          </div>
        </>
      )}

      {!enabled && (
        <p className="text-sm text-gray-500 italic">
          Checkpoint will always trigger at the specified trigger point
        </p>
      )}
    </div>
  );
}
