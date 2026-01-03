'use client';

import { useState, useEffect } from 'react';
import { apiClient, Artifact, ArtifactVersion, ArtifactVersionCreateRequest } from '@/lib/api-client';

export default function ArtifactVersionBrowser() {
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [versions, setVersions] = useState<ArtifactVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<Artifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newArtifact, setNewArtifact] = useState<ArtifactVersionCreateRequest>({
    artifact_id: '',
    content: {},
    metadata: {},
    tags: [],
  });
  const [contentJson, setContentJson] = useState('{}');
  const [metadataJson, setMetadataJson] = useState('{}');

  useEffect(() => {
    loadArtifacts();
  }, []);

  useEffect(() => {
    if (selectedArtifact) {
      loadVersions(selectedArtifact);
    }
  }, [selectedArtifact]);

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listArtifacts();
      setArtifacts(data.artifacts);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async (artifactId: string) => {
    try {
      setLoading(true);
      const data = await apiClient.listArtifactVersions(artifactId);
      setVersions(data.versions);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      setVersions([]);
    } finally {
      setLoading(false);
    }
  };

  const loadVersionDetails = async (artifactId: string, version: number) => {
    try {
      const artifact = await apiClient.getArtifactVersion(artifactId, version);
      setSelectedVersion(artifact);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteVersion = async (artifactId: string, version: number) => {
    if (!confirm(`Are you sure you want to delete version ${version} of artifact ${artifactId}?`)) {
      return;
    }

    try {
      await apiClient.deleteArtifactVersion(artifactId, version);
      await loadVersions(artifactId);
      if (selectedVersion && selectedVersion.version === version) {
        setSelectedVersion(null);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddArtifact = async () => {
    try {
      setError(null);

      // Parse content and metadata JSON
      let content = {};
      let metadata = {};

      try {
        content = JSON.parse(contentJson);
      } catch (e) {
        setError('Invalid JSON in content field');
        return;
      }

      try {
        metadata = JSON.parse(metadataJson);
      } catch (e) {
        setError('Invalid JSON in metadata field');
        return;
      }

      // Parse tags from comma-separated string
      const tagsInput = (newArtifact.tags as any);
      const tags = typeof tagsInput === 'string'
        ? tagsInput.split(',').map((t: string) => t.trim()).filter(Boolean)
        : tagsInput || [];

      await apiClient.createArtifactVersion({
        artifact_id: newArtifact.artifact_id,
        content,
        parent_version: newArtifact.parent_version,
        metadata,
        tags,
      });

      // Reset form and close modal
      setNewArtifact({
        artifact_id: '',
        content: {},
        metadata: {},
        tags: [],
      });
      setContentJson('{}');
      setMetadataJson('{}');
      setShowAddModal(false);

      // Reload artifacts
      await loadArtifacts();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleApplyVersionLimit = async (artifactId: string) => {
    const maxVersionsStr = prompt('Enter maximum versions to keep:', '10');
    if (!maxVersionsStr) return;

    const maxVersions = parseInt(maxVersionsStr);
    if (isNaN(maxVersions) || maxVersions < 1) {
      alert('Please enter a valid number greater than 0');
      return;
    }

    try {
      const result = await apiClient.applyVersionLimit(artifactId, maxVersions);
      alert(`Version limit applied: ${result.deleted_count} versions deleted`);
      await loadVersions(artifactId);
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

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (loading && artifacts.length === 0) {
    return <div className="text-center py-8">Loading artifacts...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Artifact Version Browser</h3>
        <p className="text-sm text-blue-700">
          Browse artifact versions with lineage tracking. Click an artifact to view its version history.
        </p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}

      <div className="flex justify-end">
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          + Add Artifact Version
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Artifacts List */}
        <div className="col-span-1">
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-semibold text-gray-900">Artifacts</h4>
              <p className="text-xs text-gray-500 mt-1">{artifacts.length} total</p>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {artifacts.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No artifacts found. Add a new artifact to get started.
                </div>
              ) : (
                artifacts.map((artifactId) => (
                  <div
                    key={artifactId}
                    onClick={() => setSelectedArtifact(artifactId)}
                    className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedArtifact === artifactId ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-900 break-all">{artifactId}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Versions List */}
        <div className="col-span-1">
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-semibold text-gray-900">Versions</h4>
              {selectedArtifact && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500">{versions.length} versions</p>
                  <button
                    onClick={() => handleApplyVersionLimit(selectedArtifact)}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                  >
                    Apply Version Limit
                  </button>
                </div>
              )}
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {!selectedArtifact ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  Select an artifact to view versions
                </div>
              ) : versions.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No versions found
                </div>
              ) : (
                versions.map((version) => (
                  <div
                    key={version.version}
                    onClick={() => loadVersionDetails(version.artifact_id, version.version)}
                    className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedVersion?.version === version.version ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">
                          v{version.version}
                          {version.parent_version && (
                            <span className="text-xs text-gray-500 ml-2">
                              (from v{version.parent_version})
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {formatDate(version.created_at)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatBytes(version.size_bytes)}
                        </div>
                        {version.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {version.tags.map((tag, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteVersion(version.artifact_id, version.version);
                        }}
                        className="text-red-600 hover:text-red-800 text-xs ml-2"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Version Details */}
        <div className="col-span-1">
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-semibold text-gray-900">Version Details</h4>
            </div>
            <div className="p-4 max-h-96 overflow-y-auto">
              {!selectedVersion ? (
                <div className="text-center text-gray-500 text-sm">
                  Select a version to view details
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Handle</label>
                    <div className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded break-all">
                      {selectedVersion.handle}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Version</label>
                    <div className="text-sm text-gray-900">v{selectedVersion.version}</div>
                  </div>

                  {selectedVersion.parent_version && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Parent Version</label>
                      <div className="text-sm text-gray-900">v{selectedVersion.parent_version}</div>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Created At</label>
                    <div className="text-sm text-gray-900">{formatDate(selectedVersion.created_at)}</div>
                  </div>

                  {selectedVersion.tags.length > 0 && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Tags</label>
                      <div className="flex flex-wrap gap-1">
                        {selectedVersion.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {Object.keys(selectedVersion.metadata).length > 0 && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Metadata</label>
                      <pre className="text-xs text-gray-900 bg-gray-50 p-2 rounded overflow-auto">
                        {JSON.stringify(selectedVersion.metadata, null, 2)}
                      </pre>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Content</label>
                    <pre className="text-xs text-gray-900 bg-gray-50 p-2 rounded overflow-auto max-h-64">
                      {JSON.stringify(selectedVersion.content, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Artifact Version Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Artifact Version</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-black mb-1">Artifact ID</label>
                <input
                  type="text"
                  value={newArtifact.artifact_id}
                  onChange={(e) => setNewArtifact({ ...newArtifact, artifact_id: e.target.value })}
                  placeholder="e.g., evidence_map_001"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter a new artifact ID to create first version, or existing ID to add a new version
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Content (JSON)</label>
                <textarea
                  value={contentJson}
                  onChange={(e) => setContentJson(e.target.value)}
                  placeholder='{"key": "value"}'
                  rows={6}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black font-mono"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter valid JSON for artifact content
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Parent Version (optional)</label>
                <input
                  type="number"
                  value={newArtifact.parent_version || ''}
                  onChange={(e) => setNewArtifact({ ...newArtifact, parent_version: parseInt(e.target.value) || undefined })}
                  placeholder="Leave empty for first version"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Metadata (JSON, optional)</label>
                <textarea
                  value={metadataJson}
                  onChange={(e) => setMetadataJson(e.target.value)}
                  placeholder='{"author": "system"}'
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-black mb-1">Tags (comma-separated, optional)</label>
                <input
                  type="text"
                  value={Array.isArray(newArtifact.tags) ? newArtifact.tags.join(', ') : newArtifact.tags || ''}
                  onChange={(e) => setNewArtifact({ ...newArtifact, tags: e.target.value as any })}
                  placeholder="e.g., draft, approved, final"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-black"
                />
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
                onClick={handleAddArtifact}
                disabled={!newArtifact.artifact_id.trim() || !contentJson.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                Add Version
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
