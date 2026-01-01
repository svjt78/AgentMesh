'use client';

import { useState, useEffect } from 'react';
import { apiClient, WorkflowDefinition, CheckpointConfig, HITLRole, TimeoutLimits } from '@/lib/api-client';
import CheckpointForm from './checkpoint-config/CheckpointForm';
import { createEmptyCheckpoint } from './checkpoint-config/templates';

export default function HITLCheckpointsTab() {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowDefinition | null>(null);
  const [checkpoints, setCheckpoints] = useState<CheckpointConfig[]>([]);
  const [roles, setRoles] = useState<HITLRole[]>([]);
  const [timeoutLimits, setTimeoutLimits] = useState<TimeoutLimits>({
    min_timeout_seconds: 300,
    max_timeout_seconds: 86400,
    default_timeout_seconds: 3600
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCheckpoint, setEditingCheckpoint] = useState<CheckpointConfig | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadWorkflows(),
        loadRoles()
      ]);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflows = async () => {
    const data = await apiClient.listWorkflows();
    setWorkflows(data.workflows);
    if (data.workflows.length > 0 && !selectedWorkflow) {
      handleWorkflowSelect(data.workflows[0]);
    }
    return data.workflows;
  };

  const loadRoles = async () => {
    try {
      // Try to fetch from governance API if available
      const governanceData = await apiClient.getGovernancePolicies();
      const hitlConfig = governanceData.policies?.hitl_access_control;

      if (hitlConfig) {
        const rolesData: HITLRole[] = (hitlConfig.roles || []).map((role: any) => ({
          role_id: role.role_id,
          role_name: role.role_name || role.role_id,
          allowed_checkpoint_types: role.allowed_checkpoint_types || [],
          permissions: role.permissions || []
        }));
        setRoles(rolesData);

        if (hitlConfig.checkpoint_timeout_limits) {
          setTimeoutLimits(hitlConfig.checkpoint_timeout_limits);
        }
      }
    } catch (err) {
      console.error('Failed to load roles:', err);
      // Fallback to default roles
      setRoles([
        { role_id: 'reviewer', role_name: 'Reviewer', allowed_checkpoint_types: [], permissions: [] },
        { role_id: 'approver', role_name: 'Approver', allowed_checkpoint_types: [], permissions: [] },
        { role_id: 'admin', role_name: 'Admin', allowed_checkpoint_types: [], permissions: [] }
      ]);
    }
  };

  const handleWorkflowSelect = (workflow: WorkflowDefinition) => {
    setSelectedWorkflow(workflow);
    setCheckpoints(workflow.hitl_checkpoints || []);
  };

  const handleAddCheckpoint = () => {
    setEditingCheckpoint(createEmptyCheckpoint('approval'));
    setModalOpen(true);
  };

  const handleEditCheckpoint = (checkpoint: CheckpointConfig) => {
    setEditingCheckpoint({ ...checkpoint });
    setModalOpen(true);
  };

  const handleSaveCheckpoint = async (checkpoint: CheckpointConfig) => {
    if (!selectedWorkflow) return;

    try {
      setError(null);

      // Update or add checkpoint to workflow
      const existingIndex = (selectedWorkflow.hitl_checkpoints || []).findIndex(
        cp => cp.checkpoint_id === checkpoint.checkpoint_id
      );

      let updatedCheckpoints: CheckpointConfig[];
      if (existingIndex >= 0) {
        // Update existing
        updatedCheckpoints = [...(selectedWorkflow.hitl_checkpoints || [])];
        updatedCheckpoints[existingIndex] = checkpoint;
      } else {
        // Add new
        updatedCheckpoints = [...(selectedWorkflow.hitl_checkpoints || []), checkpoint];
      }

      // Update workflow with new checkpoints
      const updatedWorkflow: WorkflowDefinition = {
        ...selectedWorkflow,
        hitl_checkpoints: updatedCheckpoints
      };

      await apiClient.updateWorkflow(selectedWorkflow.workflow_id, updatedWorkflow);

      // Reload workflows and get the fresh data
      const freshWorkflows = await loadWorkflows();

      // Update selected workflow with fresh data
      const refreshedWorkflow = freshWorkflows.find(w => w.workflow_id === selectedWorkflow.workflow_id);
      if (refreshedWorkflow) {
        handleWorkflowSelect(refreshedWorkflow);
      }

      setModalOpen(false);
      setEditingCheckpoint(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteCheckpoint = async (checkpointId: string) => {
    if (!selectedWorkflow) return;

    if (!confirm(`Delete checkpoint '${checkpointId}'? This cannot be undone.`)) return;

    try {
      setError(null);

      const updatedCheckpoints = (selectedWorkflow.hitl_checkpoints || []).filter(
        cp => cp.checkpoint_id !== checkpointId
      );

      const updatedWorkflow: WorkflowDefinition = {
        ...selectedWorkflow,
        hitl_checkpoints: updatedCheckpoints
      };

      await apiClient.updateWorkflow(selectedWorkflow.workflow_id, updatedWorkflow);

      // Reload workflows and get the fresh data
      const freshWorkflows = await loadWorkflows();

      // Update selected workflow with fresh data
      const refreshedWorkflow = freshWorkflows.find(w => w.workflow_id === selectedWorkflow.workflow_id);
      if (refreshedWorkflow) {
        handleWorkflowSelect(refreshedWorkflow);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCancelEdit = () => {
    setModalOpen(false);
    setEditingCheckpoint(null);
  };

  if (loading) {
    return <div className="text-center py-8">Loading HITL checkpoints...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">
          HITL Checkpoint Configuration
        </h2>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {workflows.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-sm text-yellow-800">
            No workflows found. Create a workflow first before configuring checkpoints.
          </p>
        </div>
      ) : (
        <>
          {/* Workflow Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Workflow
            </label>
            <select
              value={selectedWorkflow?.workflow_id || ''}
              onChange={(e) => {
                const workflow = workflows.find(w => w.workflow_id === e.target.value);
                if (workflow) handleWorkflowSelect(workflow);
              }}
              className="w-full max-w-md border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              {workflows.map((workflow) => (
                <option key={workflow.workflow_id} value={workflow.workflow_id}>
                  {workflow.name} ({workflow.workflow_id})
                </option>
              ))}
            </select>
          </div>

          {selectedWorkflow && (
            <>
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  {checkpoints.length} checkpoint{checkpoints.length !== 1 ? 's' : ''} configured
                </p>
                <button
                  onClick={handleAddCheckpoint}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  + Add Checkpoint
                </button>
              </div>

              {/* Checkpoint List */}
              {checkpoints.length === 0 ? (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                  <p className="text-gray-600 mb-4">No checkpoints configured for this workflow</p>
                  <button
                    onClick={handleAddCheckpoint}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    + Add First Checkpoint
                  </button>
                </div>
              ) : (
                <div className="grid gap-4">
                  {checkpoints.map((checkpoint) => (
                    <div key={checkpoint.checkpoint_id} className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-sm transition-shadow">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold text-gray-900">{checkpoint.checkpoint_name}</h3>
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {checkpoint.checkpoint_type}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{checkpoint.description}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>
                              Trigger: <span className="font-medium">{checkpoint.trigger_point}</span>
                              {checkpoint.agent_id && ` → ${checkpoint.agent_id}`}
                            </span>
                            <span>
                              Role: <span className="font-medium">{checkpoint.required_role}</span>
                            </span>
                            {checkpoint.trigger_condition?.condition && (
                              <span>
                                Condition: <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">
                                  {checkpoint.trigger_condition.condition}
                                </code>
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleEditCheckpoint(checkpoint)}
                            className="text-sm px-3 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteCheckpoint(checkpoint.checkpoint_id)}
                            className="text-sm px-3 py-1 rounded bg-red-50 text-red-600 hover:bg-red-100"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Modal for Add/Edit */}
      {modalOpen && selectedWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <CheckpointForm
                checkpoint={editingCheckpoint}
                workflow={selectedWorkflow}
                roles={roles}
                timeoutLimits={timeoutLimits}
                onSave={handleSaveCheckpoint}
                onCancel={handleCancelEdit}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
