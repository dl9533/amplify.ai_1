"""Unit tests for RoadmapSubagent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.roadmap_agent import RoadmapSubagent
from app.agents.base import BaseSubagent


@pytest.fixture
def roadmap_agent():
    return RoadmapSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


class TestRoadmapSubagentSetup:
    """Tests for roadmap agent configuration."""

    def test_roadmap_agent_extends_base_subagent(self, roadmap_agent):
        """RoadmapSubagent should extend BaseSubagent."""
        assert isinstance(roadmap_agent, BaseSubagent)

    def test_roadmap_agent_type_is_roadmap(self, roadmap_agent):
        """Agent type should be 'roadmap'."""
        assert roadmap_agent.agent_type == "roadmap"


class TestPrioritization:
    """Tests for candidate prioritization."""

    @pytest.mark.asyncio
    async def test_prioritize_candidates_by_score(self, roadmap_agent):
        """Should prioritize candidates by priority score."""
        candidates = [
            MagicMock(id="c1", role_name="Engineer", priority_score=0.6),
            MagicMock(id="c2", role_name="Analyst", priority_score=0.9),
            MagicMock(id="c3", role_name="Manager", priority_score=0.7),
        ]

        result = await roadmap_agent.prioritize(candidates)

        assert result[0].id == "c2"  # Highest priority first
        assert result[1].id == "c3"
        assert result[2].id == "c1"

    @pytest.mark.asyncio
    async def test_assign_priority_tiers(self, roadmap_agent):
        """Should assign high/medium/low tiers based on scores."""
        candidates = [
            MagicMock(id="c1", priority_score=0.85),  # High
            MagicMock(id="c2", priority_score=0.55),  # Medium
            MagicMock(id="c3", priority_score=0.25),  # Low
        ]

        result = await roadmap_agent.assign_tiers(candidates)

        assert result["c1"] == "high"
        assert result["c2"] == "medium"
        assert result["c3"] == "low"


class TestTimelineGeneration:
    """Tests for implementation timeline."""

    @pytest.mark.asyncio
    async def test_generate_quarterly_timeline(self, roadmap_agent):
        """Should organize candidates into quarterly timeline."""
        candidates = [
            MagicMock(id="c1", priority_score=0.9, complexity_score=0.2),
            MagicMock(id="c2", priority_score=0.7, complexity_score=0.5),
            MagicMock(id="c3", priority_score=0.5, complexity_score=0.8),
        ]

        timeline = await roadmap_agent.generate_timeline(candidates, quarters=4)

        assert "Q1" in timeline
        assert "Q2" in timeline
        assert len(timeline["Q1"]) >= 1  # High priority, low complexity first


class TestBrainstormingFlow:
    """Tests for brainstorming-style roadmap planning."""

    @pytest.mark.asyncio
    async def test_process_asks_about_priorities(self, roadmap_agent):
        """Should ask about prioritization preferences."""
        roadmap_agent._candidates = [MagicMock(), MagicMock()]

        response = await roadmap_agent.process("Create a roadmap")

        assert response.get("message") is not None or response.get("question") is not None

    @pytest.mark.asyncio
    async def test_process_offers_timeline_options(self, roadmap_agent):
        """Should offer timeline duration options."""
        roadmap_agent._prioritized = True

        response = await roadmap_agent.process("Generate timeline")

        assert response.get("choices") is not None
