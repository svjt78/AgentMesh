from fastapi import APIRouter, HTTPException

from ..models.schemas import DLQListResponse, RegistryOperationResponse
from ..services.dlq_store import get_dlq_store

router = APIRouter(prefix="/dlq", tags=["dlq"])


@router.get("", response_model=DLQListResponse)
async def list_dlq():
    store = get_dlq_store()
    items = store.list_items()
    return DLQListResponse(items=items, total_count=len(items))


@router.post("/{item_id}/reprocess", response_model=RegistryOperationResponse)
async def reprocess_dlq(item_id: str):
    store = get_dlq_store()
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    return RegistryOperationResponse(
        success=True,
        message=f"Reprocess scheduled for {item_id}",
    )
