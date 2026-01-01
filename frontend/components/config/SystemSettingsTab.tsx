'use client';

import { useState, useEffect } from 'react';
import { apiClient, SystemConfig } from '@/lib/api-client';
import Tooltip from './Tooltip';

export default function SystemSettingsTab() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [editedConfig, setEditedConfig] = useState<SystemConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSystemConfig();
      setConfig(data);
      setEditedConfig(JSON.parse(JSON.stringify(data))); // Deep clone
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editedConfig) return;

    try {
      setSaving(true);
      setError(null);
      await apiClient.updateSystemConfig(editedConfig);
      await loadConfig();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (config) {
      setEditedConfig(JSON.parse(JSON.stringify(config))); // Deep clone
      setError(null);
    }
  };

  const updateField = (category: keyof SystemConfig, field: string, value: any) => {
    if (!editedConfig) return;
    setEditedConfig({
      ...editedConfig,
      [category]: {
        ...(editedConfig[category] as any),
        [field]: value,
      },
    });
  };

  if (loading) {
    return <div className="text-center py-8">Loading system settings...</div>;
  }

  if (!config || !editedConfig) {
    return <div className="text-gray-600 py-8">No system configuration found</div>;
  }

  const hasChanges = JSON.stringify(config) !== JSON.stringify(editedConfig);

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Controllability</h3>
        <p className="text-sm text-blue-700">
          Configure execution limits, timeouts, and safety thresholds for the entire AgentMesh system. These settings
          override environment variables and apply immediately after saving.
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

      <div className="space-y-6">
        {/* Orchestrator Limits */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Orchestrator Limits</h4>
          <p className="text-xs text-gray-500 mb-4">
            Meta-agent ReAct loop controls. Limits how many reasoning cycles the orchestrator can perform when
            coordinating worker agents.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Iterations
                <Tooltip content="Maximum number of reasoning cycles the orchestrator agent can perform when coordinating worker agents. Each iteration involves analyzing the workflow state and deciding which agents to invoke next. Higher values allow more adaptive workflows but increase execution time and cost.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.orchestrator.max_iterations}
                onChange={(e) => updateField('orchestrator', 'max_iterations', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 10</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Iteration Timeout (seconds)
                <Tooltip content="Maximum time in seconds allowed for each orchestrator reasoning cycle. If a single iteration exceeds this timeout, the orchestrator will be forced to complete or terminate. Prevents individual LLM calls from hanging indefinitely.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.orchestrator.iteration_timeout_seconds}
                onChange={(e) => updateField('orchestrator', 'iteration_timeout_seconds', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 30</p>
            </div>
          </div>
        </div>

        {/* Workflow Limits */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Workflow Limits</h4>
          <p className="text-xs text-gray-500 mb-4">
            Session-wide constraints. Hard timeout for entire workflow execution and maximum total agent calls.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Duration (seconds)
                <Tooltip content="Hard timeout in seconds for the entire workflow execution from start to finish. Once this limit is reached, the workflow is terminated regardless of completion state. Critical safety mechanism to prevent runaway workflows and control infrastructure costs.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.workflow.max_duration_seconds}
                onChange={(e) => updateField('workflow', 'max_duration_seconds', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 300 (5 minutes)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Agent Invocations
                <Tooltip content="Maximum total number of worker agent calls allowed within a single workflow session. Prevents excessive agent chaining and helps bound computational costs. Includes both successful and failed agent invocations.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.workflow.max_agent_invocations}
                onChange={(e) => updateField('workflow', 'max_agent_invocations', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 20</p>
            </div>
          </div>
        </div>

        {/* Agent Defaults */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Agent Defaults</h4>
          <p className="text-xs text-gray-500 mb-4">
            Default worker agent limits. Can be overridden per-agent in agent_registry.json.
          </p>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Default Max Iterations
                <Tooltip content="Default maximum ReAct iterations for worker agents unless overridden in agent_registry.json. Each iteration allows an agent to reason, select a tool, and observe results. Higher values enable more complex multi-step reasoning but increase latency.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.agent.default_max_iterations}
                onChange={(e) => updateField('agent', 'default_max_iterations', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 5</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Iteration Timeout (seconds)
                <Tooltip content="Default timeout in seconds for each worker agent ReAct iteration. Applied unless overridden per-agent in the registry. Ensures individual agent tool calls don't exceed reasonable time bounds.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.agent.default_iteration_timeout_seconds}
                onChange={(e) => updateField('agent', 'default_iteration_timeout_seconds', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 30</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Duplicate Invocations
                <Tooltip content="Maximum number of times the orchestrator can invoke the same agent with identical inputs in a single workflow. Prevents infinite loops where an agent is called repeatedly with no progress. Set to 2 to allow one retry.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.agent.max_duplicate_invocations}
                onChange={(e) => updateField('agent', 'max_duplicate_invocations', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 2</p>
            </div>
          </div>
        </div>

        {/* LLM Configuration */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">LLM Configuration</h4>
          <p className="text-xs text-gray-500 mb-4">
            LLM API interaction limits. Controls timeouts, retry behavior, and token budgets for cost control.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Timeout (seconds)
                <Tooltip content="Maximum time in seconds to wait for LLM API responses before timing out. Applies to both orchestrator and agent LLM calls. Increase for complex prompts with large context, but be aware of potential slowdowns during API outages.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.llm.timeout_seconds}
                onChange={(e) => updateField('llm', 'timeout_seconds', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 30</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Retries
                <Tooltip content="Number of automatic retry attempts for failed LLM API calls due to transient errors (rate limits, timeouts, server errors). Uses exponential backoff between retries. Set to 0 to disable retries and fail fast.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.llm.max_retries}
                onChange={(e) => updateField('llm', 'max_retries', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 3</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Tokens Per Request
                <Tooltip content="Maximum number of tokens the LLM can generate in a single API call response. Controls response length and prevents excessively long outputs. Typical agent outputs are 200-500 tokens; orchestrator reasoning is 100-300 tokens.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.llm.max_tokens_per_request}
                onChange={(e) => updateField('llm', 'max_tokens_per_request', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 2000</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Tokens Per Session
                <Tooltip content="Cumulative token budget across all LLM calls in a workflow session for cost control. Includes both prompt and completion tokens. Prevents runaway token usage in complex workflows with many agent invocations.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.llm.max_tokens_per_session}
                onChange={(e) => updateField('llm', 'max_tokens_per_session', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 50000</p>
            </div>
          </div>
        </div>

        {/* Governance Limits */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Governance Limits</h4>
          <p className="text-xs text-gray-500 mb-4">
            Session-wide governance limits for compliance and cost control. Prevents runaway tool/LLM usage.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max Tool Invocations Per Session
                <Tooltip content="Session-wide limit on total tool invocations across all agents. Independent of agent invocation limits. Critical for bounding external API calls and preventing abuse of expensive or rate-limited external services.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.governance.max_tool_invocations_per_session}
                onChange={(e) =>
                  updateField('governance', 'max_tool_invocations_per_session', parseInt(e.target.value))
                }
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 50</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Max LLM Calls Per Session
                <Tooltip content="Session-wide limit on total LLM API calls across orchestrator and all agents. Used for cost control and preventing runaway LLM usage. Each agent iteration typically makes 1 LLM call, orchestrator iterations make 1 call each.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.governance.max_llm_calls_per_session}
                onChange={(e) => updateField('governance', 'max_llm_calls_per_session', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 30</p>
            </div>
          </div>
        </div>

        {/* Safety Thresholds */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Safety Thresholds</h4>
          <p className="text-xs text-gray-500 mb-4">
            Error recovery and circuit breaker mechanisms. Terminates agents stuck in loops or producing invalid
            outputs.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Consecutive No-Progress Limit
                <Tooltip content="Number of consecutive agent iterations with no meaningful progress (same reasoning, same tool calls) before forcing termination. Circuit breaker to detect stuck agents repeating themselves. Typical value: 2-3 iterations.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.safety.consecutive_no_progress_limit}
                onChange={(e) => updateField('safety', 'consecutive_no_progress_limit', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 2</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Malformed Response Limit
                <Tooltip content="Number of consecutive malformed LLM responses (invalid JSON, schema violations) before terminating an agent. Prevents infinite retry loops when the LLM consistently produces invalid output. Typical value: 3 attempts.">
                  <span className="ml-2 text-blue-600 hover:text-blue-800 text-base">ℹ️</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={editedConfig.safety.malformed_response_limit}
                onChange={(e) => updateField('safety', 'malformed_response_limit', parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <p className="text-xs text-gray-500 mt-1">Default: 3</p>
            </div>
          </div>
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
