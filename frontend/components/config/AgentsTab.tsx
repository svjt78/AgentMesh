'use client';

import { useState, useEffect } from 'react';
import { apiClient, AgentMetadata, ModelProfile } from '@/lib/api-client';
import JsonSchemaEditor from './JsonSchemaEditor';

export default function AgentsTab() {
  const [agents, setAgents] = useState<AgentMetadata[]>([]);
  const [modelProfiles, setModelProfiles] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);

  const emptyAgent: AgentMetadata = {
    agent_id: '',
    name: '',
    description: '',
    capabilities: [],
    allowed_tools: [],
    model_profile_id: '',
    max_iterations: 10,
    iteration_timeout_seconds: 60,
    input_schema: { type: 'object', properties: {} },
    output_schema: { type: 'object', properties: {} },
    context_requirements: {},
  };

  useEffect(() => {
    loadAgents();
    loadModelProfiles();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listAgents(true); // Exclude orchestrator
      setAgents(data.agents);
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

  const handleCreate = () => {
    setEditingAgent(emptyAgent);
    setModalOpen(true);
  };

  const handleEdit = (agent: AgentMetadata) => {
    setEditingAgent({ ...agent });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!editingAgent) return;

    try {
      setError(null);
      const isNew = !agents.find((a) => a.agent_id === editingAgent.agent_id);

      if (isNew) {
        await apiClient.createAgent(editingAgent);
      } else {
        await apiClient.updateAgent(editingAgent.agent_id, editingAgent);
      }

      await loadAgents();
      setModalOpen(false);
      setEditingAgent(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (agentId: string) => {
    if (!confirm(`Delete agent '${agentId}'? This cannot be undone.`)) return;

    try {
      setError(null);
      await apiClient.deleteAgent(agentId);
      await loadAgents();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-900">Loading agents...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Agents ({agents.length})</h2>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + Add Agent
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Agent ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Capabilities
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Model
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {agents.map((agent) => (
              <tr key={agent.agent_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{agent.agent_id}</td>
                <td className="px-6 py-4 text-sm text-gray-700">{agent.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {agent.capabilities.slice(0, 2).join(', ')}
                  {agent.capabilities.length > 2 && '...'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{agent.model_profile_id}</td>
                <td className="px-6 py-4 text-right text-sm space-x-2">
                  <button
                    onClick={() => handleEdit(agent)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(agent.agent_id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modalOpen && editingAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {agents.find((a) => a.agent_id === editingAgent.agent_id) ? 'Edit' : 'Create'} Agent
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Agent ID *</label>
                  <input
                    type="text"
                    value={editingAgent.agent_id}
                    onChange={(e) =>
                      setEditingAgent({ ...editingAgent, agent_id: e.target.value })
                    }
                    disabled={!!agents.find((a) => a.agent_id === editingAgent.agent_id)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={editingAgent.name}
                    onChange={(e) => setEditingAgent({ ...editingAgent, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  value={editingAgent.description}
                  onChange={(e) =>
                    setEditingAgent({ ...editingAgent, description: e.target.value })
                  }
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Capabilities (comma-separated) *
                </label>
                <input
                  type="text"
                  value={editingAgent.capabilities.join(', ')}
                  onChange={(e) =>
                    setEditingAgent({
                      ...editingAgent,
                      capabilities: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Allowed Tools (comma-separated)
                </label>
                <input
                  type="text"
                  value={editingAgent.allowed_tools.join(', ')}
                  onChange={(e) =>
                    setEditingAgent({
                      ...editingAgent,
                      allowed_tools: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model Profile *
                  </label>
                  <select
                    value={editingAgent.model_profile_id}
                    onChange={(e) =>
                      setEditingAgent({ ...editingAgent, model_profile_id: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Iterations
                  </label>
                  <input
                    type="number"
                    value={editingAgent.max_iterations}
                    onChange={(e) =>
                      setEditingAgent({ ...editingAgent, max_iterations: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timeout (s)
                  </label>
                  <input
                    type="number"
                    value={editingAgent.iteration_timeout_seconds}
                    onChange={(e) =>
                      setEditingAgent({
                        ...editingAgent,
                        iteration_timeout_seconds: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
              </div>

              {/* Context Requirements */}
              <div className="border-t pt-4 space-y-4">
                <h4 className="font-semibold text-gray-900 text-sm">Context Requirements</h4>
                <p className="text-xs text-gray-500">
                  Configure which prior agent outputs this agent needs and its token budget
                </p>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Required Prior Outputs (comma-separated agent IDs)
                  </label>
                  <input
                    type="text"
                    value={editingAgent.context_requirements?.requires_prior_outputs?.join(', ') || ''}
                    onChange={(e) =>
                      setEditingAgent({
                        ...editingAgent,
                        context_requirements: {
                          ...editingAgent.context_requirements,
                          requires_prior_outputs: e.target.value
                            .split(',')
                            .map((s) => s.trim())
                            .filter(Boolean),
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                    placeholder="e.g., intake, coverage, fraud"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Which prior agent outputs should be included in this agent's context
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Context Tokens
                  </label>
                  <input
                    type="number"
                    value={editingAgent.context_requirements?.max_context_tokens || ''}
                    onChange={(e) =>
                      setEditingAgent({
                        ...editingAgent,
                        context_requirements: {
                          ...editingAgent.context_requirements,
                          max_context_tokens: e.target.value ? parseInt(e.target.value) : undefined,
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                    placeholder="e.g., 5000"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Per-agent token budget override (overrides LLM_MAX_TOKENS_PER_REQUEST)
                  </p>
                </div>
              </div>

              <JsonSchemaEditor
                label="Input Schema"
                value={editingAgent.input_schema || { type: 'object', properties: {} }}
                onChange={(value) => setEditingAgent({ ...editingAgent, input_schema: value })}
              />

              <JsonSchemaEditor
                label="Output Schema *"
                value={editingAgent.output_schema}
                onChange={(value) => setEditingAgent({ ...editingAgent, output_schema: value })}
              />
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={() => {
                  setModalOpen(false);
                  setEditingAgent(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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
