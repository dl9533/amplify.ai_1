"""Unit tests for ChatService with LLM integration.

Tests the ChatService class with mocked LLMService and ContextService
following TDD methodology.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.exceptions import LLMAuthError, LLMConnectionError, LLMError, LLMRateLimitError
from app.services.chat_service import ChatService, get_chat_service
from app.services.context_service import ContextService
from app.services.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service for testing."""
    service = MagicMock(spec=LLMService)
    service.generate_response = AsyncMock(return_value="This is a helpful response.")
    return service


@pytest.fixture
def mock_context_service():
    """Create mock context service for testing."""
    service = MagicMock(spec=ContextService)
    service.build_context = MagicMock(return_value={
        "current_step": 1,
        "step_name": "Upload",
        "session_id": str(uuid4()),
        "suggested_actions": [],
    })
    return service


@pytest.fixture
def chat_service(mock_llm_service, mock_context_service):
    """Create a ChatService instance with mocked dependencies."""
    return ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )


class TestChatServiceInit:
    """Tests for ChatService initialization."""

    def test_init_accepts_llm_service(self, mock_llm_service, mock_context_service):
        """ChatService should accept LLMService as dependency."""
        service = ChatService(
            llm_service=mock_llm_service,
            context_service=mock_context_service,
        )
        assert service.llm_service is mock_llm_service

    def test_init_accepts_context_service(self, mock_llm_service, mock_context_service):
        """ChatService should accept ContextService as dependency."""
        service = ChatService(
            llm_service=mock_llm_service,
            context_service=mock_context_service,
        )
        assert service.context_service is mock_context_service

    def test_init_stores_dependencies(self, mock_llm_service, mock_context_service):
        """ChatService should store both dependencies."""
        service = ChatService(
            llm_service=mock_llm_service,
            context_service=mock_context_service,
        )
        assert hasattr(service, "llm_service")
        assert hasattr(service, "context_service")


