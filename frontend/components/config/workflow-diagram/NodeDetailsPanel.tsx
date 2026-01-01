/**
 * Node Details Panel - shows detailed information about selected node
 */

'use client';

import { DiagramNode, isAgentData, isToolData, isOrchestratorData } from './types';

interface NodeDetailsPanelProps {
  node: DiagramNode;
  onClose: () => void;
}

export default function NodeDetailsPanel({ node, onClose }: NodeDetailsPanelProps) {
  const data = node.data;

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-white border-l border-gray-300 shadow-lg overflow-y-auto z-10">
      {/* Header */}
      <div className="sticky top-0 bg-gray-50 border-b border-gray-300 px-4 py-3 flex justify-between items-center">
        <h3 className="font-semibold text-gray-900">Node Details</h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
          aria-label="Close panel"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {isOrchestratorData(data) && (
          <>
            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Type</div>
              <div className="mt-1 text-sm text-gray-900">Orchestrator (Meta-Agent)</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Name</div>
              <div className="mt-1 text-sm text-gray-900">{data.name}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Max Iterations</div>
              <div className="mt-1 text-sm text-gray-900">{data.maxIterations}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Model Profile</div>
              <div className="mt-1 text-sm text-gray-900">{data.modelProfile}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">
                Allowed Agents ({data.allowedAgents.length})
              </div>
              <div className="mt-1 space-y-1">
                {data.allowedAgents.map((agentId, idx) => (
                  <div key={idx} className="text-sm text-gray-700 bg-gray-50 px-2 py-1 rounded">
                    {agentId}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {isAgentData(data) && (
          <>
            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Type</div>
              <div className="mt-1 text-sm text-gray-900">Worker Agent</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Agent ID</div>
              <div className="mt-1 text-sm text-gray-900 font-mono text-xs">{data.agentId}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Name</div>
              <div className="mt-1 text-sm text-gray-900">{data.name}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Description</div>
              <div className="mt-1 text-sm text-gray-700">{data.description}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">
                Capabilities ({data.capabilities.length})
              </div>
              <div className="mt-1 space-y-1">
                {data.capabilities.map((capability, idx) => (
                  <div key={idx} className="text-sm text-gray-700 bg-blue-50 px-2 py-1 rounded">
                    • {capability}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Max Iterations</div>
              <div className="mt-1 text-sm text-gray-900">{data.maxIterations}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Model Profile</div>
              <div className="mt-1 text-sm text-gray-900">{data.modelProfile}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">
                Allowed Tools ({data.allowedTools.length})
              </div>
              <div className="mt-1 space-y-1">
                {data.allowedTools.length > 0 ? (
                  data.allowedTools.map((toolId, idx) => (
                    <div key={idx} className="text-sm text-gray-700 bg-gray-50 px-2 py-1 rounded font-mono text-xs">
                      {toolId}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-500 italic">No tools</div>
                )}
              </div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">
                Context Dependencies ({data.contextRequires.length})
              </div>
              <div className="mt-1 space-y-1">
                {data.contextRequires.length > 0 ? (
                  data.contextRequires.map((depId, idx) => (
                    <div key={idx} className="text-sm text-gray-700 bg-purple-50 px-2 py-1 rounded">
                      Requires output from: <span className="font-mono text-xs">{depId}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-500 italic">No dependencies (entry point)</div>
                )}
              </div>
            </div>
          </>
        )}

        {isToolData(data) && (
          <>
            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Type</div>
              <div className="mt-1 text-sm text-gray-900">Tool</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Tool ID</div>
              <div className="mt-1 text-sm text-gray-900 font-mono text-xs">{data.toolId}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Name</div>
              <div className="mt-1 text-sm text-gray-900">{data.name}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Description</div>
              <div className="mt-1 text-sm text-gray-700">{data.description}</div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">Endpoint</div>
              <div className="mt-1 text-sm text-gray-900 font-mono text-xs bg-gray-50 px-2 py-1 rounded">
                {data.endpoint}
              </div>
            </div>

            <div>
              <div className="text-xs text-gray-500 uppercase font-medium">
                Lineage Tags ({data.lineageTags.length})
              </div>
              <div className="mt-1 flex flex-wrap gap-1">
                {data.lineageTags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
