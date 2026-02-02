# discovery/tests/unit/agents/test_orchestrator_impl.py
"""Unit tests for orchestrator implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_route_to_upload_agent():
    """Test routing to upload agent in step 1."""
    from app.agents.orchestrator import DiscoveryOrchestrator
    from app.enums import DiscoveryStep

    mock_services = {
        "upload": AsyncMock(),
        "mapping": AsyncMock(),
        "activity": AsyncMock(),
        "analysis": AsyncMock(),
        "roadmap": AsyncMock(),
    }

    session = MagicMock()
    session.id = uuid4()
    session.current_step = DiscoveryStep.UPLOAD

    orchestrator = DiscoveryOrchestrator(session=session, services=mock_services)
    result = await orchestrator.process("Hello")

    assert "message" in result


@pytest.mark.asyncio
async def test_advance_step_on_completion():
    """Test step advances when subagent completes."""
    from app.agents.orchestrator import DiscoveryOrchestrator
    from app.enums import DiscoveryStep

    mock_services = {"upload": AsyncMock()}

    session = MagicMock()
    session.id = uuid4()
    session.current_step = DiscoveryStep.UPLOAD

    orchestrator = DiscoveryOrchestrator(session=session, services=mock_services)

    # Simulate subagent completion
    orchestrator._subagents["upload"] = AsyncMock()
    orchestrator._subagents["upload"].process.return_value = {
        "message": "Done",
        "step_complete": True,
    }

    result = await orchestrator.process("Confirm mappings")

    assert session.current_step == DiscoveryStep.MAP_ROLES


@pytest.mark.asyncio
async def test_get_conversation_history():
    """Test getting conversation history."""
    from app.agents.orchestrator import DiscoveryOrchestrator
    from app.enums import DiscoveryStep

    mock_services = {"upload": AsyncMock()}

    session = MagicMock()
    session.id = uuid4()
    session.current_step = DiscoveryStep.UPLOAD

    orchestrator = DiscoveryOrchestrator(session=session, services=mock_services)

    # Mock the subagent
    orchestrator._subagents["upload"] = AsyncMock()
    orchestrator._subagents["upload"].process.return_value = {
        "message": "Hi there!",
        "step_complete": False,
    }

    await orchestrator.process("Hello")

    history = orchestrator.get_conversation_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_subagent_initialization():
    """Test subagents are properly initialized."""
    from app.agents.orchestrator import DiscoveryOrchestrator
    from app.enums import DiscoveryStep

    mock_services = {
        "upload": AsyncMock(),
        "mapping": AsyncMock(),
    }

    session = MagicMock()
    session.id = uuid4()
    session.current_step = DiscoveryStep.UPLOAD

    orchestrator = DiscoveryOrchestrator(session=session, services=mock_services)

    # Check that subagents were initialized
    assert "upload" in orchestrator._subagents
    assert "mapping" in orchestrator._subagents
