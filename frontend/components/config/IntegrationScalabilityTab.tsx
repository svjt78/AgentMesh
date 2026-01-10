'use client';

import { useMemo, useState } from 'react';
import Tooltip from '@/components/config/Tooltip';

type BackpressureMode = 'reject' | 'queue' | 'shed_load';
type WorkflowPriority = 'critical' | 'standard' | 'bulk';

const connectorDefaults = [
  {
    id: 'guidewire_claims',
    name: 'Guidewire Claims',
    scaling: { maxConcurrency: 10, qpsLimit: 25, burstLimit: 50 },
    circuit: { failureThreshold: 5, openDurationMs: 30000, halfOpenAttempts: 2 },
    region: { primary: 'us-west-2', fallback: 'us-east-1' },
  },
  {
    id: 'duckcreek_policy',
    name: 'Duck Creek Policy',
    scaling: { maxConcurrency: 8, qpsLimit: 20, burstLimit: 40 },
    circuit: { failureThreshold: 4, openDurationMs: 20000, halfOpenAttempts: 2 },
    region: { primary: 'us-east-1', fallback: 'us-west-2' },
  },
  {
    id: 'socotra_billing',
    name: 'Socotra Billing',
    scaling: { maxConcurrency: 6, qpsLimit: 15, burstLimit: 30 },
    circuit: { failureThreshold: 3, openDurationMs: 15000, halfOpenAttempts: 1 },
    region: { primary: 'us-central-1', fallback: 'us-east-1' },
  },
  {
    id: 'mainframe_legacy',
    name: 'Mainframe Legacy',
    scaling: { maxConcurrency: 4, qpsLimit: 8, burstLimit: 16 },
    circuit: { failureThreshold: 2, openDurationMs: 45000, halfOpenAttempts: 1 },
    region: { primary: 'us-east-1', fallback: '' },
  },
];

const workflowDefaults = [
  {
    id: 'claim_fnol_sync',
    name: 'Claim FNOL Sync',
    priority: 'critical' as WorkflowPriority,
    sla: { maxLatencyMs: 1500, timeoutMs: 5000, fastFailThreshold: 2 },
    throughput: { maxConcurrency: 5, queueDepthLimit: 100 },
  },
  {
    id: 'claim_status_update',
    name: 'Claim Status Update',
    priority: 'standard' as WorkflowPriority,
    sla: { maxLatencyMs: 2000, timeoutMs: 6000, fastFailThreshold: 2 },
    throughput: { maxConcurrency: 4, queueDepthLimit: 120 },
  },
  {
    id: 'billing_sync',
    name: 'Billing Sync',
    priority: 'standard' as WorkflowPriority,
    sla: { maxLatencyMs: 2500, timeoutMs: 7000, fastFailThreshold: 2 },
    throughput: { maxConcurrency: 3, queueDepthLimit: 80 },
  },
  {
    id: 'integration_failure_drill',
    name: 'Integration Failure Drill',
    priority: 'bulk' as WorkflowPriority,
    sla: { maxLatencyMs: 4000, timeoutMs: 10000, fastFailThreshold: 1 },
    throughput: { maxConcurrency: 2, queueDepthLimit: 40 },
  },
];

const authProfiles = [
  {
    id: 'gw_oauth',
    name: 'Guidewire OAuth',
    tenantId: 'enterprise-001',
    qpsLimit: 20,
    burstLimit: 40,
    priorityOverride: 'critical' as WorkflowPriority,
  },
  {
    id: 'duckcreek_token',
    name: 'Duck Creek Token',
    tenantId: 'enterprise-002',
    qpsLimit: 15,
    burstLimit: 30,
    priorityOverride: 'standard' as WorkflowPriority,
  },
  {
    id: 'socotra_api_key',
    name: 'Socotra API Key',
    tenantId: 'enterprise-003',
    qpsLimit: 10,
    burstLimit: 20,
    priorityOverride: 'standard' as WorkflowPriority,
  },
  {
    id: 'mainframe_service_account',
    name: 'Mainframe Service Account',
    tenantId: 'legacy-001',
    qpsLimit: 5,
    burstLimit: 10,
    priorityOverride: 'bulk' as WorkflowPriority,
  },
];

