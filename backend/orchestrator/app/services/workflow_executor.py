"""
Workflow Executor - Background workflow execution with SSE streaming.

Demonstrates:
- Async workflow execution
- Event broadcasting
- Error handling
- Resource cleanup
- Integration with orchestrator
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .orchestrator_runner import OrchestratorRunner, create_orchestrator_runner
from .sse_broadcaster import get_broadcaster
from .progress_store import get_progress_store
from .storage import get_session_writer, get_artifact_store
from .registry_manager import get_registry_manager
from .llm_client import create_llm_client

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Execute workflows in background with SSE broadcasting.

    Scalability patterns:
    - Background task management
    - Non-blocking execution
    - Event streaming
    - Artifact persistence
    """

    def __init__(self):
        self.broadcaster = get_broadcaster()
        self.session_writer = get_session_writer()
        self.artifact_store = get_artifact_store()

        # Track running workflows
        self._running_workflows: Dict[str, asyncio.Task] = {}

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Execute workflow in background.

        Args:
            workflow_id: Workflow to execute
            input_data: Input data for workflow
            session_id: Optional session ID

        Returns:
            Session ID

        Demonstrates: Async task creation pattern
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id()

        # Initialize progress store for real-time streaming
        progress_store = get_progress_store()
        progress_store.create_session(session_id, workflow_id)

        # Log workflow start
        await self.broadcaster.broadcast_event(
            session_id=session_id,
            event_type="workflow_started",
            event_data={
                "workflow_id": workflow_id,
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat() + "Z"
            }
        )

        # Create background task
        task = asyncio.create_task(
            self._run_workflow_task(session_id, workflow_id, input_data)
        )

        self._running_workflows[session_id] = task

        return session_id

    async def _run_workflow_task(
        self,
        session_id: str,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Background task to run workflow.

        Demonstrates:
        - Sync-to-async bridging (orchestrator is sync)
        - Error handling
        - Resource cleanup
        """
        try:
            logger.info(f"Starting workflow execution: session={session_id}")

            # Get registry manager to fetch model profile
            registry = get_registry_manager()

            # Get orchestrator agent to find its model profile
            orchestrator_agent = registry.get_agent("orchestrator_agent")
            if not orchestrator_agent:
                raise ValueError("Orchestrator agent not found in registry")

            # Get model profile for LLM client
            model_profile = registry.get_model_profile(orchestrator_agent.model_profile_id)
            if not model_profile:
                raise ValueError(f"Model profile '{orchestrator_agent.model_profile_id}' not found in registry")

            # Create LLM client for orchestrator
            llm_client = create_llm_client(model_profile, session_id)
            logger.info(f"Created LLM client: provider={model_profile.provider}, model={model_profile.model_name}")

            # Create orchestrator runner with LLM client
            orchestrator = create_orchestrator_runner(
                session_id=session_id,
                workflow_id=workflow_id,
                llm_client=llm_client
            )

            # Execute workflow (this is synchronous, wrap in executor)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                orchestrator.execute,
                input_data
            )

            # Broadcast completion
            await self.broadcaster.broadcast_event(
                session_id=session_id,
                event_type="workflow_completed",
                event_data={
                    "status": result.status,
                    "completion_reason": result.completion_reason,
                    "agents_executed": result.agents_executed,
                    "total_iterations": result.total_iterations,
                    "total_agent_invocations": result.total_agent_invocations,
                    "completed_at": datetime.utcnow().isoformat() + "Z"
                }
            )

            # Save evidence map as artifact
            if result.evidence_map:
                artifact_id = f"{session_id}_evidence_map"
                self.artifact_store.save_artifact(
                    artifact_id=artifact_id,
                    data=result.evidence_map
                )

            # Update progress store status
            progress_store = get_progress_store()
            progress_store.update_status(session_id, "completed")

            # Complete session
            await self.broadcaster.complete_session(session_id)

            # Schedule cleanup after delay
            async def cleanup_after_delay():
                await asyncio.sleep(300)  # 5 minutes
                progress_store.cleanup_session(session_id)
                logger.info(f"Cleaned up progress store for session={session_id}")

            asyncio.create_task(cleanup_after_delay())

            logger.info(f"Workflow completed: session={session_id}, status={result.status}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Broadcast error
            await self.broadcaster.broadcast_event(
                session_id=session_id,
                event_type="workflow_error",
                event_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "failed_at": datetime.utcnow().isoformat() + "Z"
                }
            )

            # Update progress store status
            progress_store = get_progress_store()
            progress_store.update_status(session_id, "error")

            # Complete session even on error
            await self.broadcaster.complete_session(session_id)

            # Schedule cleanup after delay
            async def cleanup_after_delay():
                await asyncio.sleep(300)  # 5 minutes
                progress_store.cleanup_session(session_id)
                logger.info(f"Cleaned up progress store for session={session_id}")

            asyncio.create_task(cleanup_after_delay())

        finally:
            # Remove from running workflows
            if session_id in self._running_workflows:
                del self._running_workflows[session_id]

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"session_{timestamp}_{unique_id}"

    def get_running_sessions(self) -> list:
        """Get list of currently running session IDs."""
        return list(self._running_workflows.keys())

    def is_running(self, session_id: str) -> bool:
        """Check if session is currently running."""
        return session_id in self._running_workflows

    async def cancel_workflow(self, session_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            session_id: Session to cancel

        Returns:
            True if cancelled, False if not found

        Demonstrates: Graceful cancellation
        """
        if session_id not in self._running_workflows:
            return False

        task = self._running_workflows[session_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"Workflow cancelled: session={session_id}")

        # Broadcast cancellation
        await self.broadcaster.broadcast_event(
            session_id=session_id,
            event_type="workflow_cancelled",
            event_data={
                "cancelled_at": datetime.utcnow().isoformat() + "Z"
            }
        )

        await self.broadcaster.complete_session(session_id)

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get executor statistics for observability.

        Returns:
            Dict with current stats
        """
        return {
            "running_workflows": len(self._running_workflows),
            "running_session_ids": self.get_running_sessions()
        }


# Global executor instance
_executor: Optional[WorkflowExecutor] = None


def get_workflow_executor() -> WorkflowExecutor:
    """Get singleton workflow executor."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor()
    return _executor


def reset_workflow_executor() -> None:
    """Reset workflow executor (for testing)."""
    global _executor
    _executor = None
