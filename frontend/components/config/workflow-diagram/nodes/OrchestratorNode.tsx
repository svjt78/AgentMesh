/**
 * Orchestrator Node Component
 */

'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { OrchestratorData } from '../types';

const OrchestratorNode = memo(({ data, selected }: NodeProps<OrchestratorData>) => {
  return (
    <div
      className={`rounded-lg border-2 ${
        selected ? 'border-blue-900 shadow-xl' : 'border-blue-400'
      } bg-gradient-to-br from-blue-500 to-blue-600 text-white transition-shadow hover:shadow-lg min-w-[300px]`}
    >
      {/* Header */}
      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="font-bold text-lg">{data.name}</div>
          <span className="text-xs bg-blue-400 bg-opacity-50 px-2 py-1 rounded">
            Meta-Agent
          </span>
        </div>

        {/* Stats */}
        <div className="flex gap-3 text-xs">
          <div className="bg-blue-400 bg-opacity-30 px-2 py-1 rounded">
            Max Iterations: {data.maxIterations}
          </div>
          <div className="bg-blue-400 bg-opacity-30 px-2 py-1 rounded">
            {data.allowedAgents.length} Agents
          </div>
        </div>

        {/* Model Profile */}
        <div className="text-xs opacity-90">
          Model: {data.modelProfile}
        </div>
      </div>

      {/* Bottom handle for invoking agents */}
      <Handle type="source" position={Position.Bottom} className="w-4 h-4" />
    </div>
  );
});

OrchestratorNode.displayName = 'OrchestratorNode';

export default OrchestratorNode;
