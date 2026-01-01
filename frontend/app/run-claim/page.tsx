/**
 * Run Claim Page - Submit claim and watch live execution
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, RunWorkflowResponse } from '@/lib/api-client';
import { useSSE } from '@/hooks/use-sse';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

export default function RunClaimPage() {
  const router = useRouter();
  const [claimData, setClaimData] = useState({
    claim_id: '',
    policy_id: 'POL-001',
    claim_date: '',
    loss_type: 'collision',
    claim_amount: '',
    incident_date: '',
    description: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runResponse, setRunResponse] = useState<RunWorkflowResponse | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  const { events, isConnected } = useSSE(streamUrl, {
    onComplete: () => {
      console.log('Workflow complete');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await apiClient.createRun({
        workflow_id: 'claims_triage',
        input_data: {
          ...claimData,
          claim_amount: parseFloat(claimData.claim_amount),
        },
      });

      setRunResponse(response);
      setStreamUrl(apiClient.getStreamUrl(response.session_id));
    } catch (error) {
      console.error('Failed to submit claim:', error);
      alert('Failed to submit claim');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewEvidence = () => {
    if (runResponse) {
      router.push(`/evidence/${runResponse.session_id}`);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Run Claim Triage</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Claim Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Claim Information</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Claim ID</label>
              <input
                type="text"
                value={claimData.claim_id}
                onChange={(e) => setClaimData({ ...claimData, claim_id: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
                placeholder="CLM-2024-001"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Policy ID</label>
              <select
                value={claimData.policy_id}
                onChange={(e) => setClaimData({ ...claimData, policy_id: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
              >
                <option value="POL-001">POL-001 (Auto - John Doe)</option>
                <option value="POL-002">POL-002 (Home - Jane Smith)</option>
                <option value="POL-003">POL-003 (Auto - Bob Johnson)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Loss Type</label>
              <select
                value={claimData.loss_type}
                onChange={(e) => setClaimData({ ...claimData, loss_type: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
              >
                <option value="collision">Collision</option>
                <option value="comprehensive">Comprehensive</option>
                <option value="theft">Theft</option>
                <option value="fire">Fire</option>
                <option value="water_damage">Water Damage</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Claim Amount ($)</label>
              <input
                type="number"
                step="0.01"
                value={claimData.claim_amount}
                onChange={(e) => setClaimData({ ...claimData, claim_amount: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
                placeholder="15000.00"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Incident Date</label>
              <input
                type="date"
                value={claimData.incident_date}
                onChange={(e) => setClaimData({ ...claimData, incident_date: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Description</label>
              <textarea
                value={claimData.description}
                onChange={(e) => setClaimData({ ...claimData, description: e.target.value })}
                className="w-full border rounded px-3 py-2 text-gray-900 bg-white"
                rows={3}
                placeholder="Brief description of the incident..."
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !!runResponse}
              className="w-full bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : runResponse ? 'Submitted' : 'Submit Claim'}
            </button>
          </form>
        </div>

        {/* Right: Live Progress */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Live Progress</h2>
            {isConnected && (
              <span className="flex items-center text-green-600 text-sm">
                <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse" />
                Connected
              </span>
            )}
          </div>

          {!runResponse ? (
            <p className="text-gray-500 text-center py-8">Submit a claim to see live progress</p>
          ) : (
            <div className="space-y-4">
              {/* Session Info */}
              <div className="bg-gray-50 rounded p-3 text-sm">
                <div>
                  <span className="font-medium">Session ID:</span>{' '}
                  <code className="text-xs">{runResponse.session_id}</code>
                </div>
                <div>
                  <span className="font-medium">Workflow:</span> {runResponse.workflow_id}
                </div>
              </div>

              {/* Event Timeline */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.map((event, index) => (
                  <EventCard key={index} event={event} />
                ))}
              </div>

              {/* View Evidence Button */}
              {events.some((e) => e.data.status === 'completed') && (
                <button
                  onClick={handleViewEvidence}
                  className="w-full bg-green-600 text-white py-2 rounded font-medium hover:bg-green-700"
                >
                  View Evidence Map
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EventCard({ event }: { event: any }) {
  const eventType = event.data.event_type || event.data.event || 'unknown';
  const eventData = event.data;
  const timestamp = new Date(event.timestamp);

  const getEventIcon = () => {
    if (eventType.includes('completed')) {
      return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
    } else if (eventType.includes('error') || eventType.includes('denied')) {
      return <ExclamationCircleIcon className="w-5 h-5 text-red-600" />;
    } else if (eventType === 'checkpoint_created') {
      return <span className="text-lg">⏸️</span>;
    } else if (eventType === 'checkpoint_resolved') {
      return <span className="text-lg">▶️</span>;
    } else if (eventType === 'checkpoint_timeout') {
      return <span className="text-lg">⏱️</span>;
    }
    return <div className="w-5 h-5 border-2 border-blue-600 rounded-full animate-pulse" />;
  };

  const formatMessage = () => {
    switch (eventType) {
      case 'orchestrator_started':
        return `Starting workflow: ${eventData.workflow_id}`;

      case 'orchestrator_reasoning':
        return `Orchestrator thinking (iteration ${eventData.iteration}): ${eventData.reasoning || 'Analyzing workflow state...'}`;

      case 'agent_invocation_started':
        return `Starting agent: ${eventData.agent_id}`;

      case 'agent_invocation_denied':
        return `❌ Agent blocked: ${eventData.reason}`;

      case 'agent_started':
        return `Agent ${eventData.agent_id} initialized (max iterations: ${eventData.max_iterations})`;

      case 'agent_reasoning':
        return `${eventData.agent_id} reasoning (iteration ${eventData.iteration}): ${eventData.reasoning || 'Deciding next action...'}`;

      case 'tool_invocation':
        return `${eventData.agent_id} using tool: ${eventData.tool_id}`;

      case 'tool_denied':
        return `❌ Tool access denied: ${eventData.tool_id} - ${eventData.reason}`;

      case 'agent_completed':
      case 'agent_invocation_completed':
        return `✅ Agent ${eventData.agent_id} completed (${eventData.iterations_used || 0} iterations)`;

      case 'agent_incomplete':
      case 'agent_invocation_incomplete':
        return `⚠️ Agent ${eventData.agent_id} stopped: ${eventData.reason}`;

      case 'agent_error':
      case 'agent_invocation_error':
        return `❌ Agent ${eventData.agent_id} error: ${eventData.error}`;

      case 'orchestrator_completed':
        return `✅ Workflow completed: ${eventData.completion_reason} (${eventData.total_iterations} iterations, ${eventData.total_agent_invocations} agents)`;

      case 'orchestrator_incomplete':
        return `⚠️ Workflow incomplete: ${eventData.completion_reason}`;

      case 'workflow_completed':
        return `✅ All processing complete`;

      case 'workflow_error':
        return `❌ Workflow failed: ${eventData.error}`;

      case 'checkpoint_created':
        return `⏸️ Workflow paused: ${eventData.checkpoint_name} - awaiting human intervention (role: ${eventData.required_role})`;

      case 'checkpoint_resolved':
        return `▶️ Workflow resumed: ${eventData.checkpoint_name} resolved by ${eventData.resolution?.user_id || 'user'} (${eventData.resolution?.action})`;

      case 'checkpoint_timeout':
        return `⏱️ Checkpoint timeout: ${eventData.checkpoint_name} - ${eventData.timeout_action || 'default action applied'}`;

      case 'checkpoint_cancelled':
        return `🚫 Checkpoint cancelled: ${eventData.checkpoint_name} by ${eventData.cancelled_by}`;

      default:
        return eventType.replace(/_/g, ' ');
    }
  };

  return (
    <div className="flex gap-3 p-3 bg-gray-50 rounded border-l-4 border-blue-400">
      {getEventIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500 uppercase tracking-wide">
            {eventType.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-gray-400">
            {formatDistanceToNow(timestamp, { addSuffix: true })}
          </span>
        </div>
        <p className="text-sm text-gray-900 mt-1 font-medium">
          {formatMessage()}
        </p>
      </div>
    </div>
  );
}
