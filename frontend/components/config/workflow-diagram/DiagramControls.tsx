/**
 * Diagram Controls - filters and legend for the workflow diagram
 */

'use client';

import { DiagramFilters } from './types';

interface DiagramControlsProps {
  filters: DiagramFilters;
  onFilterChange: (filters: DiagramFilters) => void;
}

export default function DiagramControls({ filters, onFilterChange }: DiagramControlsProps) {
  const handleToggle = (key: keyof DiagramFilters) => {
    onFilterChange({
      ...filters,
      [key]: !filters[key],
    });
  };

  return (
    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md border border-gray-300 p-3 space-y-3 z-10 max-w-xs">
      {/* Title */}
      <div className="font-semibold text-sm text-gray-900">Diagram Controls</div>

      {/* Filters */}
      <div className="space-y-2">
        <div className="text-xs text-gray-500 uppercase font-medium">Show/Hide</div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showWorkflowEdges}
            onChange={() => handleToggle('showWorkflowEdges')}
            className="rounded text-green-600 focus:ring-green-500"
          />
          <span className="text-sm text-gray-700">Workflow Sequence</span>
          <span className="ml-auto w-3 h-3 rounded-full bg-green-600"></span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showDependencies}
            onChange={() => handleToggle('showDependencies')}
            className="rounded text-purple-600 focus:ring-purple-500"
          />
          <span className="text-sm text-gray-700">Context Dependencies</span>
          <span className="ml-auto w-3 h-0.5 bg-purple-600" style={{ borderTop: '2px dashed' }}></span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showToolEdges}
            onChange={() => handleToggle('showToolEdges')}
            className="rounded text-gray-600 focus:ring-gray-500"
          />
          <span className="text-sm text-gray-700">Tool Invocations</span>
          <span className="ml-auto w-3 h-3 rounded-full bg-gray-600"></span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showGovernance}
            onChange={() => handleToggle('showGovernance')}
            className="rounded text-red-600 focus:ring-red-500"
          />
          <span className="text-sm text-gray-700">Governance Constraints</span>
          <span className="ml-auto w-3 h-3 rounded-full bg-red-600"></span>
        </label>
      </div>

      {/* Legend */}
      <div className="pt-2 border-t border-gray-200">
        <div className="text-xs text-gray-500 uppercase font-medium mb-2">Legend</div>

        <div className="space-y-1.5 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-gradient-to-br from-blue-500 to-blue-600"></div>
            <span className="text-gray-700">Orchestrator</span>
          </div>

          <div>
            <div className="text-gray-700 mb-1">Agents (color-coded):</div>
            <div className="ml-2 space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-500"></div>
                <span className="text-gray-600">Intake</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-blue-500"></div>
                <span className="text-gray-600">Coverage</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-purple-500"></div>
                <span className="text-gray-600">Fraud</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-orange-500"></div>
                <span className="text-gray-600">Severity</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-indigo-500"></div>
                <span className="text-gray-600">Recommendation</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-pink-500"></div>
                <span className="text-gray-600">Explainability</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-gray-400"></div>
            <span className="text-gray-700">Tool</span>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="pt-2 border-t border-gray-200 text-xs text-gray-600">
        <p>Click nodes for details. Zoom and pan to navigate.</p>
      </div>
    </div>
  );
}
