/**
 * HITL (Human-in-the-Loop) Dashboard
 *
 * Displays pending checkpoints and allows human intervention.
 */

'use client';

import { useState, useEffect } from 'react';
import { apiClient, CheckpointInstance, EvidenceMap } from '@/lib/api-client';
import { formatDistanceToNow } from 'date-fns';
import EvidenceDisplay from '@/components/EvidenceDisplay';
import { DEMO_EVIDENCE_MAP } from '@/lib/demo-evidence';

/**
 * Extract evidence map from checkpoint context_data
 * Converts agent outputs from context into evidence map format
 */
function extractEvidenceFromContext(contextData: Record<string, any>): any | null {
  if (!contextData) return null;

  try {
    const priorOutputs = contextData.prior_outputs || {};
    const agentOutput = contextData.agent_output || {};

    // Try to find evidence in various locations
    let decision: any = null;
    let supportingEvidence: any[] = [];
    let agentChain: string[] = [];

    // Extract from prior_outputs (multiple agents)
    if (Object.keys(priorOutputs).length > 0) {
      Object.entries(priorOutputs).forEach(([agentId, output]: [string, any]) => {
        agentChain.push(agentId);

        // Extract decision info
        if (output.recommendation || output.decision || output.outcome) {
          decision = {
            outcome: output.recommendation || output.decision || output.outcome || 'Review Required',
            confidence: output.confidence_score || output.confidence || 0.75,
            basis: output.rationale || output.reasoning || output.summary || 'Based on automated analysis',
            estimated_exposure: output.claim_amount || output.estimated_exposure,
            potential_savings: output.potential_savings
          };
        }

        // Extract supporting evidence
        if (output.fraud_indicators || output.analysis || output.findings) {
          supportingEvidence.push({
            source: agentId,
            evidence_type: output.analysis_type || 'automated_analysis',
            summary: output.summary || output.analysis || JSON.stringify(output.fraud_indicators || output.findings),
            weight: output.evidence_weight || 0.2,
            risk_score: output.fraud_score || output.risk_score
          });
        }
      });
    }

    // Extract from single agent_output
    if (Object.keys(agentOutput).length > 0) {
      const agentId = contextData.agent_id || 'current_agent';
      agentChain.push(agentId);

      if (agentOutput.recommendation || agentOutput.decision) {
        decision = {
          outcome: agentOutput.recommendation || agentOutput.decision || 'Review Required',
          confidence: agentOutput.confidence_score || agentOutput.confidence || 0.75,
          basis: agentOutput.rationale || agentOutput.reasoning || agentOutput.summary || 'Based on automated analysis',
          estimated_exposure: agentOutput.claim_amount || agentOutput.estimated_exposure,
          potential_savings: agentOutput.potential_savings
        };
      }

      if (agentOutput.fraud_indicators || agentOutput.analysis || agentOutput.findings) {
        supportingEvidence.push({
          source: agentId,
          evidence_type: agentOutput.analysis_type || 'automated_analysis',
          summary: agentOutput.summary || agentOutput.analysis || JSON.stringify(agentOutput.fraud_indicators || agentOutput.findings),
          weight: agentOutput.evidence_weight || 0.3,
          risk_score: agentOutput.fraud_score || agentOutput.risk_score
        });
      }
    }

    // If we have at least some data, return it
    if (decision || supportingEvidence.length > 0) {
      return {
        decision: decision || {
          outcome: 'Manual Review Required',
          confidence: 0.5,
          basis: 'Automated analysis completed. Human review required for final decision.'
        },
        supporting_evidence: supportingEvidence.length > 0 ? supportingEvidence : [{
          source: 'system',
          evidence_type: 'automated_processing',
          summary: 'Workflow execution completed. Review context data for details.',
          weight: 1.0
        }],
        agent_chain: agentChain.filter((v, i, a) => a.indexOf(v) === i), // unique
        assumptions: [
          'Evidence extracted from automated agent analysis',
          'Manual review recommended for final decision'
        ],
        limitations: [
          'Evidence map generated from checkpoint context - may not include full workflow evidence',
          'Some detailed analysis may be available in raw context view'
        ]
      };
    }

    return null;
  } catch (error) {
    console.error('Failed to extract evidence from context:', error);
    return null;
  }
}

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
  const [evidenceMap, setEvidenceMap] = useState<any>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(true);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [showRawContext, setShowRawContext] = useState(false);

  useEffect(() => {
    const loadEvidence = async () => {
      try {
        setLoadingEvidence(true);
        const data = await apiClient.getEvidenceMap(checkpoint.session_id);
        setEvidenceMap(data.evidence_map);
        setEvidenceError(null);
      } catch (err: any) {
        // Evidence map not available - try to extract from context
        setEvidenceError(err.message);

        // Try to extract evidence from context_data
        const extractedEvidence = extractEvidenceFromContext(checkpoint.context_data);
        if (extractedEvidence) {
          console.log('Evidence extracted from checkpoint context data');
          setEvidenceMap(extractedEvidence);
        } else {
          // Fall back to demo evidence only if extraction fails
          console.warn('No evidence available - using demo evidence for reference');
          setEvidenceMap(DEMO_EVIDENCE_MAP);
        }
      } finally {
        setLoadingEvidence(false);
      }
    };

    loadEvidence();
  }, [checkpoint.session_id, checkpoint.context_data]);

  return (
    <div>
      {/* Evidence Display */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900 text-lg">Decision Context & Evidence</h4>
          <button
            onClick={() => setShowRawContext(!showRawContext)}
            className="text-sm text-blue-600 hover:text-blue-700 underline"
          >
            {showRawContext ? 'Show Evidence Map' : 'Show Raw Context'}
          </button>
        </div>

        {loadingEvidence ? (
          <div className="bg-gray-50 p-6 rounded-lg text-center text-gray-500">
            Loading evidence map...
          </div>
        ) : showRawContext ? (
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <pre className="text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(checkpoint.context_data, null, 2)}
            </pre>
          </div>
        ) : (
          <>
            {evidenceError && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-800">
                <div className="font-semibold mb-1">Evidence Map Status</div>
                {evidenceMap && evidenceMap !== DEMO_EVIDENCE_MAP ? (
                  <span>Evidence extracted from checkpoint context data. For complete evidence, view the session in the Replay tab after workflow completion.</span>
                ) : (
                  <span>Evidence map not yet available for this session. Showing demo evidence for reference.</span>
                )}
              </div>
            )}
            <EvidenceDisplay evidence={evidenceMap} compact={true} />
          </>
        )}
      </div>

      {/* Comments Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">
          Your Decision Comments
        </label>
        <textarea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
          rows={4}
          placeholder="Add your reasoning or comments about this decision..."
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {checkpoint.ui_schema.actions?.map((action: string) => (
          <button
            key={action}
            onClick={() => onResolve(action, comments)}
            disabled={isSubmitting}
            className={`px-6 py-3 rounded-lg font-semibold transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed shadow-sm ${
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
  const [evidenceMap, setEvidenceMap] = useState<any>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(true);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [showRawContext, setShowRawContext] = useState(false);
  const options = checkpoint.ui_schema.decision_options || [];

  useEffect(() => {
    const loadEvidence = async () => {
      try {
        setLoadingEvidence(true);
        const data = await apiClient.getEvidenceMap(checkpoint.session_id);
        setEvidenceMap(data.evidence_map);
        setEvidenceError(null);
      } catch (err: any) {
        // Evidence map not available - try to extract from context
        setEvidenceError(err.message);

        // Try to extract evidence from context_data
        const extractedEvidence = extractEvidenceFromContext(checkpoint.context_data);
        if (extractedEvidence) {
          console.log('Evidence extracted from checkpoint context data');
          setEvidenceMap(extractedEvidence);
        } else {
          // Fall back to demo evidence only if extraction fails
          console.warn('No evidence available - using demo evidence for reference');
          setEvidenceMap(DEMO_EVIDENCE_MAP);
        }
      } finally {
        setLoadingEvidence(false);
      }
    };

    loadEvidence();
  }, [checkpoint.session_id, checkpoint.context_data]);

  return (
    <div>
      {/* Evidence Display */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900 text-lg">Decision Context & Evidence</h4>
          <button
            onClick={() => setShowRawContext(!showRawContext)}
            className="text-sm text-blue-600 hover:text-blue-700 underline"
          >
            {showRawContext ? 'Show Evidence Map' : 'Show Raw Context'}
          </button>
        </div>

        {loadingEvidence ? (
          <div className="bg-gray-50 p-6 rounded-lg text-center text-gray-500">
            Loading evidence map...
          </div>
        ) : showRawContext ? (
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            {checkpoint.ui_schema.display_fields?.map((field: string) => (
              <div key={field} className="mb-3">
                <span className="text-sm font-semibold text-gray-700">{field}: </span>
                <span className="text-sm text-gray-900">{JSON.stringify(checkpoint.context_data[field])}</span>
              </div>
            ))}
          </div>
        ) : (
          <>
            {evidenceError && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-800">
                <div className="font-semibold mb-1">Evidence Map Status</div>
                {evidenceMap && evidenceMap !== DEMO_EVIDENCE_MAP ? (
                  <span>Evidence extracted from checkpoint context data. For complete evidence, view the session in the Replay tab after workflow completion.</span>
                ) : (
                  <span>Evidence map not yet available for this session. Showing demo evidence for reference.</span>
                )}
              </div>
            )}
            <EvidenceDisplay evidence={evidenceMap} compact={true} />
          </>
        )}
      </div>

      {/* Decision Options */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Select Your Decision</label>
        <div className="space-y-3">
          {options.map((option: any) => (
            <label key={option.value} className="flex items-start p-4 border-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="radio"
                name="decision"
                value={option.value}
                checked={selectedOption === option.value}
                onChange={(e) => setSelectedOption(e.target.value)}
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600 mt-1">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Comments */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700">Decision Reasoning</label>
        <textarea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
          rows={4}
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
        className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow-sm"
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
