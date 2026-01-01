'use client';

import { useState, useEffect } from 'react';
import { apiClient, GovernancePolicies } from '@/lib/api-client';

export default function GovernanceTab() {
  const [policies, setPolicies] = useState<GovernancePolicies | null>(null);
  const [editedPolicies, setEditedPolicies] = useState<GovernancePolicies | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['agent_invocation_access']));

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getGovernancePolicies();
      setPolicies(data);
      setEditedPolicies(JSON.parse(JSON.stringify(data))); // Deep clone
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editedPolicies) return;

    try {
      setSaving(true);
      setError(null);
      await apiClient.updateGovernancePolicies(editedPolicies);
      await loadPolicies();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (policies) {
      setEditedPolicies(JSON.parse(JSON.stringify(policies))); // Deep clone
      setError(null);
    }
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const updatePolicyField = (policyKey: string, field: string, value: any) => {
    if (!editedPolicies) return;
    setEditedPolicies({
      ...editedPolicies,
      policies: {
        ...editedPolicies.policies,
        [policyKey]: {
          ...editedPolicies.policies[policyKey],
          [field]: value,
        },
      },
    });
  };

  const addAgentInvocationRule = () => {
    if (!editedPolicies) return;
    const currentRules = editedPolicies.policies.agent_invocation_access?.rules || [];
    updatePolicyField('agent_invocation_access', 'rules', [
      ...currentRules,
      { agent_id: '', allowed_agents: [], denied_agents: [] },
    ]);
  };

  const updateAgentInvocationRule = (index: number, field: string, value: any) => {
    if (!editedPolicies) return;
    const rules = [...(editedPolicies.policies.agent_invocation_access?.rules || [])];
    rules[index] = { ...rules[index], [field]: value };
    updatePolicyField('agent_invocation_access', 'rules', rules);
  };

  const removeAgentInvocationRule = (index: number) => {
    if (!editedPolicies) return;
    const rules = [...(editedPolicies.policies.agent_invocation_access?.rules || [])];
    rules.splice(index, 1);
    updatePolicyField('agent_invocation_access', 'rules', rules);
  };

  const addToolAccessRule = () => {
    if (!editedPolicies) return;
    const currentRules = editedPolicies.policies.agent_tool_access?.rules || [];
    updatePolicyField('agent_tool_access', 'rules', [
      ...currentRules,
      { agent_id: '', allowed_tools: [], denied_tools: [] },
    ]);
  };

  const updateToolAccessRule = (index: number, field: string, value: any) => {
    if (!editedPolicies) return;
    const rules = [...(editedPolicies.policies.agent_tool_access?.rules || [])];
    rules[index] = { ...rules[index], [field]: value };
    updatePolicyField('agent_tool_access', 'rules', rules);
  };

  const removeToolAccessRule = (index: number) => {
    if (!editedPolicies) return;
    const rules = [...(editedPolicies.policies.agent_tool_access?.rules || [])];
    rules.splice(index, 1);
    updatePolicyField('agent_tool_access', 'rules', rules);
  };

  const addIterationOverride = () => {
    if (!editedPolicies) return;
    const currentOverrides = editedPolicies.policies.iteration_limits?.agent_overrides || [];
    updatePolicyField('iteration_limits', 'agent_overrides', [
      ...currentOverrides,
      { agent_id: '', max_iterations: 5 },
    ]);
  };

  const updateIterationOverride = (index: number, field: string, value: any) => {
    if (!editedPolicies) return;
    const overrides = [...(editedPolicies.policies.iteration_limits?.agent_overrides || [])];
    overrides[index] = { ...overrides[index], [field]: value };
    updatePolicyField('iteration_limits', 'agent_overrides', overrides);
  };

  const removeIterationOverride = (index: number) => {
    if (!editedPolicies) return;
    const overrides = [...(editedPolicies.policies.iteration_limits?.agent_overrides || [])];
    overrides.splice(index, 1);
    updatePolicyField('iteration_limits', 'agent_overrides', overrides);
  };

  if (loading) {
    return <div className="text-center py-8">Loading governance policies...</div>;
  }

  if (error && !policies) {
    return <div className="text-red-600 py-8">Error: {error}</div>;
  }

  if (!policies || !editedPolicies) {
    return <div className="text-gray-600 py-8">No governance policies found</div>;
  }

  const hasChanges = JSON.stringify(policies) !== JSON.stringify(editedPolicies);

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Governance Policies</h3>
        <p className="text-sm text-blue-700">
          Governance policies control agent and tool access, execution limits, and compliance rules. Changes are applied
          immediately after saving.
        </p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}

      {hasChanges && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex justify-between items-center">
          <span className="text-sm text-yellow-700">You have unsaved changes</span>
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="px-3 py-1 text-sm border border-yellow-300 rounded-md hover:bg-yellow-100"
            >
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {/* Agent Invocation Access */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('agent_invocation_access')}
            className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          >
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">Agent Invocation Access</h3>
              <p className="text-xs text-gray-600">
                {editedPolicies.policies.agent_invocation_access?.description}
              </p>
            </div>
            <span className="text-gray-500">{expandedSections.has('agent_invocation_access') ? '▼' : '▶'}</span>
          </button>

          {expandedSections.has('agent_invocation_access') && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Enforcement Level</label>
                <select
                  value={editedPolicies.policies.agent_invocation_access?.enforcement_level || 'strict'}
                  onChange={(e) => updatePolicyField('agent_invocation_access', 'enforcement_level', e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                >
                  <option value="strict">Strict</option>
                  <option value="permissive">Permissive</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-900 text-sm">Rules</h4>
                  <button
                    onClick={addAgentInvocationRule}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    + Add Rule
                  </button>
                </div>

                {editedPolicies.policies.agent_invocation_access?.rules?.map((rule: any, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3 mb-2 space-y-2">
                    <div className="flex justify-between items-start">
                      <div className="flex-1 space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Agent ID</label>
                          <input
                            type="text"
                            value={rule.agent_id}
                            onChange={(e) => updateAgentInvocationRule(index, 'agent_id', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., orchestrator_agent"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Allowed Agents (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={rule.allowed_agents?.join(', ') || ''}
                            onChange={(e) =>
                              updateAgentInvocationRule(
                                index,
                                'allowed_agents',
                                e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                              )
                            }
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., intake_agent, coverage_agent"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Denied Agents (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={rule.denied_agents?.join(', ') || ''}
                            onChange={(e) =>
                              updateAgentInvocationRule(
                                index,
                                'denied_agents',
                                e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                              )
                            }
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., orchestrator_agent"
                          />
                        </div>
                      </div>

                      <button
                        onClick={() => removeAgentInvocationRule(index)}
                        className="ml-2 px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Agent Tool Access */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('agent_tool_access')}
            className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          >
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">Agent Tool Access</h3>
              <p className="text-xs text-gray-600">{editedPolicies.policies.agent_tool_access?.description}</p>
            </div>
            <span className="text-gray-500">{expandedSections.has('agent_tool_access') ? '▼' : '▶'}</span>
          </button>

          {expandedSections.has('agent_tool_access') && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enforcement Level</label>
                <select
                  value={editedPolicies.policies.agent_tool_access?.enforcement_level || 'strict'}
                  onChange={(e) => updatePolicyField('agent_tool_access', 'enforcement_level', e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="strict">Strict</option>
                  <option value="permissive">Permissive</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-900 text-sm">Rules</h4>
                  <button
                    onClick={addToolAccessRule}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    + Add Rule
                  </button>
                </div>

                {editedPolicies.policies.agent_tool_access?.rules?.map((rule: any, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3 mb-2 space-y-2">
                    <div className="flex justify-between items-start">
                      <div className="flex-1 space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Agent ID</label>
                          <input
                            type="text"
                            value={rule.agent_id}
                            onChange={(e) => updateToolAccessRule(index, 'agent_id', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., fraud_agent"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Allowed Tools (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={rule.allowed_tools?.join(', ') || ''}
                            onChange={(e) =>
                              updateToolAccessRule(
                                index,
                                'allowed_tools',
                                e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                              )
                            }
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., fraud_rules, similarity"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Denied Tools (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={rule.denied_tools?.join(', ') || ''}
                            onChange={(e) =>
                              updateToolAccessRule(
                                index,
                                'denied_tools',
                                e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                              )
                            }
                            className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                            placeholder="e.g., policy_snapshot, decision_rules"
                          />
                        </div>
                      </div>

                      <button
                        onClick={() => removeToolAccessRule(index)}
                        className="ml-2 px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Iteration Limits */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('iteration_limits')}
            className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          >
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">Iteration Limits</h3>
              <p className="text-xs text-gray-600">{editedPolicies.policies.iteration_limits?.description}</p>
            </div>
            <span className="text-gray-500">{expandedSections.has('iteration_limits') ? '▼' : '▶'}</span>
          </button>

          {expandedSections.has('iteration_limits') && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Global Max Iterations</label>
                <input
                  type="number"
                  value={editedPolicies.policies.iteration_limits?.global_max_iterations || 5}
                  onChange={(e) =>
                    updatePolicyField('iteration_limits', 'global_max_iterations', parseInt(e.target.value))
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-900 text-sm">Agent Overrides</h4>
                  <button
                    onClick={addIterationOverride}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    + Add Override
                  </button>
                </div>

                {editedPolicies.policies.iteration_limits?.agent_overrides?.map((override: any, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3 mb-2">
                    <div className="flex gap-2 items-start">
                      <div className="flex-1">
                        <label className="block text-xs font-medium text-gray-700 mb-1">Agent ID</label>
                        <input
                          type="text"
                          value={override.agent_id}
                          onChange={(e) => updateIterationOverride(index, 'agent_id', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                          placeholder="e.g., fraud_agent"
                        />
                      </div>

                      <div className="flex-1">
                        <label className="block text-xs font-medium text-gray-700 mb-1">Max Iterations</label>
                        <input
                          type="number"
                          value={override.max_iterations}
                          onChange={(e) => updateIterationOverride(index, 'max_iterations', parseInt(e.target.value))}
                          className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                        />
                      </div>

                      <button
                        onClick={() => removeIterationOverride(index)}
                        className="mt-5 px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Execution Constraints */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('execution_constraints')}
            className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          >
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">Execution Constraints</h3>
              <p className="text-xs text-gray-600">{editedPolicies.policies.execution_constraints?.description}</p>
            </div>
            <span className="text-gray-500">{expandedSections.has('execution_constraints') ? '▼' : '▶'}</span>
          </button>

          {expandedSections.has('execution_constraints') && (
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Workflow Duration (seconds)
                  </label>
                  <input
                    type="number"
                    value={editedPolicies.policies.execution_constraints?.max_workflow_duration_seconds || 300}
                    onChange={(e) =>
                      updatePolicyField('execution_constraints', 'max_workflow_duration_seconds', parseInt(e.target.value))
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Tool Invocations Per Session
                  </label>
                  <input
                    type="number"
                    value={editedPolicies.policies.execution_constraints?.max_tool_invocations_per_session || 50}
                    onChange={(e) =>
                      updatePolicyField('execution_constraints', 'max_tool_invocations_per_session', parseInt(e.target.value))
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max LLM Calls Per Session</label>
                  <input
                    type="number"
                    value={editedPolicies.policies.execution_constraints?.max_llm_calls_per_session || 30}
                    onChange={(e) =>
                      updatePolicyField('execution_constraints', 'max_llm_calls_per_session', parseInt(e.target.value))
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {hasChanges && (
        <div className="sticky bottom-0 bg-white border-t border-gray-200 py-4 flex justify-end gap-2">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Reset Changes
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      )}
    </div>
  );
}
