'use client';

import { useState, useEffect } from 'react';
import { apiClient, ToolMetadata } from '@/lib/api-client';
import JsonSchemaEditor from './JsonSchemaEditor';

export default function ToolsTab() {
  const [tools, setTools] = useState<ToolMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTool, setEditingTool] = useState<ToolMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [docsModalOpen, setDocsModalOpen] = useState(false);

  const emptyTool: ToolMetadata = {
    tool_id: '',
    name: '',
    description: '',
    endpoint: '',
    input_schema: { type: 'object', properties: {} },
    output_schema: { type: 'object', properties: {} },
    lineage_tags: [],
  };

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listTools();
      setTools(data.tools);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTool(emptyTool);
    setModalOpen(true);
  };

  const handleEdit = (tool: ToolMetadata) => {
    setEditingTool({ ...tool });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!editingTool) return;

    try {
      setError(null);
      const isNew = !tools.find((t) => t.tool_id === editingTool.tool_id);

      if (isNew) {
        await apiClient.createTool(editingTool);
      } else {
        await apiClient.updateTool(editingTool.tool_id, editingTool);
      }

      await loadTools();
      setModalOpen(false);
      setEditingTool(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (toolId: string) => {
    if (!confirm(`Delete tool '${toolId}'? This cannot be undone.`)) return;

    try {
      setError(null);
      await apiClient.deleteTool(toolId);
      await loadTools();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCancel = () => {
    setModalOpen(false);
    setEditingTool(null);
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-900">Loading tools...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Tools ({tools.length})</h2>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + Add Tool
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tool ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Endpoint
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Lineage Tags
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tools.map((tool) => (
              <tr key={tool.tool_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{tool.tool_id}</td>
                <td className="px-6 py-4 text-sm text-gray-700">{tool.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {tool.description.length > 50
                    ? `${tool.description.substring(0, 50)}...`
                    : tool.description}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 font-mono">{tool.endpoint}</td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {tool.lineage_tags.length > 2
                    ? `${tool.lineage_tags.slice(0, 2).join(', ')}...`
                    : tool.lineage_tags.join(', ')}
                </td>
                <td className="px-6 py-4 text-right text-sm space-x-2">
                  <button
                    onClick={() => handleEdit(tool)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(tool.tool_id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalOpen && editingTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {tools.find((t) => t.tool_id === editingTool.tool_id) ? 'Edit' : 'Create'} Tool
            </h2>

            <div className="space-y-4">
              {/* Row 1: tool_id and name */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tool ID *</label>
                  <input
                    type="text"
                    value={editingTool.tool_id}
                    onChange={(e) =>
                      setEditingTool({ ...editingTool, tool_id: e.target.value })
                    }
                    disabled={!!tools.find((t) => t.tool_id === editingTool.tool_id)}
                    className={`w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 ${
                      tools.find((t) => t.tool_id === editingTool.tool_id) ? 'bg-gray-100' : ''
                    }`}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={editingTool.name}
                    onChange={(e) => setEditingTool({ ...editingTool, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
              </div>

              {/* Row 2: description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <textarea
                  value={editingTool.description}
                  onChange={(e) =>
                    setEditingTool({ ...editingTool, description: e.target.value })
                  }
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                />
              </div>

              {/* Row 3: endpoint and lineage_tags */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint *</label>
                  <input
                    type="text"
                    value={editingTool.endpoint}
                    onChange={(e) => setEditingTool({ ...editingTool, endpoint: e.target.value })}
                    disabled={!!tools.find((t) => t.tool_id === editingTool.tool_id)}
                    className={`w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 font-mono text-sm ${
                      tools.find((t) => t.tool_id === editingTool.tool_id) ? 'bg-gray-100' : ''
                    }`}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lineage Tags * (comma-separated)
                    <button
                      type="button"
                      onClick={() => setDocsModalOpen(true)}
                      className="ml-2 text-blue-600 hover:text-blue-800 text-base"
                      title="Learn about lineage tags"
                    >
                      ℹ️
                    </button>
                  </label>
                  <input
                    type="text"
                    value={editingTool.lineage_tags.join(', ')}
                    onChange={(e) =>
                      setEditingTool({
                        ...editingTool,
                        lineage_tags: e.target.value
                          .split(',')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                    placeholder="fraud_detection, rule_based"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"
                  />
                </div>
              </div>

              {/* Row 4: input_schema */}
              <JsonSchemaEditor
                label="Input Schema *"
                value={editingTool.input_schema}
                onChange={(value) => setEditingTool({ ...editingTool, input_schema: value })}
              />

              {/* Row 5: output_schema */}
              <JsonSchemaEditor
                label="Output Schema *"
                value={editingTool.output_schema}
                onChange={(value) => setEditingTool({ ...editingTool, output_schema: value })}
              />
            </div>

            {/* Footer buttons */}
            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lineage Tags Documentation Modal */}
      {docsModalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setDocsModalOpen(false)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Lineage Tags Documentation</h2>
              <button
                onClick={() => setDocsModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                title="Close"
              >
                ×
              </button>
            </div>

            <div className="space-y-6 text-gray-900">
              {/* Purpose Section */}
              <section>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Purpose of Lineage Tags</h3>
                <p className="text-gray-700 mb-3">Lineage tags serve three primary purposes:</p>

                <div className="space-y-3 ml-4">
                  <div>
                    <h4 className="font-semibold text-gray-900">1. Tool Categorization & Discovery</h4>
                    <ul className="list-disc ml-6 text-gray-700 space-y-1">
                      <li>Help organize tools by their domain and purpose</li>
                      <li>Enable filtering and searching tools by category</li>
                      <li>Support future features like "show me all fraud detection tools"</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900">2. Data Lineage Tracking</h4>
                    <ul className="list-disc ml-6 text-gray-700 space-y-1">
                      <li>Document what type of data the tool produces</li>
                      <li>Track the provenance and reliability of tool outputs</li>
                      <li>Support audit trails for compliance (important in insurance)</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900">3. Methodology Classification</h4>
                    <ul className="list-disc ml-6 text-gray-700 space-y-1">
                      <li>Describe the approach the tool uses</li>
                      <li>Indicate the reliability and trustworthiness of results</li>
                      <li>Help agents understand which tools to trust for authoritative vs. analytical purposes</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Tag Categories Section */}
              <section className="border-t pt-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Tag Categories and Meanings</h3>
                <p className="text-gray-700 mb-4">
                  The lineage_tags fall into two main categories:
                </p>

                {/* Data Domain Tags */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    Data Domain Tags <span className="text-sm font-normal text-gray-600">(What the tool does)</span>
                  </h4>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-700 mb-2">Current examples from your registry:</p>
                    <ul className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <li><code className="bg-gray-200 px-2 py-1 rounded">policy_data</code> - Works with policy information</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">coverage_validation</code> - Validates coverage</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">coverage_analysis</code> - Analyzes coverage determination</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">fraud_detection</code> - Detects fraud indicators</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">pattern_analysis</code> - Analyzes patterns in data</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">historical_data</code> - Uses historical claims data</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">validation</code> - Validates data schema/quality</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">data_quality</code> - Checks data completeness</li>
                      <li><code className="bg-gray-200 px-2 py-1 rounded">decision_support</code> - Supports decision-making</li>
                    </ul>
                  </div>
                </div>

                {/* Methodology Tags */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    Methodology Tags <span className="text-sm font-normal text-gray-600">(How the tool works)</span>
                  </h4>

                  <div className="space-y-4">
                    {/* Authoritative */}
                    <div className="border-l-4 border-blue-500 pl-4">
                      <h5 className="font-semibold text-gray-900">
                        1. <code className="bg-blue-100 px-2 py-1 rounded">authoritative</code>
                        <span className="text-sm font-normal text-gray-600 ml-2">(Used by: policy_snapshot)</span>
                      </h5>
                      <p className="text-gray-700 mt-1"><strong>Meaning:</strong> Tool provides definitive, official, single-source-of-truth data</p>
                      <p className="text-sm text-gray-600 mt-2"><strong>Characteristics:</strong></p>
                      <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                        <li>Returns factual data from authoritative systems (policy database, coverage limits)</li>
                        <li>Results are not debatable or probabilistic</li>
                        <li>Should be trusted as ground truth</li>
                      </ul>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Example:</strong> Policy snapshot retrieves official policy data - this is the authoritative source for coverage limits and deductibles
                      </p>
                    </div>

                    {/* Deterministic */}
                    <div className="border-l-4 border-green-500 pl-4">
                      <h5 className="font-semibold text-gray-900">
                        2. <code className="bg-green-100 px-2 py-1 rounded">deterministic</code>
                        <span className="text-sm font-normal text-gray-600 ml-2">(Used by: fraud_rules)</span>
                      </h5>
                      <p className="text-gray-700 mt-1"><strong>Meaning:</strong> Tool uses rule-based logic that produces consistent, repeatable results</p>
                      <p className="text-sm text-gray-600 mt-2"><strong>Characteristics:</strong></p>
                      <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                        <li>Same input always produces same output</li>
                        <li>Uses explicit business rules (if-then logic)</li>
                        <li>No randomness or probability</li>
                        <li>Fully explainable and auditable</li>
                      </ul>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Example:</strong> Fraud rules engine - if claim amount &gt; $10k AND submitted within 30 days of policy start, trigger rule #42
                      </p>
                    </div>

                    {/* Heuristic */}
                    <div className="border-l-4 border-purple-500 pl-4">
                      <h5 className="font-semibold text-gray-900">
                        3. <code className="bg-purple-100 px-2 py-1 rounded">heuristic</code>
                        <span className="text-sm font-normal text-gray-600 ml-2">(Used by: similarity)</span>
                      </h5>
                      <p className="text-gray-700 mt-1"><strong>Meaning:</strong> Tool uses pattern-matching, similarity analysis, or probabilistic methods</p>
                      <p className="text-sm text-gray-600 mt-2"><strong>Characteristics:</strong></p>
                      <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                        <li>Results are approximate, not exact</li>
                        <li>Uses algorithms like cosine similarity, clustering</li>
                        <li>Provides insights but not definitive answers</li>
                        <li>May produce different results as data changes</li>
                      </ul>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Example:</strong> Similar claims finder - uses heuristic algorithms to find patterns and anomalies in historical data
                      </p>
                    </div>

                    {/* Rule-based */}
                    <div className="border-l-4 border-orange-500 pl-4">
                      <h5 className="font-semibold text-gray-900">
                        4. <code className="bg-orange-100 px-2 py-1 rounded">rule_based</code>
                        <span className="text-sm font-normal text-gray-600 ml-2">(Used by: fraud_rules, coverage_rules, decision_rules)</span>
                      </h5>
                      <p className="text-gray-700 mt-1"><strong>Meaning:</strong> Tool applies explicit business rules to make decisions</p>
                      <p className="text-sm text-gray-600 mt-2"><strong>Characteristics:</strong></p>
                      <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                        <li>Uses configurable rule sets</li>
                        <li>Rules can be versioned and updated</li>
                        <li>Transparent decision logic</li>
                        <li>Often deterministic but rules can be changed</li>
                      </ul>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Example:</strong> Coverage rules engine applies exclusion rules, decision rules engine determines recommended actions
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              {/* Close button at bottom */}
              <div className="border-t pt-4 flex justify-end">
                <button
                  onClick={() => setDocsModalOpen(false)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
