/**
 * Tool Node Component
 */

'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ToolData } from '../types';

const ToolNode = memo(({ data, selected }: NodeProps<ToolData>) => {
  const topTags = data.lineageTags.slice(0, 2);

  return (
    <div
      className={`rounded-lg border-2 ${
        selected ? 'border-gray-700 shadow-md' : 'border-gray-400'
      } bg-gray-50 transition-shadow hover:shadow-sm min-w-[180px]`}
    >
      {/* Top handle for inputs from agents */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      {/* Header */}
      <div className="px-3 py-2 bg-gray-100 border-b border-gray-300">
        <div className="flex items-center gap-2">
          {/* Tool icon */}
          <svg
            className="w-4 h-4 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <div className="font-semibold text-sm text-gray-900 truncate">
            {data.name}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-3 py-2 space-y-1">
        {/* Lineage tags */}
        {topTags.length > 0 && (
          <div className="flex gap-1 flex-wrap">
            {topTags.map((tag, idx) => (
              <span
                key={idx}
                className="text-xs bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Endpoint hint */}
        <div className="text-xs text-gray-500 truncate">
          {data.endpoint}
        </div>
      </div>
    </div>
  );
});

ToolNode.displayName = 'ToolNode';

export default ToolNode;
