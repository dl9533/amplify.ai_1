"""Unit tests for O*NET sync service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_onet_sync_service_exists():
    """Test OnetSyncService is importable."""
    from app.services.onet_sync_service import OnetSyncService
    assert OnetSyncService is not None


class TestOnetSyncServiceInit:
    """Tests for OnetSyncService initialization."""

    def test_init_with_client_and_session(self):
        """Service should accept onet_client and db_session."""
        from app.services.onet_sync_service import OnetSyncService

        mock_client = AsyncMock()
        mock_session = AsyncMock()

        service = OnetSyncService(
            onet_client=mock_client,
            db_session=mock_session,
        )

        assert service.client is mock_client
        assert service.session is mock_session

    def test_sync_occupations_exists(self):
        """Test sync_occupations method exists."""
        from app.services.onet_sync_service import OnetSyncService

        mock_client = AsyncMock()
        mock_session = AsyncMock()

        service = OnetSyncService(
            onet_client=mock_client,
            db_session=mock_session,
        )

        assert hasattr(service, "sync_occupations")

    def test_sync_work_activities_exists(self):
        """Test sync_work_activities method exists."""
        from app.services.onet_sync_service import OnetSyncService

        mock_client = AsyncMock()
        mock_session = AsyncMock()

        service = OnetSyncService(
            onet_client=mock_client,
            db_session=mock_session,
        )

        assert hasattr(service, "sync_work_activities")

    def test_full_sync_exists(self):
        """Test full_sync method exists."""
        from app.services.onet_sync_service import OnetSyncService

        mock_client = AsyncMock()
        mock_session = AsyncMock()

        service = OnetSyncService(
            onet_client=mock_client,
            db_session=mock_session,
        )

        assert hasattr(service, "full_sync")


class TestOnetFileSyncService:
    """Tests for file-based O*NET sync service."""

    def test_onet_file_sync_service_exists(self):
        """Test OnetFileSyncService is importable."""
        from app.services.onet_file_sync_service import OnetFileSyncService
        assert OnetFileSyncService is not None

    def test_sync_result_dataclass(self):
        """Test SyncResult dataclass."""
        from app.services.onet_file_sync_service import SyncResult

        result = SyncResult(
            version="30.1",
            occupation_count=923,
            alternate_title_count=5000,
            task_count=20000,
            status="success",
        )

        assert result.version == "30.1"
        assert result.occupation_count == 923
        assert result.alternate_title_count == 5000
        assert result.task_count == 20000
        assert result.status == "success"

    def test_init_stores_repository(self):
        """Service should store the repository."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert service.repository is mock_repo

    def test_parse_occupations_method_exists(self):
        """Service should have _parse_occupations method."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert hasattr(service, "_parse_occupations")
        assert callable(service._parse_occupations)

    def test_parse_alternate_titles_method_exists(self):
        """Service should have _parse_alternate_titles method."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert hasattr(service, "_parse_alternate_titles")
        assert callable(service._parse_alternate_titles)

    def test_parse_tasks_method_exists(self):
        """Service should have _parse_tasks method."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert hasattr(service, "_parse_tasks")
        assert callable(service._parse_tasks)

    def test_sync_method_exists(self):
        """Service should have sync method."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert hasattr(service, "sync")
        assert callable(service.sync)

    def test_get_sync_status_exists(self):
        """Service should have get_sync_status method."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        assert hasattr(service, "get_sync_status")
        assert callable(service.get_sync_status)


class TestOnetFileSyncServiceParsing:
    """Tests for parsing methods."""

    def test_parse_occupations_returns_list(self):
        """_parse_occupations should return a list."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        content = "O*NET-SOC Code\tTitle\tDescription\n15-1252.00\tSoftware Developers\tDevelop software\n"
        occupations = service._parse_occupations(content)

        assert isinstance(occupations, list)
        assert len(occupations) == 1
        assert occupations[0]["code"] == "15-1252.00"
        assert occupations[0]["title"] == "Software Developers"

    def test_parse_alternate_titles_returns_list(self):
        """_parse_alternate_titles should return a list."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        content = "O*NET-SOC Code\tAlternate Title\n15-1252.00\tProgrammer\n15-1252.00\tCoder\n"
        titles = service._parse_alternate_titles(content)

        assert isinstance(titles, list)
        assert len(titles) == 2
        assert titles[0]["onet_code"] == "15-1252.00"
        assert titles[0]["title"] == "Programmer"

    def test_parse_tasks_returns_list(self):
        """_parse_tasks should return a list."""
        from app.services.onet_file_sync_service import OnetFileSyncService

        mock_repo = MagicMock()
        service = OnetFileSyncService(mock_repo)

        content = "O*NET-SOC Code\tTask\tTask ID\n15-1252.00\tWrite code\t1001\n"
        tasks = service._parse_tasks(content)

        assert isinstance(tasks, list)
        assert len(tasks) == 1
        assert tasks[0]["occupation_code"] == "15-1252.00"
        assert tasks[0]["description"] == "Write code"
