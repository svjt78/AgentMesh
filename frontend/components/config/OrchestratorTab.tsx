'use client';

import { useState, useEffect } from 'react';
import { apiClient, AgentMetadata, ModelProfile } from '@/lib/api-client';
import JsonSchemaEditor from './JsonSchemaEditor';

export default function OrchestratorTab() {
  const [orchestrator, setOrchestrator] = useState<AgentMetadata | null>(null);
  const [modelProfiles, setModelProfiles] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadOrchestrator();
    loadModelProfiles();
  }, []);

  const loadOrchestrator = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getOrchestrator();
      setOrchestrator(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadModelProfiles = async () => {
    try {
      const data = await apiClient.listModelProfiles();
      setModelProfiles(data.profiles);
    } catch (err: any) {
      console.error('Failed to load model profiles:', err);
    }
  };

  const handleSave = async () => {
    if (!orchestrator) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      await apiClient.updateOrchestrator(orchestrator);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-900">Loading orchestrator configuration...</div>;
  }

  if (error && !orchestrator) {
    return <div className="text-red-600 py-8">Error: {error}</div>;
  }

  if (!orchestrator) {
    return <div className="text-gray-900 py-8">Orchestrator not found</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Orchestrator Agent</h3>
        <p className="text-sm text-blue-700">
          The orchestrator agent manages workflow coordination. Update allowed agents to control which agents can be invoked.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
          Orchestrator updated successfully!
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Agent ID</label>
          <input
            type="text"
            value={orchestrator.agent_id}
            disabled
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-900"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
          <input
            type="text"
            value={orchestrator.name}
            onChange={(e) => setOrchestrator({ ...orchestrator, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
        <textarea
          value={orchestrator.description}
          onChange={(e) => setOrchestrator({ ...orchestrator, description: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Agents</label>
        <textarea
          value={(orchestrator.allowed_agents || []).join('\n')}
          onChange={(e) =>
            setOrchestrator({
              ...orchestrator,
              allowed_agents: e.target.value.split('\n').filter((s) => s.trim()),
            })
          }
          rows={6}
          placeholder="Enter one agent ID per line"
          className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
        />
        <p className="mt-1 text-xs text-gray-500">One agent ID per line</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Model Profile *</label>
          <select
            value={orchestrator.model_profile_id}
            onChange={(e) =>
              setOrchestrator({ ...orchestrator, model_profile_id: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a model profile</option>
            {modelProfiles.map((profile) => (
              <option key={profile.profile_id} value={profile.profile_id}>
                {profile.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Max Iterations</label>
          <input
            type="number"
            value={orchestrator.max_iterations}
            onChange={(e) =>
              setOrchestrator({ ...orchestrator, max_iterations: parseInt(e.target.value) })
            }
            min={1}
            max={50}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Iteration Timeout (seconds)
          </label>
          <input
            type="number"
            value={orchestrator.iteration_timeout_seconds}
            onChange={(e) =>
              setOrchestrator({
                ...orchestrator,
                iteration_timeout_seconds: parseInt(e.target.value),
              })
            }
            min={10}
            max={300}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <JsonSchemaEditor
        label="Input Schema"
        value={orchestrator.input_schema || { type: 'object', properties: {} }}
        onChange={(value) => setOrchestrator({ ...orchestrator, input_schema: value })}
      />

      <JsonSchemaEditor
        label="Output Schema"
        value={orchestrator.output_schema}
        onChange={(value) => setOrchestrator({ ...orchestrator, output_schema: value })}
      />

      <div className="flex justify-end space-x-4 pt-4 border-t">
        <button
          onClick={loadOrchestrator}
          disabled={saving}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Reset
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}
