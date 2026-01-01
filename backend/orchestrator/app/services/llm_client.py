"""
LLM Client - Multi-provider LLM integration with OpenAI and Anthropic (Claude).

Demonstrates scalability patterns:
- Multi-provider support (OpenAI, Claude)
- Factory pattern for provider routing
- Retry with exponential backoff
- Timeout handling
- Cost tracking and token usage
- Unified interface across providers
"""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ..config import get_config
from .registry_manager import ModelProfile
from .storage import get_session_writer


class LLMResponse(BaseModel):
    """Unified LLM response format across providers."""
    content: str
    model: str
    provider: str
    tokens_used: Dict[str, int]  # {"prompt": X, "completion": Y, "total": Z}
    latency_ms: int
    finish_reason: str


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Demonstrates: Provider-agnostic interface pattern.
    """

    def __init__(
        self,
        model_profile: ModelProfile,
        session_id: Optional[str] = None
    ):
        self.model_profile = model_profile
        self.session_id = session_id
        self.config = get_config()
        self.storage = get_session_writer() if session_id else None

        # Metrics
        self.total_calls = 0
        self.total_tokens = 0
        self.failed_calls = 0

    @abstractmethod
    def call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        Call LLM with messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with standardized fields
        """
        pass

    def _log_llm_call(
        self,
        messages: List[Dict[str, str]],
        response: Optional[LLMResponse],
        error: Optional[str] = None,
        attempt: int = 1
    ) -> None:
        """Log LLM call for observability."""
        if not self.storage or not self.session_id:
            return

        event = {
            "event_type": "llm_call",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": self.model_profile.provider,
            "model": self.model_profile.model_name,
            "attempt": attempt,
            "message_count": len(messages),
            "success": response is not None,
            "error": error
        }

        if response:
            event.update({
                "tokens_used": response.tokens_used,
                "latency_ms": response.latency_ms,
                "finish_reason": response.finish_reason
            })

        self.storage.write_event(self.session_id, event)


