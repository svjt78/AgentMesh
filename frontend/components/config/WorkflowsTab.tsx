'use client';

import { useState, useEffect } from 'react';
import { apiClient, WorkflowDefinition } from '@/lib/api-client';
import WorkflowDiagram from './workflow-diagram/WorkflowDiagram';
import JsonSchemaEditor from './JsonSchemaEditor';

export default function WorkflowsTab() {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedWorkflow, setExpandedWorkflow] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<WorkflowDefinition | null>(null);

  const emptyWorkflow: WorkflowDefinition = {
    workflow_id: '',
    name: '',
    description: '',
    version: '1.0.0',
    mode: 'advisory',
    goal: '',
    steps: [],
    suggested_sequence: [],
    required_agents: [],
    optional_agents: [],
    completion_criteria: {},
    constraints: {},
    metadata: {},
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listWorkflows();
      setWorkflows(data.workflows);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingWorkflow(emptyWorkflow);
    setModalOpen(true);
  };

  const handleEdit = (workflow: WorkflowDefinition) => {
    setEditingWorkflow({ ...workflow });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!editingWorkflow) return;

    try {
      setError(null);
      const isNew = !workflows.find((w) => w.workflow_id === editingWorkflow.workflow_id);

      if (isNew) {
        await apiClient.createWorkflow(editingWorkflow);
      } else {
        await apiClient.updateWorkflow(editingWorkflow.workflow_id, editingWorkflow);
      }

      await loadWorkflows();
      setModalOpen(false);
      setEditingWorkflow(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (workflowId: string) => {
    if (!confirm(`Delete workflow '${workflowId}'? This cannot be undone.`)) return;

    try {
      setError(null);
      await apiClient.deleteWorkflow(workflowId);
      await loadWorkflows();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const updateField = (field: keyof WorkflowDefinition, value: any) => {
    if (!editingWorkflow) return;
    setEditingWorkflow({ ...editingWorkflow, [field]: value });
  };

  if (loading) {
    return <div className="text-center py-8">Loading workflows...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Workflows ({workflows.length})</h2>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + Add Workflow
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}

      <div className="grid gap-4">
        {workflows.map((workflow) => (
          <div key={workflow.workflow_id} className="border border-gray-200 rounded-lg">
            <div className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{workflow.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">{workflow.mode}</span>
                  <button
                    onClick={() =>
                      setExpandedWorkflow(expandedWorkflow === workflow.workflow_id ? null : workflow.workflow_id)
                    }
                    className="text-sm px-3 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    {expandedWorkflow === workflow.workflow_id ? 'Hide Diagram' : 'View Diagram'}
                  </button>
                  <button
                    onClick={() => handleEdit(workflow)}
                    className="text-sm px-3 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(workflow.workflow_id)}
                    className="text-sm px-3 py-1 rounded bg-red-50 text-red-600 hover:bg-red-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-4 text-xs text-gray-500">
                <span>Required Agents: {workflow.required_agents?.length || 0}</span>
                <span>Optional Agents: {workflow.optional_agents?.length || 0}</span>
                <span>Steps: {workflow.steps?.length || 0}</span>
                <span>Version: {workflow.version}</span>
              </div>
            </div>

            {/* Workflow Diagram */}
            {expandedWorkflow === workflow.workflow_id && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <WorkflowDiagram workflowId={workflow.workflow_id} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Edit/Create Modal */}
      {modalOpen && editingWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {workflows.find((w) => w.workflow_id === editingWorkflow.workflow_id)
                  ? 'Edit Workflow'
                  : 'Create Workflow'}
              </h3>
            </div>

            <div className="px-6 py-4 space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900 text-sm">Basic Information</h4>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Workflow ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={editingWorkflow.workflow_id}
                      onChange={(e) => updateField('workflow_id', e.target.value)}
                      disabled={workflows.some((w) => w.workflow_id === editingWorkflow.workflow_id)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm disabled:bg-gray-100"
                      placeholder="e.g., claims_triage"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                    <input
                      type="text"
                      value={editingWorkflow.version}
                      onChange={(e) => updateField('version', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="e.g., 1.0.0"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={editingWorkflow.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    placeholder="e.g., Claims Triage Workflow"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editingWorkflow.description}
                    onChange={(e) => updateField('description', e.target.value)}
                    rows={2}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    placeholder="Workflow description..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
                    <select
                      value={editingWorkflow.mode}
                      onChange={(e) => updateField('mode', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="advisory">Advisory</option>
                      <option value="prescriptive">Prescriptive</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Advisory: Orchestrator adapts; Prescriptive: Strict sequence
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Goal</label>
                    <input
                      type="text"
                      value={editingWorkflow.goal || ''}
                      onChange={(e) => updateField('goal', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="Workflow goal..."
                    />
                  </div>
                </div>
              </div>

              {/* Agent Configuration */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Agent Configuration</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Suggested Sequence (comma-separated agent IDs)
                  </label>
                  <input
                    type="text"
                    value={editingWorkflow.suggested_sequence?.join(', ') || ''}
                    onChange={(e) =>
                      updateField(
                        'suggested_sequence',
                        e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                      )
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    placeholder="e.g., intake_agent, coverage_agent, fraud_agent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Required Agents (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editingWorkflow.required_agents?.join(', ') || ''}
                      onChange={(e) =>
                        updateField(
                          'required_agents',
                          e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="e.g., intake_agent, recommendation_agent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Optional Agents (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editingWorkflow.optional_agents?.join(', ') || ''}
                      onChange={(e) =>
                        updateField(
                          'optional_agents',
                          e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      placeholder="e.g., fraud_agent, severity_agent"
                    />
                  </div>
                </div>
              </div>

              {/* Steps (JSON Editor) */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Workflow Steps</h4>
                <p className="text-xs text-gray-500">
                  Define step sequence, agent assignments, retry policies, and context requirements
                </p>
                <JsonSchemaEditor
                  value={editingWorkflow.steps}
                  onChange={(value) => updateField('steps', value)}
                />
              </div>

              {/* Completion Criteria (JSON Editor) */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Completion Criteria</h4>
                <p className="text-xs text-gray-500">
                  Define required outputs, agents, and minimum execution thresholds
                </p>
                <JsonSchemaEditor
                  value={editingWorkflow.completion_criteria || {}}
                  onChange={(value) => updateField('completion_criteria', value)}
                />
              </div>

              {/* Constraints (JSON Editor) */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Constraints</h4>
                <p className="text-xs text-gray-500">
                  Workflow execution limits (duration, iterations, invocations)
                </p>
                <JsonSchemaEditor
                  value={editingWorkflow.constraints || {}}
                  onChange={(value) => updateField('constraints', value)}
                />
              </div>

              {/* Metadata (JSON Editor) */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-semibold text-gray-900 text-sm">Metadata</h4>
                <p className="text-xs text-gray-500">Additional workflow metadata (business owner, tags, etc.)</p>
                <JsonSchemaEditor
                  value={editingWorkflow.metadata}
                  onChange={(value) => updateField('metadata', value)}
                />
              </div>
            </div>

            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-2">
              <button
                onClick={() => {
                  setModalOpen(false);
                  setEditingWorkflow(null);
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
