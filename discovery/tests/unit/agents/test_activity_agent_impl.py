# discovery/tests/unit/agents/test_activity_agent_impl.py
"""Unit tests for activity agent implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_show_activities():
    """Test showing activity selections."""
    from app.agents.activity_agent import ActivitySubagent

    mock_activity_service = AsyncMock()
    mock_activity_service.get_selections.return_value = [
        {
            "id": str(uuid4()),
            "dwa_id": "4.A.1.a.1",
            "dwa_name": "Analyze data",
            "selected": True,
        },
        {
            "id": str(uuid4()),
            "dwa_id": "4.A.2.a.1",
            "dwa_name": "Write reports",
            "selected": False,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = ActivitySubagent(session=session, activity_service=mock_activity_service)
    result = await agent.process("Show me the activities")

    assert "message" in result


@pytest.mark.asyncio
async def test_bulk_select():
    """Test bulk selecting activities above threshold."""
    from app.agents.activity_agent import ActivitySubagent

    mock_activity_service = AsyncMock()
    mock_activity_service.bulk_select.return_value = {"selected_count": 15}
    mock_activity_service.get_selections.return_value = [
        {"id": str(uuid4()), "dwa_id": "4.A.1.a.1", "selected": True},
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = ActivitySubagent(session=session, activity_service=mock_activity_service)
    result = await agent.process("Select all activities")

    mock_activity_service.bulk_select.assert_called()
    assert "message" in result


@pytest.mark.asyncio
async def test_continue_to_analysis():
    """Test continuing to analysis step."""
    from app.agents.activity_agent import ActivitySubagent

    mock_activity_service = AsyncMock()
    mock_activity_service.get_selections.return_value = [
        {"id": str(uuid4()), "dwa_id": "4.A.1.a.1", "selected": True},
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = ActivitySubagent(session=session, activity_service=mock_activity_service)
    result = await agent.process("continue to analysis")

    assert "step_complete" in result
    assert result["step_complete"] is True


@pytest.mark.asyncio
async def test_no_selections_yet():
    """Test response when no selections exist."""
    from app.agents.activity_agent import ActivitySubagent

    mock_activity_service = AsyncMock()
    mock_activity_service.get_selections.return_value = []

    session = MagicMock()
    session.id = uuid4()

    agent = ActivitySubagent(session=session, activity_service=mock_activity_service)
    result = await agent.process("Show activities")

    assert "message" in result
