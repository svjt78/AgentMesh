/**
 * Workflow Diagram - interactive node-based visualization of orchestrator → agents → tools
 */

'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  NodeTypes,
  EdgeTypes,
  Node,
  Edge,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { apiClient } from '@/lib/api-client';
import { buildGraph, filterEdges, filterNodes } from '@/lib/diagram/graph-builder';
import { applyLayout, recenterGraph } from '@/lib/diagram/layout-engine';
import { DiagramNode, DiagramEdge, DiagramFilters } from './types';

// Custom node components
import OrchestratorNode from './nodes/OrchestratorNode';
import AgentNode from './nodes/AgentNode';
import ToolNode from './nodes/ToolNode';
import HumanTouchpointNode from './nodes/HumanTouchpointNode';

// Custom edge components
import WorkflowEdge from './edges/WorkflowEdge';
import DependencyEdge from './edges/DependencyEdge';
import ToolEdge from './edges/ToolEdge';
import InvocationEdge from './edges/InvocationEdge';

// UI components
import NodeDetailsPanel from './NodeDetailsPanel';
import DiagramControls from './DiagramControls';

interface WorkflowDiagramProps {
  workflowId: string;
}

// Define custom node types
const nodeTypes: NodeTypes = {
  orchestrator: OrchestratorNode,
  agent: AgentNode,
  tool: ToolNode,
  humanTouchpoint: HumanTouchpointNode,
};

// Define custom edge types
const edgeTypes: EdgeTypes = {
  workflow: WorkflowEdge,
  dependency: DependencyEdge,
  tool: ToolEdge,
  invocation: InvocationEdge,
};

// Default marker for edges
const defaultEdgeOptions = {
  markerEnd: {
    type: MarkerType.ArrowClosed,
  },
};

export default function WorkflowDiagram({ workflowId }: WorkflowDiagramProps) {
  const [nodes, setNodes] = useState<DiagramNode[]>([]);
  const [edges, setEdges] = useState<DiagramEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<DiagramNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DiagramFilters>({
    showWorkflowEdges: true,
    showDependencies: true,
    showToolEdges: true,
    showGovernance: false,
    showHumanTouchpoints: true,
  });

  // Load diagram data
  useEffect(() => {
    async function loadDiagram() {
      try {
        setLoading(true);
        setError(null);

        // Fetch all required data in parallel
        const [workflow, agents, tools, governance] = await Promise.all([
          apiClient.getWorkflow(workflowId),
          apiClient.listAgents(),
          apiClient.listTools(),
          apiClient.getGovernancePolicies(),
        ]);

        // Build graph from registries
        const graph = buildGraph(workflow, agents, tools, governance, filters);

        // Apply layout algorithm
        const layouted = applyLayout(graph.nodes, graph.edges);

        // Recenter graph
        const centered = recenterGraph(layouted.nodes);

        setNodes(centered);
        setEdges(layouted.edges);
      } catch (err: any) {
        console.error('Failed to load diagram:', err);
        setError(err.message || 'Failed to load workflow diagram');
      } finally {
        setLoading(false);
      }
    }

    loadDiagram();
  }, [workflowId, filters]);

  // Filter nodes based on user preferences
  const filteredNodes = useMemo(() => {
    return filterNodes(nodes, filters);
  }, [nodes, filters]);

  // Filter edges based on user preferences
  const filteredEdges = useMemo(() => {
    return filterEdges(edges, filters);
  }, [edges, filters]);

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node as DiagramNode);
  }, []);

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  if (loading) {
    return (
      <div className="h-[800px] w-full border rounded-lg bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-600">Loading workflow diagram...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-[800px] w-full border rounded-lg bg-red-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-600 font-semibold mb-2">Failed to load diagram</div>
          <div className="text-red-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[800px] w-full border rounded-lg bg-gray-50 relative">
      <ReactFlow
        nodes={filteredNodes}
        edges={filteredEdges}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        minZoom={0.1}
        maxZoom={2}
        attributionPosition="bottom-right"
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const n = node as DiagramNode;
            if (n.type === 'orchestrator') return '#3b82f6';
            if (n.type === 'agent') return '#10b981';
            if (n.type === 'humanTouchpoint') return '#f59e0b';
            return '#6b7280';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>

      {/* Controls and Legend */}
      <DiagramControls filters={filters} onFilterChange={setFilters} />

      {/* Node Details Panel */}
      {selectedNode && (
        <NodeDetailsPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
}
