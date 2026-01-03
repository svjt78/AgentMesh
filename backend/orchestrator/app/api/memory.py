"""
Memory API - Endpoints for long-term memory management.

Demonstrates:
- Memory CRUD operations
- Reactive and proactive retrieval
- Retention policy management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# ============= Request/Response Models =============

class MemoryCreateRequest(BaseModel):
    memory_type: str
    content: str
    metadata: dict
    tags: Optional[List[str]] = None
    expires_in_days: Optional[int] = None


class MemoryResponse(BaseModel):
    memory_id: str
    created_at: str
    memory_type: str
    content: str
    metadata: dict
    tags: List[str]
    expires_at: Optional[str] = None


class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total_count: int
    timestamp: str


class MemoryRetrieveRequest(BaseModel):
    query: Optional[str] = None
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    mode: str = "reactive"


# ============= Endpoints =============

@router.get("", response_model=MemoryListResponse)
async def list_memories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    tag: Optional[str] = Query(None, description="Filter by tag")
):
    """
    List all memories with pagination and filters.

    Returns:
        Paginated list of memories
    """
    try:
        from ..services.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()

        # Get memories
        if tag:
            memories = memory_manager.retrieve_memories(tags=[tag], limit=limit)
        elif memory_type:
            memories = memory_manager.retrieve_memories(memory_type=memory_type, limit=limit)
        else:
            memories = memory_manager.list_all_memories(limit=limit, offset=offset)

        return MemoryListResponse(
            memories=[
                MemoryResponse(
                    memory_id=m.memory_id,
                    created_at=m.created_at,
                    memory_type=m.memory_type,
                    content=m.content,
                    metadata=m.metadata,
                    tags=m.tags,
                    expires_at=m.expires_at
                )
                for m in memories
            ],
            total_count=len(memories),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Failed to list memories: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list memories: {str(e)}"
        )


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(request: MemoryCreateRequest):
    """
    Create a new memory.

    Args:
        request: Memory creation request

    Returns:
        Created memory
    """
    try:
        from ..services.memory_manager import get_memory_manager
        from ..services.storage import write_event

        memory_manager = get_memory_manager()

        # Store memory
        memory_id = memory_manager.store_memory(
            memory_type=request.memory_type,
            content=request.content,
            metadata=request.metadata,
            tags=request.tags,
            expires_in_days=request.expires_in_days
        )

        # Get the created memory
        memory = memory_manager.get_memory(memory_id)

        if not memory:
            raise HTTPException(
                status_code=500,
                detail="Memory created but could not be retrieved"
            )

        # Write memory creation event (optional: if you want to track this in sessions)
        # For now, we'll skip this as memories are cross-session

        logger.info(f"Memory created: {memory_id}, type={request.memory_type}")

        return MemoryResponse(
            memory_id=memory.memory_id,
            created_at=memory.created_at,
            memory_type=memory.memory_type,
            content=memory.content,
            metadata=memory.metadata,
            tags=memory.tags,
            expires_at=memory.expires_at
        )

    except Exception as e:
        logger.error(f"Failed to create memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create memory: {str(e)}"
        )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """
    Get a specific memory by ID.

    Args:
        memory_id: Memory identifier

    Returns:
        Memory details
    """
    try:
        from ..services.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()
        memory = memory_manager.get_memory(memory_id)

        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"Memory '{memory_id}' not found"
            )

        return MemoryResponse(
            memory_id=memory.memory_id,
            created_at=memory.created_at,
            memory_type=memory.memory_type,
            content=memory.content,
            metadata=memory.metadata,
            tags=memory.tags,
            expires_at=memory.expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory {memory_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory: {str(e)}"
        )


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a memory by ID.

    Args:
        memory_id: Memory identifier to delete

    Returns:
        Deletion confirmation
    """
    try:
        from ..services.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()
        success = memory_manager.delete_memory(memory_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Memory '{memory_id}' not found"
            )

        logger.info(f"Memory deleted: {memory_id}")

        return {
            "memory_id": memory_id,
            "status": "deleted",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete memory: {str(e)}"
        )


@router.post("/retrieve", response_model=MemoryListResponse)
async def retrieve_memories(request: MemoryRetrieveRequest):
    """
    Search and retrieve memories based on criteria.

    This endpoint supports both reactive and proactive memory retrieval.

    Args:
        request: Memory retrieval request

    Returns:
        Matching memories
    """
    try:
        from ..services.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()

        # Retrieve memories
        memories = memory_manager.retrieve_memories(
            query=request.query,
            memory_type=request.memory_type,
            tags=request.tags,
            limit=request.limit,
            mode=request.mode
        )

        return MemoryListResponse(
            memories=[
                MemoryResponse(
                    memory_id=m.memory_id,
                    created_at=m.created_at,
                    memory_type=m.memory_type,
                    content=m.content,
                    metadata=m.metadata,
                    tags=m.tags,
                    expires_at=m.expires_at
                )
                for m in memories
            ],
            total_count=len(memories),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve memories: {str(e)}"
        )


@router.post("/apply-retention")
async def apply_retention_policy():
    """
    Manually trigger retention policy application.

    Deletes expired memories based on expires_at timestamps.

    Returns:
        Number of memories deleted
    """
    try:
        from ..services.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()
        deleted_count = memory_manager.apply_retention_policy()

        logger.info(f"Retention policy applied: {deleted_count} memories deleted")

        return {
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to apply retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply retention policy: {str(e)}"
        )
