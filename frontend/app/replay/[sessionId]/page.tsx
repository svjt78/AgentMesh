/**
 * Session Replay Page - View complete session timeline
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, SessionDetails } from '@/lib/api-client';
import { format } from 'date-fns';

export default function ReplayPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterEventType, setFilterEventType] = useState<string>('all');

  useEffect(() => {
    loadSession();
  }, [sessionId]);

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
    new Set(session.events.map((e) => e.event_type))
  );

  const filteredEvents =
    filterEventType === 'all'
      ? session.events
      : session.events.filter((e) => e.event_type === filterEventType);

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
            <option key={type} value={type}>
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
