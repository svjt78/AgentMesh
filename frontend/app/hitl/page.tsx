/**
 * HITL (Human-in-the-Loop) Dashboard
 *
 * Displays pending checkpoints and allows human intervention.
 */

'use client';

import { useState, useEffect } from 'react';
import { apiClient, CheckpointInstance } from '@/lib/api-client';
import { formatDistanceToNow } from 'date-fns';

export default function HITLDashboard() {
  const [checkpoints, setCheckpoints] = useState<CheckpointInstance[]>([]);
  const [selectedRole, setSelectedRole] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCheckpoints();
    const interval = setInterval(loadCheckpoints, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [selectedRole]);

  const loadCheckpoints = async () => {
    try {
      setError(null);
      const data = await apiClient.getPendingCheckpoints(
        selectedRole === 'all' ? undefined : selectedRole
      );
      setCheckpoints(data.checkpoints);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Human Intervention Dashboard</h1>

      {/* Role Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700">Filter by Role:</label>
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          className="border rounded px-3 py-2 text-gray-900 bg-white"
        >
          <option value="all">All Roles</option>
          <option value="reviewer">Reviewer</option>
          <option value="fraud_investigator">Fraud Investigator</option>
          <option value="claims_adjuster">Claims Adjuster</option>
          <option value="approver">Approver</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 mb-6">
          {error}
        </div>
      )}

      {/* Checkpoints List */}
      {isLoading ? (
        <p className="text-gray-500">Loading checkpoints...</p>
      ) : checkpoints.length === 0 ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <p className="text-gray-600">No pending interventions at this time.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-600 mb-4">
            {checkpoints.length} pending checkpoint{checkpoints.length !== 1 ? 's' : ''}
          </p>
          {checkpoints.map(checkpoint => (
            <CheckpointCard
              key={checkpoint.checkpoint_instance_id}
              checkpoint={checkpoint}
              onResolve={loadCheckpoints}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CheckpointCard({
  checkpoint,
  onResolve
}: {
  checkpoint: CheckpointInstance;
  onResolve: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate time remaining for timeout
  const timeRemaining = checkpoint.timeout_at
    ? new Date(checkpoint.timeout_at).getTime() - new Date().getTime()
    : null;

  const handleResolve = async (action: string, comments?: string, dataUpdates?: Record<string, any>) => {
    setIsSubmitting(true);
    setError(null);

    try {
      await apiClient.resolveCheckpoint(checkpoint.checkpoint_instance_id, {
        action,
        user_id: 'demo-user', // In production: get from auth context
        user_role: checkpoint.required_role, // In production: get from auth context
        comments,
        data_updates: dataUpdates
      });

      onResolve(); // Refresh list
      setExpanded(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-xl font-semibold text-gray-900">{checkpoint.checkpoint_name}</h3>
            <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
              {checkpoint.checkpoint_type}
            </span>
          </div>
          <p className="text-gray-600 mb-3">{checkpoint.description}</p>

          <div className="flex flex-wrap gap-4 text-sm text-gray-500">
            <span>Session: {checkpoint.session_id}</span>
            <span>Created: {formatDistanceToNow(new Date(checkpoint.created_at))} ago</span>
            <span>Required Role: <span className="font-medium text-gray-700">{checkpoint.required_role}</span></span>
            {timeRemaining && timeRemaining > 0 && (
              <span className="text-orange-600 font-medium">
                Timeout in: {Math.floor(timeRemaining / 60000)} minutes
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          {expanded ? 'Hide' : 'View & Resolve'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Expanded Resolution UI */}
      {expanded && (
        <div className="mt-6 border-t pt-6">
          {checkpoint.checkpoint_type === 'approval' && (
            <ApprovalCheckpoint checkpoint={checkpoint} onResolve={handleResolve} isSubmitting={isSubmitting} />
          )}
          {checkpoint.checkpoint_type === 'decision' && (
            <DecisionCheckpoint checkpoint={checkpoint} onResolve={handleResolve} isSubmitting={isSubmitting} />
          )}
          {checkpoint.checkpoint_type === 'input' && (
            <InputCheckpoint checkpoint={checkpoint} onResolve={handleResolve} isSubmitting={isSubmitting} />
          )}
        </div>
      )}
    </div>
  );
}

// Approval Checkpoint Component
function ApprovalCheckpoint({
  checkpoint,
  onResolve,
  isSubmitting
}: {
  checkpoint: CheckpointInstance;
  onResolve: (action: string, comments?: string) => void;
  isSubmitting: boolean;
}) {
  const [comments, setComments] = useState('');

  return (
    <div>
      {/* Display Context Data */}
      <div className="bg-gray-50 p-4 rounded mb-4">
        <h4 className="font-semibold mb-2 text-gray-900">Context Information</h4>
        <pre className="text-sm text-gray-700 overflow-x-auto">
          {JSON.stringify(checkpoint.context_data, null, 2)}
        </pre>
      </div>

      {/* Comments Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Comments</label>
        <textarea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
          rows={3}
          placeholder="Add your reasoning or comments..."
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {checkpoint.ui_schema.actions?.map((action: string) => (
          <button
            key={action}
            onClick={() => onResolve(action, comments)}
            disabled={isSubmitting}
            className={`px-4 py-2 rounded font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed ${
              action === 'approve' ? 'bg-green-600 hover:bg-green-700 text-white' :
              action === 'reject' ? 'bg-red-600 hover:bg-red-700 text-white' :
              'bg-orange-600 hover:bg-orange-700 text-white'
            }`}
          >
            {action.charAt(0).toUpperCase() + action.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}

// Decision Checkpoint Component
function DecisionCheckpoint({
  checkpoint,
  onResolve,
  isSubmitting
}: {
  checkpoint: CheckpointInstance;
  onResolve: (action: string, comments?: string) => void;
  isSubmitting: boolean;
}) {
  const [selectedOption, setSelectedOption] = useState('');
  const [comments, setComments] = useState('');
  const options = checkpoint.ui_schema.decision_options || [];

  return (
    <div>
      {/* Display Context Data */}
      <div className="bg-gray-50 p-4 rounded mb-4">
        <h4 className="font-semibold mb-2 text-gray-900">Review Information</h4>
        {checkpoint.ui_schema.display_fields?.map((field: string) => (
          <div key={field} className="mb-2">
            <span className="text-sm font-medium text-gray-600">{field}: </span>
            <span className="text-sm text-gray-900">{JSON.stringify(checkpoint.context_data[field])}</span>
          </div>
        ))}
      </div>

      {/* Decision Options */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Select Decision</label>
        <div className="space-y-3">
          {options.map((option: any) => (
            <label key={option.value} className="flex items-start p-3 border rounded hover:bg-gray-50 cursor-pointer">
              <input
                type="radio"
                name="decision"
                value={option.value}
                checked={selectedOption === option.value}
                onChange={(e) => setSelectedOption(e.target.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-500">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Comments */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Reasoning</label>
        <textarea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
          rows={3}
          placeholder="Explain your decision..."
        />
      </div>

      {/* Submit Button */}
      <button
        onClick={() => {
          if (!selectedOption) {
            alert('Please select an option');
            return;
          }
          onResolve(selectedOption, comments);
        }}
        disabled={isSubmitting}
        className="bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Decision'}
      </button>
    </div>
  );
}

// Input Checkpoint Component
function InputCheckpoint({
  checkpoint,
  onResolve,
  isSubmitting
}: {
  checkpoint: CheckpointInstance;
  onResolve: (action: string, comments?: string, dataUpdates?: Record<string, any>) => void;
  isSubmitting: boolean;
}) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [comments, setComments] = useState('');

  useEffect(() => {
    // Initialize form data from context
    const editableFields = checkpoint.ui_schema.editable_fields || [];
    const initialData: Record<string, any> = {};
    editableFields.forEach((field: string) => {
      initialData[field] = checkpoint.context_data[field] || '';
    });
    setFormData(initialData);
  }, [checkpoint]);

  return (
    <div>
      {/* Editable Form Fields */}
      <div className="mb-4">
        <h4 className="font-semibold mb-3 text-gray-900">Correct or Supplement Data</h4>
        <div className="space-y-4">
          {(checkpoint.ui_schema.editable_fields || []).map((field: string) => (
            <div key={field}>
              <label className="block text-sm font-medium mb-1 text-gray-700">{field}</label>
              <input
                type="text"
                value={formData[field] || ''}
                onChange={(e) => setFormData({...formData, [field]: e.target.value})}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Comments */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Change Notes</label>
        <textarea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
          rows={2}
          placeholder="Explain what you changed and why..."
        />
      </div>

      {/* Submit Button */}
      <button
        onClick={() => onResolve('submit_corrections', comments, formData)}
        disabled={isSubmitting}
        className="bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Corrections'}
      </button>
    </div>
  );
}
