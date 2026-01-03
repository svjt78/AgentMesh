"""
Artifacts API - Endpoints for artifact versioning and management.

Demonstrates:
- Artifact version CRUD operations
- Handle generation
- Version lineage tracking
- Version limit enforcement
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


# ============= Request/Response Models =============

class ArtifactVersionCreateRequest(BaseModel):
    artifact_id: str
    content: Dict[str, Any]
    parent_version: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ArtifactVersionResponse(BaseModel):
    artifact_id: str
    version: int
    created_at: str
    parent_version: Optional[int] = None
    handle: str
    size_bytes: int
    metadata: Dict[str, Any]
    tags: List[str]


class ArtifactResponse(BaseModel):
    artifact_id: str
    version: int
    created_at: str
    parent_version: Optional[int] = None
    handle: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: List[str]


class ArtifactListResponse(BaseModel):
    artifacts: List[str]
    total_count: int
    timestamp: str


class VersionListResponse(BaseModel):
    artifact_id: str
    versions: List[ArtifactVersionResponse]
    total_count: int
    timestamp: str


# ============= Endpoints =============

@router.get("", response_model=ArtifactListResponse)
async def list_artifacts():
    """
    List all artifacts.

    Returns:
        List of artifact IDs
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        artifact_ids = artifact_store.list_all_artifacts()

        return ArtifactListResponse(
            artifacts=artifact_ids,
            total_count=len(artifact_ids),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list artifacts: {str(e)}"
        )


