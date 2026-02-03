"""Unit tests for role mapping agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestConfidenceTier:
    """Tests for ConfidenceTier enum."""

    def test_confidence_tier_enum_values(self):
        """ConfidenceTier should have correct string values."""
        from app.agents.role_mapping_agent import ConfidenceTier

        assert ConfidenceTier.HIGH.value == "HIGH"
        assert ConfidenceTier.MEDIUM.value == "MEDIUM"
        assert ConfidenceTier.LOW.value == "LOW"

    def test_confidence_tier_to_score(self):
        """ConfidenceTier should convert to correct numerical scores."""
        from app.agents.role_mapping_agent import ConfidenceTier

        assert ConfidenceTier.HIGH.to_score() == 0.95
        assert ConfidenceTier.MEDIUM.to_score() == 0.75
        assert ConfidenceTier.LOW.to_score() == 0.50


class TestRoleMappingResult:
    """Tests for RoleMappingResult dataclass."""

    def test_role_mapping_result_dataclass(self):
        """RoleMappingResult should store all fields correctly."""
        from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier

        result = RoleMappingResult(
            source_role="Software Engineer",
            onet_code="15-1252.00",
            onet_title="Software Developers",
            confidence=ConfidenceTier.HIGH,
            reasoning="Clear match - title directly corresponds to occupation",
        )

        assert result.source_role == "Software Engineer"
        assert result.onet_code == "15-1252.00"
        assert result.onet_title == "Software Developers"
        assert result.confidence == ConfidenceTier.HIGH
        assert result.reasoning == "Clear match - title directly corresponds to occupation"

    def test_role_mapping_result_confidence_score_property(self):
        """RoleMappingResult should compute confidence_score from tier."""
        from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier

        result = RoleMappingResult(
            source_role="Software Engineer",
            onet_code="15-1252.00",
            onet_title="Software Developers",
            confidence=ConfidenceTier.HIGH,
            reasoning="Clear match",
        )

        assert result.confidence_score == 0.95

    def test_role_mapping_result_with_null_onet(self):
        """RoleMappingResult should allow null onet_code and onet_title."""
        from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier

        result = RoleMappingResult(
            source_role="Unknown Role",
            onet_code=None,
            onet_title=None,
            confidence=ConfidenceTier.LOW,
            reasoning="No matching occupation found",
        )

        assert result.onet_code is None
        assert result.onet_title is None
        assert result.confidence_score == 0.50


class TestRoleMappingAgentInit:
    """Tests for RoleMappingAgent initialization."""

    def test_init_stores_dependencies(self):
        """Agent should store LLM service and repository."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)

        assert agent.llm_service is mock_llm
        assert agent.onet_repository is mock_repo

    def test_init_default_batch_size(self):
        """Agent should use default batch size."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)

        assert agent.batch_size == RoleMappingAgent.DEFAULT_BATCH_SIZE

    def test_init_custom_batch_size(self):
        """Agent should accept custom batch size."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo, batch_size=5)

        assert agent.batch_size == 5


class TestRoleMappingAgentGetCandidates:
    """Tests for _get_candidates method."""

    @pytest.mark.asyncio
    async def test_get_candidates_searches_repository(self):
        """Should search repository for each role."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = AsyncMock()
        mock_repo.search_with_full_text.return_value = []

        agent = RoleMappingAgent(mock_llm, mock_repo)
        await agent._get_candidates(["Software Engineer", "Data Analyst"])

        assert mock_repo.search_with_full_text.call_count == 2

    @pytest.mark.asyncio
    async def test_get_candidates_returns_dict(self):
        """Should return dict mapping roles to candidates."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = AsyncMock()
        mock_repo.search_with_full_text.return_value = []

        agent = RoleMappingAgent(mock_llm, mock_repo)
        candidates = await agent._get_candidates(["Software Engineer"])

        assert isinstance(candidates, dict)
        assert "Software Engineer" in candidates


