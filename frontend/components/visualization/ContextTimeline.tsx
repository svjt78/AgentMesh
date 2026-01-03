'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface TimelinePoint {
  compilation_id: string;
  agent_id: string;
  timestamp: string;
  tokens_before: number;
  tokens_after: number;
  max_tokens?: number;
  budget_exceeded: boolean;
  truncation_applied: boolean;
  compaction_applied: boolean;
}

interface ContextTimelineProps {
  sessionId: string;
}

export default function ContextTimeline({ sessionId }: ContextTimelineProps) {
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTimeline();
  }, [sessionId]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:8016'}/sessions/${sessionId}/token-budget-timeline`);
      if (!response.ok) {
        throw new Error('Failed to load timeline');
      }
      const data = await response.json();
      setTimeline(data.timeline || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  const getStatusColor = (point: TimelinePoint) => {
    if (point.compaction_applied) return 'bg-red-100 border-red-500';
    if (point.truncation_applied) return 'bg-yellow-100 border-yellow-500';
    if (point.budget_exceeded) return 'bg-orange-100 border-orange-500';
    return 'bg-green-100 border-green-500';
  };

  const getStatusLabel = (point: TimelinePoint) => {
    if (point.compaction_applied) return 'Compacted';
    if (point.truncation_applied) return 'Truncated';
    if (point.budget_exceeded) return 'Over Budget';
    return 'Normal';
  };

  if (loading) {
    return <div className="text-center py-4 text-gray-500">Loading timeline...</div>;
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">{error}</div>;
  }

  if (timeline.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center text-gray-500">
        No context compilations found for this session.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Context Compilation Timeline</h4>
        <div className="text-xs text-gray-500 mb-4">
          Shows token usage across all context compilations. Colors indicate status:
          <span className="inline-block ml-2 px-2 py-0.5 bg-green-100 text-green-800 rounded">Normal</span>
          <span className="inline-block ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">Truncated</span>
          <span className="inline-block ml-2 px-2 py-0.5 bg-orange-100 text-orange-800 rounded">Over Budget</span>
          <span className="inline-block ml-2 px-2 py-0.5 bg-red-100 text-red-800 rounded">Compacted</span>
        </div>

        <div className="space-y-2">
          {timeline.map((point, idx) => (
            <div
              key={point.compilation_id}
              className={`border-l-4 ${getStatusColor(point)} p-3 rounded`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      {point.agent_id}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      point.compaction_applied ? 'bg-red-200 text-red-800' :
                      point.truncation_applied ? 'bg-yellow-200 text-yellow-800' :
                      point.budget_exceeded ? 'bg-orange-200 text-orange-800' :
                      'bg-green-200 text-green-800'
                    }`}>
                      {getStatusLabel(point)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatTime(point.timestamp)}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {point.tokens_before.toLocaleString()} → {point.tokens_after.toLocaleString()} tokens
                  </div>
                  <div className="text-xs text-gray-500">
                    {point.tokens_before > point.tokens_after && (
                      <span className="text-blue-600">
                        Reduced by {(point.tokens_before - point.tokens_after).toLocaleString()}
                      </span>
                    )}
                    {point.tokens_before === point.tokens_after && (
                      <span className="text-gray-500">No reduction</span>
                    )}
                    {point.tokens_before < point.tokens_after && (
                      <span className="text-orange-600">
                        Increased by {(point.tokens_after - point.tokens_before).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Token bar visualization */}
              <div className="mt-2">
                {(() => {
                  const maxTokens = point.max_tokens || 8000;
                  const percent = maxTokens > 0 ? (point.tokens_after / maxTokens) * 100 : 0;
                  return (
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        point.budget_exceeded ? 'bg-red-500' : 'bg-blue-500'
                      }`}
                      style={{
                        width: `${Math.min(percent, 100)}%`
                      }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right">
                    {percent.toFixed(0)}%
                  </span>
                </div>
                  );
                })()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
