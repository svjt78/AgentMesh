'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AuthProfile,
  ConnectorMetadata,
  DLQItem,
  INTEGRATION_FABRIC_URL,
  RunDetail,
  RunListItem,
  SecurityPolicy,
  SystemConfig,
  WorkflowDefinition,
  createRun,
  deleteRun,
  getIntegrationSystemConfig,
  getRun,
  listAuthProfiles,
  listConnectors,
  listDLQ,
  listIntegrationWorkflows,
  listRuns,
  listSecurityPolicies,
} from '@/lib/integration-client';
import { SSEEvent, useSSE } from '@/hooks/use-sse';
import { TrashIcon } from '@heroicons/react/24/outline';

const defaultPayload = {
  claim_id: 'CLM-2024-0012',
  policy_id: 'POL-9087',
  claimant_name: 'Jordan Lee',
  loss_date: '2024-08-20',
  loss_description: 'Rear-end collision with minor injuries',
  ssn: '***-**-6789',
  dob: '1990-02-14',
  medical_notes: 'Soft tissue injury - whiplash',
};

export default function IntegrationsPage() {
  const [connectors, setConnectors] = useState<ConnectorMetadata[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [authProfiles, setAuthProfiles] = useState<AuthProfile[]>([]);
  const [securityPolicies, setSecurityPolicies] = useState<SecurityPolicy[]>([]);
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [dlqItems, setDlqItems] = useState<DLQItem[]>([]);
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
  const [workflowId, setWorkflowId] = useState('claim_fnol_sync');
  const [payload, setPayload] = useState(JSON.stringify(defaultPayload, null, 2));
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const activeRunRef = useRef<string | null>(null);

  const workflowOptions = useMemo(() => workflows.map((workflow) => workflow.workflow_id), [workflows]);

  const loadAll = async () => {
    try {
      const [
        connectorsData,
        workflowsData,
        authData,
        securityData,
        systemData,
        runsData,
        dlqData,
      ] = await Promise.all([
        listConnectors(),
        listIntegrationWorkflows(),
        listAuthProfiles(),
        listSecurityPolicies(),
        getIntegrationSystemConfig(),
        listRuns(),
        listDLQ(),
      ]);
      setConnectors(connectorsData.connectors || []);
      setWorkflows(workflowsData.workflows || []);
      setAuthProfiles(authData.profiles || []);
      setSecurityPolicies(securityData.policies || []);
      setSystemConfig(systemData.config || null);
      setRuns(runsData.runs || []);
      setDlqItems(dlqData.items || []);
    } catch (error) {
      setStatus('Failed to load integration fabric data.');
    }
  };

  const refreshRunDetail = async (runId: string) => {
    try {
      const detail = await getRun(runId);
      setSelectedRun(detail);
    } catch (error) {
      setStatus('Failed to load run detail.');
    }
  };

  const handleDeleteRun = async (runId: string) => {
    if (!window.confirm(`Delete run ${runId}? This cannot be undone.`)) {
      return;
    }
    try {
      await deleteRun(runId);
      if (selectedRun?.run_id === runId) {
        setSelectedRun(null);
      }
      if (activeRunId === runId) {
        setActiveRunId(null);
        activeRunRef.current = null;
        setStreamUrl(null);
      }
      await loadAll();
    } catch (error) {
      setStatus('Failed to delete run.');
    }
  };

  const { events: streamEvents, isConnected: streamConnected, error: streamError } = useSSE(streamUrl, {
    eventTypes: ['run_started', 'step_completed', 'step_error', 'idempotent_skip', 'run_completed'],
    completionEvents: ['run_completed'],
    onComplete: () => {
      if (activeRunRef.current) {
        refreshRunDetail(activeRunRef.current);
        loadAll();
      }
    },
    onError: () => {
      setStatus('Live stream disconnected.');
    },
  });

  const handleRun = async () => {
    setStatus('Starting integration run...');
    try {
      const parsedPayload = JSON.parse(payload);
      const response = await createRun({
        workflow_id: workflowId,
        input_data: parsedPayload,
        simulate_failure: simulateFailure,
      });
      setStatus(`Run started: ${response.run_id}`);
      setStreamUrl(`${INTEGRATION_FABRIC_URL}${response.stream_url}`);
      setActiveRunId(response.run_id);
      activeRunRef.current = response.run_id;
      await refreshRunDetail(response.run_id);
      await loadAll();
    } catch (error) {
      setStatus('Run failed to start. Check payload JSON.');
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Integration Fabric</h1>
          <p className="mt-2 text-sm text-gray-600">
            Production-grade integration cockpit for Guidewire, Duck Creek, Socotra, and legacy ecosystems.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Capability Coverage</h2>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>API orchestration with idempotency and retry governance</li>
              <li>SSO + tokenized auth profiles for core systems</li>
              <li>PII masking policies and audit-ready evidence</li>
              <li>Observability, DLQ routing, and replay-ready traces</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Deployment Topology</h2>
            <p className="mt-4 text-sm text-gray-600">
              Single-laptop Docker Compose with modular services. Supports on-prem and cloud patterns with
              environment-driven connector endpoints.
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              {['AWS', 'Azure', 'GCP', 'On-Prem'].map((item) => (
                <span key={item} className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Control Plane</h2>
            <p className="mt-4 text-sm text-gray-600">
              Registry-driven connectors, workflows, and security policies. Configuration changes are tracked
              for SOC2 evidence and governance review.
            </p>
            <div className="mt-4 text-xs text-gray-500">{systemConfig?.version || 'Config loading...'}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Connectors</h2>
            <p className="text-sm text-gray-600">REST integration endpoints with idempotency support.</p>
            <div className="mt-4 space-y-4">
              {connectors.map((connector) => (
                <div key={connector.connector_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900">{connector.name}</h3>
                      <p className="text-xs text-gray-500">{connector.description}</p>
                    </div>
                    <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                      {connector.type}
                    </span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600">
                    <div>Base URL: {connector.base_url}</div>
                    <div>Auth Profile: {connector.auth_profile || 'None'}</div>
                    <div>Idempotency: {connector.supports_idempotency ? 'Enabled' : 'Disabled'}</div>
                    <div>Timeout: {connector.timeout_ms}ms</div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {connector.tags.map((tag) => (
                      <span key={tag} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Auth & SSO Profiles</h2>
            <p className="text-sm text-gray-600">Mock OIDC adapter with token and secret profiles.</p>
            <div className="mt-4 space-y-4">
              {authProfiles.map((profile) => (
                <div key={profile.profile_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900">{profile.name}</h3>
                      <p className="text-xs text-gray-500">{profile.type}</p>
                    </div>
                    <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full">Configured</span>
                  </div>
                  <pre className="mt-3 text-xs bg-gray-50 text-gray-700 rounded p-3 overflow-x-auto">
                    {JSON.stringify(profile.config, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Workflow Catalog</h2>
            <p className="text-sm text-gray-600">Declarative workflows with idempotent steps and governance.</p>
            <div className="mt-4 space-y-4">
              {workflows.map((workflow) => (
                <div key={workflow.workflow_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900">{workflow.name}</h3>
                      <p className="text-xs text-gray-500">{workflow.description}</p>
                    </div>
                    <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded-full">
                      {workflow.trigger}
                    </span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {workflow.steps.map((step) => (
                      <div key={step.id} className="text-xs text-gray-600 flex items-center justify-between">
                        <span>{step.id}</span>
                        <span className="text-gray-500">{step.type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Run Orchestration</h2>
            <p className="text-sm text-gray-600">Trigger an integration run and inspect traces.</p>
            <div className="mt-4 space-y-4">
              <div>
                <label className="text-xs text-gray-500">Workflow</label>
                <select
                  value={workflowId}
                  onChange={(event) => setWorkflowId(event.target.value)}
                  className="mt-2 w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {workflowOptions.map((id) => (
                    <option key={id} value={id}>
                      {id}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500">Payload</label>
                <textarea
                  value={payload}
                  onChange={(event) => setPayload(event.target.value)}
                  rows={8}
                  className="mt-2 w-full border border-gray-300 rounded-md px-3 py-2 text-xs font-mono"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-600 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={simulateFailure}
                    onChange={(event) => setSimulateFailure(event.target.checked)}
                    className="h-4 w-4"
                  />
                  Simulate failure (DLQ)
                </label>
                <button
                  onClick={handleRun}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
                >
                  Run Workflow
                </button>
              </div>
              {status && <p className="text-xs text-gray-500">{status}</p>}
              {streamUrl && (
                <div className="border-t border-gray-100 pt-4 mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-gray-700">Live Stream</span>
                    <span className={streamConnected ? 'text-green-600' : 'text-gray-500'}>
                      {streamConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  {activeRunId && (
                    <div className="text-xs text-gray-500 mt-1">Run ID: {activeRunId}</div>
                  )}
                  {streamError && <p className="text-xs text-red-600 mt-2">{streamError}</p>}
                  <div className="mt-3 space-y-2 max-h-52 overflow-y-auto">
                    {streamEvents.length === 0 ? (
                      <p className="text-xs text-gray-500">Waiting for events...</p>
                    ) : (
                      streamEvents.map((event, index) => (
                        <IntegrationEventRow key={`${event.id || 'event'}-${index}`} event={event} />
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Run Timeline</h2>
            <p className="text-sm text-gray-600">Select a run to view steps, events, and audit notes.</p>
            <div className="mt-4 space-y-3">
              {runs.map((run) => (
                <div
                  key={run.run_id}
                  role="button"
                  tabIndex={0}
                  onClick={() => refreshRunDetail(run.run_id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      refreshRunDetail(run.run_id);
                    }
                  }}
                  className="w-full text-left border border-gray-200 rounded-md px-3 py-2 text-xs hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-800">{run.workflow_id}</span>
                    <span className="text-gray-500">{run.status}</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-500">
                    <span>{run.run_id}</span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleDeleteRun(run.run_id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600"
                      aria-label={`Delete run ${run.run_id}`}
                      title="Delete run"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Run Detail</h2>
            <p className="text-sm text-gray-600">Evidence map and troubleshooting signals.</p>
            {selectedRun ? (
              <div className="mt-4 space-y-4">
                <div className="text-xs text-gray-600">
                  <div>Status: {selectedRun.status}</div>
                  <div>Run ID: {selectedRun.run_id}</div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Steps</h3>
                  <div className="space-y-2">
                    {selectedRun.steps.map((step) => (
                      <div key={step.step_id} className="text-xs border border-gray-200 rounded-md p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{step.step_id}</span>
                          <span className="text-gray-500">{step.status}</span>
                        </div>
                        <div className="text-gray-500">Attempts: {step.attempts}</div>
                        {step.error && <div className="text-red-600">Error: {step.error}</div>}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Events</h3>
                  <pre className="text-xs bg-gray-50 text-gray-700 rounded p-3 max-h-48 overflow-y-auto">
                    {JSON.stringify(selectedRun.events, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-xs text-gray-500">Select a run to inspect details.</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Dead Letter Queue</h2>
            <p className="text-sm text-gray-600">Failed steps routed for human review and replay.</p>
            <div className="mt-4 space-y-3">
              {dlqItems.length === 0 && <p className="text-xs text-gray-500">No DLQ items yet.</p>}
              {dlqItems.map((item) => (
                <div key={item.item_id} className="border border-gray-200 rounded-md p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{item.workflow_id}</span>
                    <span className="text-gray-500">{item.step_id}</span>
                  </div>
                  <div className="text-red-600">{item.error}</div>
                  <div className="text-gray-500">{item.item_id}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900">Security & Compliance</h2>
            <p className="text-sm text-gray-600">PII masking, HIPAA/PCI guardrails, SOC2 evidence.</p>
            <div className="mt-4 space-y-4">
              {securityPolicies.map((policy) => (
                <div key={policy.policy_id} className="border border-gray-200 rounded-md p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900">{policy.name}</h3>
                      <p className="text-xs text-gray-500">{policy.description}</p>
                    </div>
                    <span className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-full">PII Guard</span>
                  </div>
                  <div className="mt-3 text-xs text-gray-600 space-y-1">
                    {policy.rules.map((rule) => (
                      <div key={`${policy.policy_id}-${rule.field}`}>
                        {rule.field}: {rule.action}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900">Event-Driven & Publish/Subscribe</h2>
          <p className="text-sm text-gray-600">
            Configured channels for MQ and pub/sub integration paths. Enabled in configuration (no runtime wiring in
            prototype).
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {systemConfig?.features?.event_driven_channels?.map((channel: string) => (
              <span key={channel} className="px-3 py-1 rounded-full text-xs bg-indigo-50 text-indigo-700">
                {channel}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function IntegrationEventRow({ event }: { event: SSEEvent }) {
  const eventType = event.event || event.data?.event_type || 'event';
  const eventData = event.data || {};
  const stepId = eventData.step_id;
  const timestamp = eventData.timestamp || event.timestamp;

  const message = () => {
    switch (eventType) {
      case 'run_started':
        return `Run started for ${eventData.workflow_id || 'workflow'}`;
      case 'step_completed':
        return `Step ${stepId} completed`;
      case 'step_error':
        return `Step ${stepId} failed: ${eventData.payload?.error || 'error'}`;
      case 'idempotent_skip':
        return `Step ${stepId} skipped (idempotent)`;
      case 'run_completed':
        return `Run completed: ${eventData.status || 'unknown'}`;
      default:
        return eventType.replace(/_/g, ' ');
    }
  };

  const statusColor = () => {
    if (eventType === 'run_completed' || eventType === 'step_completed') return 'bg-green-500';
    if (eventType === 'step_error') return 'bg-red-500';
    return 'bg-blue-500';
  };

  return (
    <div className="flex items-center gap-2 text-xs text-gray-600">
      <span className={`h-2 w-2 rounded-full ${statusColor()}`} />
      <span className="font-medium text-gray-800">{message()}</span>
      <span className="ml-auto text-gray-400">{new Date(timestamp).toLocaleTimeString()}</span>
    </div>
  );
}
