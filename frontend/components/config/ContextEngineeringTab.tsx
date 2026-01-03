'use client';

import { useState, useEffect } from 'react';
import { apiClient, ContextStrategies, SystemConfig, ModelProfile } from '@/lib/api-client';

// Tooltip component for inline help
function Tooltip({ children, text }: { children: React.ReactNode; text: string }) {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block ml-1">
      <span
        className="cursor-help text-gray-400 hover:text-gray-600"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {children}
      </span>
      {show && (
        <div className="absolute z-10 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          {text}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}

// Validation errors display
function ValidationErrors({ errors }: { errors: string[] }) {
  if (errors.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h4 className="text-sm font-semibold text-red-900 mb-2">Configuration Errors:</h4>
      <ul className="list-disc list-inside space-y-1">
        {errors.map((error, i) => (
          <li key={i} className="text-sm text-red-700">
            {error}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ContextEngineeringTab() {
  const [strategies, setStrategies] = useState<ContextStrategies | null>(null);
  const [editedStrategies, setEditedStrategies] = useState<ContextStrategies | null>(null);
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [editedSystemConfig, setEditedSystemConfig] = useState<SystemConfig | null>(null);
  const [modelProfiles, setModelProfiles] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const [strategiesData, systemConfigData, modelsData] = await Promise.all([
        apiClient.getContextStrategies(),
        apiClient.getSystemConfig(),
        apiClient.listModelProfiles(),
      ]);
      setStrategies(strategiesData);
      setEditedStrategies(JSON.parse(JSON.stringify(strategiesData)));
      setSystemConfig(systemConfigData);
      setEditedSystemConfig(JSON.parse(JSON.stringify(systemConfigData)));
      setModelProfiles(modelsData.profiles);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editedStrategies || !editedSystemConfig) return;

    try {
      setSaving(true);
      setError(null);
      await Promise.all([
        apiClient.updateContextStrategies(editedStrategies),
        apiClient.updateSystemConfig(editedSystemConfig),
      ]);
      await loadConfig();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (strategies && systemConfig) {
      setEditedStrategies(JSON.parse(JSON.stringify(strategies)));
      setEditedSystemConfig(JSON.parse(JSON.stringify(systemConfig)));
      setError(null);
    }
  };

  const updateStrategyField = (category: string, field: string, value: any) => {
    if (!editedStrategies) return;
    setEditedStrategies({
      ...editedStrategies,
      [category]: {
        ...(editedStrategies[category as keyof ContextStrategies] as any),
        [field]: value,
      },
    });
  };

  const updateNestedStrategyField = (category: string, subcategory: string, field: string, value: any) => {
    if (!editedStrategies) return;
    const categoryData = editedStrategies[category as keyof ContextStrategies] as any;
    setEditedStrategies({
      ...editedStrategies,
      [category]: {
        ...categoryData,
        [subcategory]: {
          ...(categoryData?.[subcategory] || {}),
          [field]: value,
        },
      },
    });
  };

  const updateSystemConfigField = (category: string, field: string, value: any) => {
    if (!editedSystemConfig) return;
    setEditedSystemConfig({
      ...editedSystemConfig,
      [category]: {
        ...(editedSystemConfig[category as keyof SystemConfig] as any),
        [field]: value,
      },
    });
  };

  // Validate configuration
  const validateConfiguration = (): string[] => {
    const errors: string[] = [];

    if (!editedStrategies) return errors;

    // Validate token threshold
    const tokenThreshold = editedStrategies.compaction?.token_threshold || 0;
    if (tokenThreshold < 100 || tokenThreshold > 50000) {
      errors.push('Token threshold must be between 100 and 50,000');
    }

    // Validate event count threshold
    const eventThreshold = editedStrategies.compaction?.event_count_threshold || 0;
    if (eventThreshold < 10 || eventThreshold > 1000) {
      errors.push('Event count threshold must be between 10 and 1,000');
    }

    // Validate retention days
    const retentionDays = editedStrategies.memory_layer?.retention_days || 0;
    if (retentionDays < 1 || retentionDays > 365) {
      errors.push('Memory retention days must be between 1 and 365');
    }

    // Validate max versions
    const maxVersions = editedStrategies.artifact_management?.max_versions_per_artifact || 0;
    if (maxVersions < 1 || maxVersions > 100) {
      errors.push('Max versions per artifact must be between 1 and 100');
    }

    // Validate externalize threshold
    const externalizeThreshold = editedStrategies.artifact_management?.auto_externalize_threshold_kb || 0;
    if (externalizeThreshold < 1 || externalizeThreshold > 10000) {
      errors.push('Auto-externalize threshold must be between 1 and 10,000 KB');
    }

    // Validate budget allocation (must sum to 100)
    const budgetAlloc = editedStrategies.context_compilation?.default_budget_allocation;
    if (budgetAlloc) {
      const total =
        (budgetAlloc.original_input_percentage || 0) +
        (budgetAlloc.prior_outputs_percentage || 0) +
        (budgetAlloc.observations_percentage || 0);
      if (total !== 100) {
        errors.push(`Budget allocation must sum to 100% (currently: ${total}%)`);
      }
    }

    // Validate LLM summarization if enabled
    const compactionMethod = editedStrategies.compaction?.compaction_method;
    const llmSummarization = editedStrategies.compaction?.llm_summarization;
    if (compactionMethod === 'llm_based' && llmSummarization?.enabled) {
      if (!llmSummarization.model_profile_id) {
        errors.push('LLM summarization requires a model profile to be selected');
      }
    }

    return errors;
  };

  // Update validation errors when configuration changes
  useEffect(() => {
    if (editedStrategies) {
      const errors = validateConfiguration();
      setValidationErrors(errors);
    }
  }, [editedStrategies]);

  // Export configuration to JSON
  const handleExportConfig = () => {
    if (!editedStrategies || !editedSystemConfig) return;

    const exportData = {
      context_strategies: editedStrategies,
      system_config: editedSystemConfig,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agentmesh-context-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Import configuration from JSON
  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target?.result as string);
        if (importData.context_strategies) {
          setEditedStrategies(importData.context_strategies);
        }
        if (importData.system_config) {
          setEditedSystemConfig(importData.system_config);
        }
        setError(null);
      } catch (err: any) {
        setError('Failed to import configuration: ' + err.message);
      }
    };
    reader.readAsText(file);
  };

  // Reset to default values
  const handleResetToDefaults = () => {
    if (!confirm('Are you sure you want to reset all settings to default values? This cannot be undone.')) {
      return;
    }

    // Load defaults from server
    loadConfig();
  };

  if (loading) {
    return <div className="text-center py-8">Loading context engineering settings...</div>;
  }

  if (!strategies || !editedStrategies || !systemConfig || !editedSystemConfig) {
    return (
      <div className="space-y-4 py-8">
        {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}
        <div className="text-gray-600">No context engineering configuration found</div>
      </div>
    );
  }

  const hasChanges =
    JSON.stringify(strategies) !== JSON.stringify(editedStrategies) ||
    JSON.stringify(systemConfig) !== JSON.stringify(editedSystemConfig);

  const compactionMethod = editedStrategies.compaction?.compaction_method || 'rule_based';

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Context Engineering</h3>
        <p className="text-sm text-blue-700">
          Configure context engineering features including compaction, summarization, memory layer, and artifact
          management. These settings control how AgentMesh manages and optimizes context across sessions.
        </p>

        {/* Configuration actions */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={handleExportConfig}
            className="px-3 py-1 text-sm border border-blue-300 text-blue-700 rounded-md hover:bg-blue-100"
          >
            Export Configuration
          </button>
          <label className="px-3 py-1 text-sm border border-blue-300 text-blue-700 rounded-md hover:bg-blue-100 cursor-pointer">
            Import Configuration
            <input
              type="file"
              accept=".json"
              onChange={handleImportConfig}
              className="hidden"
            />
          </label>
          <button
            onClick={handleResetToDefaults}
            className="px-3 py-1 text-sm border border-blue-300 text-blue-700 rounded-md hover:bg-blue-100"
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}

      <ValidationErrors errors={validationErrors} />

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
        {/* Section 1: Compaction Settings */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">
            Compaction Settings
            <Tooltip text="Context compaction summarizes old events to reduce token usage and prevent context overflow in long-running sessions. Recommended for workflows with >100 events.">
              <span className="text-lg">ℹ️</span>
            </Tooltip>
          </h4>
          <p className="text-xs text-gray-500 mb-4">
            Control context compaction to reduce token usage and manage long-running sessions. Compaction reduces the
            size of session event logs through filtering or summarization.
          </p>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="compaction-enabled"
                checked={editedSystemConfig.compaction?.enabled || false}
                onChange={(e) => updateSystemConfigField('compaction', 'enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="compaction-enabled" className="ml-2 text-sm font-medium text-black">
                Enable Context Compaction
              </label>
              <Tooltip text="When enabled, compaction will automatically trigger when token or event count thresholds are exceeded.">
                <span className="text-xs">ℹ️</span>
              </Tooltip>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-1">Compaction Method</label>
              <select
                value={compactionMethod}
                onChange={(e) => updateStrategyField('compaction', 'compaction_method', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              >
                <option value="rule_based">Rule-Based (Fast, Deterministic)</option>
                <option value="llm_based">LLM-Based (Semantic Summarization)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Rule-based: Filters events using retention policies. LLM-based: Uses AI to create semantic summaries.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Token Threshold</label>
                <input
                  type="number"
                  value={editedStrategies.compaction?.token_threshold || 8000}
                  onChange={(e) => updateStrategyField('compaction', 'token_threshold', parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">Trigger compaction when token count exceeds this value</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Event Count Threshold</label>
                <input
                  type="number"
                  value={editedStrategies.compaction?.event_count_threshold || 100}
                  onChange={(e) => updateStrategyField('compaction', 'event_count_threshold', parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">Trigger compaction when event count exceeds this value</p>
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="sliding-window"
                checked={editedStrategies.compaction?.sliding_window?.enabled || false}
                onChange={(e) => updateNestedStrategyField('compaction', 'sliding_window', 'enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="sliding-window" className="ml-2 text-sm font-medium text-black">
                Enable Sliding Window
              </label>
            </div>

            {/* LLM Summarization Subsection */}
            {compactionMethod === 'llm_based' && (
              <div className="mt-4 border-t border-gray-200 pt-4">
                <h5 className="font-medium text-gray-900 mb-3">LLM Summarization Settings</h5>

                {/* Warning about costs */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <span className="text-yellow-600 text-lg flex-shrink-0">⚠️</span>
                    <div>
                      <h6 className="text-sm font-semibold text-yellow-900">Cost Warning</h6>
                      <p className="text-xs text-yellow-700 mt-1">
                        LLM-based summarization requires API calls and will incur additional costs. Each compaction event
                        will consume tokens based on the session history being summarized. Consider using rule-based
                        compaction for cost-sensitive deployments.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="llm-summarization-enabled"
                      checked={editedStrategies.compaction?.llm_summarization?.enabled || false}
                      onChange={(e) =>
                        updateNestedStrategyField('compaction', 'llm_summarization', 'enabled', e.target.checked)
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="llm-summarization-enabled" className="ml-2 text-sm font-medium text-black">
                      Enable LLM Summarization
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-black mb-1">Model Profile</label>
                    <select
                      value={editedStrategies.compaction?.llm_summarization?.model_profile_id || ''}
                      onChange={(e) =>
                        updateNestedStrategyField('compaction', 'llm_summarization', 'model_profile_id', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                    >
                      <option value="">Select a model profile...</option>
                      {modelProfiles.map((profile) => (
                        <option key={profile.profile_id} value={profile.profile_id}>
                          {profile.name} ({profile.provider})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-black mb-1">Quality Level</label>
                    <select
                      value={editedStrategies.compaction?.llm_summarization?.quality_level || 'standard'}
                      onChange={(e) =>
                        updateNestedStrategyField('compaction', 'llm_summarization', 'quality_level', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                    >
                      <option value="fast">Fast (Lower quality, faster)</option>
                      <option value="standard">Standard (Balanced)</option>
                      <option value="high">High (Best quality, slower)</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="preserve-critical"
                      checked={editedStrategies.compaction?.llm_summarization?.preserve_critical_events ?? true}
                      onChange={(e) =>
                        updateNestedStrategyField(
                          'compaction',
                          'llm_summarization',
                          'preserve_critical_events',
                          e.target.checked
                        )
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="preserve-critical" className="ml-2 text-sm font-medium text-black">
                      Preserve Critical Events
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Memory Layer Settings */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">
            Memory Layer Settings
            <Tooltip text="The memory layer stores long-term knowledge beyond individual sessions, enabling agents to learn from past interactions and maintain context across workflows.">
              <span className="text-lg">ℹ️</span>
            </Tooltip>
          </h4>
          <p className="text-xs text-gray-500 mb-4">
            Configure long-term memory storage beyond individual sessions. Memory enables agents to recall information
            from past interactions.
          </p>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="memory-enabled"
                checked={editedSystemConfig.memory?.enabled || false}
                onChange={(e) => updateSystemConfigField('memory', 'enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="memory-enabled" className="ml-2 text-sm font-medium text-black">
                Enable Memory Layer
              </label>
              <Tooltip text="When enabled, agents can store and retrieve memories across sessions. Memories are automatically expired based on retention policy.">
                <span className="text-xs">ℹ️</span>
              </Tooltip>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Retention Days</label>
                <input
                  type="number"
                  value={editedStrategies.memory_layer?.retention_days || 90}
                  onChange={(e) => updateStrategyField('memory_layer', 'retention_days', parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">Auto-delete memories older than this many days</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">
                  Retrieval Mode
                  <Tooltip text="Reactive mode requires agents to explicitly request memories. Proactive mode automatically retrieves relevant memories based on similarity search.">
                    <span className="text-xs ml-1">ℹ️</span>
                  </Tooltip>
                </label>
                <select
                  value={editedStrategies.memory_layer?.retrieval_mode || 'reactive'}
                  onChange={(e) => updateStrategyField('memory_layer', 'retrieval_mode', e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                >
                  <option value="reactive">Reactive (Agent-controlled)</option>
                  <option value="proactive">Proactive (Automatic retrieval)</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Reactive: Agents explicitly request memories. Proactive: System auto-retrieves relevant memories.
                </p>
              </div>
            </div>

            {/* Warning for proactive mode */}
            {editedStrategies.memory_layer?.retrieval_mode === 'proactive' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 text-lg flex-shrink-0">💡</span>
                  <div>
                    <h6 className="text-sm font-semibold text-blue-900">Proactive Memory Info</h6>
                    <p className="text-xs text-blue-700 mt-1">
                      Proactive memory retrieval uses similarity search (keyword-based by default). If embeddings are
                      enabled in system config, OpenAI API calls will be made for each context compilation, which may
                      increase costs. Keyword-based similarity works without API calls but may be less accurate.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section 3: Artifact Settings */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">
            Artifact Settings
            <Tooltip text="Artifacts are large data structures (evidence maps, documents) that can be versioned and externalized to reduce context size. Handles (artifact://id/v1) are used instead of embedding full content.">
              <span className="text-lg">ℹ️</span>
            </Tooltip>
          </h4>
          <p className="text-xs text-gray-500 mb-4">
            Configure artifact versioning and externalization. Artifacts are large objects (evidence maps, documents)
            referenced by handle instead of embedded in context.
          </p>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="versioning-enabled"
                checked={editedSystemConfig.artifacts?.versioning_enabled || false}
                onChange={(e) => updateSystemConfigField('artifacts', 'versioning_enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="versioning-enabled" className="ml-2 text-sm font-medium text-black">
                Enable Artifact Versioning
              </label>
              <Tooltip text="Track changes to artifacts over time. Each modification creates a new version with full lineage tracking.">
                <span className="text-xs">ℹ️</span>
              </Tooltip>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Max Versions Per Artifact</label>
                <input
                  type="number"
                  value={editedStrategies.artifact_management?.max_versions_per_artifact || 10}
                  onChange={(e) =>
                    updateStrategyField('artifact_management', 'max_versions_per_artifact', parseInt(e.target.value))
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">Maximum number of versions to retain per artifact</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Auto-Externalize Threshold (KB)</label>
                <input
                  type="number"
                  value={editedStrategies.artifact_management?.auto_externalize_threshold_kb || 100}
                  onChange={(e) =>
                    updateStrategyField('artifact_management', 'auto_externalize_threshold_kb', parseInt(e.target.value))
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Automatically externalize artifacts larger than this size
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Advanced Settings */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">
            Advanced Settings
            <Tooltip text="Advanced configuration options for power users. These settings affect global context engineering behavior.">
              <span className="text-lg">ℹ️</span>
            </Tooltip>
          </h4>
          <p className="text-xs text-gray-500 mb-4">
            Advanced context engineering features including prefix caching and budget allocation.
          </p>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="prefix-caching-enabled"
                checked={editedStrategies.prefix_caching?.enabled || false}
                onChange={(e) => updateStrategyField('prefix_caching', 'enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="prefix-caching-enabled" className="ml-2 text-sm font-medium text-black">
                Enable Prefix Caching
              </label>
              <Tooltip text="Caches stable context components (system instructions, agent identity) to reduce LLM API costs. Requires provider support (Anthropic Claude).">
                <span className="text-xs ml-1">ℹ️</span>
              </Tooltip>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="context-engineering-enabled"
                checked={
                  (editedSystemConfig.context_engineering?.enabled || false) &&
                  (editedSystemConfig.context_engineering?.processor_pipeline_enabled || false)
                }
                onChange={(e) => {
                  const enabled = e.target.checked;
                  updateSystemConfigField('context_engineering', 'enabled', enabled);
                  updateSystemConfigField('context_engineering', 'processor_pipeline_enabled', enabled);
                }}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="context-engineering-enabled" className="ml-2 text-sm font-medium text-black">
                Enable Context Engineering
              </label>
              <Tooltip text="Enables context engineering and the processor pipeline in one toggle.">
                <span className="text-xs ml-1">ℹ️</span>
              </Tooltip>
            </div>

            <div className="border-t border-gray-200 pt-4 mt-4">
              <h5 className="font-medium text-gray-900 mb-3">Default Budget Allocation</h5>
              <p className="text-xs text-gray-500 mb-3">
                Configure default token budget allocation percentages (must total 100%)
              </p>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-black mb-1">Original Input %</label>
                  <input
                    type="number"
                    value={
                      editedStrategies.context_compilation?.default_budget_allocation?.original_input_percentage || 30
                    }
                    onChange={(e) =>
                      updateNestedStrategyField(
                        'context_compilation',
                        'default_budget_allocation',
                        'original_input_percentage',
                        parseInt(e.target.value)
                      )
                    }
                    min="0"
                    max="100"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-1">Prior Outputs %</label>
                  <input
                    type="number"
                    value={
                      editedStrategies.context_compilation?.default_budget_allocation?.prior_outputs_percentage || 50
                    }
                    onChange={(e) =>
                      updateNestedStrategyField(
                        'context_compilation',
                        'default_budget_allocation',
                        'prior_outputs_percentage',
                        parseInt(e.target.value)
                      )
                    }
                    min="0"
                    max="100"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-1">Observations %</label>
                  <input
                    type="number"
                    value={editedStrategies.context_compilation?.default_budget_allocation?.observations_percentage || 20}
                    onChange={(e) =>
                      updateNestedStrategyField(
                        'context_compilation',
                        'default_budget_allocation',
                        'observations_percentage',
                        parseInt(e.target.value)
                      )
                    }
                    min="0"
                    max="100"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                  />
                </div>
              </div>
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
