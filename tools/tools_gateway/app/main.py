"""
Tools Gateway - FastAPI service providing mock tools for agent execution.

Demonstrates scalability patterns:
- RESTful tool invocation
- Standardized request/response format
- Tool registry integration
- Lineage tracking
- Error handling and validation
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Import tool implementations
from .tools.policy_snapshot import execute_policy_snapshot
from .tools.fraud_rules import execute_fraud_rules
from .tools.similarity import execute_similarity
from .tools.schema_validator import execute_schema_validator
from .tools.coverage_rules import execute_coverage_rules
from .tools.decision_rules import execute_decision_rules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Tools Gateway",
    description="Mock tools service for multi-agent insurance processing",
    version="1.0.0"
)


class ToolInvocationRequest(BaseModel):
    """Request model for tool invocation."""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    session_id: Optional[str] = Field(None, description="Session ID for lineage tracking")
    agent_id: Optional[str] = Field(None, description="Agent ID invoking the tool")


class ToolInvocationResponse(BaseModel):
    """Response model for tool invocation."""
    tool_id: str = Field(..., description="Tool identifier")
    result: Dict[str, Any] = Field(..., description="Tool execution result")
    lineage_tags: Dict[str, str] = Field(default_factory=dict, description="Execution lineage metadata")
    timestamp: str = Field(..., description="Execution timestamp")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


# Tool registry - maps tool_id to execution function
TOOL_REGISTRY = {
    "policy_snapshot": execute_policy_snapshot,
    "fraud_rules": execute_fraud_rules,
    "similarity": execute_similarity,
    "schema_validator": execute_schema_validator,
    "coverage_rules": execute_coverage_rules,
    "decision_rules": execute_decision_rules,
}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Tools Gateway",
        "status": "healthy",
        "available_tools": list(TOOL_REGISTRY.keys())
    }


@app.get("/tools")
async def list_tools():
    """List all available tools."""
    return {
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY)
    }


@app.post("/invoke/{tool_id}", response_model=ToolInvocationResponse)
async def invoke_tool(
    tool_id: str,
    request: ToolInvocationRequest
):
    """
    Invoke a tool by ID.

    Demonstrates: Standardized tool invocation pattern with validation and lineage.

    Args:
        tool_id: Tool identifier
        request: Tool invocation request with parameters

    Returns:
        ToolInvocationResponse with result and metadata
    """
    start_time = datetime.now()

    logger.info(
        f"Tool invocation: tool_id={tool_id}, "
        f"session_id={request.session_id}, "
        f"agent_id={request.agent_id}"
    )

    # Validate tool exists
    if tool_id not in TOOL_REGISTRY:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_id}' not found. Available tools: {list(TOOL_REGISTRY.keys())}"
        )

    try:
        # Get tool execution function
        tool_function = TOOL_REGISTRY[tool_id]

        # Execute tool
        result = tool_function(request.parameters)

        # Calculate execution time
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Build lineage tags
        lineage_tags = {
            "tool_id": tool_id,
            "timestamp": end_time.isoformat()
        }

        if request.session_id:
            lineage_tags["session_id"] = request.session_id

        if request.agent_id:
            lineage_tags["agent_id"] = request.agent_id

        logger.info(
            f"Tool execution successful: tool_id={tool_id}, "
            f"execution_time_ms={execution_time_ms:.2f}"
        )

        return ToolInvocationResponse(
            tool_id=tool_id,
            result=result,
            lineage_tags=lineage_tags,
            timestamp=end_time.isoformat(),
            execution_time_ms=execution_time_ms
        )

    except ValueError as e:
        # Tool-specific validation errors
        logger.error(f"Tool validation error: tool_id={tool_id}, error={str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Tool validation error: {str(e)}"
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Tool execution error: tool_id={tool_id}, error={str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
