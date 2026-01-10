'use client';

import { useState } from 'react';
import OrchestratorTab from '@/components/config/OrchestratorTab';
import AgentsTab from '@/components/config/AgentsTab';
import ToolsTab from '@/components/config/ToolsTab';
import ModelProfilesTab from '@/components/config/ModelProfilesTab';
import WorkflowsTab from '@/components/config/WorkflowsTab';
import HITLCheckpointsTab from '@/components/config/HITLCheckpointsTab';
import GovernanceTab from '@/components/config/GovernanceTab';
import SystemSettingsTab from '@/components/config/SystemSettingsTab';
import ContextEngineeringTab from '@/components/config/ContextEngineeringTab';
import IntegrationScalabilityTab from '@/components/config/IntegrationScalabilityTab';

type TabName =
  | 'orchestrator'
  | 'agents'
  | 'tools'
  | 'models'
  | 'workflows'
  | 'hitl_checkpoints'
  | 'governance'
  | 'system'
  | 'context_engineering'
  | 'integration_scalability';

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState<TabName>('orchestrator');

  const tabs: { id: TabName; label: string }[] = [
    { id: 'orchestrator', label: 'Orchestrator' },
    { id: 'agents', label: 'Agents' },
    { id: 'tools', label: 'Tools' },
    { id: 'models', label: 'Model Profiles' },
    { id: 'workflows', label: 'Workflows' },
    { id: 'hitl_checkpoints', label: 'Accountability' },
    { id: 'governance', label: 'Governance' },
    { id: 'system', label: 'Controllability' },
    { id: 'context_engineering', label: 'Context Engineering' },
    { id: 'integration_scalability', label: 'Integration Scalability' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Registry Configuration</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage agents, tools, model profiles, workflows, and governance policies
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          {activeTab === 'orchestrator' && <OrchestratorTab />}
          {activeTab === 'agents' && <AgentsTab />}
          {activeTab === 'tools' && <ToolsTab />}
          {activeTab === 'models' && <ModelProfilesTab />}
          {activeTab === 'workflows' && <WorkflowsTab />}
          {activeTab === 'hitl_checkpoints' && <HITLCheckpointsTab />}
          {activeTab === 'governance' && <GovernanceTab />}
          {activeTab === 'system' && <SystemSettingsTab />}
          {activeTab === 'context_engineering' && <ContextEngineeringTab />}
          {activeTab === 'integration_scalability' && <IntegrationScalabilityTab />}
        </div>
      </div>
    </div>
  );
}
