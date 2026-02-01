# discovery/tests/unit/test_message_formatter.py
"""Tests for ChatMessageFormatter."""
import pytest
from datetime import datetime

from app.agents.message_formatter import ChatMessageFormatter


@pytest.fixture
def formatter():
    return ChatMessageFormatter()


class TestMessageFormatting:
    """Tests for chat message formatting."""

    def test_format_agent_message(self, formatter):
        """Should format agent message with metadata."""
        result = formatter.format_agent_message(
            content="Which column contains roles?",
            agent_type="upload",
        )

        assert result.role == "assistant"
        assert result.content == "Which column contains roles?"
        assert result.agent_type == "upload"

    def test_format_user_message(self, formatter):
        """Should format user message."""
        result = formatter.format_user_message(
            content="Column B",
        )

        assert result.role == "user"
        assert result.content == "Column B"

    def test_include_timestamp(self, formatter):
        """Should include timestamp in messages."""
        result = formatter.format_agent_message(
            content="Hello",
            agent_type="orchestrator",
        )

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestQuickActionFormatting:
    """Tests for quick action chip formatting."""

    def test_format_choices_as_quick_actions(self, formatter):
        """Should format choices as quick action chips."""
        result = formatter.format_with_quick_actions(
            content="Select a column:",
            choices=["Column A", "Column B"],
        )

        assert len(result.quick_actions) == 2
        assert result.quick_actions[0].label == "Column A"

    def test_quick_action_includes_value(self, formatter):
        """Quick actions should include value for API."""
        result = formatter.format_with_quick_actions(
            content="Choose:",
            choices=[("Display Text", "api_value")],
        )

        assert result.quick_actions[0].label == "Display Text"
        assert result.quick_actions[0].value == "api_value"

    def test_simple_string_choices_use_label_as_value(self, formatter):
        """Simple string choices should use label as value."""
        result = formatter.format_with_quick_actions(
            content="Choose:",
            choices=["Option A"],
        )

        assert result.quick_actions[0].label == "Option A"
        assert result.quick_actions[0].value == "Option A"


class TestConversationHistory:
    """Tests for conversation history formatting."""

    def test_format_history_for_display(self, formatter):
        """Should format message history for UI display."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!", "agent_type": "orchestrator"},
        ]

        result = formatter.format_history(messages)

        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"

    def test_group_by_conversation_turn(self, formatter):
        """Should group messages by conversation turn."""
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]

        result = formatter.group_by_turn(messages)

        assert len(result) == 2  # Two turns
        assert result[0].user_message.content == "Q1"
        assert result[0].agent_message.content == "A1"
