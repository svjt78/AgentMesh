"""
Tools Gateway Client - HTTP client for invoking tools via Tools Gateway service.

Demonstrates scalability patterns:
- Service-to-service communication
- Retry logic with exponential backoff
- Timeout handling
- Error recovery
- Lineage tracking
"""

import httpx
import time
import logging
from typing import Dict, Any, Optional
from ..config import get_config

logger = logging.getLogger(__name__)


class ToolsGatewayError(Exception):
    """Exception raised for Tools Gateway errors."""
    pass


class ToolsGatewayClient:
    """
    HTTP client for invoking tools through Tools Gateway service.

    Demonstrates: Production-grade service client with retry and error handling.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        """
        Initialize Tools Gateway client.

        Args:
            base_url: Tools Gateway base URL (defaults to config)
            session_id: Session ID for lineage tracking
            agent_id: Agent ID invoking tools
        """
        config = get_config()

        self.base_url = base_url or "http://tools_gateway:8001"
        self.session_id = session_id
        self.agent_id = agent_id

        # Retry configuration from config
        self.max_retries = config.llm.max_retries  # Reuse LLM retry config
        self.timeout_seconds = 30

        # HTTP client with timeout
        self.client = httpx.Client(timeout=self.timeout_seconds)

        logger.info(
            f"ToolsGatewayClient initialized: base_url={self.base_url}, "
            f"session_id={session_id}, agent_id={agent_id}"
        )

    def invoke_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a tool by ID.

        Demonstrates: Retry logic with exponential backoff and timeout handling.

        Args:
            tool_id: Tool identifier
            parameters: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolsGatewayError: If tool invocation fails after retries
        """
        url = f"{self.base_url}/invoke/{tool_id}"

        # Build request payload
        payload = {
            "parameters": parameters
        }

        if self.session_id:
            payload["session_id"] = self.session_id

        if self.agent_id:
            payload["agent_id"] = self.agent_id

        logger.info(
            f"Invoking tool: tool_id={tool_id}, "
            f"session_id={self.session_id}, "
            f"agent_id={self.agent_id}"
        )

        # Retry loop with exponential backoff
        last_error = None
        initial_delay = 1.0  # 1 second
        backoff_multiplier = 2.0

        for attempt in range(1, self.max_retries + 1):
            try:
                # Make HTTP POST request
                response = self.client.post(url, json=payload)

                # Check for HTTP errors
                if response.status_code == 200:
                    result = response.json()

                    logger.info(
                        f"Tool invocation successful: tool_id={tool_id}, "
                        f"execution_time_ms={result.get('execution_time_ms', 0):.2f}"
                    )

                    return result

                elif response.status_code == 404:
                    # Tool not found - don't retry
                    error_detail = response.json().get("detail", "Tool not found")
                    logger.error(f"Tool not found: tool_id={tool_id}")
                    raise ToolsGatewayError(f"Tool '{tool_id}' not found: {error_detail}")

                elif response.status_code == 400:
                    # Validation error - don't retry
                    error_detail = response.json().get("detail", "Validation error")
                    logger.error(f"Tool validation error: tool_id={tool_id}, error={error_detail}")
                    raise ToolsGatewayError(f"Tool validation error: {error_detail}")

                else:
                    # Server error - retry
                    error_detail = response.json().get("detail", f"HTTP {response.status_code}")
                    last_error = ToolsGatewayError(f"Tool gateway error: {error_detail}")

                    logger.warning(
                        f"Tool invocation failed (attempt {attempt}/{self.max_retries}): "
                        f"tool_id={tool_id}, status={response.status_code}, error={error_detail}"
                    )

            except httpx.TimeoutException as e:
                last_error = ToolsGatewayError(f"Tool invocation timeout after {self.timeout_seconds}s: {str(e)}")

                logger.warning(
                    f"Tool invocation timeout (attempt {attempt}/{self.max_retries}): "
                    f"tool_id={tool_id}, timeout={self.timeout_seconds}s"
                )

            except httpx.RequestError as e:
                last_error = ToolsGatewayError(f"Tool gateway connection error: {str(e)}")

                logger.warning(
                    f"Tool gateway connection error (attempt {attempt}/{self.max_retries}): "
                    f"tool_id={tool_id}, error={str(e)}"
                )

            except Exception as e:
                last_error = ToolsGatewayError(f"Unexpected error invoking tool: {str(e)}")

                logger.error(
                    f"Unexpected error invoking tool (attempt {attempt}/{self.max_retries}): "
                    f"tool_id={tool_id}, error={str(e)}",
                    exc_info=True
                )

            # Retry logic: exponential backoff
            if attempt < self.max_retries:
                delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

        # All retries exhausted
        logger.error(
            f"Tool invocation failed after {self.max_retries} attempts: "
            f"tool_id={tool_id}"
        )

        raise last_error if last_error else ToolsGatewayError("Tool invocation failed")

    def invoke_tools_batch(
        self,
        tool_requests: list
    ) -> list:
        """
        Invoke multiple tools sequentially.

        Note: Tools are invoked sequentially, not in parallel.
        For parallel invocation, use async client or threading.

        Args:
            tool_requests: List of dicts with 'tool_id' and 'parameters'

        Returns:
            List of tool results (same order as requests)
        """
        results = []

        for i, tool_req in enumerate(tool_requests):
            tool_id = tool_req.get("tool_id")
            parameters = tool_req.get("parameters", {})

            logger.info(
                f"Invoking tool {i+1}/{len(tool_requests)}: tool_id={tool_id}"
            )

            try:
                result = self.invoke_tool(tool_id, parameters)
                results.append({
                    "status": "success",
                    "tool_id": tool_id,
                    "result": result
                })

            except ToolsGatewayError as e:
                logger.error(
                    f"Tool invocation failed: tool_id={tool_id}, error={str(e)}"
                )

                results.append({
                    "status": "error",
                    "tool_id": tool_id,
                    "error": str(e)
                })

        return results

    def health_check(self) -> bool:
        """
        Check if Tools Gateway is healthy.

        Returns:
            True if gateway is healthy, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/", timeout=5.0)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"Tools Gateway health check failed: {str(e)}")
            return False

    def list_available_tools(self) -> list:
        """
        List all available tools from Tools Gateway.

        Returns:
            List of available tool IDs
        """
        try:
            response = self.client.get(f"{self.base_url}/tools", timeout=5.0)

            if response.status_code == 200:
                data = response.json()
                return data.get("tools", [])

            logger.warning(f"Failed to list tools: HTTP {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_tools_gateway_client(
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None
) -> ToolsGatewayClient:
    """
    Factory function to create ToolsGatewayClient.

    Args:
        session_id: Session ID for lineage tracking
        agent_id: Agent ID invoking tools

    Returns:
        ToolsGatewayClient instance
    """
    return ToolsGatewayClient(
        session_id=session_id,
        agent_id=agent_id
    )
