"""Anthropic LLM service for chat and orchestration.

This module provides an async client for interacting with Anthropic's Claude API
to generate responses for the Discovery chat/orchestrator.

Uses the Anthropic Python SDK with AsyncAnthropic for async operations.
"""

import logging
from collections.abc import AsyncIterator

import anthropic
from anthropic import AsyncAnthropic

from app.config import Settings
from app.exceptions import LLMAuthError, LLMConnectionError, LLMError, LLMRateLimitError

logger = logging.getLogger(__name__)


class LLMService:
    """Async service for Anthropic Claude API interactions.

    Provides methods to generate responses (both single-shot and streaming)
    using Claude models configured via application settings.

    Attributes:
        settings: Application settings containing API configuration.
        model: The Claude model to use for completions.
        max_tokens: Maximum tokens in generated responses.
        temperature: Temperature for response generation (0-1).
    """

    def __init__(
        self,
        settings: Settings,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the LLM service.

        Args:
            settings: Application settings with anthropic_api_key and anthropic_model.
            max_tokens: Maximum tokens for generated responses. Defaults to 4096.
            temperature: Temperature for generation (0-1). Defaults to 0.7.

        Raises:
            ValueError: If the API key is empty or missing.
        """
        self.settings = settings
        api_key = settings.anthropic_api_key.get_secret_value()

        if not api_key:
            raise ValueError("Anthropic API key is required but not configured")

        self.model = settings.anthropic_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: The system prompt to set context for the assistant.
            user_message: The user's message to respond to.
            conversation_history: Optional list of previous messages in the format
                [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            The generated response text.

        Raises:
            LLMAuthError: If authentication fails (invalid API key).
            LLMRateLimitError: If rate limit is exceeded.
            LLMConnectionError: If connection to the API fails.
            LLMError: For other API errors.
        """
        messages = self._build_messages(user_message, conversation_history)

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            )
            return self._extract_text_content(response)
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise LLMAuthError("LLM API authentication failed") from e
        except anthropic.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise LLMRateLimitError("LLM API rate limit exceeded") from e
        except anthropic.APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise LLMConnectionError("Failed to connect to LLM API") from e
        except anthropic.APIError as e:
            logger.error(f"API error: {e}")
            raise LLMError(f"LLM API error: {e}") from e

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM.

        Args:
            system_prompt: The system prompt to set context for the assistant.
            user_message: The user's message to respond to.
            conversation_history: Optional list of previous messages in the format
                [{"role": "user"|"assistant", "content": "..."}].

        Yields:
            String chunks of the generated response.

        Raises:
            LLMAuthError: If authentication fails (invalid API key).
            LLMRateLimitError: If rate limit is exceeded.
            LLMConnectionError: If connection to the API fails.
            LLMError: For other API errors.
        """
        messages = self._build_messages(user_message, conversation_history)

        try:
            async with self._client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield event.delta.text
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise LLMAuthError("LLM API authentication failed") from e
        except anthropic.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise LLMRateLimitError("LLM API rate limit exceeded") from e
        except anthropic.APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise LLMConnectionError("Failed to connect to LLM API") from e
        except anthropic.APIError as e:
            logger.error(f"API error: {e}")
            raise LLMError(f"LLM API error: {e}") from e

    def _build_messages(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None,
    ) -> list[dict[str, str]]:
        """Build the messages list for the API request.

        Args:
            user_message: The current user message.
            conversation_history: Optional previous messages.

        Returns:
            List of message dictionaries for the API.
        """
        messages: list[dict[str, str]] = []

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})
        return messages

    def _extract_text_content(self, response) -> str:
        """Extract text content from the API response.

        Args:
            response: The Anthropic API response object.

        Returns:
            Concatenated text from all content blocks.
        """
        if not response.content:
            return ""

        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "".join(text_parts)


def get_llm_service(settings: Settings) -> LLMService:
    """FastAPI dependency for getting an LLMService instance.

    Args:
        settings: Application settings (injected by FastAPI).

    Returns:
        An LLMService instance configured with the provided settings.
    """
    return LLMService(settings=settings)
