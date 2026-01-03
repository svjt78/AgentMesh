"""
Artifact Resolver Processor (Phase 4 Implementation)

Resolves artifact handles to their content during context compilation.
Supports on-demand and preload modes for artifact access.
"""

import time
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.services.processors.base_processor import BaseProcessor, ProcessorResult
from app.config import get_config
from app.services.storage import write_event

logger = logging.getLogger(__name__)


class ArtifactResolverProcessor(BaseProcessor):
    """
    Resolves artifact handles to their content.

    - On-demand mode: Only resolves explicitly requested handles
    - Preload mode: Automatically discovers and resolves handles in context
    - Adds resolved artifacts to context for agent consumption
    - Enforces artifact access governance limits
    """

    # Regex pattern for artifact handles: artifact://{artifact_id}/v{version}
    ARTIFACT_HANDLE_PATTERN = re.compile(r'artifact://([a-zA-Z0-9_-]+)/v(\d+)')

    def process(
        self, context: Dict[str, Any], agent_id: str, session_id: str
    ) -> ProcessorResult:
        start_time = time.time()

        try:
            config = get_config()
            modifications = {}

            # Check if artifact versioning is enabled
            if not hasattr(config, 'artifacts') or not config.artifacts.versioning_enabled:
                execution_time_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    context=context,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    modifications_made={"status": "artifact_versioning_disabled"},
                )

            # Import ArtifactVersionStore
            from app.services.artifact_version_store import get_artifact_version_store

            artifact_store = get_artifact_version_store()

            artifacts_resolved = []

            # Get agent's artifact access mode from registry or config
            artifact_access_mode = self._get_artifact_access_mode(agent_id)

            if artifact_access_mode == "on_demand":
                # On-demand mode: Only resolve explicitly requested handles
                artifact_requests = context.get("artifact_requests", [])

                if artifact_requests:
                    logger.info(
                        f"On-demand artifact resolution triggered for agent={agent_id}, "
                        f"requests={len(artifact_requests)}"
                    )

                    for request in artifact_requests:
                        handle = request.get("handle")
                        if handle:
                            artifact = self._resolve_handle(artifact_store, handle)
                            if artifact:
                                artifacts_resolved.append({
                                    "artifact_id": artifact.artifact_id,
                                    "version": artifact.version,
                                    "handle": artifact.handle,
                                    "content": artifact.content,
                                    "metadata": artifact.metadata,
                                    "tags": artifact.tags,
                                })

                    # Add to context
                    if "artifacts" not in context:
                        context["artifacts"] = []
                    context["artifacts"].extend(artifacts_resolved)

                    modifications["access_mode"] = "on_demand"
                    modifications["artifacts_resolved"] = len(artifacts_resolved)
                    modifications["requested"] = len(artifact_requests)
                else:
                    modifications["access_mode"] = "on_demand"
                    modifications["artifacts_resolved"] = 0
                    modifications["reason"] = "no_requests_provided"

            elif artifact_access_mode == "preload":
                # Preload mode: Automatically discover and resolve handles
                logger.info(
                    f"Preload artifact resolution triggered for agent={agent_id}"
                )

                # Discover handles in context
                handles = self._discover_handles(context)

                logger.debug(f"Discovered {len(handles)} artifact handles in context")

                # Apply governance limit
                max_artifacts = self._get_max_artifacts_limit()
                if len(handles) > max_artifacts:
                    logger.warning(
                        f"Too many artifact handles discovered ({len(handles)}), "
                        f"limiting to {max_artifacts}"
                    )
                    handles = handles[:max_artifacts]

                # Resolve each handle
                for handle in handles:
                    artifact = self._resolve_handle(artifact_store, handle)
                    if artifact:
                        artifacts_resolved.append({
                            "artifact_id": artifact.artifact_id,
                            "version": artifact.version,
                            "handle": artifact.handle,
                            "content": artifact.content,
                            "metadata": artifact.metadata,
                            "tags": artifact.tags,
                        })

                # Add to context
                if "artifacts" not in context:
                    context["artifacts"] = []
                context["artifacts"].extend(artifacts_resolved)

                modifications["access_mode"] = "preload"
                modifications["artifacts_resolved"] = len(artifacts_resolved)
                modifications["discovered_handles"] = len(handles)

            # Write artifact resolved event if artifacts were loaded
            if artifacts_resolved:
                artifact_event = {
                    "event_type": "artifact_resolved",
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "access_mode": artifact_access_mode,
                    "artifacts_resolved": len(artifacts_resolved),
                    "artifact_handles": [a["handle"] for a in artifacts_resolved],
                }

                write_event(session_id, artifact_event)

                logger.info(
                    f"Artifact resolution completed for session={session_id}: "
                    f"{len(artifacts_resolved)} artifacts resolved"
                )

            execution_time_ms = (time.time() - start_time) * 1000

            return self._create_result(
                context=context,
                success=True,
                execution_time_ms=execution_time_ms,
                modifications_made=modifications,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"ArtifactResolver failed for session={session_id}: {e}",
                exc_info=True,
            )
            return self._create_result(
                context=context,
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )

    def _get_artifact_access_mode(self, agent_id: str) -> str:
        """
        Get artifact access mode for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Access mode ("on_demand" or "preload")
        """
        try:
            from app.services.registry_manager import get_registry_manager

            registry = get_registry_manager()
            agent = registry.get_agent(agent_id)

            if agent and "context_requirements" in agent:
                context_reqs = agent["context_requirements"]
                if "artifact_access_mode" in context_reqs:
                    return context_reqs["artifact_access_mode"]

        except Exception as e:
            logger.warning(f"Failed to get artifact access mode for {agent_id}: {e}")

        # Default to on_demand
        return "on_demand"

    def _get_max_artifacts_limit(self) -> int:
        """
        Get max artifacts per invocation from governance policies.

        Returns:
            Max artifacts limit (default: 5)
        """
        try:
            from app.services.registry_manager import get_registry_manager

            registry = get_registry_manager()
            policies = registry.get_governance_policies()

            if policies and "context_governance" in policies:
                context_gov = policies["context_governance"]
                if "max_artifact_loads_per_invocation" in context_gov:
                    return context_gov["max_artifact_loads_per_invocation"]

        except Exception as e:
            logger.warning(f"Failed to get max artifacts limit: {e}")

        # Default limit
        return 5

    def _discover_handles(self, context: Dict[str, Any]) -> List[str]:
        """
        Discover artifact handles in context.

        Searches for artifact:// handles in:
        - prior_outputs
        - observations
        - original_input

        Args:
            context: Context dictionary

        Returns:
            List of unique artifact handles
        """
        handles = set()

        # Search in context fields
        fields_to_search = ["prior_outputs", "observations", "original_input"]

        for field in fields_to_search:
            if field in context:
                handles.update(self._extract_handles_from_value(context[field]))

        return list(handles)

    def _extract_handles_from_value(self, value: Any) -> List[str]:
        """
        Recursively extract artifact handles from a value.

        Args:
            value: Value to search (string, dict, list, etc.)

        Returns:
            List of handles found
        """
        handles = []

        if isinstance(value, str):
            # Search for handles in string
            matches = self.ARTIFACT_HANDLE_PATTERN.findall(value)
            for artifact_id, version in matches:
                handle = f"artifact://{artifact_id}/v{version}"
                handles.append(handle)

        elif isinstance(value, dict):
            # Recursively search dict values
            for v in value.values():
                handles.extend(self._extract_handles_from_value(v))

        elif isinstance(value, list):
            # Recursively search list items
            for item in value:
                handles.extend(self._extract_handles_from_value(item))

        return handles

    def _resolve_handle(
        self, artifact_store, handle: str
    ) -> Optional[Any]:
        """
        Resolve an artifact handle to its content.

        Args:
            artifact_store: ArtifactVersionStore instance
            handle: Artifact handle (e.g., artifact://evidence_map/v3)

        Returns:
            Artifact object or None if not found
        """
        try:
            # Parse handle
            match = self.ARTIFACT_HANDLE_PATTERN.match(handle)
            if not match:
                logger.warning(f"Invalid artifact handle format: {handle}")
                return None

            artifact_id = match.group(1)
            version = int(match.group(2))

            # Retrieve artifact
            artifact = artifact_store.get_artifact_version(artifact_id, version)

            if artifact is None:
                logger.warning(f"Artifact not found: {handle}")
                return None

            return artifact

        except Exception as e:
            logger.error(f"Failed to resolve artifact handle {handle}: {e}")
            return None
