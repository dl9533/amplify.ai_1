"""Test OnetRepository bulk_upsert_industries."""
import pytest
from unittest.mock import AsyncMock


class TestBulkUpsertIndustries:
    """Test bulk upserting industry data."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_industries(self):
        """Test inserting new industry records."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        repo = OnetRepository(mock_session)

        industries = [
            {
                "occupation_code": "13-2051.00",
                "naics_code": "522110",
                "naics_title": "Commercial Banking",
                "employment_percent": 0.25,
            },
            {
                "occupation_code": "13-2051.00",
                "naics_code": "523110",
                "naics_title": "Investment Banking",
                "employment_percent": 0.15,
            },
        ]

        result = await repo.bulk_upsert_industries(industries)

        assert result == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_upsert_handles_empty_list(self):
        """Test handling empty industry list."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        result = await repo.bulk_upsert_industries([])

        assert result == 0
        mock_session.execute.assert_not_called()


def test_bulk_upsert_industries_method_exists():
    """Test bulk_upsert_industries method exists."""
    from app.repositories.onet_repository import OnetRepository

    assert hasattr(OnetRepository, "bulk_upsert_industries")
    assert callable(getattr(OnetRepository, "bulk_upsert_industries"))
