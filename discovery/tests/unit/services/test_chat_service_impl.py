# discovery/tests/unit/services/test_chat_service_impl.py
"""Unit tests for chat service implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_send_message_with_llm():
    """Test send_message uses LLM service."""
    from app.services.chat_service import ChatService

    mock_llm_service = AsyncMock()
    mock_llm_service.generate_response.return_value = "Hello! How can I help?"

    mock_context_service = MagicMock()
    mock_context_service.build_context.return_value = {
        "step_name": "Upload",
        "session_id": str(uuid4()),
    }

    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    session_id = uuid4()
    result = await service.send_message(session_id, "Hi there", current_step=1)

    assert "response" in result
    assert "quick_actions" in result
    mock_llm_service.generate_response.assert_called()


@pytest.mark.asyncio
async def test_get_quick_actions():
    """Test getting quick actions for a step."""
    from app.services.chat_service import ChatService

    mock_llm_service = AsyncMock()
    mock_context_service = MagicMock()

    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    actions = service._get_quick_actions(1)
    assert len(actions) > 0
    assert "label" in actions[0]


@pytest.mark.asyncio
async def test_build_system_prompt():
    """Test building system prompt."""
    from app.services.chat_service import ChatService

    mock_llm_service = AsyncMock()
    mock_context_service = MagicMock()

    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    context = {"step_name": "Upload", "session_id": str(uuid4())}
    prompt = service._build_system_prompt(context)

    assert "Discovery assistant" in prompt
    assert "Upload" in prompt
