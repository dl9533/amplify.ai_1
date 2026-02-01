"""Tests for discovery chat router."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.chat import router
from app.services.chat_service import get_chat_service
from app.schemas.chat import (
    ChatMessage,
    ChatResponse,
    ChatHistoryItem,
    QuickAction,
    QuickActionRequest,
    QuickActionResponse,
)


@pytest.fixture
def mock_chat_service():
    """Mock chat service for testing."""
    service = MagicMock()
    service.send_message = AsyncMock()
    service.get_history = AsyncMock()
    service.execute_action = AsyncMock()
    service.stream_response = AsyncMock()
    return service


@pytest.fixture
def app(mock_chat_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestSendMessage:
    """Tests for POST /discovery/sessions/{session_id}/chat."""

    def test_send_message_returns_200(self, client, mock_chat_service):
        """Should send message and return response with quick_actions."""
        session_id = uuid4()

        mock_chat_service.send_message.return_value = {
            "response": "Hello! How can I help you?",
            "quick_actions": [
                {"label": "Upload Data", "action": "upload"},
                {"label": "View Roadmap", "action": "roadmap"},
            ],
        }

        response = client.post(
            f"/discovery/sessions/{session_id}/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help you?"
        assert len(data["quick_actions"]) == 2
        assert data["quick_actions"][0]["label"] == "Upload Data"
        assert data["quick_actions"][0]["action"] == "upload"
        mock_chat_service.send_message.assert_called_once()

    def test_send_message_returns_empty_quick_actions(self, client, mock_chat_service):
        """Should return empty quick_actions when none available."""
        session_id = uuid4()

        mock_chat_service.send_message.return_value = {
            "response": "Got it!",
            "quick_actions": [],
        }

        response = client.post(
            f"/discovery/sessions/{session_id}/chat",
            json={"message": "Thanks"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Got it!"
        assert data["quick_actions"] == []

    def test_send_message_session_not_found_returns_404(self, client, mock_chat_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_chat_service.send_message.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_send_message_validates_uuid(self, client, mock_chat_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 422

    def test_send_message_requires_message_field(self, client, mock_chat_service):
        """Should require message field in request body."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/chat",
            json={},
        )

        assert response.status_code == 422


