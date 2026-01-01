/**
 * Agent Node Component
 */

'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { AgentData } from '../types';

const AgentNode = memo(({ data, selected }: NodeProps<AgentData>) => {
  const topCapabilities = data.capabilities.slice(0, 2);
  const hasMoreCapabilities = data.capabilities.length > 2;

  // Color scheme based on agent type
  const getAgentColor = (agentId: string): string => {
    if (agentId.includes('intake')) return 'bg-green-500';
    if (agentId.includes('coverage')) return 'bg-blue-500';
    if (agentId.includes('fraud')) return 'bg-purple-500';
    if (agentId.includes('severity')) return 'bg-orange-500';
    if (agentId.includes('recommendation')) return 'bg-indigo-500';
    if (agentId.includes('explainability')) return 'bg-pink-500';
    return 'bg-gray-500';
  };

  const colorClass = getAgentColor(data.agentId);

  return (
    <div
      className={`rounded-lg border-2 ${
        selected ? 'border-gray-900 shadow-lg' : 'border-gray-300'
      } bg-white transition-shadow hover:shadow-md min-w-[220px]`}
    >
      {/* Top handle for inputs */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      {/* Header with agent type color */}
      <div className={`${colorClass} text-white px-3 py-2 rounded-t-md`}>
        <div className="font-semibold text-sm truncate">{data.name}</div>
      </div>

      {/* Body */}
      <div className="px-3 py-2 space-y-2">
        {/* Capabilities */}
        <div className="text-xs space-y-1">
          {topCapabilities.map((capability, idx) => (
            <div key={idx} className="text-gray-600 truncate">
              • {capability}
            </div>
          ))}
          {hasMoreCapabilities && (
            <div className="text-gray-400 italic">
              +{data.capabilities.length - 2} more...
            </div>
          )}
        </div>

        {/* Badges */}
        <div className="flex gap-1 flex-wrap">
          {/* Iteration limit badge */}
          <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
            Max: {data.maxIterations}
          </span>

          {/* Tool count badge */}
          {data.allowedTools.length > 0 && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              {data.allowedTools.length} tool{data.allowedTools.length !== 1 ? 's' : ''}
            </span>
          )}

          {/* Dependency indicator */}
          {data.contextRequires.length > 0 && (
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
              {data.contextRequires.length} dep{data.contextRequires.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Bottom handle for outputs */}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';

export default AgentNode;
