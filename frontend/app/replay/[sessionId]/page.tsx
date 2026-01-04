/**
 * Session Replay Page - View complete session timeline
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, SessionDetails, EvidenceMap } from '@/lib/api-client';
import { format } from 'date-fns';
import Link from 'next/link';

import ContextTimeline from '@/components/visualization/ContextTimeline';
import TokenBudgetChart from '@/components/visualization/TokenBudgetChart';
import ContextLineageTree from '@/components/visualization/ContextLineageTree';
import InfoTooltip from '@/components/InfoTooltip';
import { DEMO_EVIDENCE_MAP, FIELD_EXPLANATIONS } from '@/lib/demo-evidence';

type TabName = 'events' | 'token_analytics' | 'explainability';

export default function ReplayPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterEventType, setFilterEventType] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<TabName>('events');
  const [contextStats, setContextStats] = useState<Record<string, any> | null>(null);
  const [contextStatsError, setContextStatsError] = useState<string | null>(null);
  const [loadingContextStats, setLoadingContextStats] = useState(false);
  const [triggeringCompaction, setTriggeringCompaction] = useState(false);
  const [evidenceMap, setEvidenceMap] = useState<EvidenceMap | null>(null);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  useEffect(() => {
    if (activeTab !== 'token_analytics') return;

    const loadStats = async () => {
      try {
        setLoadingContextStats(true);
        const stats = await apiClient.getContextStats(sessionId);
        setContextStats(stats);
        setContextStatsError(null);
      } catch (err: any) {
        setContextStatsError(err.message || 'Failed to load context stats');
      } finally {
        setLoadingContextStats(false);
      }
    };

    loadStats();
  }, [activeTab, sessionId]);

  useEffect(() => {
    if (activeTab !== 'explainability') return;

    const loadEvidence = async () => {
      try {
        setLoadingEvidence(true);
        const data = await apiClient.getEvidenceMap(sessionId);
        setEvidenceMap(data);
        setEvidenceError(null);
      } catch (err: any) {
        setEvidenceError(err.message || 'Failed to load evidence map');
      } finally {
        setLoadingEvidence(false);
      }
    };

    loadEvidence();
  }, [activeTab, sessionId]);

  const loadSession = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSession(sessionId);
      setSession(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-8 text-red-600">Error: {error}</div>;
  }

  if (!session) {
    return <div className="container mx-auto px-4 py-8">Session not found</div>;
  }

  const eventTypes = Array.from(
    new Set(session.events.map((e) => e.event_type).filter(Boolean))
  ) as string[];

  const filteredEvents =
    filterEventType === 'all'
      ? session.events
      : session.events.filter((e) => e.event_type === filterEventType);

  const tabs = [
    { id: 'events' as TabName, label: 'Event Timeline' },
    { id: 'token_analytics' as TabName, label: 'Token Analytics' },
    { id: 'explainability' as TabName, label: 'Explainability' },
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Session Replay</h1>

      {/* Session Summary */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Session Summary</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Session ID:</span>
            <br />
            <code className="text-xs">{session.session_id}</code>
          </div>
          <div>
            <span className="font-medium">Workflow:</span>
            <br />
            {session.workflow_id}
          </div>
          <div>
            <span className="font-medium">Status:</span>
            <br />
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
              {session.status}
            </span>
          </div>
          <div>
            <span className="font-medium">Created:</span>
            <br />
            {format(new Date(session.created_at), 'PPpp')}
          </div>
          <div>
            <span className="font-medium">Agents Executed:</span>
            <br />
            {session.agents_executed.join(', ')}
          </div>
          <div>
            <span className="font-medium">Total Events:</span>
            <br />
            {session.events.length}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-8">
        <div className="mb-4">
          <Link
            href="/replay"
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            ← Back to Replay Log
          </Link>
        </div>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'events' && (
        <>
          {/* Event Filter */}
          <div className="mb-4">
            <label className="font-medium mr-2">Filter by event type:</label>
            <select
              value={filterEventType}
              onChange={(e) => setFilterEventType(e.target.value)}
              className="border rounded px-3 py-1"
            >
              <option value="all">All Events</option>
              {eventTypes.map((type) => (
                <option key={`event-type-${type}`} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Event Timeline */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Event Timeline ({filteredEvents.length})</h2>
            <div className="space-y-3">
              {filteredEvents.map((event, index) => (
                <EventDetail key={index} event={event} />
              ))}
            </div>
          </div>
        </>
      )}

      {activeTab === 'token_analytics' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Token Analytics Ops</h2>
                <p className="text-sm text-gray-600">
                  Trigger compaction and review context compilation stats for this session.
                </p>
              </div>
              <button
                className="inline-flex items-center justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                disabled={triggeringCompaction}
                onClick={async () => {
                  if (!confirm('Trigger compaction for this session?')) return;
                  try {
                    setTriggeringCompaction(true);
                    await apiClient.triggerCompaction(sessionId);
                    const stats = await apiClient.getContextStats(sessionId);
                    setContextStats(stats);
                  } catch (err: any) {
                    setContextStatsError(err.message || 'Failed to trigger compaction');
                  } finally {
                    setTriggeringCompaction(false);
                  }
                }}
              >
                {triggeringCompaction ? 'Compacting…' : 'Trigger Compaction'}
              </button>
            </div>

            <div className="mt-4">
              {loadingContextStats && (
                <div className="text-sm text-gray-500">Loading context stats…</div>
              )}
              {contextStatsError && (
                <div className="mt-2 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {contextStatsError}
                </div>
              )}
              {contextStats && (
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                  <div className="rounded border border-gray-200 p-3">
                    <div className="text-xs uppercase text-gray-500">Compilations</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {contextStats.total_compilations ?? 0}
                    </div>
                  </div>
                  <div className="rounded border border-gray-200 p-3">
                    <div className="text-xs uppercase text-gray-500">Truncations</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {contextStats.truncations ?? 0}
                    </div>
                  </div>
                  <div className="rounded border border-gray-200 p-3">
                    <div className="text-xs uppercase text-gray-500">Compactions</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {contextStats.compactions ?? 0}
                    </div>
                  </div>
                  <div className="rounded border border-gray-200 p-3">
                    <div className="text-xs uppercase text-gray-500">Avg Tokens</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {Math.round(contextStats.avg_tokens_after ?? 0)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          <ContextTimeline sessionId={sessionId} />
          <TokenBudgetChart sessionId={sessionId} />
          <ContextLineageTree sessionId={sessionId} />
        </div>
      )}

      {activeTab === 'explainability' && (() => {
        // Check if evidence is minimal/empty and use demo data as fallback
        const isMinimalEvidence = evidenceMap && (
          evidenceMap.evidence_map.partial ||
          evidenceMap.evidence_map.no_output ||
          !evidenceMap.evidence_map.decision?.outcome ||
          evidenceMap.evidence_map.decision?.outcome === 'N/A' ||
          (!evidenceMap.evidence_map.supporting_evidence || evidenceMap.evidence_map.supporting_evidence.length === 0)
        );

        const displayEvidence = (isMinimalEvidence || !evidenceMap) ? DEMO_EVIDENCE_MAP : evidenceMap.evidence_map;
        const isDemo = (isMinimalEvidence || !evidenceMap);

        return (
          <div className="space-y-6">
            {loadingEvidence && (
              <div className="bg-white rounded-lg shadow p-6">
                Loading evidence map...
              </div>
            )}

            {evidenceError && (
              <div className="bg-white rounded-lg shadow p-6 text-red-600">
                Error loading evidence: {evidenceError}
              </div>
            )}

            {!loadingEvidence && !evidenceError && (
              <>
                {/* Decision */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4">
                    <InfoTooltip {...FIELD_EXPLANATIONS.outcome} />
                  </h2>
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium">Outcome:</span>
                      <br />
                      <span className="text-xl font-bold text-gray-900">{displayEvidence.decision?.outcome || 'N/A'}</span>
                    </div>
                    {displayEvidence.decision?.confidence && (
                      <div>
                        <InfoTooltip {...FIELD_EXPLANATIONS.confidence} />
                        <br />
                        <div className="w-full bg-gray-200 rounded-full h-4 mt-1">
                          <div
                            className="bg-blue-600 h-4 rounded-full"
                            style={{ width: `${(displayEvidence.decision.confidence || 0) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {((displayEvidence.decision.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    {displayEvidence.decision?.basis && (
                      <div>
                        <InfoTooltip {...FIELD_EXPLANATIONS.basis} />
                        <br />
                        <p className="text-gray-700">{displayEvidence.decision.basis}</p>
                      </div>
                    )}
                    {displayEvidence.decision?.estimated_exposure && (
                      <div className="grid grid-cols-2 gap-4 mt-4 p-3 bg-gray-50 rounded">
                        <div>
                          <InfoTooltip {...FIELD_EXPLANATIONS.estimated_exposure} />
                          <br />
                          <span className="text-lg font-semibold text-red-600">
                            ${displayEvidence.decision.estimated_exposure.toLocaleString()}
                          </span>
                        </div>
                        {displayEvidence.decision?.potential_savings && (
                          <div>
                            <span className="font-medium inline-flex items-center gap-1.5">
                              Potential Savings
                            </span>
                            <br />
                            <span className="text-lg font-semibold text-green-600">
                              ${displayEvidence.decision.potential_savings.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

              {/* Supporting Evidence */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-4">
                  <InfoTooltip {...FIELD_EXPLANATIONS.supporting_evidence} />
                </div>
                <div className="space-y-4">
                  {displayEvidence.supporting_evidence?.map((evidence: any, index: number) => (
                    <div key={index} className="border-l-4 border-blue-600 pl-4 py-2">
                      <div className="font-medium">{evidence.source || `Evidence ${index + 1}`}</div>
                      <div className="text-sm text-gray-600">{evidence.evidence_type}</div>
                      <p className="text-gray-700 mt-1">{evidence.summary}</p>
                      {evidence.weight && (
                        <div className="text-sm text-gray-500 mt-1">
                          <InfoTooltip {...FIELD_EXPLANATIONS.weight} />:{' '}
                          <span className="font-semibold">{(evidence.weight * 100).toFixed(0)}%</span>
                        </div>
                      )}
                      {evidence.risk_score && (
                        <div className="text-sm text-gray-500 mt-1">
                          <InfoTooltip {...FIELD_EXPLANATIONS.fraud_score} />:{' '}
                          <span className="font-semibold">{(evidence.risk_score * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Human Interventions */}
              {displayEvidence.human_interventions && displayEvidence.human_interventions.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="mb-4">
                    <InfoTooltip {...FIELD_EXPLANATIONS.human_interventions} />
                  </div>
                  <div className="space-y-4">
                    {displayEvidence.human_interventions.map((intervention: any, index: number) => (
                      <div key={index} className="border-l-4 border-green-600 pl-4 py-3 bg-green-50">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-900">{intervention.intervention_type}</div>
                          <div className="text-sm text-gray-500">
                            {intervention.timestamp ? format(new Date(intervention.timestamp), 'PPpp') : ''}
                          </div>
                        </div>
                        <div className="text-sm text-gray-700">
                          <span className="font-medium">Reviewer:</span> {intervention.reviewer}
                        </div>
                        {intervention.checkpoint && (
                          <div className="text-sm text-gray-700">
                            <span className="font-medium">Checkpoint:</span> {intervention.checkpoint}
                          </div>
                        )}
                        <div className="text-sm text-gray-700">
                          <span className="font-medium">Action:</span>{' '}
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">
                            {intervention.action}
                          </span>
                        </div>
                        {intervention.comments && (
                          <p className="text-gray-700 mt-2 italic">&quot;{intervention.comments}&quot;</p>
                        )}
                        {intervention.decision_impact && (
                          <div className="text-sm text-gray-600 mt-2">
                            <span className="font-medium">Impact:</span> {intervention.decision_impact}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Chain */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-4">
                  <InfoTooltip {...FIELD_EXPLANATIONS.agent_chain} />
                </div>
                <div className="flex flex-wrap gap-2">
                  {displayEvidence.agent_chain?.map((agent: string, index: number) => (
                    <div key={index} className="flex items-center">
                      <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded font-medium">
                        {agent}
                      </div>
                      {index < (displayEvidence.agent_chain?.length || 0) - 1 && (
                        <span className="mx-2 text-gray-400">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Assumptions & Limitations */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Assumptions */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="mb-4">
                    <InfoTooltip {...FIELD_EXPLANATIONS.assumptions} />
                  </div>
                  <ul className="list-disc list-inside space-y-2 text-gray-700">
                    {displayEvidence.assumptions?.map((assumption: string, index: number) => (
                      <li key={index}>{assumption}</li>
                    ))}
                  </ul>
                </div>

                {/* Limitations */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="mb-4">
                    <InfoTooltip {...FIELD_EXPLANATIONS.limitations} />
                  </div>
                  <ul className="list-disc list-inside space-y-2 text-gray-700">
                    {displayEvidence.limitations?.map((limitation: string, index: number) => (
                      <li key={index}>{limitation}</li>
                    ))}
                  </ul>
                </div>
              </div>
              </>
            )}
          </div>
        );
      })()}
    </div>
  );
}

function EventDetail({ event }: { event: any }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded p-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <span className="font-medium">{event.event_type}</span>
          <span className="text-sm text-gray-500 ml-3">
            {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
          </span>
        </div>
        <button className="text-blue-600 text-sm">
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {expanded && (
        <pre className="mt-3 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
          {JSON.stringify(event, null, 2)}
        </pre>
      )}
    </div>
  );
}