class TestRoleMappingAgentChunkRoles:
    """Tests for _chunk_roles method."""

    def test_chunk_roles_correct_size(self):
        """Should chunk roles into correct batch sizes."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo, batch_size=3)
        roles = ["Role1", "Role2", "Role3", "Role4", "Role5"]
        candidates = {r: [] for r in roles}

        batches = agent._chunk_roles(roles, candidates)

        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 2

    def test_chunk_roles_exact_batch_size(self):
        """Should handle roles that exactly fill batches."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo, batch_size=3)
        roles = ["Role1", "Role2", "Role3", "Role4", "Role5", "Role6"]
        candidates = {r: [] for r in roles}

        batches = agent._chunk_roles(roles, candidates)

        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3

    def test_chunk_roles_empty_list(self):
        """Should handle empty roles list."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo, batch_size=3)
        batches = agent._chunk_roles([], {})

        assert len(batches) == 0


class TestRoleMappingAgentMapRoles:
    """Tests for map_roles method."""

    @pytest.mark.asyncio
    async def test_map_roles_empty_list_returns_empty(self):
        """Should return empty list for empty input."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = AsyncMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)
        results = await agent.map_roles([])

        assert results == []

    @pytest.mark.asyncio
    async def test_map_roles_returns_results(self):
        """Should return RoleMappingResult objects."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = """[
            {
                "role": "Software Engineer",
                "onet_code": "15-1252.00",
                "onet_title": "Software Developers",
                "confidence": "HIGH",
                "reasoning": "Clear match"
            }
        ]"""

        mock_repo = AsyncMock()
        mock_repo.search_with_full_text.return_value = []

        agent = RoleMappingAgent(mock_llm, mock_repo)
        results = await agent.map_roles(["Software Engineer"])

        assert len(results) == 1
        assert results[0].source_role == "Software Engineer"


class TestRoleMappingAgentParseResponse:
    """Tests for _parse_response method."""

    def test_parse_response_valid_json(self):
        """Should parse valid JSON response."""
        from app.agents.role_mapping_agent import RoleMappingAgent, ConfidenceTier

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)

        response = """[
            {
                "role": "Software Engineer",
                "onet_code": "15-1252.00",
                "onet_title": "Software Developers",
                "confidence": "HIGH",
                "reasoning": "Clear match"
            }
        ]"""

        results = agent._parse_response(response, [("Software Engineer", [])])

        assert len(results) == 1
        assert results[0].onet_code == "15-1252.00"
        assert results[0].confidence == ConfidenceTier.HIGH

    def test_parse_response_markdown_code_block(self):
        """Should handle JSON wrapped in markdown code block."""
        from app.agents.role_mapping_agent import RoleMappingAgent

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)

        response = """```json
[
    {
        "role": "Data Analyst",
        "onet_code": "15-2051.00",
        "onet_title": "Data Scientists",
        "confidence": "MEDIUM",
        "reasoning": "Related field"
    }
]
```"""

        results = agent._parse_response(response, [("Data Analyst", [])])

        assert len(results) == 1
        assert results[0].onet_code == "15-2051.00"

    def test_parse_response_invalid_json_returns_fallback(self):
        """Should return fallback results for invalid JSON."""
        from app.agents.role_mapping_agent import RoleMappingAgent, ConfidenceTier

        mock_llm = MagicMock()
        mock_repo = MagicMock()

        agent = RoleMappingAgent(mock_llm, mock_repo)

        # Create a mock occupation for fallback
        mock_occ = MagicMock()
        mock_occ.code = "15-1252.00"
        mock_occ.title = "Software Developers"

        response = "This is not valid JSON"
        results = agent._parse_response(response, [("Software Engineer", [mock_occ])])

        assert len(results) == 1
        assert results[0].confidence == ConfidenceTier.LOW
        assert "Parse error" in results[0].reasoning