class OpenAIClient(BaseLLMClient):
    """
    OpenAI provider client.

    Demonstrates: Provider-specific implementation with retry and timeout.
    """

    def __init__(
        self,
        model_profile: ModelProfile,
        session_id: Optional[str] = None
    ):
        super().__init__(model_profile, session_id)

        # Import OpenAI SDK
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.config.openai_api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        Call OpenAI API with retry logic.

        Demonstrates: Exponential backoff retry pattern.
        """
        retry_policy = self.model_profile.retry_policy
        max_retries = retry_policy.get("max_retries", 3)
        backoff_multiplier = retry_policy.get("backoff_multiplier", 2)
        initial_delay = retry_policy.get("initial_delay_ms", 1000) / 1000.0  # Convert to seconds

        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()

                # Build request parameters
                request_params = {
                    "model": self.model_profile.model_name,
                    "messages": messages,
                    "temperature": self.model_profile.parameters.get("temperature", 0.3),
                    "max_tokens": self.model_profile.parameters.get("max_tokens", 2000),
                    "top_p": self.model_profile.parameters.get("top_p", 1.0),
                    "frequency_penalty": self.model_profile.parameters.get("frequency_penalty", 0.0),
                    "presence_penalty": self.model_profile.parameters.get("presence_penalty", 0.0),
                    "timeout": self.model_profile.timeout_seconds
                }

                # Enable JSON mode if supported
                if self.model_profile.json_mode:
                    request_params["response_format"] = {"type": "json_object"}

                # Override with any kwargs
                request_params.update(kwargs)

                # Call OpenAI API
                response = self.client.chat.completions.create(**request_params)

                latency_ms = int((time.time() - start_time) * 1000)

                # Extract response
                llm_response = LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider="openai",
                    tokens_used={
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens
                    },
                    latency_ms=latency_ms,
                    finish_reason=response.choices[0].finish_reason
                )

                # Update metrics
                self.total_calls += 1
                self.total_tokens += llm_response.tokens_used["total"]

                # Log success
                self._log_llm_call(messages, llm_response, attempt=attempt)

                return llm_response

            except Exception as e:
                last_error = str(e)
                self.failed_calls += 1

                # Log failure
                self._log_llm_call(messages, None, error=last_error, attempt=attempt)

                if attempt < max_retries:
                    # Calculate delay with exponential backoff
                    delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    raise RuntimeError(
                        f"OpenAI API call failed after {max_retries} attempts. Last error: {last_error}"
                    )


class ClaudeClient(BaseLLMClient):
    """
    Anthropic (Claude) provider client.

    Demonstrates: Multi-provider support with different API patterns.
    """

    def __init__(
        self,
        model_profile: ModelProfile,
        session_id: Optional[str] = None
    ):
        super().__init__(model_profile, session_id)

        # Import Anthropic SDK
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.config.anthropic_api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        Call Anthropic API with retry logic.

        Note: Claude doesn't have native JSON mode, so we use prompt engineering.
        """
        retry_policy = self.model_profile.retry_policy
        max_retries = retry_policy.get("max_retries", 3)
        backoff_multiplier = retry_policy.get("backoff_multiplier", 2)
        initial_delay = retry_policy.get("initial_delay_ms", 1000) / 1000.0

        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()

                # Claude API expects system message separate from messages
                system_message = None
                chat_messages = []

                for msg in messages:
                    if msg["role"] == "system":
                        # Extract system message (Claude expects it separate)
                        system_message = msg["content"]
                    else:
                        chat_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })

                # Build request parameters
                request_params = {
                    "model": self.model_profile.model_name,
                    "messages": chat_messages,
                    "temperature": self.model_profile.parameters.get("temperature", 0.3),
                    "max_tokens": self.model_profile.parameters.get("max_tokens", 4000),
                    "top_p": self.model_profile.parameters.get("top_p", 1.0),
                    "timeout": self.model_profile.timeout_seconds
                }

                # Add system message if present
                if system_message:
                    request_params["system"] = system_message

                # Override with any kwargs
                request_params.update(kwargs)

                # Call Anthropic API
                response = self.client.messages.create(**request_params)

                latency_ms = int((time.time() - start_time) * 1000)

                # Extract response
                llm_response = LLMResponse(
                    content=response.content[0].text,
                    model=response.model,
                    provider="anthropic",
                    tokens_used={
                        "prompt": response.usage.input_tokens,
                        "completion": response.usage.output_tokens,
                        "total": response.usage.input_tokens + response.usage.output_tokens
                    },
                    latency_ms=latency_ms,
                    finish_reason=response.stop_reason
                )

                # Update metrics
                self.total_calls += 1
                self.total_tokens += llm_response.tokens_used["total"]

                # Log success
                self._log_llm_call(messages, llm_response, attempt=attempt)

                return llm_response

            except Exception as e:
                last_error = str(e)
                self.failed_calls += 1

                # Log failure
                self._log_llm_call(messages, None, error=last_error, attempt=attempt)

                if attempt < max_retries:
                    delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Anthropic API call failed after {max_retries} attempts. Last error: {last_error}"
                    )


def create_llm_client(
    model_profile: ModelProfile,
    session_id: Optional[str] = None
) -> BaseLLMClient:
    """
    Factory function to create appropriate LLM client based on provider.

    Demonstrates: Factory pattern for multi-provider routing.

    Args:
        model_profile: Model profile from registry
        session_id: Optional session ID for logging

    Returns:
        BaseLLMClient instance (OpenAIClient or ClaudeClient)

    Raises:
        ValueError: If provider is unknown
    """
    provider = model_profile.provider.lower()

    if provider == "openai":
        return OpenAIClient(model_profile, session_id)
    elif provider == "anthropic":
        return ClaudeClient(model_profile, session_id)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Supported providers: openai, anthropic"
        )
