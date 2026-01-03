'use client';

import { useEffect, useState } from 'react';
import { apiClient, Memory } from '@/lib/api-client';

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const [memoryType, setMemoryType] = useState('insight');
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState('{"source":"ui"}');
  const [tags, setTags] = useState('');
  const [expiresInDays, setExpiresInDays] = useState<string>('');

  const loadMemories = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listMemories(50, 0);
      setMemories(response.memories || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load memories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleCreate = async () => {
    try {
      setCreating(true);
      const parsedMetadata = JSON.parse(metadata || '{}');
      const tagList = tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean);
      const expiresValue = expiresInDays ? parseInt(expiresInDays, 10) : undefined;

      await apiClient.createMemory({
        memory_type: memoryType,
        content,
        metadata: parsedMetadata,
        tags: tagList.length ? tagList : undefined,
        expires_in_days: Number.isFinite(expiresValue) ? expiresValue : undefined,
      });

      setContent('');
      setTags('');
      setExpiresInDays('');
      await loadMemories();
    } catch (err: any) {
      setError(err.message || 'Failed to create memory');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!confirm(`Delete memory ${memoryId}?`)) return;
    try {
      await apiClient.deleteMemory(memoryId);
      setMemories((prev) => prev.filter((m) => m.memory_id !== memoryId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete memory');
    }
  };

  const handleApplyRetention = async () => {
    try {
      await apiClient.applyRetentionPolicy();
      await loadMemories();
    } catch (err: any) {
      setError(err.message || 'Failed to apply retention policy');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Memory Browser</h1>
        <p className="mt-2 text-sm text-gray-600">
          Inspect and manage long-term memories used by the context engineering pipeline.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Create Memory</h2>
          <div className="mt-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Memory Type</label>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={memoryType}
                onChange={(e) => setMemoryType(e.target.value)}
              >
                <option value="insight">insight</option>
                <option value="session_conclusion">session_conclusion</option>
                <option value="user_preference">user_preference</option>
                <option value="fact">fact</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Content</label>
              <textarea
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Metadata (JSON)</label>
              <textarea
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
                rows={3}
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Tags (comma separated)</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Expires In Days (optional)</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                type="number"
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(e.target.value)}
              />
            </div>

            <button
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              onClick={handleCreate}
              disabled={creating || !content.trim()}
            >
              {creating ? 'Saving…' : 'Create Memory'}
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Stored Memories</h2>
            <button
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
              onClick={handleApplyRetention}
            >
              Apply Retention
            </button>
          </div>

          {loading ? (
            <div className="mt-4 text-sm text-gray-500">Loading memories…</div>
          ) : memories.length === 0 ? (
            <div className="mt-4 rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
              No memories found yet.
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {memories.map((memory) => (
                <div key={memory.memory_id} className="rounded border border-gray-200 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{memory.memory_type}</div>
                      <div className="text-xs text-gray-500">{memory.memory_id}</div>
                    </div>
                    <button
                      className="text-xs text-red-600 hover:text-red-700"
                      onClick={() => handleDelete(memory.memory_id)}
                    >
                      Delete
                    </button>
                  </div>
                  <p className="mt-2 text-sm text-gray-700">{memory.content}</p>
                  {memory.tags.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      Tags: {memory.tags.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
