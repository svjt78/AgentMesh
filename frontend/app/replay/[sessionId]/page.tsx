/**
 * Session Replay Page - View complete session timeline
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, SessionDetails } from '@/lib/api-client';
import { format } from 'date-fns';
import Link from 'next/link';

import ContextTimeline from '@/components/visualization/ContextTimeline';
import TokenBudgetChart from '@/components/visualization/TokenBudgetChart';
import ContextLineageTree from '@/components/visualization/ContextLineageTree';

type TabName = 'events' | 'context_engineering';

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

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  useEffect(() => {
    if (activeTab !== 'context_engineering') return;

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
    { id: 'context_engineering' as TabName, label: 'Context Engineering' },
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

      {activeTab === 'context_engineering' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Context Engineering Ops</h2>
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