class TestGetHistory:
    """Tests for GET /discovery/sessions/{session_id}/chat."""

    def test_get_history_returns_list(self, client, mock_chat_service):
        """Should return chat history as a list."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_chat_service.get_history.return_value = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": now.isoformat(),
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": now.isoformat(),
            },
        ]

        response = client.get(f"/discovery/sessions/{session_id}/chat")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Hello"
        assert data[1]["role"] == "assistant"
        mock_chat_service.get_history.assert_called_once()

    def test_get_history_returns_empty_list(self, client, mock_chat_service):
        """Should return empty list when no history."""
        session_id = uuid4()
        mock_chat_service.get_history.return_value = []

        response = client.get(f"/discovery/sessions/{session_id}/chat")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_history_session_not_found_returns_404(self, client, mock_chat_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_chat_service.get_history.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/chat")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_history_validates_uuid(self, client, mock_chat_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/chat")

        assert response.status_code == 422


class TestStreamChat:
    """Tests for GET /discovery/sessions/{session_id}/chat/stream."""

    def test_stream_returns_event_stream_content_type(self, client, mock_chat_service):
        """Should return text/event-stream content type."""
        session_id = uuid4()

        async def mock_generator():
            yield 'data: {"chunk": "Hello"}\n\n'
            yield 'data: {"chunk": " World"}\n\n'

        mock_chat_service.stream_response.return_value = mock_generator()

        response = client.get(f"/discovery/sessions/{session_id}/chat/stream")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_stream_session_not_found_returns_404(self, client, mock_chat_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_chat_service.stream_response.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/chat/stream")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_stream_validates_uuid(self, client, mock_chat_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/chat/stream")

        assert response.status_code == 422


class TestExecuteAction:
    """Tests for POST /discovery/sessions/{session_id}/chat/action."""

    def test_execute_action_returns_response_with_data(self, client, mock_chat_service):
        """Should execute action and return response with data."""
        session_id = uuid4()

        mock_chat_service.execute_action.return_value = {
            "response": "Navigating to roadmap view",
            "data": {"route": "/roadmap", "params": {"filter": "all"}},
        }

        response = client.post(
            f"/discovery/sessions/{session_id}/chat/action",
            json={"action": "navigate", "params": {"destination": "roadmap"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Navigating to roadmap view"
        assert data["data"]["route"] == "/roadmap"
        mock_chat_service.execute_action.assert_called_once()

    def test_execute_action_with_empty_params(self, client, mock_chat_service):
        """Should accept action with empty params."""
        session_id = uuid4()

        mock_chat_service.execute_action.return_value = {
            "response": "Action executed",
            "data": {},
        }

        response = client.post(
            f"/discovery/sessions/{session_id}/chat/action",
            json={"action": "refresh"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Action executed"
        assert data["data"] == {}

    def test_execute_action_session_not_found_returns_404(self, client, mock_chat_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_chat_service.execute_action.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/chat/action",
            json={"action": "test"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_execute_action_validates_uuid(self, client, mock_chat_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/chat/action",
            json={"action": "test"},
        )

        assert response.status_code == 422

    def test_execute_action_requires_action_field(self, client, mock_chat_service):
        """Should require action field in request body."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/chat/action",
            json={},
        )

        assert response.status_code == 422


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_quick_action_has_required_fields(self):
        """QuickAction should have label and action fields."""
        action = QuickAction(label="Test", action="test_action")
        assert action.label == "Test"
        assert action.action == "test_action"

    def test_chat_message_has_message_field(self):
        """ChatMessage should have message field."""
        msg = ChatMessage(message="Hello world")
        assert msg.message == "Hello world"

    def test_chat_response_has_required_fields(self):
        """ChatResponse should have response and quick_actions."""
        resp = ChatResponse(
            response="Test response",
            quick_actions=[QuickAction(label="Action", action="act")],
        )
        assert resp.response == "Test response"
        assert len(resp.quick_actions) == 1

    def test_chat_response_defaults_empty_quick_actions(self):
        """ChatResponse should default to empty quick_actions."""
        resp = ChatResponse(response="Test")
        assert resp.quick_actions == []

    def test_chat_history_item_has_required_fields(self):
        """ChatHistoryItem should have role, content, and timestamp."""
        now = datetime.now(timezone.utc)
        item = ChatHistoryItem(
            role="user",
            content="Hello",
            timestamp=now,
        )
        assert item.role == "user"
        assert item.content == "Hello"
        assert item.timestamp == now

    def test_quick_action_request_has_required_fields(self):
        """QuickActionRequest should have action field."""
        req = QuickActionRequest(action="test")
        assert req.action == "test"
        assert req.params == {}

    def test_quick_action_request_accepts_params(self):
        """QuickActionRequest should accept params dict."""
        req = QuickActionRequest(action="test", params={"key": "value"})
        assert req.params == {"key": "value"}

    def test_quick_action_response_has_required_fields(self):
        """QuickActionResponse should have response and data."""
        resp = QuickActionResponse(
            response="Done",
            data={"result": "success"},
        )
        assert resp.response == "Done"
        assert resp.data == {"result": "success"}

    def test_quick_action_response_defaults_empty_data(self):
        """QuickActionResponse should default to empty data."""
        resp = QuickActionResponse(response="Done")
        assert resp.data == {}

    def test_chat_history_item_rejects_invalid_role(self):
        """Test that ChatHistoryItem rejects invalid role values."""
        with pytest.raises(ValidationError):
            ChatHistoryItem(
                role="invalid",  # Should fail
                content="Test",
                timestamp=datetime.now(timezone.utc),
            )
