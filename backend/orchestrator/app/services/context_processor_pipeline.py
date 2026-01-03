"""
Context Processor Pipeline

Orchestrates the execution of ordered context processors for compilation.
Provides transparent, inspectable, and governable context assembly.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.services.registry_manager import RegistryManager
from app.services.processors.base_processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Configuration for a single processor"""

    processor_id: str
    name: str
    enabled: bool
    order: int
    config: Dict[str, Any]


class ContextProcessorPipeline:
    """
    Executes context compilation through an ordered pipeline of processors.

    Each processor transforms the context in a specific way (filtering,
    enrichment, transformation, truncation, etc.). The pipeline provides
    full visibility into what happens during context compilation.
    """

    def __init__(self, session_id: str, registry_manager: RegistryManager):
        """
        Initialize the processor pipeline.

        Args:
            session_id: Current session ID for logging
            registry_manager: Registry manager for loading processor configs
        """
        self.session_id = session_id
        self.registry = registry_manager
        self.processors: List[BaseProcessor] = []
        self._load_processors()

    def _load_processors(self) -> None:
        """Load and instantiate processors from registry"""
        try:
            # Load processor pipeline configuration
            import os
            registry_path = os.environ.get("REGISTRY_PATH", "/registries")
            pipeline_config_path = os.path.join(registry_path, "context_processor_pipeline.json")
            with open(pipeline_config_path, "r") as f:
                pipeline_config = json.load(f)

            processor_configs = pipeline_config.get("processors", [])

            # Sort by order
            processor_configs.sort(key=lambda p: p.get("order", 999))

            # Instantiate enabled processors
            for proc_config in processor_configs:
                if not proc_config.get("enabled", True):
                    logger.info(
                        f"Processor {proc_config['processor_id']} is disabled, skipping"
                    )
                    continue

                processor = self._instantiate_processor(proc_config)
                if processor:
                    self.processors.append(processor)
                    logger.debug(
                        f"Loaded processor: {proc_config['processor_id']} "
                        f"(order: {proc_config.get('order')})"
                    )

            logger.info(f"Loaded {len(self.processors)} processors for pipeline")

        except Exception as e:
            logger.error(f"Failed to load processor pipeline: {e}")
            # Pipeline can operate with no processors (passthrough mode)
            self.processors = []

    def _instantiate_processor(
        self, proc_config: Dict[str, Any]
    ) -> Optional[BaseProcessor]:
        """
        Instantiate a processor from configuration.

        Args:
            proc_config: Processor configuration dict

        Returns:
            Instantiated processor or None if not found
        """
        processor_id = proc_config["processor_id"]
        config = proc_config.get("config", {})

        # Import processors dynamically
        try:
            if processor_id == "content_selector":
                from app.services.processors.content_selector import (
                    ContentSelectorProcessor,
                )

                return ContentSelectorProcessor(processor_id, config)

            elif processor_id == "compaction_checker":
                from app.services.processors.compaction_checker import (
                    CompactionCheckerProcessor,
                )

                return CompactionCheckerProcessor(processor_id, config)

            elif processor_id == "memory_retriever":
                from app.services.processors.memory_retriever import (
                    MemoryRetrieverProcessor,
                )

                return MemoryRetrieverProcessor(processor_id, config)

            elif processor_id == "artifact_resolver":
                from app.services.processors.artifact_resolver import (
                    ArtifactResolverProcessor,
                )

                return ArtifactResolverProcessor(processor_id, config)

            elif processor_id == "transformer":
                from app.services.processors.transformer import TransformerProcessor

                return TransformerProcessor(processor_id, config)

            elif processor_id == "token_budget_enforcer":
                from app.services.processors.token_budget_enforcer import (
                    TokenBudgetEnforcerProcessor,
                )

                return TokenBudgetEnforcerProcessor(processor_id, config)

            elif processor_id == "injector":
                from app.services.processors.injector import InjectorProcessor

                return InjectorProcessor(processor_id, config)

            else:
                logger.warning(f"Unknown processor: {processor_id}")
                return None

        except ImportError as e:
            logger.warning(
                f"Processor {processor_id} not yet implemented, skipping: {e}"
            )
            return None

    def execute(
        self, raw_context: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Execute the context compilation pipeline.

        Args:
            raw_context: Raw context data to process
            agent_id: ID of the agent this context is for

        Returns:
            Compiled context after all processors have run
        """
        context = raw_context.copy()
        execution_log = []

        logger.info(
            f"Starting context compilation pipeline for agent={agent_id}, "
            f"session={self.session_id}, processors={len(self.processors)}"
        )

        for processor in self.processors:
            start_time = time.time()

            try:
                result = processor.process(context, agent_id, self.session_id)
                execution_time_ms = (time.time() - start_time) * 1000

                if not result.success:
                    logger.error(
                        f"Processor {processor.processor_id} failed: {result.error}"
                    )
                    # Continue with original context on failure
                    execution_log.append(
                        {
                            "processor_id": processor.processor_id,
                            "success": False,
                            "error": result.error,
                            "execution_time_ms": execution_time_ms,
                        }
                    )
                    continue

                # Update context with processor result
                context = result.context

                # Log execution
                log_entry = {
                    "processor_id": processor.processor_id,
                    "success": True,
                    "execution_time_ms": result.execution_time_ms,
                }

                if result.modifications_made:
                    log_entry["modifications_made"] = result.modifications_made

                execution_log.append(log_entry)

                logger.debug(
                    f"Processor {processor.processor_id} completed in "
                    f"{result.execution_time_ms:.2f}ms"
                )

            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Processor {processor.processor_id} raised exception: {e}",
                    exc_info=True,
                )
                execution_log.append(
                    {
                        "processor_id": processor.processor_id,
                        "success": False,
                        "error": str(e),
                        "execution_time_ms": execution_time_ms,
                    }
                )
                # Continue with previous context on exception

        # Attach execution log to context metadata
        if "metadata" not in context:
            context["metadata"] = {}

        context["metadata"]["processor_execution_log"] = execution_log
        context["metadata"]["total_processors"] = len(self.processors)
        context["metadata"]["successful_processors"] = sum(
            1 for log in execution_log if log.get("success", False)
        )

        logger.info(
            f"Context compilation pipeline completed: "
            f"{context['metadata']['successful_processors']}/{len(self.processors)} "
            f"processors succeeded"
        )

        return context

    def get_processor_count(self) -> int:
        """Get the number of processors in the pipeline"""
        return len(self.processors)

    def get_processor_ids(self) -> List[str]:
        """Get list of processor IDs in execution order"""
        return [p.processor_id for p in self.processors]
