import pytest

from app.agents.base import BaseSubagent


def test_base_subagent_has_agent_type():
    """BaseSubagent should define agent_type."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

        async def process(self, message: str):
            return message

    agent = TestAgent(session=None, memory_service=None)
    assert agent.agent_type == "test_agent"


def test_base_subagent_protocol_flags_default_false():
    """Protocol flags should default to False."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

        async def process(self, message: str):
            return message

    agent = TestAgent(session=None, memory_service=None)
    assert agent.mcp_enabled is False
    assert agent.a2a_enabled is False
    assert agent.a2ui_enabled is False


def test_base_subagent_process_abstract():
    """Subagents must implement process method."""
    with pytest.raises(TypeError):
        BaseSubagent(session=None, memory_service=None)


def test_base_subagent_uses_brainstorming_style():
    """Subagent should format responses with brainstorming style."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

        async def process(self, message: str):
            return self.format_response("What column?", choices=["A", "B"])

    agent = TestAgent(session=None, memory_service=None)
    # Verify format_response exists and returns structured response
    assert hasattr(agent, "format_response")


def test_format_response_returns_structured_response():
    """format_response should return a properly structured dictionary."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"
        async def process(self, message: str):
            return message

    agent = TestAgent(session=None, memory_service=None)
    response = agent.format_response("Test message", choices=["A", "B"], custom_field="value")

    assert response["message"] == "Test message"
    assert response["agent_type"] == "test_agent"
    assert response["choices"] == ["A", "B"]
    assert response["custom_field"] == "value"


def test_format_response_without_choices():
    """format_response should work without choices."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"
        async def process(self, message: str):
            return message

    agent = TestAgent(session=None, memory_service=None)
    response = agent.format_response("Test message")

    assert "choices" not in response
    assert response["message"] == "Test message"
