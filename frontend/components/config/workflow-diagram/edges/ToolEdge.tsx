/**
 * Tool Edge - shows agent to tool invocations
 */

'use client';

import { memo } from 'react';
import { EdgeProps, getStraightPath } from 'reactflow';

const ToolEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
}: EdgeProps) => {
  const [edgePath] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <path
      id={id}
      className="react-flow__edge-path"
      d={edgePath}
      strokeWidth={1.5}
      stroke="#6b7280"
      markerEnd={markerEnd}
    />
  );
});

ToolEdge.displayName = 'ToolEdge';

export default ToolEdge;
