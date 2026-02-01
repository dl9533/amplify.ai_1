"""Tests for AnalysisSubagent score calculation and insight generation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.analysis_agent import AnalysisSubagent
from app.agents.base import BaseSubagent


@pytest.fixture
def analysis_agent():
    return AnalysisSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_scoring_service():
    service = MagicMock()
    service.score_session = AsyncMock(return_value=MagicMock(
        role_scores={"role-1": MagicMock(exposure=0.8, impact=0.6, priority=0.75)},
        dimension_aggregations=[],
    ))
    return service


class TestAnalysisSubagentSetup:
    """Tests for analysis agent configuration."""

    def test_analysis_agent_extends_base_subagent(self, analysis_agent):
        """AnalysisSubagent should extend BaseSubagent."""
        assert isinstance(analysis_agent, BaseSubagent)

    def test_analysis_agent_type_is_analysis(self, analysis_agent):
        """Agent type should be 'analysis'."""
        assert analysis_agent.agent_type == "analysis"


class TestScoreCalculation:
    """Tests for score calculation orchestration."""

    @pytest.mark.asyncio
    async def test_trigger_scoring_uses_scoring_service(
        self, analysis_agent, mock_scoring_service
    ):
        """Should delegate to ScoringService for calculations."""
        analysis_agent._scoring_service = mock_scoring_service

        result = await analysis_agent.calculate_scores()

        mock_scoring_service.score_session.assert_called_once()
        assert result.role_scores["role-1"].exposure == 0.8

    @pytest.mark.asyncio
    async def test_calculate_scores_raises_without_service(self, analysis_agent):
        """Should raise ValueError when no scoring service is configured."""
        with pytest.raises(ValueError, match="No scoring service configured"):
            await analysis_agent.calculate_scores()


class TestInsightGeneration:
    """Tests for insight generation."""

    @pytest.mark.asyncio
    async def test_generate_top_opportunities_insight(self, analysis_agent):
        """Should generate insight about top automation opportunities."""
        analysis_agent._scoring_result = MagicMock(
            role_scores={
                "role-1": MagicMock(priority=0.9, exposure=0.85),
                "role-2": MagicMock(priority=0.6, exposure=0.5),
            }
        )

        insights = await analysis_agent.generate_insights()

        assert any("opportunity" in i.lower() or "priority" in i.lower() for i in insights)

    @pytest.mark.asyncio
    async def test_generate_insights_returns_empty_when_no_result(self, analysis_agent):
        """Should return empty list when no scoring result exists."""
        insights = await analysis_agent.generate_insights()
        assert insights == []

    @pytest.mark.asyncio
    async def test_generate_department_summary_insight(self, analysis_agent):
        """Should summarize scores by department."""
        analysis_agent._scoring_result = MagicMock(
            dimension_aggregations=[
                MagicMock(dimension="DEPARTMENT", dimension_value="Engineering", ai_exposure_score=0.8),
                MagicMock(dimension="DEPARTMENT", dimension_value="HR", ai_exposure_score=0.4),
            ]
        )

        summary = await analysis_agent.get_dimension_summary("DEPARTMENT")

        assert len(summary) == 2

    @pytest.mark.asyncio
    async def test_get_dimension_summary_returns_empty_for_unknown_dimension(self, analysis_agent):
        """Should return empty list for non-existent dimension."""
        analysis_agent._scoring_result = MagicMock(
            dimension_aggregations=[
                MagicMock(dimension="DEPARTMENT", dimension_value="Engineering"),
            ]
        )
        summary = await analysis_agent.get_dimension_summary("UNKNOWN")
        assert summary == []


class TestBrainstormingFlow:
    """Tests for brainstorming-style analysis presentation."""

    @pytest.mark.asyncio
    async def test_process_presents_analysis_dimensions(self, analysis_agent):
        """Should ask which dimension to explore."""
        analysis_agent._scores_calculated = True

        response = await analysis_agent.process("Show me the analysis")

        assert response.get("message") is not None or response.get("question") is not None
        assert response.get("choices") is not None
        # Should offer dimension choices
        dimension_names = ["role", "department", "geography", "task"]
        assert any(d in str(response.get("choices", [])).lower() for d in dimension_names)

    @pytest.mark.asyncio
    async def test_process_prompts_to_calculate_when_not_calculated(self, analysis_agent):
        """Should prompt to calculate scores when not yet calculated."""
        response = await analysis_agent.process("Hello")

        assert "Calculate scores" in str(response.get("choices", []))