export default function IntegrationScalabilityTab() {
  const [status, setStatus] = useState('');
  const [systemDefaults, setSystemDefaults] = useState({
    maxConcurrency: 50,
    qpsLimit: 200,
    burstLimit: 400,
    queueDepthLimit: 1000,
    backpressureMode: 'queue' as BackpressureMode,
  });
  const [retryProfiles, setRetryProfiles] = useState([
    { id: 'standard', maxAttempts: 3, baseBackoffMs: 250, maxBackoffMs: 2000, jitterPct: 20 },
    { id: 'aggressive', maxAttempts: 5, baseBackoffMs: 150, maxBackoffMs: 1500, jitterPct: 10 },
  ]);
  const [eventChannels, setEventChannels] = useState({
    pubsub: { enabled: true, batchSize: 50, pollIntervalMs: 200, maxParallelConsumers: 16 },
    mq: { enabled: true, batchSize: 20, pollIntervalMs: 500, maxParallelConsumers: 8 },
    event_bridge: { enabled: false, batchSize: 10, pollIntervalMs: 1000, maxParallelConsumers: 4 },
  });
  const [selectedConnectorId, setSelectedConnectorId] = useState(connectorDefaults[0].id);
  const [connectorState, setConnectorState] = useState(connectorDefaults);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(workflowDefaults[0].id);
  const [workflowState, setWorkflowState] = useState(workflowDefaults);
  const [selectedAuthId, setSelectedAuthId] = useState(authProfiles[0].id);
  const [authState, setAuthState] = useState(authProfiles);

  const selectedConnector = useMemo(
    () => connectorState.find((item) => item.id === selectedConnectorId) || connectorState[0],
    [connectorState, selectedConnectorId],
  );

  const selectedWorkflow = useMemo(
    () => workflowState.find((item) => item.id === selectedWorkflowId) || workflowState[0],
    [workflowState, selectedWorkflowId],
  );

  const selectedAuth = useMemo(
    () => authState.find((item) => item.id === selectedAuthId) || authState[0],
    [authState, selectedAuthId],
  );

  const saveNotice = (label: string) => {
    setStatus(`${label} saved locally (not yet wired to backend).`);
    setTimeout(() => setStatus(''), 2500);
  };

  const updateConnectorField = (field: string, value: number | string) => {
    setConnectorState((prev) =>
      prev.map((item) => {
        if (item.id !== selectedConnectorId) return item;
        if (field in item.scaling) {
          return { ...item, scaling: { ...item.scaling, [field]: value as number } };
        }
        if (field in item.circuit) {
          return { ...item, circuit: { ...item.circuit, [field]: value as number } };
        }
        if (field === 'primary' || field === 'fallback') {
          return { ...item, region: { ...item.region, [field]: value as string } };
        }
        return item;
      }),
    );
  };

  const updateWorkflowField = (field: string, value: number | string) => {
    setWorkflowState((prev) =>
      prev.map((item) => {
        if (item.id !== selectedWorkflowId) return item;
        if (field === 'priority') {
          return { ...item, priority: value as WorkflowPriority };
        }
        if (field in item.sla) {
          return { ...item, sla: { ...item.sla, [field]: value as number } };
        }
        if (field in item.throughput) {
          return { ...item, throughput: { ...item.throughput, [field]: value as number } };
        }
        return item;
      }),
    );
  };

  const updateAuthField = (field: string, value: number | string) => {
    setAuthState((prev) =>
      prev.map((item) => {
        if (item.id !== selectedAuthId) return item;
        return { ...item, [field]: value };
      }),
    );
  };

  const LabelWithTooltip = ({ label, tooltip }: { label: string; tooltip: string }) => (
    <div className="flex items-center gap-2">
      <span>{label}</span>
      <Tooltip content={tooltip}>
        <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-gray-200 text-[10px] text-gray-700">
          ?
        </span>
      </Tooltip>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Integration Scalability</h2>
        <p className="text-sm text-gray-600">
          Configure throughput, resiliency, and tenant limits with form controls. Changes are saved locally for now.
        </p>
        {status && <p className="mt-2 text-xs text-green-600">{status}</p>}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">System Defaults</h3>
            <button
              onClick={() => saveNotice('System defaults')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Max Concurrency"
                tooltip="Hard cap on simultaneous integrations across the platform."
              />
              <input
                type="number"
                value={systemDefaults.maxConcurrency}
                onChange={(event) =>
                  setSystemDefaults((prev) => ({ ...prev, maxConcurrency: Number(event.target.value) }))
                }
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip label="QPS Limit" tooltip="Maximum requests per second across all connectors." />
              <input
                type="number"
                value={systemDefaults.qpsLimit}
                onChange={(event) =>
                  setSystemDefaults((prev) => ({ ...prev, qpsLimit: Number(event.target.value) }))
                }
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Burst Limit"
                tooltip="Short-term burst capacity allowed above steady-state QPS."
              />
              <input
                type="number"
                value={systemDefaults.burstLimit}
                onChange={(event) =>
                  setSystemDefaults((prev) => ({ ...prev, burstLimit: Number(event.target.value) }))
                }
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Queue Depth"
                tooltip="Maximum number of queued tasks waiting for execution."
              />
              <input
                type="number"
                value={systemDefaults.queueDepthLimit}
                onChange={(event) =>
                  setSystemDefaults((prev) => ({ ...prev, queueDepthLimit: Number(event.target.value) }))
                }
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1 col-span-2">
              <LabelWithTooltip
                label="Backpressure Mode"
                tooltip="What to do when capacity is exceeded: reject, queue, or shed load."
              />
              <select
                value={systemDefaults.backpressureMode}
                onChange={(event) =>
                  setSystemDefaults((prev) => ({ ...prev, backpressureMode: event.target.value as BackpressureMode }))
                }
                className="w-full border rounded px-2 py-1"
              >
                <option value="queue">Queue</option>
                <option value="reject">Reject</option>
                <option value="shed_load">Shed Load</option>
              </select>
            </label>
          </div>
        </div>

        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Retry Profiles</h3>
            <button
              onClick={() => saveNotice('Retry profiles')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <div className="space-y-4">
            {retryProfiles.map((profile, index) => (
              <div key={profile.id} className="border border-gray-100 rounded-md p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-800">{profile.id}</span>
                  <span className="text-[11px] text-gray-500">Profile {index + 1}</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs text-gray-600">
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Max Attempts"
                      tooltip="Total tries before marking a step as failed."
                    />
                    <input
                      type="number"
                      value={profile.maxAttempts}
                      onChange={(event) => {
                        const next = Number(event.target.value);
                        setRetryProfiles((prev) =>
                          prev.map((item) => (item.id === profile.id ? { ...item, maxAttempts: next } : item)),
                        );
                      }}
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Base Backoff (ms)"
                      tooltip="Initial wait time before the first retry."
                    />
                    <input
                      type="number"
                      value={profile.baseBackoffMs}
                      onChange={(event) => {
                        const next = Number(event.target.value);
                        setRetryProfiles((prev) =>
                          prev.map((item) => (item.id === profile.id ? { ...item, baseBackoffMs: next } : item)),
                        );
                      }}
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Max Backoff (ms)"
                      tooltip="Upper bound on exponential backoff delay."
                    />
                    <input
                      type="number"
                      value={profile.maxBackoffMs}
                      onChange={(event) => {
                        const next = Number(event.target.value);
                        setRetryProfiles((prev) =>
                          prev.map((item) => (item.id === profile.id ? { ...item, maxBackoffMs: next } : item)),
                        );
                      }}
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                  <label className="space-y-1">
                    <LabelWithTooltip label="Jitter %" tooltip="Randomization added to spread retry spikes." />
                    <input
                      type="number"
                      value={profile.jitterPct}
                      onChange={(event) => {
                        const next = Number(event.target.value);
                        setRetryProfiles((prev) =>
                          prev.map((item) => (item.id === profile.id ? { ...item, jitterPct: next } : item)),
                        );
                      }}
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Event Channels</h3>
            <button
              onClick={() => saveNotice('Event channel policies')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <div className="space-y-4">
            {Object.entries(eventChannels).map(([key, channel]) => (
              <div key={key} className="border border-gray-100 rounded-md p-3">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-gray-800">{key}</span>
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    <input
                      type="checkbox"
                      checked={channel.enabled}
                      onChange={(event) =>
                        setEventChannels((prev) => ({
                          ...prev,
                          [key]: { ...prev[key as keyof typeof prev], enabled: event.target.checked },
                        }))
                      }
                    />
                    <LabelWithTooltip
                      label="Enabled"
                      tooltip="Toggle the channel configuration on or off."
                    />
                  </label>
                </div>
                <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Batch Size"
                      tooltip="Number of messages pulled per poll cycle."
                    />
                    <input
                      type="number"
                      value={channel.batchSize}
                      onChange={(event) =>
                        setEventChannels((prev) => ({
                          ...prev,
                          [key]: { ...prev[key as keyof typeof prev], batchSize: Number(event.target.value) },
                        }))
                      }
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Poll Interval"
                      tooltip="Time between polls for new messages."
                    />
                    <input
                      type="number"
                      value={channel.pollIntervalMs}
                      onChange={(event) =>
                        setEventChannels((prev) => ({
                          ...prev,
                          [key]: { ...prev[key as keyof typeof prev], pollIntervalMs: Number(event.target.value) },
                        }))
                      }
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                  <label className="space-y-1">
                    <LabelWithTooltip
                      label="Consumers"
                      tooltip="Parallel consumers assigned to this channel."
                    />
                    <input
                      type="number"
                      value={channel.maxParallelConsumers}
                      onChange={(event) =>
                        setEventChannels((prev) => ({
                          ...prev,
                          [key]: { ...prev[key as keyof typeof prev], maxParallelConsumers: Number(event.target.value) },
                        }))
                      }
                      className="w-full border rounded px-2 py-1"
                    />
                  </label>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Connector Scalability</h3>
            <button
              onClick={() => saveNotice('Connector settings')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <select
            value={selectedConnectorId}
            onChange={(event) => setSelectedConnectorId(event.target.value)}
            className="mb-3 w-full border border-gray-300 rounded-md px-3 py-2 text-xs"
          >
            {connectorState.map((connector) => (
              <option key={connector.id} value={connector.id}>
                {connector.name}
              </option>
            ))}
          </select>
          <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Max Concurrency"
                tooltip="Connector-level cap on in-flight requests."
              />
              <input
                type="number"
                value={selectedConnector.scaling.maxConcurrency}
                onChange={(event) => updateConnectorField('maxConcurrency', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="QPS Limit"
                tooltip="Requests per second allowed for this connector."
              />
              <input
                type="number"
                value={selectedConnector.scaling.qpsLimit}
                onChange={(event) => updateConnectorField('qpsLimit', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Burst Limit"
                tooltip="Short spike allowance for this connector."
              />
              <input
                type="number"
                value={selectedConnector.scaling.burstLimit}
                onChange={(event) => updateConnectorField('burstLimit', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Failure Threshold"
                tooltip="Failures before circuit breaker opens."
              />
              <input
                type="number"
                value={selectedConnector.circuit.failureThreshold}
                onChange={(event) => updateConnectorField('failureThreshold', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Open Duration (ms)"
                tooltip="Time to keep the breaker open before half-open tries."
              />
              <input
                type="number"
                value={selectedConnector.circuit.openDurationMs}
                onChange={(event) => updateConnectorField('openDurationMs', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Half-Open Attempts"
                tooltip="Trial requests allowed before closing the breaker."
              />
              <input
                type="number"
                value={selectedConnector.circuit.halfOpenAttempts}
                onChange={(event) => updateConnectorField('halfOpenAttempts', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Primary Region"
                tooltip="Preferred region for connector execution."
              />
              <input
                type="text"
                value={selectedConnector.region.primary}
                onChange={(event) => updateConnectorField('primary', event.target.value)}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Fallback Region"
                tooltip="Secondary region used when primary is unhealthy."
              />
              <input
                type="text"
                value={selectedConnector.region.fallback}
                onChange={(event) => updateConnectorField('fallback', event.target.value)}
                className="w-full border rounded px-2 py-1"
              />
            </label>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Workflow Scaling</h3>
            <button
              onClick={() => saveNotice('Workflow settings')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <select
            value={selectedWorkflowId}
            onChange={(event) => setSelectedWorkflowId(event.target.value)}
            className="mb-3 w-full border border-gray-300 rounded-md px-3 py-2 text-xs"
          >
            {workflowState.map((workflow) => (
              <option key={workflow.id} value={workflow.id}>
                {workflow.name}
              </option>
            ))}
          </select>
          <label className="block text-xs text-gray-600 mb-2">
            <LabelWithTooltip
              label="Priority"
              tooltip="Scheduling tier for this workflow."
            />
            <select
              value={selectedWorkflow.priority}
              onChange={(event) => updateWorkflowField('priority', event.target.value)}
              className="mt-1 w-full border rounded px-2 py-1"
            >
              <option value="critical">Critical</option>
              <option value="standard">Standard</option>
              <option value="bulk">Bulk</option>
            </select>
          </label>
          <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Max Latency (ms)"
                tooltip="Target p95 latency for workflow completion."
              />
              <input
                type="number"
                value={selectedWorkflow.sla.maxLatencyMs}
                onChange={(event) => updateWorkflowField('maxLatencyMs', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Timeout (ms)"
                tooltip="Hard timeout for the workflow execution."
              />
              <input
                type="number"
                value={selectedWorkflow.sla.timeoutMs}
                onChange={(event) => updateWorkflowField('timeoutMs', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Fast Fail"
                tooltip="Errors before short-circuiting the workflow."
              />
              <input
                type="number"
                value={selectedWorkflow.sla.fastFailThreshold}
                onChange={(event) => updateWorkflowField('fastFailThreshold', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Max Concurrency"
                tooltip="Concurrent runs allowed for this workflow."
              />
              <input
                type="number"
                value={selectedWorkflow.throughput.maxConcurrency}
                onChange={(event) => updateWorkflowField('maxConcurrency', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Queue Depth"
                tooltip="Maximum queued runs for this workflow."
              />
              <input
                type="number"
                value={selectedWorkflow.throughput.queueDepthLimit}
                onChange={(event) => updateWorkflowField('queueDepthLimit', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
          </div>
        </div>

        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Tenant Limits</h3>
            <button
              onClick={() => saveNotice('Tenant limits')}
              className="px-3 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
            >
              Save
            </button>
          </div>
          <select
            value={selectedAuthId}
            onChange={(event) => setSelectedAuthId(event.target.value)}
            className="mb-3 w-full border border-gray-300 rounded-md px-3 py-2 text-xs"
          >
            {authState.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.name}
              </option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-3 text-xs text-gray-600">
            <label className="space-y-1">
              <LabelWithTooltip
                label="Tenant ID"
                tooltip="Tenant or business unit this limit applies to."
              />
              <input
                type="text"
                value={selectedAuth.tenantId}
                onChange={(event) => updateAuthField('tenantId', event.target.value)}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Priority Override"
                tooltip="Force a scheduling tier for this tenant."
              />
              <select
                value={selectedAuth.priorityOverride}
                onChange={(event) => updateAuthField('priorityOverride', event.target.value)}
                className="w-full border rounded px-2 py-1"
              >
                <option value="critical">Critical</option>
                <option value="standard">Standard</option>
                <option value="bulk">Bulk</option>
              </select>
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="QPS Limit"
                tooltip="Per-tenant requests per second cap."
              />
              <input
                type="number"
                value={selectedAuth.qpsLimit}
                onChange={(event) => updateAuthField('qpsLimit', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
            <label className="space-y-1">
              <LabelWithTooltip
                label="Burst Limit"
                tooltip="Per-tenant short burst allowance."
              />
              <input
                type="number"
                value={selectedAuth.burstLimit}
                onChange={(event) => updateAuthField('burstLimit', Number(event.target.value))}
                className="w-full border rounded px-2 py-1"
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
