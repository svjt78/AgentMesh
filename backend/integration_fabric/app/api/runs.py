import asyncio
import copy
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..models.schemas import RunDetail, RunListResponse, RunResponse, RunRequest, WorkflowStep
from ..services.registry_manager import get_registry_manager
from ..services.run_store import get_run_store
from ..services.sse_broadcaster import get_broadcaster
from ..services.workflow_runner import WorkflowRunner

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunResponse)
async def create_run(request: RunRequest):
    registry = get_registry_manager()
    workflow = registry.get_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow '{request.workflow_id}' not found")

    workflow_to_run = copy.deepcopy(workflow)
    if request.simulate_failure:
        workflow_to_run.steps.append(
            WorkflowStep(
                id="simulate_failure",
                type="failure_simulation",
                failure_policy="dead_letter",
            )
        )

    run_id = f"run_{uuid.uuid4().hex[:10]}"
    runner = WorkflowRunner()
    run_store = get_run_store()
    run_payload = run_store.create_run(run_id, request.workflow_id, request.input_data)
    asyncio.create_task(runner.run(workflow_to_run, request.input_data, run_id, run_payload))

    return RunResponse(
        run_id=run_id,
        workflow_id=request.workflow_id,
        status="running",
        created_at=run_payload["created_at"],
        stream_url=f"/runs/{run_id}/stream",
        run_url=f"/runs/{run_id}",
    )


@router.get("", response_model=RunListResponse)
async def list_runs():
    run_store = get_run_store()
    runs = run_store.list_runs()
    return RunListResponse(
        runs=[
            {
                "run_id": item["run_id"],
                "workflow_id": item["workflow_id"],
                "status": item["status"],
                "created_at": item["created_at"],
                "completed_at": item.get("completed_at"),
            }
            for item in runs
        ],
        total_count=len(runs),
    )


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str):
    run_store = get_run_store()
    try:
        return run_store.get_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.delete("/{run_id}", status_code=204)
async def delete_run(run_id: str):
    run_store = get_run_store()
    try:
        run_store.delete_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return None


@router.get("/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    broadcaster = get_broadcaster()
    last_event_id = request.headers.get("Last-Event-ID")

    async def event_generator():
        async for event in broadcaster.subscribe(run_id, last_event_id=last_event_id):
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream")
