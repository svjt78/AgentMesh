'use client';

import { useState, useEffect } from 'react';
import { apiClient, Memory, MemoryCreateRequest } from '@/lib/api-client';

export default function MemoryBrowser() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterTag, setFilterTag] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newMemory, setNewMemory] = useState<MemoryCreateRequest>({
    memory_type: 'insight',
    content: '',
    metadata: {},
    tags: [],
    expires_in_days: 90,
  });

  useEffect(() => {
    loadMemories();
  }, [filterType, filterTag]);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listMemories(50, 0, filterType || undefined, filterTag || undefined);
      setMemories(data.memories);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadMemories();
      return;
    }

    try {
      setLoading(true);
      const data = await apiClient.retrieveMemories({
        query: searchQuery,
        limit: 50,
        mode: 'reactive',
      });
      setMemories(data.memories);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) {
      return;
    }

    try {
      await apiClient.deleteMemory(memoryId);
      await loadMemories();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddMemory = async () => {
    try {
      setError(null);

      // Parse tags from comma-separated string
      const tagsInput = (newMemory.tags as any);
      const tags = typeof tagsInput === 'string'
        ? tagsInput.split(',').map((t: string) => t.trim()).filter(Boolean)
        : tagsInput || [];

      await apiClient.createMemory({
        ...newMemory,
        tags,
      });

      // Reset form and close modal
      setNewMemory({
        memory_type: 'insight',
        content: '',
        metadata: {},
        tags: [],
        expires_in_days: 90,
      });
      setShowAddModal(false);

      // Reload memories
      await loadMemories();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleApplyRetention = async () => {
    if (!confirm('Apply retention policy to delete expired memories?')) {
      return;
    }

    try {
      const result = await apiClient.applyRetentionPolicy();
      alert(`Retention policy applied: ${result.deleted_count} memories deleted`);
      await loadMemories();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  if (loading && memories.length === 0) {
    return <div className="text-center py-8">Loading memories...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Memory Browser</h3>
        <p className="text-sm text-blue-700">
          Browse, search, and manage long-term memories. Memories enable agents to recall information from past sessions.
        </p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}

      {/* Search and Filter Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-4 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-black mb-1">Search Content</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search memory content..."
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
              />
              <button
                onClick={handleSearch}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Search
              </button>
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    loadMemories();
                  }}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-black mb-1">Filter by Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
            >
              <option value="">All Types</option>
              <option value="session_conclusion">Session Conclusion</option>
              <option value="insight">Insight</option>
              <option value="user_preference">User Preference</option>
              <option value="fact">Fact</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-black mb-1">Filter by Tag</label>
            <input
              type="text"
              value={filterTag}
              onChange={(e) => setFilterTag(e.target.value)}
              placeholder="e.g., fraud, approved"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={handleApplyRetention}
            className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Apply Retention Policy
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            + Add Memory
          </button>
        </div>
      </div>

      {/* Memory Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Content
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tags
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expires
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {memories.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    No memories found. Add a new memory to get started.
                  </td>
                </tr>
              ) : (
                memories.map((memory) => (
                  <tr key={memory.memory_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                        {memory.memory_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-md">
                      <div className="truncate" title={memory.content}>
                        {truncateContent(memory.content, 100)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      <div className="flex flex-wrap gap-1">
                        {memory.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(memory.created_at)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {memory.expires_at ? formatDate(memory.expires_at) : 'Never'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <button
                        onClick={() => handleDelete(memory.memory_id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Memory</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Memory Type</label>
                <select
                  value={newMemory.memory_type}
                  onChange={(e) => setNewMemory({ ...newMemory, memory_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                >
                  <option value="session_conclusion">Session Conclusion</option>
                  <option value="insight">Insight</option>
                  <option value="user_preference">User Preference</option>
                  <option value="fact">Fact</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Content</label>
                <textarea
                  value={newMemory.content}
                  onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                  placeholder="Enter memory content..."
                  rows={4}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Tags (comma-separated)</label>
                <input
                  type="text"
                  value={Array.isArray(newMemory.tags) ? newMemory.tags.join(', ') : newMemory.tags || ''}
                  onChange={(e) => setNewMemory({ ...newMemory, tags: e.target.value as any })}
                  placeholder="e.g., fraud, high-priority, approved"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Expires In (days)</label>
                <input
                  type="number"
                  value={newMemory.expires_in_days || ''}
                  onChange={(e) => setNewMemory({ ...newMemory, expires_in_days: parseInt(e.target.value) || undefined })}
                  placeholder="90"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddMemory}
                disabled={!newMemory.content.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                Add Memory
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
