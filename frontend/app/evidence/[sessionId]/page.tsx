/**
 * Evidence Map Page - Display final evidence map
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, EvidenceMap } from '@/lib/api-client';
import { format } from 'date-fns';

export default function EvidenceMapPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [evidenceMap, setEvidenceMap] = useState<EvidenceMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEvidenceMap();
  }, [sessionId]);

  const loadEvidenceMap = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getEvidenceMap(sessionId);
      setEvidenceMap(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading evidence map...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-8 text-red-600">Error: {error}</div>;
  }

  if (!evidenceMap) {
    return <div className="container mx-auto px-4 py-8">Evidence map not found</div>;
  }

  const map = evidenceMap.evidence_map;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Evidence Map</h1>

      {/* Session Info */}
      <div className="bg-gray-50 rounded-lg p-4 mb-8 text-sm">
        <div>
          <span className="font-medium">Session:</span> <code>{sessionId}</code>
        </div>
        <div>
          <span className="font-medium">Generated:</span>{' '}
          {format(new Date(evidenceMap.generated_at), 'PPpp')}
        </div>
      </div>

      {/* Decision */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4">Decision</h2>
        <div className="space-y-3">
          <div>
            <span className="font-medium">Outcome:</span>
            <br />
            <span className="text-xl">{map.decision?.outcome || 'N/A'}</span>
          </div>
          {map.decision?.confidence && (
            <div>
              <span className="font-medium">Confidence:</span>
              <br />
              <div className="w-full bg-gray-200 rounded-full h-4 mt-1">
                <div
                  className="bg-blue-600 h-4 rounded-full"
                  style={{ width: `${(map.decision.confidence || 0) * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">
                {((map.decision.confidence || 0) * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {map.decision?.basis && (
            <div>
              <span className="font-medium">Basis:</span>
              <br />
              <p className="text-gray-700">{map.decision.basis}</p>
            </div>
          )}
        </div>
      </div>

      {/* Supporting Evidence */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Supporting Evidence</h2>
        <div className="space-y-4">
          {map.supporting_evidence?.map((evidence: any, index: number) => (
            <div key={index} className="border-l-4 border-blue-600 pl-4 py-2">
              <div className="font-medium">{evidence.source || `Evidence ${index + 1}`}</div>
              <div className="text-sm text-gray-600">{evidence.evidence_type}</div>
              <p className="text-gray-700 mt-1">{evidence.summary}</p>
              {evidence.weight && (
                <div className="text-sm text-gray-500 mt-1">
                  Weight: {(evidence.weight * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Agent Chain */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Agent Execution Chain</h2>
        <div className="flex flex-wrap gap-2">
          {map.agent_chain?.map((agent: string, index: number) => (
            <div key={index} className="flex items-center">
              <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded">
                {agent}
              </div>
              {index < (map.agent_chain?.length || 0) - 1 && (
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
          <h2 className="text-xl font-semibold mb-4">Assumptions</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {map.assumptions?.map((assumption: string, index: number) => (
              <li key={index}>{assumption}</li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Limitations</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {map.limitations?.map((limitation: string, index: number) => (
              <li key={index}>{limitation}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
