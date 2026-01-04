'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { apiClient, SessionSummary } from '@/lib/api-client';
import { TrashIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

export default function ReplayIndexPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoading(true);
        const data = await apiClient.listSessions(50, 0);
        setSessions(data.filter((session) => !session.session_id.endsWith('_context_lineage')));
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load sessions');
      } finally {
        setLoading(false);
      }
    };

    loadSessions();
  }, []);

  const handleDelete = async (event: React.MouseEvent, sessionId: string) => {
    event.preventDefault();
    event.stopPropagation();

    if (!confirm(`Delete session ${sessionId}? This cannot be undone.`)) {
      return;
    }

    try {
      setDeletingSessionId(sessionId);
      await apiClient.deleteSession(sessionId);
      setSessions((prev) => prev.filter((session) => session.session_id !== sessionId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete session');
    } finally {
      setDeletingSessionId(null);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading sessions...</div>;
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 text-red-600">
        Error loading sessions: {error}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Replay Sessions</h1>
        <p className="mt-2 text-sm text-gray-600">
          Select a session to view the full event timeline and context engineering views.
        </p>
      </div>

      {sessions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-gray-600">
          No sessions found. Run a claim to generate a session.
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="grid grid-cols-7 gap-4 px-4 py-3 text-xs font-semibold text-gray-500 bg-gray-50">
            <div className="col-span-2">Session</div>
            <div>Workflow</div>
            <div>Status</div>
            <div>Created</div>
            <div>Events</div>
            <div className="text-right">Actions</div>
          </div>
          <div className="divide-y divide-gray-100">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="grid grid-cols-7 gap-4 px-4 py-4 text-sm hover:bg-gray-50"
              >
                <div className="col-span-2">
                  <Link
                    href={`/replay/${session.session_id}`}
                    className="font-medium text-gray-900 hover:text-blue-600"
                  >
                    {session.session_id}
                  </Link>
                  <div className="text-xs text-gray-500">
                    Agents: {session.agents_executed.join(', ') || 'n/a'}
                  </div>
                </div>
                <div className="text-gray-700">
                  {session.workflow_id && session.workflow_id !== 'unknown'
                    ? session.workflow_id
                    : 'claim_triage_001'}
                </div>
                <div className="text-gray-700">{session.status}</div>
                <div className="text-gray-700">
                  {session.created_at ? format(new Date(session.created_at), 'PPpp') : 'n/a'}
                </div>
                <div className="text-gray-700">{session.event_count}</div>
                <div className="flex justify-end gap-2">
                  <Link
                    href={`/evidence/${session.session_id}`}
                    className="p-1 text-gray-400 hover:text-blue-600"
                    aria-label={`View evidence for session ${session.session_id}`}
                    title="View Evidence"
                  >
                    <DocumentTextIcon className="h-4 w-4" />
                  </Link>
                  <button
                    type="button"
                    onClick={(event) => handleDelete(event, session.session_id)}
                    className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-50"
                    disabled={deletingSessionId === session.session_id}
                    aria-label={`Delete session ${session.session_id}`}
                    title="Delete session"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
