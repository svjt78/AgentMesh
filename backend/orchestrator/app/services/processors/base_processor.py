"""
Base Processor Abstract Class

All context processors must inherit from BaseProcessor and implement the process() method.
Processors are stateless and side-effect-free (except for logging).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessorResult:
    """Result from a processor execution"""

    context: Dict[str, Any]
    """The transformed context"""

    success: bool
    """Whether the processor executed successfully"""

    processor_id: str
    """ID of the processor that generated this result"""

    execution_time_ms: float
    """Time taken to execute the processor"""

    modifications_made: Optional[Dict[str, Any]] = None
    """Optional metadata about what modifications were made"""

    error: Optional[str] = None
    """Error message if success=False"""


class BaseProcessor(ABC):
    """
    Abstract base class for all context processors.

    Processors are executed in order by the ContextProcessorPipeline.
    Each processor receives context from the previous processor and
    returns transformed context for the next processor.
    """

    def __init__(self, processor_id: str, config: Dict[str, Any]):
        """
        Initialize the processor.

        Args:
            processor_id: Unique identifier for this processor
            config: Configuration dict from context_processor_pipeline.json
        """
        self.processor_id = processor_id
        self.config = config

    @abstractmethod
    def process(
        self,
        context: Dict[str, Any],
        agent_id: str,
        session_id: str
    ) -> ProcessorResult:
        """
        Process the context.

        Args:
            context: The context dict to process
            agent_id: ID of the agent this context is being compiled for
            session_id: Current session ID

        Returns:
            ProcessorResult with transformed context and execution metadata
        """
        pass

    def _create_result(
        self,
        context: Dict[str, Any],
        success: bool,
        execution_time_ms: float,
        modifications_made: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> ProcessorResult:
        """Helper to create a ProcessorResult"""
        return ProcessorResult(
            context=context,
            success=success,
            processor_id=self.processor_id,
            execution_time_ms=execution_time_ms,
            modifications_made=modifications_made,
            error=error
        )
