"""
ArtifactVersionStore - Service for managing artifact versioning and lineage.

Demonstrates:
- Artifact version storage and retrieval
- Lineage tracking (parent-child relationships)
- Handle generation (artifact://{id}/v{version})
- Version metadata management
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============= Data Models =============

class ArtifactVersion(BaseModel):
    """Metadata for a single artifact version."""
    version: int
    created_at: str
    parent_version: Optional[int] = None
    handle: str
    size_bytes: int
    metadata: Dict[str, Any] = {}
    tags: List[str] = []


class ArtifactMetadata(BaseModel):
    """Complete metadata for an artifact across all versions."""
    artifact_id: str
    current_version: int
    versions: List[ArtifactVersion]


class Artifact(BaseModel):
    """Complete artifact with content and metadata."""
    artifact_id: str
    version: int
    created_at: str
    parent_version: Optional[int] = None
    handle: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    tags: List[str] = []


# ============= ArtifactVersionStore Service =============

class ArtifactVersionStore:
    """
    Manages artifact versioning with lineage tracking.

    Storage structure:
    - storage/artifacts/{artifact_id}/v1.json (version content)
    - storage/artifacts/{artifact_id}/v2.json
    - storage/artifacts/{artifact_id}/metadata.json (lineage)
    """

    def __init__(self, storage_path: str = "storage/artifacts"):
        """
        Initialize artifact version store.

        Args:
            storage_path: Base path for artifact storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ArtifactVersionStore initialized at {self.storage_path}")

    def _get_artifact_dir(self, artifact_id: str) -> Path:
        """Get directory path for an artifact."""
        return self.storage_path / artifact_id

    def _get_version_file_path(self, artifact_id: str, version: int) -> Path:
        """Get file path for a specific version."""
        return self._get_artifact_dir(artifact_id) / f"v{version}.json"

    def _get_metadata_file_path(self, artifact_id: str) -> Path:
        """Get file path for artifact metadata."""
        return self._get_artifact_dir(artifact_id) / "metadata.json"

    def _load_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """Load artifact metadata from disk."""
        metadata_path = self._get_metadata_file_path(artifact_id)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            return ArtifactMetadata(**data)
        except Exception as e:
            logger.error(f"Failed to load metadata for artifact {artifact_id}: {e}")
            return None

    def _save_metadata(self, metadata: ArtifactMetadata) -> None:
        """Save artifact metadata to disk."""
        artifact_dir = self._get_artifact_dir(metadata.artifact_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = self._get_metadata_file_path(metadata.artifact_id)

        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata for artifact {metadata.artifact_id}: {e}")
            raise

    def generate_handle(self, artifact_id: str, version: int) -> str:
        """
        Generate artifact handle for a specific version.

        Args:
            artifact_id: Artifact identifier
            version: Version number

        Returns:
            Handle string (format: artifact://{artifact_id}/v{version})
        """
        return f"artifact://{artifact_id}/v{version}"

    def save_artifact_version(
        self,
        artifact_id: str,
        content: Dict[str, Any],
        parent_version: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Save a new version of an artifact.

        Args:
            artifact_id: Artifact identifier
            content: Artifact content (JSON-serializable dict)
            parent_version: Parent version number (None for first version)
            metadata: Additional metadata for this version
            tags: Tags for categorization

        Returns:
            Handle for the created version
        """
        try:
            # Load existing metadata or create new
            artifact_metadata = self._load_metadata(artifact_id)

            if artifact_metadata is None:
                # First version
                new_version = 1
                artifact_metadata = ArtifactMetadata(
                    artifact_id=artifact_id,
                    current_version=1,
                    versions=[]
                )
            else:
                # Increment version
                new_version = artifact_metadata.current_version + 1
                artifact_metadata.current_version = new_version

            # Generate handle
            handle = self.generate_handle(artifact_id, new_version)

            # Serialize content to calculate size
            content_json = json.dumps(content, indent=2)
            size_bytes = len(content_json.encode('utf-8'))

            # Create version metadata
            version_metadata = ArtifactVersion(
                version=new_version,
                created_at=datetime.utcnow().isoformat() + "Z",
                parent_version=parent_version,
                handle=handle,
                size_bytes=size_bytes,
                metadata=metadata or {},
                tags=tags or []
            )

            # Add to versions list
            artifact_metadata.versions.append(version_metadata)

            # Save version content
            version_path = self._get_version_file_path(artifact_id, new_version)
            version_path.parent.mkdir(parents=True, exist_ok=True)

            with open(version_path, 'w') as f:
                f.write(content_json)

            # Save metadata
            self._save_metadata(artifact_metadata)

            logger.info(
                f"Artifact version created: {handle}, "
                f"parent={parent_version}, size={size_bytes} bytes"
            )

            return handle

        except Exception as e:
            logger.error(f"Failed to save artifact version {artifact_id}: {e}")
            raise

    def get_artifact_version(
        self,
        artifact_id: str,
        version: Optional[int] = None
    ) -> Optional[Artifact]:
        """
        Retrieve a specific version of an artifact.

        Args:
            artifact_id: Artifact identifier
            version: Version number (None for latest)

        Returns:
            Artifact object or None if not found
        """
        try:
            # Load metadata
            artifact_metadata = self._load_metadata(artifact_id)

            if artifact_metadata is None:
                logger.warning(f"Artifact not found: {artifact_id}")
                return None

            # Determine version to retrieve
            if version is None:
                version = artifact_metadata.current_version

            # Find version metadata
            version_meta = None
            for v in artifact_metadata.versions:
                if v.version == version:
                    version_meta = v
                    break

            if version_meta is None:
                logger.warning(f"Version {version} not found for artifact {artifact_id}")
                return None

            # Load version content
            version_path = self._get_version_file_path(artifact_id, version)

            if not version_path.exists():
                logger.error(f"Version file missing: {version_path}")
                return None

            with open(version_path, 'r') as f:
                content = json.load(f)

            # Create Artifact object
            artifact = Artifact(
                artifact_id=artifact_id,
                version=version_meta.version,
                created_at=version_meta.created_at,
                parent_version=version_meta.parent_version,
                handle=version_meta.handle,
                content=content,
                metadata=version_meta.metadata,
                tags=version_meta.tags
            )

            return artifact

        except Exception as e:
            logger.error(f"Failed to get artifact version {artifact_id}/v{version}: {e}")
            return None

    def list_artifact_versions(self, artifact_id: str) -> List[ArtifactVersion]:
        """
        List all versions of an artifact.

        Args:
            artifact_id: Artifact identifier

        Returns:
            List of version metadata (sorted by version number)
        """
        artifact_metadata = self._load_metadata(artifact_id)

        if artifact_metadata is None:
            return []

        return sorted(artifact_metadata.versions, key=lambda v: v.version)

    def list_all_artifacts(self) -> List[str]:
        """
        List all artifact IDs in storage.

        Returns:
            List of artifact IDs
        """
        if not self.storage_path.exists():
            return []

        artifact_ids = []

        for artifact_dir in self.storage_path.iterdir():
            if artifact_dir.is_dir():
                metadata_path = artifact_dir / "metadata.json"
                if metadata_path.exists():
                    artifact_ids.append(artifact_dir.name)

        return sorted(artifact_ids)

    def delete_artifact_version(self, artifact_id: str, version: int) -> bool:
        """
        Delete a specific version of an artifact.

        WARNING: This does not handle version dependencies. Use with caution.

        Args:
            artifact_id: Artifact identifier
            version: Version number to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Load metadata
            artifact_metadata = self._load_metadata(artifact_id)

            if artifact_metadata is None:
                return False

            # Find version to delete
            version_to_delete = None
            for v in artifact_metadata.versions:
                if v.version == version:
                    version_to_delete = v
                    break

            if version_to_delete is None:
                return False

            # Delete version file
            version_path = self._get_version_file_path(artifact_id, version)
            if version_path.exists():
                version_path.unlink()

            # Remove from metadata
            artifact_metadata.versions = [
                v for v in artifact_metadata.versions if v.version != version
            ]

            # Update current version if necessary
            if artifact_metadata.versions:
                artifact_metadata.current_version = max(v.version for v in artifact_metadata.versions)
                self._save_metadata(artifact_metadata)
            else:
                # No versions left, delete entire artifact directory
                artifact_dir = self._get_artifact_dir(artifact_id)
                for file in artifact_dir.iterdir():
                    file.unlink()
                artifact_dir.rmdir()

            logger.info(f"Artifact version deleted: {artifact_id}/v{version}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete artifact version {artifact_id}/v{version}: {e}")
            return False

    def get_version_lineage(self, artifact_id: str, version: int) -> List[int]:
        """
        Get lineage chain for a version (from root to this version).

        Args:
            artifact_id: Artifact identifier
            version: Version number

        Returns:
            List of version numbers in lineage order (root first)
        """
        artifact_metadata = self._load_metadata(artifact_id)

        if artifact_metadata is None:
            return []

        # Build parent map
        parent_map = {}
        for v in artifact_metadata.versions:
            parent_map[v.version] = v.parent_version

        # Traverse backwards from version to root
        lineage = []
        current = version

        while current is not None:
            lineage.append(current)
            current = parent_map.get(current)

        # Reverse to get root-first order
        return list(reversed(lineage))

    def apply_version_limit(self, artifact_id: str, max_versions: int) -> int:
        """
        Apply version limit by deleting oldest versions.

        Keeps the most recent max_versions, deletes older ones.
        Does not delete versions that are parents of kept versions.

        Args:
            artifact_id: Artifact identifier
            max_versions: Maximum versions to keep

        Returns:
            Number of versions deleted
        """
        artifact_metadata = self._load_metadata(artifact_id)

        if artifact_metadata is None:
            return 0

        if len(artifact_metadata.versions) <= max_versions:
            return 0

        # Sort by version number
        sorted_versions = sorted(artifact_metadata.versions, key=lambda v: v.version, reverse=True)

        # Keep most recent max_versions
        versions_to_keep = sorted_versions[:max_versions]
        keep_version_numbers = {v.version for v in versions_to_keep}

        # Also keep any versions that are parents of kept versions
        for v in versions_to_keep:
            if v.parent_version is not None:
                keep_version_numbers.add(v.parent_version)

        # Delete others
        deleted_count = 0
        for v in artifact_metadata.versions:
            if v.version not in keep_version_numbers:
                if self.delete_artifact_version(artifact_id, v.version):
                    deleted_count += 1

        logger.info(
            f"Applied version limit to {artifact_id}: "
            f"kept {len(keep_version_numbers)}, deleted {deleted_count}"
        )

        return deleted_count


# ============= Singleton Access =============

_artifact_version_store: Optional[ArtifactVersionStore] = None


def get_artifact_version_store() -> ArtifactVersionStore:
    """Get singleton instance of ArtifactVersionStore."""
    global _artifact_version_store

    if _artifact_version_store is None:
        from ..config import get_config
        config = get_config()

        # Get storage path from config or default
        storage_path = Path(config.storage_path) / "artifacts"
        _artifact_version_store = ArtifactVersionStore(str(storage_path))

    return _artifact_version_store
