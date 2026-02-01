"""Unit tests for Anthropic LLM service.

Tests the LLMService class with mocked Anthropic SDK following TDD methodology.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic

from app.config import Settings
from app.exceptions import LLMAuthError, LLMConnectionError, LLMError, LLMRateLimitError
from app.services.llm_service import LLMService, get_llm_service


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.anthropic_api_key = MagicMock()
    settings.anthropic_api_key.get_secret_value.return_value = "test_api_key"
    settings.anthropic_model = "claude-sonnet-4-20250514"
    return settings


@pytest.fixture
def mock_settings_empty_key():
    """Create mock settings with empty API key."""
    settings = MagicMock(spec=Settings)
    settings.anthropic_api_key = MagicMock()
    settings.anthropic_api_key.get_secret_value.return_value = ""
    settings.anthropic_model = "claude-sonnet-4-20250514"
    return settings


@pytest.fixture
def llm_service(mock_settings):
    """Create an LLMService instance for testing."""
    with patch("app.services.llm_service.AsyncAnthropic"):
        return LLMService(settings=mock_settings)


class TestLLMServiceInit:
    """Tests for LLMService initialization."""

    def test_init_with_settings(self, mock_settings):
        """LLMService should initialize with Settings dependency."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            service = LLMService(settings=mock_settings)

            assert service.settings is mock_settings
            mock_client_class.assert_called_once_with(api_key="test_api_key")

    def test_init_extracts_api_key(self, mock_settings):
        """LLMService should extract API key from settings."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            LLMService(settings=mock_settings)

            mock_client_class.assert_called_once_with(api_key="test_api_key")

    def test_init_raises_value_error_for_empty_api_key(self, mock_settings_empty_key):
        """LLMService should raise ValueError if API key is empty."""
        with pytest.raises(ValueError) as exc_info:
            LLMService(settings=mock_settings_empty_key)

        assert "api key" in str(exc_info.value).lower()

    def test_init_raises_value_error_for_missing_api_key(self):
        """LLMService should raise ValueError if API key is missing."""
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = MagicMock()
        settings.anthropic_api_key.get_secret_value.return_value = None
        settings.anthropic_model = "claude-sonnet-4-20250514"

        with pytest.raises(ValueError) as exc_info:
            LLMService(settings=settings)

        assert "api key" in str(exc_info.value).lower()

    def test_init_sets_model_from_settings(self, mock_settings):
        """LLMService should use model from settings."""
        with patch("app.services.llm_service.AsyncAnthropic"):
            service = LLMService(settings=mock_settings)

            assert service.model == "claude-sonnet-4-20250514"

    def test_init_default_max_tokens(self, mock_settings):
        """LLMService should have default max_tokens of 4096."""
        with patch("app.services.llm_service.AsyncAnthropic"):
            service = LLMService(settings=mock_settings)

            assert service.max_tokens == 4096

    def test_init_default_temperature(self, mock_settings):
        """LLMService should have default temperature of 0.7."""
        with patch("app.services.llm_service.AsyncAnthropic"):
            service = LLMService(settings=mock_settings)

            assert service.temperature == 0.7

    def test_init_custom_max_tokens(self, mock_settings):
        """LLMService should accept custom max_tokens."""
        with patch("app.services.llm_service.AsyncAnthropic"):
            service = LLMService(settings=mock_settings, max_tokens=2048)

            assert service.max_tokens == 2048

    def test_init_custom_temperature(self, mock_settings):
        """LLMService should accept custom temperature."""
        with patch("app.services.llm_service.AsyncAnthropic"):
            service = LLMService(settings=mock_settings, temperature=0.5)

            assert service.temperature == 0.5


class TestGenerateResponse:
    """Tests for generate_response method."""

    @pytest.mark.asyncio
    async def test_generate_response_returns_string(self, mock_settings):
        """Should return response text as string."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Hello, how can I help you?")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            result = await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            )

            assert isinstance(result, str)
            assert result == "Hello, how can I help you?"

    @pytest.mark.asyncio
    async def test_generate_response_calls_api_correctly(self, mock_settings):
        """Should call Anthropic API with correct parameters."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            )

            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["system"] == "You are a helpful assistant."
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, mock_settings):
        """Should include conversation history in messages."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            history = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ]
            await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="New question",
                conversation_history=history,
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            expected_messages = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
                {"role": "user", "content": "New question"},
            ]
            assert call_kwargs["messages"] == expected_messages

    @pytest.mark.asyncio
    async def test_generate_response_without_conversation_history(self, mock_settings):
        """Should work without conversation history."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
                conversation_history=None,
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_generate_response_uses_custom_temperature(self, mock_settings):
        """Should use custom temperature when specified."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings, temperature=0.3)
            await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.3