@router.post("/versions", response_model=ArtifactVersionResponse, status_code=201)
async def create_artifact_version(
    request: ArtifactVersionCreateRequest,
    session_id: Optional[str] = Query(None, description="Associated session ID for event logging")
):
    """
    Create a new version of an artifact.

    Args:
        request: Artifact version creation request
        session_id: Optional session ID for event logging

    Returns:
        Created artifact version metadata
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store
        from ..services.storage import write_event

        artifact_store = get_artifact_version_store()

        # Save artifact version
        handle = artifact_store.save_artifact_version(
            artifact_id=request.artifact_id,
            content=request.content,
            parent_version=request.parent_version,
            metadata=request.metadata,
            tags=request.tags
        )

        # Get the created version
        artifact = artifact_store.get_artifact_version(request.artifact_id)

        if not artifact:
            raise HTTPException(
                status_code=500,
                detail="Artifact version created but could not be retrieved"
            )

        # Write artifact_version_created event
        if session_id:
            artifact_event = {
                "event_type": "artifact_version_created",
                "session_id": session_id,
                "artifact_id": artifact.artifact_id,
                "version": artifact.version,
                "parent_version": artifact.parent_version,
                "handle": artifact.handle,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            write_event(session_id, artifact_event)

        logger.info(
            f"Artifact version created: {handle}, "
            f"parent={request.parent_version}, size={len(request.content)} fields"
        )

        # Find the version metadata
        versions = artifact_store.list_artifact_versions(artifact.artifact_id)
        version_meta = next((v for v in versions if v.version == artifact.version), None)

        if not version_meta:
            raise HTTPException(
                status_code=500,
                detail="Version metadata not found"
            )

        return ArtifactVersionResponse(
            artifact_id=version_meta.version,
            version=version_meta.version,
            created_at=version_meta.created_at,
            parent_version=version_meta.parent_version,
            handle=version_meta.handle,
            size_bytes=version_meta.size_bytes,
            metadata=version_meta.metadata,
            tags=version_meta.tags
        )

    except Exception as e:
        logger.error(f"Failed to create artifact version: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create artifact version: {str(e)}"
        )


@router.get("/{artifact_id}/versions", response_model=VersionListResponse)
async def list_artifact_versions(artifact_id: str):
    """
    List all versions of an artifact.

    Args:
        artifact_id: Artifact identifier

    Returns:
        List of version metadata
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        versions = artifact_store.list_artifact_versions(artifact_id)

        if not versions:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{artifact_id}' not found"
            )

        return VersionListResponse(
            artifact_id=artifact_id,
            versions=[
                ArtifactVersionResponse(
                    artifact_id=artifact_id,
                    version=v.version,
                    created_at=v.created_at,
                    parent_version=v.parent_version,
                    handle=v.handle,
                    size_bytes=v.size_bytes,
                    metadata=v.metadata,
                    tags=v.tags
                )
                for v in versions
            ],
            total_count=len(versions),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list versions for artifact {artifact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list artifact versions: {str(e)}"
        )


@router.get("/{artifact_id}/versions/{version}", response_model=ArtifactResponse)
async def get_artifact_version(
    artifact_id: str,
    version: int
):
    """
    Get a specific version of an artifact with content.

    Args:
        artifact_id: Artifact identifier
        version: Version number

    Returns:
        Artifact with content
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        artifact = artifact_store.get_artifact_version(artifact_id, version)

        if not artifact:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{artifact_id}' version {version} not found"
            )

        return ArtifactResponse(
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            created_at=artifact.created_at,
            parent_version=artifact.parent_version,
            handle=artifact.handle,
            content=artifact.content,
            metadata=artifact.metadata,
            tags=artifact.tags
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifact {artifact_id}/v{version}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get artifact version: {str(e)}"
        )


@router.get("/{artifact_id}/versions/latest", response_model=ArtifactResponse)
async def get_latest_artifact_version(artifact_id: str):
    """
    Get the latest version of an artifact.

    Args:
        artifact_id: Artifact identifier

    Returns:
        Latest artifact version with content
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        artifact = artifact_store.get_artifact_version(artifact_id, version=None)

        if not artifact:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{artifact_id}' not found"
            )

        return ArtifactResponse(
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            created_at=artifact.created_at,
            parent_version=artifact.parent_version,
            handle=artifact.handle,
            content=artifact.content,
            metadata=artifact.metadata,
            tags=artifact.tags
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest artifact {artifact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest artifact: {str(e)}"
        )


@router.delete("/{artifact_id}/versions/{version}")
async def delete_artifact_version(
    artifact_id: str,
    version: int,
    session_id: Optional[str] = Query(None, description="Associated session ID for event logging")
):
    """
    Delete a specific version of an artifact.

    WARNING: This does not check for dependencies. Use with caution.

    Args:
        artifact_id: Artifact identifier
        version: Version number to delete
        session_id: Optional session ID for event logging

    Returns:
        Deletion confirmation
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store
        from ..services.storage import write_event

        artifact_store = get_artifact_version_store()
        success = artifact_store.delete_artifact_version(artifact_id, version)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{artifact_id}' version {version} not found"
            )

        # Write deletion event
        if session_id:
            deletion_event = {
                "event_type": "artifact_version_deleted",
                "session_id": session_id,
                "artifact_id": artifact_id,
                "version": version,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            write_event(session_id, deletion_event)

        logger.info(f"Artifact version deleted: {artifact_id}/v{version}")

        return {
            "artifact_id": artifact_id,
            "version": version,
            "status": "deleted",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete artifact {artifact_id}/v{version}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete artifact version: {str(e)}"
        )


@router.get("/{artifact_id}/lineage/{version}")
async def get_version_lineage(
    artifact_id: str,
    version: int
):
    """
    Get lineage chain for a specific version.

    Returns the chain from root to the specified version.

    Args:
        artifact_id: Artifact identifier
        version: Version number

    Returns:
        Lineage chain (list of version numbers)
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        lineage = artifact_store.get_version_lineage(artifact_id, version)

        if not lineage:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{artifact_id}' version {version} not found"
            )

        return {
            "artifact_id": artifact_id,
            "version": version,
            "lineage": lineage,
            "lineage_depth": len(lineage),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lineage for {artifact_id}/v{version}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get version lineage: {str(e)}"
        )


@router.post("/{artifact_id}/apply-version-limit")
async def apply_version_limit(
    artifact_id: str,
    max_versions: int = Query(10, ge=1, le=100, description="Maximum versions to keep")
):
    """
    Apply version limit to an artifact by deleting oldest versions.

    Keeps the most recent max_versions, deletes older ones.
    Does not delete versions that are parents of kept versions.

    Args:
        artifact_id: Artifact identifier
        max_versions: Maximum versions to keep

    Returns:
        Number of versions deleted
    """
    try:
        from ..services.artifact_version_store import get_artifact_version_store

        artifact_store = get_artifact_version_store()
        deleted_count = artifact_store.apply_version_limit(artifact_id, max_versions)

        logger.info(
            f"Version limit applied to {artifact_id}: "
            f"{deleted_count} versions deleted, keeping {max_versions}"
        )

        return {
            "artifact_id": artifact_id,
            "max_versions": max_versions,
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to apply version limit to {artifact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply version limit: {str(e)}"
        )
