"""Unit tests for O*NET repository."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_onet_repository_exists():
    """Test OnetRepository is importable."""
    from app.repositories.onet_repository import OnetRepository
    assert OnetRepository is not None


class TestOnetRepositoryInit:
    """Tests for OnetRepository initialization."""

    def test_init_stores_session(self):
        """Repository should store the database session."""
        from app.repositories.onet_repository import OnetRepository
        mock_session = MagicMock()
        repo = OnetRepository(mock_session)
        assert repo.session is mock_session


class TestOnetRepositorySearch:
    """Tests for OnetRepository search methods."""

    @pytest.mark.asyncio
    async def test_search_occupations_exists(self):
        """Test search_occupations method exists."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "search_occupations")
        assert callable(repo.search_occupations)

    @pytest.mark.asyncio
    async def test_search_with_full_text(self):
        """Search should use full-text search method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        # search_with_full_text should exist for enhanced full-text search
        assert hasattr(repo, "search_with_full_text")
        assert callable(repo.search_with_full_text)

    @pytest.mark.asyncio
    async def test_get_by_code(self):
        """Test get_by_code method signature."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "get_by_code")
        assert callable(repo.get_by_code)


class TestOnetRepositoryWorkActivities:
    """Tests for work activity methods."""

    @pytest.mark.asyncio
    async def test_get_gwas(self):
        """Test get_gwas method signature."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "get_gwas")
        assert callable(repo.get_gwas)

    @pytest.mark.asyncio
    async def test_get_dwas_for_occupation(self):
        """Test get_dwas_for_occupation method signature."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "get_dwas_for_occupation")
        assert callable(repo.get_dwas_for_occupation)


class TestOnetRepositoryAlternateTitles:
    """Tests for alternate title methods."""

    @pytest.mark.asyncio
    async def test_search_alternate_titles_exists(self):
        """Repository should have search_alternate_titles method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "search_alternate_titles")
        assert callable(repo.search_alternate_titles)

    @pytest.mark.asyncio
    async def test_get_alternate_titles_for_occupation(self):
        """Repository should have method to get alternate titles."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "get_alternate_titles_for_occupation")
        assert callable(repo.get_alternate_titles_for_occupation)


class TestOnetRepositoryBulkOperations:
    """Tests for bulk upsert methods."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_occupations_exists(self):
        """Repository should have bulk_upsert_occupations method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "bulk_upsert_occupations")
        assert callable(repo.bulk_upsert_occupations)

    @pytest.mark.asyncio
    async def test_bulk_upsert_alternate_titles_exists(self):
        """Repository should have bulk_upsert_alternate_titles method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "bulk_upsert_alternate_titles")
        assert callable(repo.bulk_upsert_alternate_titles)

    @pytest.mark.asyncio
    async def test_bulk_upsert_tasks_exists(self):
        """Repository should have bulk_upsert_tasks method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "bulk_upsert_tasks")
        assert callable(repo.bulk_upsert_tasks)


class TestOnetRepositorySyncLog:
    """Tests for sync log methods."""

    @pytest.mark.asyncio
    async def test_log_sync_exists(self):
        """Repository should have log_sync method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "log_sync")
        assert callable(repo.log_sync)

    @pytest.mark.asyncio
    async def test_get_latest_sync_exists(self):
        """Repository should have get_latest_sync method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "get_latest_sync")
        assert callable(repo.get_latest_sync)

    @pytest.mark.asyncio
    async def test_count_exists(self):
        """Repository should have count method."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        assert hasattr(repo, "count")
        assert callable(repo.count)


class TestOnetRepositoryInputValidation:
    """Tests for input validation in search methods."""

    @pytest.mark.asyncio
    async def test_search_with_full_text_empty_query_returns_empty_list(self):
        """Empty query should return empty list without database call."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        result = await repo.search_with_full_text("")
        assert result == []
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_with_full_text_whitespace_query_returns_empty_list(self):
        """Whitespace-only query should return empty list."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        result = await repo.search_with_full_text("   \t\n  ")
        assert result == []
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_with_full_text_query_too_long_raises_error(self):
        """Query exceeding max length should raise ValueError."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        long_query = "x" * 501  # Exceeds MAX_QUERY_LENGTH of 500
        with pytest.raises(ValueError, match="exceeds maximum length"):
            await repo.search_with_full_text(long_query)

    @pytest.mark.asyncio
    async def test_search_with_full_text_max_length_query_allowed(self):
        """Query at exactly max length should be allowed."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        repo = OnetRepository(mock_session)

        max_query = "x" * 500  # Exactly MAX_QUERY_LENGTH
        result = await repo.search_with_full_text(max_query)
        assert result == []
        mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_search_alternate_titles_empty_query_returns_empty_list(self):
        """Empty query should return empty list for alternate titles search."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        result = await repo.search_alternate_titles("")
        assert result == []
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_alternate_titles_query_too_long_raises_error(self):
        """Query exceeding max length should raise ValueError for alternate titles."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        long_query = "x" * 501
        with pytest.raises(ValueError, match="exceeds maximum length"):
            await repo.search_alternate_titles(long_query)

    def test_max_query_length_constant_exists(self):
        """Repository should have MAX_QUERY_LENGTH constant."""
        from app.repositories.onet_repository import OnetRepository

        assert hasattr(OnetRepository, "MAX_QUERY_LENGTH")
        assert OnetRepository.MAX_QUERY_LENGTH == 500
