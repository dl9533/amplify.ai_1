# discovery/tests/unit/agents/test_analysis_agent_impl.py
"""Unit tests for analysis agent implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_trigger_analysis():
    """Test triggering analysis calculation."""
    from app.agents.analysis_agent import AnalysisSubagent

    mock_analysis_service = AsyncMock()
    mock_analysis_service.trigger_analysis.return_value = {
        "status": "completed",
        "count": 10,
    }
    mock_analysis_service.get_all_dimensions.return_value = None

    session = MagicMock()
    session.id = uuid4()

    agent = AnalysisSubagent(session=session, analysis_service=mock_analysis_service)
    result = await agent.process("Calculate scores")

    mock_analysis_service.trigger_analysis.assert_called()
    assert "message" in result


@pytest.mark.asyncio
async def test_show_dimension_summary():
    """Test showing analysis by dimension."""
    from app.agents.analysis_agent import AnalysisSubagent

    mock_analysis_service = AsyncMock()
    mock_analysis_service.get_by_dimension.return_value = {
        "dimension": "role",
        "results": [
            {"name": "Engineer", "ai_exposure_score": 0.78, "priority_tier": "now"},
        ],
    }
    mock_analysis_service.get_all_dimensions.return_value = {"role": {"count": 5}}

    session = MagicMock()
    session.id = uuid4()

    agent = AnalysisSubagent(session=session, analysis_service=mock_analysis_service)
    agent._analysis_complete = True
    result = await agent.process("Show by role")

    assert "message" in result


@pytest.mark.asyncio
async def test_continue_to_roadmap():
    """Test continuing to roadmap step."""
    from app.agents.analysis_agent import AnalysisSubagent

    mock_analysis_service = AsyncMock()
    mock_analysis_service.get_all_dimensions.return_value = {"role": {"count": 5}}

    session = MagicMock()
    session.id = uuid4()

    agent = AnalysisSubagent(session=session, analysis_service=mock_analysis_service)
    agent._analysis_complete = True
    result = await agent.process("continue to roadmap")

    assert "step_complete" in result
    assert result["step_complete"] is True


@pytest.mark.asyncio
async def test_no_analysis_yet():
    """Test response when no analysis has been run."""
    from app.agents.analysis_agent import AnalysisSubagent

    mock_analysis_service = AsyncMock()
    mock_analysis_service.get_all_dimensions.return_value = None

    session = MagicMock()
    session.id = uuid4()

    agent = AnalysisSubagent(session=session, analysis_service=mock_analysis_service)
    result = await agent.process("Show results")

    assert "message" in result
    assert "calculate" in result["message"].lower() or "run" in result["message"].lower()
