"""Test RoleMappingService industry-aware matching."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_onet_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_lob_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_role_mapping_agent():
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_role_mapping_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_role_mapping_repository, mock_role_mapping_agent, mock_onet_repo, mock_lob_service):
    from app.services.role_mapping_service import RoleMappingService
    return RoleMappingService(
        repository=mock_role_mapping_repository,
        role_mapping_agent=mock_role_mapping_agent,
        onet_repository=mock_onet_repo,
        lob_service=mock_lob_service,
    )


class TestMatchRoleWithIndustry:
    """Test industry-aware role matching."""

    @pytest.mark.asyncio
    async def test_industry_boosts_relevant_occupation(
        self, service, mock_onet_repo, mock_lob_service
    ):
        """Test that industry match boosts occupation score."""
        from app.services.lob_mapping_service import LobNaicsResult

        # Mock occupation search candidates - return dicts directly
        mock_onet_repo.search_occupations.return_value = [
            MagicMock(code="13-2051.00", title="Financial Analysts"),
            MagicMock(code="13-2011.00", title="Accountants"),
        ]

        # Mock LOB mapping
        mock_lob_service.map_lob_to_naics.return_value = LobNaicsResult(
            lob="Retail Banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )

        # Mock industry scores - Financial Analysts matches banking better
        async def mock_industry_score(code, naics):
            if code == "13-2051.00":  # Financial Analysts
                return 0.9  # Strong banking match
            return 0.2  # Accountants - weak match

        mock_onet_repo.calculate_industry_score.side_effect = mock_industry_score

        result = await service.match_role_with_industry(
            job_title="Financial Analyst",
            lob="Retail Banking",
        )

        # Financial Analysts should have industry boost
        assert len(result) == 2
        analyst_result = next(r for r in result if r["code"] == "13-2051.00")
        assert analyst_result["industry_match"] > 0
        assert "original_score" in analyst_result

    @pytest.mark.asyncio
    async def test_without_lob_no_industry_boost(
        self, service, mock_onet_repo, mock_lob_service
    ):
        """Test that without LOB, no industry boost is applied."""
        mock_onet_repo.search_occupations.return_value = [
            MagicMock(code="13-2051.00", title="Financial Analysts"),
        ]

        result = await service.match_role_with_industry(
            job_title="Financial Analyst",
            lob=None,
        )

        # Should return results without industry data
        assert len(result) == 1
        assert result[0].get("industry_match") is None
        mock_lob_service.map_lob_to_naics.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_naics_no_industry_boost(
        self, service, mock_onet_repo, mock_lob_service
    ):
        """Test that empty NAICS codes return unmodified results."""
        from app.services.lob_mapping_service import LobNaicsResult

        mock_onet_repo.search_occupations.return_value = [
            MagicMock(code="13-2051.00", title="Financial Analysts"),
        ]

        mock_lob_service.map_lob_to_naics.return_value = LobNaicsResult(
            lob="Unknown",
            naics_codes=[],
            confidence=0.0,
            source="none",
        )

        result = await service.match_role_with_industry(
            job_title="Financial Analyst",
            lob="Unknown Business",
        )

        assert len(result) == 1
        assert result[0].get("industry_match") is None

    @pytest.mark.asyncio
    async def test_no_candidates_returns_empty(
        self, service, mock_onet_repo
    ):
        """Test empty candidates returns empty list."""
        mock_onet_repo.search_occupations.return_value = []

        result = await service.match_role_with_industry(
            job_title="Unknown Role",
            lob="Retail Banking",
        )

        assert result == []


class TestIndustryBoostFactor:
    """Test INDUSTRY_BOOST_FACTOR constant."""

    def test_industry_boost_factor_exists(self):
        """Test constant is defined."""
        from app.services.role_mapping_service import RoleMappingService
        assert hasattr(RoleMappingService, "INDUSTRY_BOOST_FACTOR")

    def test_industry_boost_factor_value(self):
        """Test constant value is 0.25 (25% max boost)."""
        from app.services.role_mapping_service import RoleMappingService
        assert RoleMappingService.INDUSTRY_BOOST_FACTOR == 0.25


def test_match_role_with_industry_method_exists():
    """Test match_role_with_industry method exists."""
    from app.services.role_mapping_service import RoleMappingService
    assert hasattr(RoleMappingService, "match_role_with_industry")
    assert callable(getattr(RoleMappingService, "match_role_with_industry"))
