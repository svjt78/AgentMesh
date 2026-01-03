'use client';

import { useEffect, useState } from 'react';
import { apiClient, ArtifactVersion } from '@/lib/api-client';

interface ArtifactListResponse {
  artifacts: string[];
  total_count: number;
  timestamp: string;
}

export default function ArtifactsPage() {
  const [artifactIds, setArtifactIds] = useState<string[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string>('');
  const [versions, setVersions] = useState<ArtifactVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      const response = (await apiClient.listArtifacts()) as ArtifactListResponse;
      setArtifactIds(response.artifacts || []);
      setSelectedArtifact(response.artifacts?.[0] || '');
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load artifacts');
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async (artifactId: string) => {
    if (!artifactId) return;
    try {
      setLoadingVersions(true);
      const response = await apiClient.listArtifactVersions(artifactId);
      setVersions(response.versions || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load artifact versions');
    } finally {
      setLoadingVersions(false);
    }
  };

  useEffect(() => {
    loadArtifacts();
  }, []);

  useEffect(() => {
    if (selectedArtifact) {
      loadVersions(selectedArtifact);
    }
  }, [selectedArtifact]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Artifact Versions</h1>
        <p className="mt-2 text-sm text-gray-600">
          Browse artifact handles and version metadata produced by the workflow.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Artifacts</h2>
            <p className="text-sm text-gray-600">Select an artifact to view versions.</p>
          </div>
          <button
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
            onClick={loadArtifacts}
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="mt-4 text-sm text-gray-500">Loading artifacts…</div>
        ) : artifactIds.length === 0 ? (
          <div className="mt-4 rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            No artifacts found yet.
          </div>
        ) : (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Artifact ID</label>
            <select
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={selectedArtifact}
              onChange={(e) => setSelectedArtifact(e.target.value)}
            >
              {artifactIds.map((artifactId) => (
                <option key={artifactId} value={artifactId}>
                  {artifactId}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="mt-6">
          <h3 className="text-md font-semibold">Versions</h3>
          {loadingVersions ? (
            <div className="mt-3 text-sm text-gray-500">Loading versions…</div>
          ) : versions.length === 0 ? (
            <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
              No versions found for this artifact.
            </div>
          ) : (
            <div className="mt-3 overflow-hidden rounded border border-gray-200">
              <div className="grid grid-cols-5 gap-4 bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-500">
                <div>Version</div>
                <div>Handle</div>
                <div>Created</div>
                <div>Size</div>
                <div>Parent</div>
              </div>
              {versions.map((version) => (
                <div key={version.version} className="grid grid-cols-5 gap-4 border-t px-4 py-3 text-sm">
                  <div>{version.version}</div>
                  <div className="truncate" title={version.handle}>
                    {version.handle}
                  </div>
                  <div>{new Date(version.created_at).toLocaleString()}</div>
                  <div>{version.size_bytes} bytes</div>
                  <div>{version.parent_version ?? '—'}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
