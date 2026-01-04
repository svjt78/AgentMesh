/**
 * Human Touchpoint Node Component
 */

'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { HumanTouchpointData } from '../types';

const HumanTouchpointNode = memo(({ data, selected }: NodeProps<HumanTouchpointData>) => {
  return (
    <div
      className={`rounded-lg shadow-lg border-2 ${
        selected ? 'border-amber-900 shadow-xl' : 'border-amber-700'
      } bg-gradient-to-br from-amber-500 to-orange-600 transition-shadow hover:shadow-xl min-w-[220px]`}
    >
      {/* Top handle for inputs */}
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-amber-700" />

      {/* Body */}
      <div className="px-4 py-3 space-y-2">
        {/* Icon and Title */}
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-white flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
          </svg>
          <h4 className="font-semibold text-white text-sm">{data.name}</h4>
        </div>

        {/* Description */}
        <p className="text-xs text-amber-100 leading-snug">{data.description}</p>

        {/* Metadata Badges */}
        <div className="flex flex-wrap gap-1">
          {data.approverRole && (
            <span className="px-2 py-0.5 bg-amber-900/40 text-amber-100 rounded text-xs">
              {data.approverRole}
            </span>
          )}
          <span className="px-2 py-0.5 bg-white/20 text-white rounded text-xs font-medium">
            Manual Approval
          </span>
        </div>
      </div>

      {/* Bottom handle for outputs */}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-amber-700" />
    </div>
  );
});

HumanTouchpointNode.displayName = 'HumanTouchpointNode';

export default HumanTouchpointNode;
