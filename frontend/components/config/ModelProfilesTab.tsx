'use client';

import { useState, useEffect } from 'react';
import { apiClient, ModelProfile } from '@/lib/api-client';

export default function ModelProfilesTab() {
  const [profiles, setProfiles] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<ModelProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const emptyProfile: ModelProfile = {
    profile_id: '',
    name: '',
    description: '',
    provider: 'openai',
    model_name: '',
    intended_usage: 'general_reasoning',
    parameters: {
      temperature: 0.3,
      max_tokens: 2000,
      top_p: 1.0,
      frequency_penalty: 0.0,
      presence_penalty: 0.0,
    },
    json_mode: true,
    constraints: {
      max_context_tokens: 16385,
      max_output_tokens: 4096,
    },
    retry_policy: {
      max_retries: 3,
      backoff_multiplier: 2,
      initial_delay_ms: 1000,
    },
    timeout_seconds: 30,
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listModelProfiles();
      setProfiles(data.profiles);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingProfile(emptyProfile);
    setModalOpen(true);
  };

  const handleEdit = (profile: ModelProfile) => {
    setEditingProfile({ ...profile });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!editingProfile) return;

    try {
      setError(null);
      const isNew = !profiles.find((p) => p.profile_id === editingProfile.profile_id);

      if (isNew) {
        await apiClient.createModelProfile(editingProfile);
      } else {
        await apiClient.updateModelProfile(editingProfile.profile_id, editingProfile);
      }

      await loadProfiles();
      setModalOpen(false);
      setEditingProfile(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (profileId: string) => {
    if (!confirm(`Delete model profile '${profileId}'? This cannot be undone.`)) return;

    try {
      setError(null);
      await apiClient.deleteModelProfile(profileId);
      await loadProfiles();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const updateField = (field: keyof ModelProfile, value: any) => {
    if (!editingProfile) return;
    setEditingProfile({ ...editingProfile, [field]: value });
  };

  const updateNestedField = (parent: 'parameters' | 'constraints' | 'retry_policy', field: string, value: any) => {
    if (!editingProfile) return;
    setEditingProfile({
      ...editingProfile,
      [parent]: {
        ...editingProfile[parent],
        [field]: value,
      },
    });
  };

  if (loading) {
    return <div className="text-center py-8">Loading model profiles...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Model Profiles ({profiles.length})</h2>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + Add Model Profile
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      <div className="grid gap-4">
        {profiles.map((profile) => (
          <div key={profile.profile_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900">{profile.name}</h3>
                  <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                    {profile.provider}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
                <div className="mt-2 grid grid-cols-2 gap-4 text-xs text-gray-500">
                  <span>Model: {profile.model_name}</span>
                  <span>Usage: {profile.intended_usage}</span>
                  <span>Timeout: {profile.timeout_seconds}s</span>
                  <span>JSON Mode: {profile.json_mode ? 'Yes' : 'No'}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(profile)}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(profile.profile_id)}
                  className="px-3 py-1 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Edit/Create Modal */}
      {modalOpen && editingProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {profiles.find((p) => p.profile_id === editingProfile.profile_id)
                  ? 'Edit Model Profile'
                  : 'Create Model Profile'}
              </h3>
            </div>

            <div className="px-6 py-4 space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900 text-sm">Basic Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Profile ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={editingProfile.profile_id}
                    onChange={(e) => updateField('profile_id', e.target.value)}
                    disabled={profiles.some((p) => p.profile_id === editingProfile.profile_id)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm disabled:bg-gray-100"
                    placeholder="e.g., custom_gpt4"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={editingProfile.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    placeholder="e.g., Custom GPT-4"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editingProfile.description}
                    onChange={(e) => updateField('description', e.target.value)}
                    rows={2}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    placeholder="Model description..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Provider <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={editingProfile.provider}
                      onChange={(e) => updateField('provider', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Model Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={editingProfile.model_name}
                      onChange={(e) => updateField('model_name', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="e.g., gpt-4-turbo"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Intended Usage</label>
                    <input
                      type="text"
                      value={editingProfile.intended_usage}
                      onChange={(e) => updateField('intended_usage', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="e.g., complex_reasoning"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                    <input
                      type="number"
                      value={editingProfile.timeout_seconds}
                      onChange={(e) => updateField('timeout_seconds', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editingProfile.json_mode}
                      onChange={(e) => updateField('json_mode', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">JSON Mode</span>
                  </label>
                  <p className="text-xs text-gray-500 mt-1 ml-6">
                    Enable JSON mode for structured outputs (OpenAI only)
                  </p>
                </div>
              </div>

              {/* Parameters */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">LLM Parameters</h4>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      value={editingProfile.parameters.temperature}
                      onChange={(e) => updateNestedField('parameters', 'temperature', parseFloat(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                    <input
                      type="number"
                      value={editingProfile.parameters.max_tokens}
                      onChange={(e) => updateNestedField('parameters', 'max_tokens', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Top P</label>
                    <input
                      type="number"
                      step="0.1"
                      value={editingProfile.parameters.top_p}
                      onChange={(e) => updateNestedField('parameters', 'top_p', parseFloat(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                {editingProfile.provider === 'openai' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Frequency Penalty</label>
                      <input
                        type="number"
                        step="0.1"
                        value={editingProfile.parameters.frequency_penalty || 0}
                        onChange={(e) => updateNestedField('parameters', 'frequency_penalty', parseFloat(e.target.value))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Presence Penalty</label>
                      <input
                        type="number"
                        step="0.1"
                        value={editingProfile.parameters.presence_penalty || 0}
                        onChange={(e) => updateNestedField('parameters', 'presence_penalty', parseFloat(e.target.value))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Constraints */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Model Constraints</h4>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Context Tokens</label>
                    <input
                      type="number"
                      value={editingProfile.constraints.max_context_tokens}
                      onChange={(e) => updateNestedField('constraints', 'max_context_tokens', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Output Tokens</label>
                    <input
                      type="number"
                      value={editingProfile.constraints.max_output_tokens}
                      onChange={(e) => updateNestedField('constraints', 'max_output_tokens', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>

              {/* Retry Policy */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Retry Policy</h4>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
                    <input
                      type="number"
                      value={editingProfile.retry_policy.max_retries}
                      onChange={(e) => updateNestedField('retry_policy', 'max_retries', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Backoff Multiplier</label>
                    <input
                      type="number"
                      step="0.1"
                      value={editingProfile.retry_policy.backoff_multiplier}
                      onChange={(e) => updateNestedField('retry_policy', 'backoff_multiplier', parseFloat(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Initial Delay (ms)</label>
                    <input
                      type="number"
                      value={editingProfile.retry_policy.initial_delay_ms}
                      onChange={(e) => updateNestedField('retry_policy', 'initial_delay_ms', parseInt(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-2">
              <button
                onClick={() => {
                  setModalOpen(false);
                  setEditingProfile(null);
                }}
                className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
