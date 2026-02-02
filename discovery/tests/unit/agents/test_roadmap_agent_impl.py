# discovery/tests/unit/agents/test_roadmap_agent_impl.py
"""Unit tests for roadmap agent implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_generate_candidates():
    """Test generating candidates from analysis."""
    from app.agents.roadmap_agent import RoadmapSubagent

    mock_roadmap_service = AsyncMock()
    mock_roadmap_service.generate_candidates.return_value = [
        {
            "id": str(uuid4()),
            "name": "Data Entry Agent",
            "priority_tier": "now",
            "estimated_impact": 0.85,
        },
    ]
    mock_roadmap_service.get_candidates.return_value = []

    session = MagicMock()
    session.id = uuid4()

    agent = RoadmapSubagent(session=session, roadmap_service=mock_roadmap_service)
    result = await agent.process("Generate candidates")

    mock_roadmap_service.generate_candidates.assert_called()
    assert "message" in result


@pytest.mark.asyncio
async def test_show_candidates():
    """Test showing candidate list."""
    from app.agents.roadmap_agent import RoadmapSubagent

    mock_roadmap_service = AsyncMock()
    mock_roadmap_service.get_candidates.return_value = [
        {
            "id": str(uuid4()),
            "name": "Data Entry Agent",
            "priority_tier": "now",
            "estimated_impact": 0.85,
            "selected_for_build": False,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = RoadmapSubagent(session=session, roadmap_service=mock_roadmap_service)
    result = await agent.process("Show candidates")

    assert "message" in result
    assert "Data Entry Agent" in result["message"]


@pytest.mark.asyncio
async def test_select_for_build():
    """Test selecting candidate for build."""
    from app.agents.roadmap_agent import RoadmapSubagent

    mock_roadmap_service = AsyncMock()
    mock_roadmap_service.get_candidates.return_value = [
        {
            "id": str(uuid4()),
            "name": "Data Entry Agent",
            "priority_tier": "now",
            "estimated_impact": 0.85,
            "selected_for_build": False,
        },
    ]
    mock_roadmap_service.select_for_build.return_value = {"selected_for_build": True}

    session = MagicMock()
    session.id = uuid4()

    agent = RoadmapSubagent(session=session, roadmap_service=mock_roadmap_service)
    agent._pending_selection = str(uuid4())  # Simulate pending selection
    result = await agent.process("Yes, select this")

    assert "message" in result


@pytest.mark.asyncio
async def test_complete_discovery():
    """Test completing the discovery workflow."""
    from app.agents.roadmap_agent import RoadmapSubagent

    mock_roadmap_service = AsyncMock()
    mock_roadmap_service.get_candidates.return_value = [
        {
            "id": str(uuid4()),
            "name": "Data Entry Agent",
            "priority_tier": "now",
            "estimated_impact": 0.85,
            "selected_for_build": True,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = RoadmapSubagent(session=session, roadmap_service=mock_roadmap_service)
    result = await agent.process("Finish and handoff")

    assert "step_complete" in result
    assert result["step_complete"] is True