class TestSendMessage:
    """Tests for send_message method."""

    @pytest.mark.asyncio
    async def test_send_message_returns_dict(self, chat_service):
        """send_message should return a dictionary."""
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello, how do I upload a file?",
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_send_message_includes_response(self, chat_service):
        """send_message result should include response key."""
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        assert "response" in result
        assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_send_message_includes_quick_actions(self, chat_service):
        """send_message result should include quick_actions key."""
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        assert "quick_actions" in result
        assert isinstance(result["quick_actions"], list)

    @pytest.mark.asyncio
    async def test_send_message_gets_context(
        self, chat_service, mock_context_service
    ):
        """send_message should get session context from ContextService."""
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=2,
        )
        mock_context_service.build_context.assert_called_once()
        call_kwargs = mock_context_service.build_context.call_args.kwargs
        assert call_kwargs["session_id"] == session_id
        assert call_kwargs["current_step"] == 2
        assert call_kwargs["user_message"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_message_calls_llm(
        self, chat_service, mock_llm_service
    ):
        """send_message should call LLMService.generate_response."""
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        mock_llm_service.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_passes_system_prompt_to_llm(
        self, chat_service, mock_llm_service, mock_context_service
    ):
        """send_message should pass system prompt to LLM."""
        mock_context_service.build_context.return_value = {
            "current_step": 2,
            "step_name": "Map Roles",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=2,
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        assert "system_prompt" in call_kwargs
        assert "Map Roles" in call_kwargs["system_prompt"]

    @pytest.mark.asyncio
    async def test_send_message_passes_user_message_to_llm(
        self, chat_service, mock_llm_service
    ):
        """send_message should pass user message to LLM."""
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="What should I do next?",
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        assert call_kwargs["user_message"] == "What should I do next?"

    @pytest.mark.asyncio
    async def test_send_message_returns_llm_response(
        self, chat_service, mock_llm_service
    ):
        """send_message should return the LLM response."""
        mock_llm_service.generate_response.return_value = "I can help you with that!"
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        assert result["response"] == "I can help you with that!"


class TestSystemPrompt:
    """Tests for system prompt generation."""

    @pytest.mark.asyncio
    async def test_system_prompt_includes_step_name(
        self, chat_service, mock_llm_service, mock_context_service
    ):
        """System prompt should include the current step name."""
        mock_context_service.build_context.return_value = {
            "current_step": 3,
            "step_name": "Select Activities",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=3,
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        assert "Select Activities" in call_kwargs["system_prompt"]

    @pytest.mark.asyncio
    async def test_system_prompt_includes_session_data(
        self, chat_service, mock_llm_service, mock_context_service
    ):
        """System prompt should include session data when available."""
        mock_context_service.build_context.return_value = {
            "current_step": 3,
            "step_name": "Select Activities",
            "session_id": str(uuid4()),
            "suggested_actions": [],
            "activities": {"total_activities": 35},
            "selection_count": 10,
        }
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=3,
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        # Session data should be included in the system prompt
        assert "session_data" in call_kwargs["system_prompt"].lower() or \
               "35" in call_kwargs["system_prompt"] or \
               "activities" in call_kwargs["system_prompt"].lower()

    @pytest.mark.asyncio
    async def test_system_prompt_mentions_discovery_assistant(
        self, chat_service, mock_llm_service
    ):
        """System prompt should identify as a Discovery assistant."""
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        assert "discovery" in call_kwargs["system_prompt"].lower()


class TestQuickActionsByStep:
    """Tests for quick action generation based on step."""

    @pytest.mark.asyncio
    async def test_upload_step_quick_actions(
        self, chat_service, mock_context_service
    ):
        """Upload step should have relevant quick actions."""
        mock_context_service.build_context.return_value = {
            "current_step": 1,
            "step_name": "Upload",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=1,
        )
        action_labels = [a["label"] for a in result["quick_actions"]]
        assert any("upload" in label.lower() for label in action_labels)

    @pytest.mark.asyncio
    async def test_map_roles_step_quick_actions(
        self, chat_service, mock_context_service
    ):
        """Map Roles step should have relevant quick actions."""
        mock_context_service.build_context.return_value = {
            "current_step": 2,
            "step_name": "Map Roles",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=2,
        )
        action_labels = [a["label"].lower() for a in result["quick_actions"]]
        # Should have mapping-related actions
        assert any("mapping" in label or "onet" in label or "confirm" in label
                   for label in action_labels)

    @pytest.mark.asyncio
    async def test_activities_step_quick_actions(
        self, chat_service, mock_context_service
    ):
        """Select Activities step should have relevant quick actions."""
        mock_context_service.build_context.return_value = {
            "current_step": 3,
            "step_name": "Select Activities",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=3,
        )
        action_labels = [a["label"].lower() for a in result["quick_actions"]]
        # Should have selection-related actions
        assert any("select" in label or "clear" in label or "exposure" in label
                   for label in action_labels)

    @pytest.mark.asyncio
    async def test_analysis_step_quick_actions(
        self, chat_service, mock_context_service
    ):
        """Analysis step should have relevant quick actions."""
        mock_context_service.build_context.return_value = {
            "current_step": 4,
            "step_name": "Analysis",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=4,
        )
        action_labels = [a["label"].lower() for a in result["quick_actions"]]
        # Should have analysis-related actions
        assert any("view" in label or "role" in label or "department" in label
                   for label in action_labels)

    @pytest.mark.asyncio
    async def test_roadmap_step_quick_actions(
        self, chat_service, mock_context_service
    ):
        """Roadmap step should have relevant quick actions."""
        mock_context_service.build_context.return_value = {
            "current_step": 5,
            "step_name": "Roadmap",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=5,
        )
        action_labels = [a["label"].lower() for a in result["quick_actions"]]
        # Should have roadmap-related actions
        assert any("now" in label or "export" in label or "roadmap" in label
                   for label in action_labels)

    @pytest.mark.asyncio
    async def test_quick_actions_have_required_fields(
        self, chat_service, mock_context_service
    ):
        """Quick actions should have label and action fields."""
        mock_context_service.build_context.return_value = {
            "current_step": 1,
            "step_name": "Upload",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=1,
        )
        for action in result["quick_actions"]:
            assert "label" in action
            assert "action" in action


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_llm_auth_error_gracefully(
        self, chat_service, mock_llm_service
    ):
        """Should handle LLMAuthError gracefully."""
        mock_llm_service.generate_response.side_effect = LLMAuthError("Auth failed")
        session_id = uuid4()

        with pytest.raises(LLMAuthError):
            await chat_service.send_message(
                session_id=session_id,
                message="Hello",
            )

    @pytest.mark.asyncio
    async def test_handles_llm_rate_limit_error_gracefully(
        self, chat_service, mock_llm_service
    ):
        """Should handle LLMRateLimitError gracefully."""
        mock_llm_service.generate_response.side_effect = LLMRateLimitError("Rate limited")
        session_id = uuid4()

        with pytest.raises(LLMRateLimitError):
            await chat_service.send_message(
                session_id=session_id,
                message="Hello",
            )

    @pytest.mark.asyncio
    async def test_handles_llm_connection_error_gracefully(
        self, chat_service, mock_llm_service
    ):
        """Should handle LLMConnectionError gracefully."""
        mock_llm_service.generate_response.side_effect = LLMConnectionError("Connection failed")
        session_id = uuid4()

        with pytest.raises(LLMConnectionError):
            await chat_service.send_message(
                session_id=session_id,
                message="Hello",
            )

    @pytest.mark.asyncio
    async def test_handles_generic_llm_error_gracefully(
        self, chat_service, mock_llm_service
    ):
        """Should handle generic LLMError gracefully."""
        mock_llm_service.generate_response.side_effect = LLMError("Generic error")
        session_id = uuid4()

        with pytest.raises(LLMError):
            await chat_service.send_message(
                session_id=session_id,
                message="Hello",
            )

    @pytest.mark.asyncio
    async def test_handles_context_service_value_error(
        self, chat_service, mock_context_service
    ):
        """Should propagate ValueError from ContextService."""
        mock_context_service.build_context.side_effect = ValueError("Invalid step")
        session_id = uuid4()

        with pytest.raises(ValueError):
            await chat_service.send_message(
                session_id=session_id,
                message="Hello",
                current_step=99,  # Invalid step
            )


class TestDefaultCurrentStep:
    """Tests for default current_step handling."""

    @pytest.mark.asyncio
    async def test_default_current_step_is_one(
        self, chat_service, mock_context_service
    ):
        """Default current_step should be 1 if not provided."""
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        call_kwargs = mock_context_service.build_context.call_args.kwargs
        assert call_kwargs["current_step"] == 1

    @pytest.mark.asyncio
    async def test_accepts_custom_current_step(
        self, chat_service, mock_context_service
    ):
        """Should accept custom current_step parameter."""
        mock_context_service.build_context.return_value = {
            "current_step": 4,
            "step_name": "Analysis",
            "session_id": str(uuid4()),
            "suggested_actions": [],
        }
        session_id = uuid4()
        await chat_service.send_message(
            session_id=session_id,
            message="Hello",
            current_step=4,
        )
        call_kwargs = mock_context_service.build_context.call_args.kwargs
        assert call_kwargs["current_step"] == 4


class TestGetChatService:
    """Tests for the get_chat_service dependency function."""

    def test_get_chat_service_returns_chat_service(self):
        """get_chat_service should return a ChatService instance."""
        with patch("app.services.chat_service.LLMService") as mock_llm_class, \
             patch("app.services.chat_service.ContextService") as mock_context_class, \
             patch("app.services.chat_service.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.anthropic_api_key = MagicMock()
            mock_settings.anthropic_api_key.get_secret_value.return_value = "test_key"
            mock_settings.anthropic_model = "claude-sonnet-4-20250514"
            mock_get_settings.return_value = mock_settings

            service = get_chat_service()

            assert isinstance(service, ChatService)

    def test_get_chat_service_creates_llm_service(self):
        """get_chat_service should create an LLMService."""
        with patch("app.services.chat_service.LLMService") as mock_llm_class, \
             patch("app.services.chat_service.ContextService") as mock_context_class, \
             patch("app.services.chat_service.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.anthropic_api_key = MagicMock()
            mock_settings.anthropic_api_key.get_secret_value.return_value = "test_key"
            mock_settings.anthropic_model = "claude-sonnet-4-20250514"
            mock_get_settings.return_value = mock_settings

            get_chat_service()

            mock_llm_class.assert_called_once()

    def test_get_chat_service_creates_context_service(self):
        """get_chat_service should create a ContextService."""
        with patch("app.services.chat_service.LLMService") as mock_llm_class, \
             patch("app.services.chat_service.ContextService") as mock_context_class, \
             patch("app.services.chat_service.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.anthropic_api_key = MagicMock()
            mock_settings.anthropic_api_key.get_secret_value.return_value = "test_key"
            mock_settings.anthropic_model = "claude-sonnet-4-20250514"
            mock_get_settings.return_value = mock_settings

            get_chat_service()

            mock_context_class.assert_called_once()


class TestConversationHistory:
    """Tests for conversation history handling."""

    @pytest.mark.asyncio
    async def test_accepts_conversation_history(
        self, chat_service, mock_llm_service
    ):
        """send_message should accept conversation history."""
        session_id = uuid4()
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        await chat_service.send_message(
            session_id=session_id,
            message="Follow-up question",
            conversation_history=history,
        )
        call_kwargs = mock_llm_service.generate_response.call_args.kwargs
        assert call_kwargs.get("conversation_history") == history

    @pytest.mark.asyncio
    async def test_works_without_conversation_history(
        self, chat_service, mock_llm_service
    ):
        """send_message should work without conversation history."""
        session_id = uuid4()
        result = await chat_service.send_message(
            session_id=session_id,
            message="Hello",
        )
        assert "response" in result