class TestStreamResponse:
    """Tests for stream_response method."""

    @pytest.mark.asyncio
    async def test_stream_response_yields_strings(self, mock_settings):
        """Should yield response chunks as strings."""
        mock_text_delta1 = MagicMock()
        mock_text_delta1.type = "content_block_delta"
        mock_text_delta1.delta = MagicMock(text="Hello")

        mock_text_delta2 = MagicMock()
        mock_text_delta2.type = "content_block_delta"
        mock_text_delta2.delta = MagicMock(text=" World")

        # Create a proper async iterator for the stream
        class MockAsyncIterator:
            def __init__(self, items):
                self.items = iter(items)

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.items)
                except StopIteration:
                    raise StopAsyncIteration

        # Create async context manager mock
        class MockStreamContextManager:
            def __init__(self, mock_stream):
                self.mock_stream = mock_stream

            async def __aenter__(self):
                return self.mock_stream

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        mock_stream = MockAsyncIterator([mock_text_delta1, mock_text_delta2])
        mock_context_manager = MockStreamContextManager(mock_stream)

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.stream.return_value = mock_context_manager
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            chunks = []
            async for chunk in service.stream_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            ):
                chunks.append(chunk)

            assert all(isinstance(chunk, str) for chunk in chunks)
            assert "Hello" in chunks
            assert " World" in chunks

    @pytest.mark.asyncio
    async def test_stream_response_calls_api_correctly(self, mock_settings):
        """Should call Anthropic streaming API with correct parameters."""

        # Create a proper async iterator for the stream (empty)
        class MockAsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        class MockStreamContextManager:
            async def __aenter__(self):
                return MockAsyncIterator()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.stream.return_value = MockStreamContextManager()
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            async for _ in service.stream_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            ):
                pass

            mock_client.messages.stream.assert_called_once()
            call_kwargs = mock_client.messages.stream.call_args.kwargs
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["system"] == "You are a helpful assistant."
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_stream_response_with_conversation_history(self, mock_settings):
        """Should include conversation history in streaming request."""

        # Create a proper async iterator for the stream (empty)
        class MockAsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        class MockStreamContextManager:
            async def __aenter__(self):
                return MockAsyncIterator()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.stream.return_value = MockStreamContextManager()
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            history = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ]
            async for _ in service.stream_response(
                system_prompt="You are a helpful assistant.",
                user_message="New question",
                conversation_history=history,
            ):
                pass

            call_kwargs = mock_client.messages.stream.call_args.kwargs
            expected_messages = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
                {"role": "user", "content": "New question"},
            ]
            assert call_kwargs["messages"] == expected_messages


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_auth_error_on_invalid_api_key(self, mock_settings):
        """Should raise LLMAuthError on authentication failure."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            # Create a mock response for the exception
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.messages.create.side_effect = anthropic.AuthenticationError(
                message="Invalid API key",
                response=mock_response,
                body=None,
            )
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)

            with pytest.raises(LLMAuthError):
                await service.generate_response(
                    system_prompt="You are a helpful assistant.",
                    user_message="Hello",
                )

    @pytest.mark.asyncio
    async def test_rate_limit_error_on_429(self, mock_settings):
        """Should raise LLMRateLimitError on rate limit."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_client.messages.create.side_effect = anthropic.RateLimitError(
                message="Rate limit exceeded",
                response=mock_response,
                body=None,
            )
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)

            with pytest.raises(LLMRateLimitError):
                await service.generate_response(
                    system_prompt="You are a helpful assistant.",
                    user_message="Hello",
                )

    @pytest.mark.asyncio
    async def test_connection_error_on_network_failure(self, mock_settings):
        """Should raise LLMConnectionError on network failure."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_request = MagicMock()
            mock_client.messages.create.side_effect = anthropic.APIConnectionError(
                request=mock_request,
            )
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)

            with pytest.raises(LLMConnectionError):
                await service.generate_response(
                    system_prompt="You are a helpful assistant.",
                    user_message="Hello",
                )

    @pytest.mark.asyncio
    async def test_generic_llm_error_on_api_error(self, mock_settings):
        """Should raise LLMError on generic API errors."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_request = MagicMock()
            mock_client.messages.create.side_effect = anthropic.APIStatusError(
                message="Server error",
                response=mock_response,
                body=None,
            )
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)

            with pytest.raises(LLMError):
                await service.generate_response(
                    system_prompt="You are a helpful assistant.",
                    user_message="Hello",
                )

    @pytest.mark.asyncio
    async def test_stream_auth_error(self, mock_settings):
        """Should raise LLMAuthError on streaming auth failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        class MockStreamContextManager:
            async def __aenter__(self):
                raise anthropic.AuthenticationError(
                    message="Invalid API key",
                    response=mock_response,
                    body=None,
                )

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.stream.return_value = MockStreamContextManager()
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)

            with pytest.raises(LLMAuthError):
                async for _ in service.stream_response(
                    system_prompt="You are a helpful assistant.",
                    user_message="Hello",
                ):
                    pass


class TestGetLLMService:
    """Tests for the get_llm_service dependency function."""

    def test_get_llm_service_returns_llm_service(self):
        """get_llm_service should return an LLMService instance."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.anthropic_api_key = MagicMock()
        mock_settings.anthropic_api_key.get_secret_value.return_value = "test_key"
        mock_settings.anthropic_model = "claude-sonnet-4-20250514"

        with patch("app.services.llm_service.AsyncAnthropic"):
            service = get_llm_service(settings=mock_settings)

            assert isinstance(service, LLMService)

    def test_get_llm_service_passes_settings(self):
        """get_llm_service should pass settings to LLMService."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.anthropic_api_key = MagicMock()
        mock_settings.anthropic_api_key.get_secret_value.return_value = "test_key"
        mock_settings.anthropic_model = "claude-sonnet-4-20250514"

        with patch("app.services.llm_service.AsyncAnthropic"):
            service = get_llm_service(settings=mock_settings)

            assert service.settings is mock_settings


class TestAsyncAnthropicUsage:
    """Tests to verify AsyncAnthropic client is used correctly."""

    def test_uses_async_anthropic_client(self, mock_settings):
        """Should use anthropic.AsyncAnthropic for async operations."""
        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            LLMService(settings=mock_settings)

            mock_client_class.assert_called_once_with(api_key="test_api_key")

    @pytest.mark.asyncio
    async def test_client_is_reused_across_calls(self, mock_settings):
        """Should reuse the same client instance for multiple calls."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            await service.generate_response(
                system_prompt="Prompt 1",
                user_message="Message 1",
            )
            await service.generate_response(
                system_prompt="Prompt 2",
                user_message="Message 2",
            )

            # AsyncAnthropic should only be instantiated once
            assert mock_client_class.call_count == 1
            # But messages.create should be called twice
            assert mock_client.messages.create.call_count == 2


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_conversation_history(self, mock_settings):
        """Should handle empty conversation history list."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
                conversation_history=[],
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_multiple_content_blocks_in_response(self, mock_settings):
        """Should handle responses with multiple content blocks."""
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="First part"),
            MagicMock(text="Second part"),
        ]

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            result = await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            )

            # Should concatenate multiple text blocks
            assert "First part" in result
            assert "Second part" in result

    @pytest.mark.asyncio
    async def test_empty_response_content(self, mock_settings):
        """Should handle empty response content gracefully."""
        mock_message = MagicMock()
        mock_message.content = []

        with patch("app.services.llm_service.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client

            service = LLMService(settings=mock_settings)
            result = await service.generate_response(
                system_prompt="You are a helpful assistant.",
                user_message="Hello",
            )

            assert result == ""
