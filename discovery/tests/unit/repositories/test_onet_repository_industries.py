"""Test OnetRepository industry methods."""
import pytest
from unittest.mock import AsyncMock
from app.repositories.onet_repository import OnetRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return OnetRepository(mock_session)


class TestGetIndustriesForOccupation:
    """Test getting industries for an occupation."""

    @pytest.mark.asyncio
    async def test_get_industries(self, repository, mock_session):
        """Test getting industry list for occupation code."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
                employment_percent=25.0,
            ),
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="523110",
                naics_title="Investment Banking",
                employment_percent=15.0,
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        result = await repository.get_industries_for_occupation("13-2051.00")

        assert len(result) == 2
        assert result[0].naics_code == "522110"

    @pytest.mark.asyncio
    async def test_get_industries_empty(self, repository, mock_session):
        """Test empty result when no industries."""
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        result = await repository.get_industries_for_occupation("99-9999.00")

        assert len(result) == 0


class TestCalculateIndustryScore:
    """Test industry match score calculation."""

    @pytest.mark.asyncio
    async def test_exact_naics_match(self, repository, mock_session):
        """Test perfect match score for exact NAICS code."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
                employment_percent=25.0,
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        score = await repository.calculate_industry_score("13-2051.00", ["522110"])

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_partial_naics_match(self, repository, mock_session):
        """Test partial match when NAICS prefix matches."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        # Match 2-digit prefix
        score = await repository.calculate_industry_score("13-2051.00", ["52"])

        assert 0.3 <= score <= 0.5  # Partial match

    @pytest.mark.asyncio
    async def test_no_match_zero_score(self, repository, mock_session):
        """Test zero score when no industry match."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        score = await repository.calculate_industry_score("13-2051.00", ["62"])  # Healthcare

        assert score == 0.0

    @pytest.mark.asyncio
    async def test_no_naics_codes_returns_zero(self, repository):
        """Test empty NAICS codes returns zero."""
        score = await repository.calculate_industry_score("13-2051.00", [])

        assert score == 0.0

    @pytest.mark.asyncio
    async def test_no_industries_returns_zero(self, repository, mock_session):
        """Test no industries returns zero."""
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        score = await repository.calculate_industry_score("99-9999.00", ["52"])

        assert score == 0.0


class TestNaicsMatchScore:
    """Test NAICS code matching helper."""

    def test_exact_match_returns_one(self, repository):
        """Test exact code match returns 1.0."""
        assert repository._naics_match_score("522110", "522110") == 1.0

    def test_four_digit_prefix_match(self, repository):
        """Test 4-digit prefix match returns 0.8."""
        assert repository._naics_match_score("522110", "5221") == 0.8

    def test_three_digit_prefix_match(self, repository):
        """Test 3-digit prefix match returns 0.6."""
        assert repository._naics_match_score("522110", "522") == 0.6

    def test_two_digit_prefix_match(self, repository):
        """Test 2-digit prefix match returns 0.4."""
        assert repository._naics_match_score("522110", "52") == 0.4

    def test_no_match_returns_zero(self, repository):
        """Test no match returns 0.0."""
        assert repository._naics_match_score("522110", "62") == 0.0


def test_onet_repository_has_industry_methods():
    """Test OnetRepository has industry methods."""
    from app.repositories.onet_repository import OnetRepository

    assert hasattr(OnetRepository, "get_industries_for_occupation")
    assert hasattr(OnetRepository, "calculate_industry_score")
    assert hasattr(OnetRepository, "_naics_match_score")
