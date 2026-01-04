/**
 * TypeScript type definitions for the workflow diagram
 */

import { Node, Edge } from 'reactflow';

// Node data types

export interface OrchestratorData {
  name: string;
  maxIterations: number;
  allowedAgents: string[];
  modelProfile: string;
}

export interface AgentData {
  agentId: string;
  name: string;
  capabilities: string[];
  allowedTools: string[];
  maxIterations: number;
  contextRequires: string[];
  modelProfile: string;
  description: string;
}

export interface ToolData {
  toolId: string;
  name: string;
  description: string;
  lineageTags: string[];
  endpoint: string;
}

export interface HumanTouchpointData {
  touchpointId: string;
  name: string;
  description: string;
  afterStep: string;
  beforeStep: string;
  triggerCondition?: string;
  approverRole?: string;
}

// Extended node types

export interface DiagramNode extends Node {
  type: 'orchestrator' | 'agent' | 'tool' | 'humanTouchpoint';
  data: OrchestratorData | AgentData | ToolData | HumanTouchpointData;
}

// Edge data types

export interface EdgeData {
  sequence?: number;
  label?: string;
  isDenied?: boolean;
  stepId?: string;
}

export type DiagramEdge = Edge & {
  type?: 'workflow' | 'dependency' | 'tool' | 'invocation';
  data?: EdgeData;
}

// Filter state

export interface DiagramFilters {
  showWorkflowEdges: boolean;
  showDependencies: boolean;
  showToolEdges: boolean;
  showGovernance: boolean;
  showHumanTouchpoints: boolean;
}

// Graph structure

export interface DiagramGraph {
  nodes: DiagramNode[];
  edges: DiagramEdge[];
}

// Helper type guards

export function isOrchestratorData(data: any): data is OrchestratorData {
  return 'allowedAgents' in data;
}

export function isAgentData(data: any): data is AgentData {
  return 'agentId' in data && 'capabilities' in data;
}

export function isToolData(data: any): data is ToolData {
  return 'toolId' in data && 'endpoint' in data;
}

export function isHumanTouchpointData(data: any): data is HumanTouchpointData {
  return 'touchpointId' in data && 'afterStep' in data;
}
