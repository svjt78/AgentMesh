/**
 * Evidence Display Component
 *
 * Reusable component for displaying evidence maps in plain English.
 * Used in both HITL interventions and Explainability tabs.
 */

'use client';

import { format } from 'date-fns';
import InfoTooltip from './InfoTooltip';
import { FIELD_EXPLANATIONS } from '@/lib/demo-evidence';

interface EvidenceDisplayProps {
  evidence: any;
  compact?: boolean; // If true, shows simplified view suitable for HITL checkpoint
}

export default function EvidenceDisplay({ evidence, compact = false }: EvidenceDisplayProps) {
  if (!evidence) {
    return (
      <div className="text-gray-500 text-sm">
        No evidence map available for this session.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Decision Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-xl font-semibold mb-4 text-gray-900">
          <InfoTooltip {...FIELD_EXPLANATIONS.outcome} />
        </h3>
        <div className="space-y-3">
          <div>
            <span className="text-sm font-medium text-gray-600">Outcome:</span>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {evidence.decision?.outcome || 'N/A'}
            </div>
          </div>

          {evidence.decision?.confidence !== undefined && (
            <div>
              <InfoTooltip {...FIELD_EXPLANATIONS.confidence} />
              <div className="w-full bg-gray-200 rounded-full h-6 mt-2">
                <div
                  className="bg-blue-600 h-6 rounded-full flex items-center justify-center text-white text-xs font-medium"
                  style={{ width: `${(evidence.decision.confidence || 0) * 100}%` }}
                >
                  {((evidence.decision.confidence || 0) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          )}

          {evidence.decision?.basis && (
            <div>
              <InfoTooltip {...FIELD_EXPLANATIONS.basis} />
              <p className="text-gray-700 mt-2 leading-relaxed">
                {evidence.decision.basis}
              </p>
            </div>
          )}

          {(evidence.decision?.estimated_exposure || evidence.decision?.potential_savings) && (
            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-blue-200">
              {evidence.decision.estimated_exposure !== undefined && (
                <div>
                  <InfoTooltip {...FIELD_EXPLANATIONS.estimated_exposure} />
                  <div className="text-2xl font-semibold text-red-600 mt-1">
                    ${evidence.decision.estimated_exposure.toLocaleString()}
                  </div>
                </div>
              )}
              {evidence.decision.potential_savings !== undefined && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Potential Savings</span>
                  <div className="text-2xl font-semibold text-green-600 mt-1">
                    ${evidence.decision.potential_savings.toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Supporting Evidence */}
      {evidence.supporting_evidence && evidence.supporting_evidence.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="mb-4">
            <InfoTooltip {...FIELD_EXPLANATIONS.supporting_evidence} />
          </div>
          <div className="space-y-4">
            {evidence.supporting_evidence.map((item: any, index: number) => (
              <div
                key={index}
                className="border-l-4 border-blue-600 pl-4 py-3 bg-blue-50 rounded-r"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="font-semibold text-gray-900">
                    {item.source || `Evidence ${index + 1}`}
                  </div>
                  {item.weight !== undefined && (
                    <div className="text-sm text-gray-600">
                      <InfoTooltip {...FIELD_EXPLANATIONS.weight} />:{' '}
                      <span className="font-semibold">{(item.weight * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>

                <div className="text-xs text-gray-500 uppercase mb-2">
                  {item.evidence_type}
                </div>

                <p className="text-gray-700 leading-relaxed">
                  {item.summary}
                </p>

                {item.risk_score !== undefined && (
                  <div className="mt-2 text-sm">
                    <InfoTooltip {...FIELD_EXPLANATIONS.fraud_score} />:{' '}
                    <span className={`font-semibold ${
                      item.risk_score > 0.7 ? 'text-red-600' :
                      item.risk_score > 0.4 ? 'text-orange-600' :
                      'text-green-600'
                    }`}>
                      {(item.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!compact && (
        <>
          {/* Agent Execution Chain */}
          {evidence.agent_chain && evidence.agent_chain.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="mb-4">
                <InfoTooltip {...FIELD_EXPLANATIONS.agent_chain} />
              </div>
              <div className="flex flex-wrap gap-2">
                {evidence.agent_chain.map((agent: string, index: number) => (
                  <div key={index} className="flex items-center">
                    <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg font-medium text-sm">
                      {agent}
                    </div>
                    {index < evidence.agent_chain.length - 1 && (
                      <span className="mx-2 text-gray-400 text-xl">→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Assumptions & Limitations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Assumptions */}
            {evidence.assumptions && evidence.assumptions.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                <div className="mb-4">
                  <InfoTooltip {...FIELD_EXPLANATIONS.assumptions} />
                </div>
                <ul className="list-disc list-inside space-y-2 text-gray-700 text-sm">
                  {evidence.assumptions.map((assumption: string, index: number) => (
                    <li key={index} className="leading-relaxed">{assumption}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Limitations */}
            {evidence.limitations && evidence.limitations.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                <div className="mb-4">
                  <InfoTooltip {...FIELD_EXPLANATIONS.limitations} />
                </div>
                <ul className="list-disc list-inside space-y-2 text-gray-700 text-sm">
                  {evidence.limitations.map((limitation: string, index: number) => (
                    <li key={index} className="leading-relaxed">{limitation}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Human Interventions */}
          {evidence.human_interventions && evidence.human_interventions.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="mb-4">
                <InfoTooltip {...FIELD_EXPLANATIONS.human_interventions} />
              </div>
              <div className="space-y-4">
                {evidence.human_interventions.map((intervention: any, index: number) => (
                  <div key={index} className="border-l-4 border-green-600 pl-4 py-3 bg-green-50 rounded-r">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium text-gray-900">{intervention.intervention_type}</div>
                      {intervention.timestamp && (
                        <div className="text-sm text-gray-500">
                          {format(new Date(intervention.timestamp), 'PPpp')}
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-gray-700 mb-1">
                      <span className="font-medium">Reviewer:</span> {intervention.reviewer}
                    </div>
                    {intervention.checkpoint && (
                      <div className="text-sm text-gray-700 mb-1">
                        <span className="font-medium">Checkpoint:</span> {intervention.checkpoint}
                      </div>
                    )}
                    <div className="text-sm text-gray-700 mb-2">
                      <span className="font-medium">Action:</span>{' '}
                      <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium">
                        {intervention.action}
                      </span>
                    </div>
                    {intervention.comments && (
                      <p className="text-gray-700 italic text-sm">&quot;{intervention.comments}&quot;</p>
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
        </>
      )}
    </div>
  );
}
