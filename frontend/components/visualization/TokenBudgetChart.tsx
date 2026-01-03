'use client';

import { useState, useEffect } from 'react';

interface Compilation {
  compilation_id: string;
  agent_id: string;
  tokens_before: number;
  tokens_after: number;
  components_before: {
    original_input: number;
    prior_outputs: number;
    observations: number;
  };
  components_after: {
    original_input: number;
    prior_outputs: number;
    observations: number;
  };
  budget_allocation: {
    original_input_percentage: number;
    prior_outputs_percentage: number;
    observations_percentage: number;
  };
  budget_exceeded: boolean;
}

interface TokenBudgetChartProps {
  sessionId: string;
}

export default function TokenBudgetChart({ sessionId }: TokenBudgetChartProps) {
  const [compilations, setCompilations] = useState<Compilation[]>([]);
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
        throw new Error('Failed to load compilations');
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

  const calculatePercentage = (value: number, total: number) => {
    return total > 0 ? (value / total) * 100 : 0;
  };

  if (loading) {
    return <div className="text-center py-4 text-gray-500">Loading budget chart...</div>;
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">{error}</div>;
  }

  if (compilations.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center text-gray-500">
        No compilations found for budget analysis.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Token Budget Analysis</h4>
        <div className="text-xs text-gray-500 mb-4">
          Breakdown of token allocation across context components. Colors:
          <span className="inline-block ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded">Original Input</span>
          <span className="inline-block ml-2 px-2 py-0.5 bg-green-100 text-green-800 rounded">Prior Outputs</span>
          <span className="inline-block ml-2 px-2 py-0.5 bg-purple-100 text-purple-800 rounded">Observations</span>
        </div>

        <div className="space-y-4">
          {compilations.map((compilation, idx) => (
            <div key={compilation.compilation_id} className="border border-gray-200 rounded p-3">
              <div className="flex justify-between items-center mb-2">
                <div className="text-sm font-medium text-gray-900">
                  {compilation.agent_id}
                </div>
                <div className="text-xs text-gray-500">
                  Total: {compilation.tokens_after.toLocaleString()} tokens
                  {compilation.budget_exceeded && (
                    <span className="ml-2 text-red-600 font-medium">⚠ Over Budget</span>
                  )}
                </div>
              </div>

              {/* Stacked bar chart */}
              <div className="mb-2">
                <div className="flex h-8 rounded overflow-hidden border border-gray-300">
                  <div
                    className="bg-blue-500 flex items-center justify-center text-white text-xs font-medium"
                    style={{
                      width: `${calculatePercentage(
                        compilation.components_after.original_input,
                        compilation.tokens_after
                      )}%`
                    }}
                  >
                    {compilation.components_after.original_input > 0 && (
                      <span className="px-1">
                        {compilation.components_after.original_input.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div
                    className="bg-green-500 flex items-center justify-center text-white text-xs font-medium"
                    style={{
                      width: `${calculatePercentage(
                        compilation.components_after.prior_outputs,
                        compilation.tokens_after
                      )}%`
                    }}
                  >
                    {compilation.components_after.prior_outputs > 0 && (
                      <span className="px-1">
                        {compilation.components_after.prior_outputs.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div
                    className="bg-purple-500 flex items-center justify-center text-white text-xs font-medium"
                    style={{
                      width: `${calculatePercentage(
                        compilation.components_after.observations,
                        compilation.tokens_after
                      )}%`
                    }}
                  >
                    {compilation.components_after.observations > 0 && (
                      <span className="px-1">
                        {compilation.components_after.observations.toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Component breakdown */}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-blue-50 p-2 rounded">
                  <div className="text-blue-900 font-medium">Original Input</div>
                  <div className="text-blue-700">
                    {compilation.components_after.original_input.toLocaleString()} tokens
                  </div>
                  <div className="text-blue-600">
                    {calculatePercentage(
                      compilation.components_after.original_input,
                      compilation.tokens_after
                    ).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-green-50 p-2 rounded">
                  <div className="text-green-900 font-medium">Prior Outputs</div>
                  <div className="text-green-700">
                    {compilation.components_after.prior_outputs.toLocaleString()} tokens
                  </div>
                  <div className="text-green-600">
                    {calculatePercentage(
                      compilation.components_after.prior_outputs,
                      compilation.tokens_after
                    ).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-purple-50 p-2 rounded">
                  <div className="text-purple-900 font-medium">Observations</div>
                  <div className="text-purple-700">
                    {compilation.components_after.observations.toLocaleString()} tokens
                  </div>
                  <div className="text-purple-600">
                    {calculatePercentage(
                      compilation.components_after.observations,
                      compilation.tokens_after
                    ).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Budget allocation vs actual */}
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Budget Allocation:</span>{' '}
                  {compilation.budget_allocation.original_input_percentage}% / {' '}
                  {compilation.budget_allocation.prior_outputs_percentage}% / {' '}
                  {compilation.budget_allocation.observations_percentage}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
