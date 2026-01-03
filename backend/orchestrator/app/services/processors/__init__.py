"""
Context Engineering Processors

This module contains the processor pipeline for context compilation.
Each processor is a discrete, testable unit that transforms context data.
"""

from .base_processor import BaseProcessor, ProcessorResult

__all__ = ["BaseProcessor", "ProcessorResult"]
