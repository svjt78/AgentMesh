'use client';

import { useState, useEffect } from 'react';

interface ProcessorExecution {
  processor_id: string;
  execution_time_ms: number;
  success: boolean;
  modifications_made: Record<string, any>;
  error?: string;
}

interface Compilation {
  compilation_id: string;
  agent_id: string;
  timestamp: string;
  tokens_before: number;
  tokens_after: number;
  processors_executed: ProcessorExecution[];
  truncation_applied: boolean;
  compaction_applied: boolean;
  memories_retrieved: number;
  artifacts_resolved: number;
}

interface ContextLineageTreeProps {
  sessionId: string;
}

export default function ContextLineageTree({ sessionId }: ContextLineageTreeProps) {
  const [compilations, setCompilations] = useState<Compilation[]>([]);
  const [expandedCompilation, setExpandedCompilation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCompilations();
  }, [sessionId]);

  const loadCompilations = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:8016'}/sessions/${sessionId}/context-lineage`
      );
      if (!response.ok) {
        throw new Error('Failed to load lineage');
      }
      const data = await response.json();
      setCompilations(data.compilations || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleCompilation = (compilationId: string) => {
    setExpandedCompilation(expandedCompilation === compilationId ? null : compilationId);
  };

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return <div className="text-center py-4 text-gray-500">Loading lineage tree...</div>;
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">{error}</div>;
  }

  if (compilations.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center text-gray-500">
        No context lineage found for this session.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Context Compilation Lineage</h4>
        <div className="text-xs text-gray-500 mb-4">
          Click to expand and see processor execution details for each compilation.
        </div>

        <div className="space-y-2">
          {compilations.map((compilation) => (
            <div key={compilation.compilation_id} className="border border-gray-200 rounded">
              {/* Compilation header */}
              <div
                onClick={() => toggleCompilation(compilation.compilation_id)}
                className="p-3 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {compilation.agent_id}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTime(compilation.timestamp)}
                      </span>
                      {expandedCompilation === compilation.compilation_id ? (
                        <span className="text-xs text-gray-400">▼</span>
                      ) : (
                        <span className="text-xs text-gray-400">▶</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {compilation.processors_executed.length} processors •{' '}
                      {compilation.tokens_before.toLocaleString()} → {compilation.tokens_after.toLocaleString()} tokens
                      {compilation.truncation_applied && <span className="ml-2 text-yellow-600">• Truncated</span>}
                      {compilation.compaction_applied && <span className="ml-2 text-red-600">• Compacted</span>}
                      {compilation.memories_retrieved > 0 && (
                        <span className="ml-2 text-blue-600">• {compilation.memories_retrieved} memories</span>
                      )}
                      {compilation.artifacts_resolved > 0 && (
                        <span className="ml-2 text-purple-600">• {compilation.artifacts_resolved} artifacts</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded processor details */}
              {expandedCompilation === compilation.compilation_id && (
                <div className="border-t border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs font-medium text-gray-700 mb-2">Processor Pipeline:</div>
                  <div className="space-y-2">
                    {compilation.processors_executed.map((processor, idx) => (
                      <div
                        key={idx}
                        className={`border-l-4 pl-3 py-2 ${
                          processor.success
                            ? 'border-green-500 bg-white'
                            : 'border-red-500 bg-red-50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="text-sm font-medium text-gray-900">
                              {idx + 1}. {processor.processor_id}
                            </div>
                            {processor.error && (
                              <div className="text-xs text-red-600 mt-1">Error: {processor.error}</div>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            {processor.execution_time_ms.toFixed(2)}ms
                          </div>
                        </div>

                        {/* Modifications made */}
                        {processor.success && Object.keys(processor.modifications_made).length > 0 && (
                          <div className="mt-2 text-xs">
                            <div className="text-gray-600 font-medium mb-1">Modifications:</div>
                            <div className="bg-gray-50 p-2 rounded">
                              {Object.entries(processor.modifications_made).map(([key, value]) => (
                                <div key={key} className="text-gray-700">
                                  <span className="font-medium">{key}:</span>{' '}
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
