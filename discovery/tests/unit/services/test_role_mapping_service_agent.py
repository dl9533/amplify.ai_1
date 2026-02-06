"""Unit tests for role mapping service with LLM agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier


class TestRoleMappingServiceWithAgent:
    """Tests for RoleMappingService with LLM agent."""

    def test_init_requires_role_mapping_agent(self):
        """Service should require role_mapping_agent parameter."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = MagicMock()
        mock_agent = MagicMock()

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
        )

        assert service.role_mapping_agent is mock_agent
        assert service.repository is mock_repo

    def test_init_upload_service_optional(self):
        """Service should accept optional upload_service."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = MagicMock()
        mock_agent = MagicMock()
        mock_upload_service = MagicMock()

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
            upload_service=mock_upload_service,
        )

        assert service.upload_service is mock_upload_service

    @pytest.mark.asyncio
    async def test_create_mappings_uses_agent(self):
        """Service should use agent for mapping."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_agent = AsyncMock()
        mock_upload_service = AsyncMock()

        # Setup mock returns
        mock_repo.delete_for_session.return_value = 0  # No existing mappings to delete
        mock_upload_service.get_file_content.return_value = b"role\nSoftware Engineer\n"
        mock_upload = MagicMock()
        mock_upload.file_name = "test.csv"
        mock_upload_service.repository.get_by_id.return_value = mock_upload

        mock_agent.map_roles.return_value = [
            RoleMappingResult(
                source_role="Software Engineer",
                onet_code="15-1252.00",
                onet_title="Software Developers",
                confidence=ConfidenceTier.HIGH,
                reasoning="Clear match",
            )
        ]

        mock_repo.create.return_value = MagicMock(
            id="123",
            source_role="Software Engineer",
            onet_code="15-1252.00",
            confidence_score=0.95,
            row_count=1,
            user_confirmed=False,
        )

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
            upload_service=mock_upload_service,
        )

        # Patch file parser
        with patch.object(service, "_file_parser") as mock_parser:
            mock_parser.extract_role_lob_values.return_value = [
                {"role": "Software Engineer", "lob": None, "count": 1}
            ]

            import uuid
            result = await service.create_mappings_from_upload(
                session_id=uuid.uuid4(),
                upload_id=uuid.uuid4(),
                role_column="role",
            )

        # Agent should be called
        mock_agent.map_roles.assert_called_once()
        assert len(result) == 1
        assert result[0]["confidence_tier"] == "HIGH"
        assert result[0]["reasoning"] == "Clear match"

    @pytest.mark.asyncio
    async def test_map_roles_returns_results(self):
        """Service map_roles method should return formatted results."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_agent = AsyncMock()

        mock_agent.map_roles.return_value = [
            RoleMappingResult(
                source_role="Data Analyst",
                onet_code="15-2051.00",
                onet_title="Data Scientists",
                confidence=ConfidenceTier.MEDIUM,
                reasoning="Related role",
            )
        ]

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
        )

        result = await service.map_roles(["Data Analyst"])

        assert len(result) == 1
        assert result[0]["source_role"] == "Data Analyst"
        assert result[0]["onet_code"] == "15-2051.00"
        assert result[0]["confidence_tier"] == "MEDIUM"
        assert result[0]["confidence_score"] == 0.75

    @pytest.mark.asyncio
    async def test_bulk_confirm_uses_threshold(self):
        """Service should bulk confirm mappings above threshold."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_agent = MagicMock()

        # Mock mappings - one above threshold, one below
        mock_mappings = [
            MagicMock(
                id="1",
                user_confirmed=False,
                onet_code="15-1252.00",
                confidence_score=0.95,
            ),
            MagicMock(
                id="2",
                user_confirmed=False,
                onet_code="15-2051.00",
                confidence_score=0.70,
            ),
        ]
        mock_repo.get_for_session.return_value = mock_mappings

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
        )

        import uuid
        result = await service.bulk_confirm(
            session_id=uuid.uuid4(),
            threshold=0.85,
        )

        # Only one should be confirmed (above 0.85 threshold)
        assert result["confirmed_count"] == 1
        mock_repo.confirm.assert_called_once()


class TestGetRoleMappingService:
    """Tests for get_role_mapping_service dependency."""

    def test_get_role_mapping_service_exists(self):
        """Should have dependency function that creates service with agent."""
        from app.services.role_mapping_service import get_role_mapping_service

        assert callable(get_role_mapping_service)


class TestOnetService:
    """Tests for OnetService."""

    def test_onet_service_uses_repository(self):
        """OnetService should use local repository."""
        from app.services.role_mapping_service import OnetService

        mock_repo = MagicMock()
        service = OnetService(repository=mock_repo)

        assert service.repository is mock_repo

    @pytest.mark.asyncio
    async def test_onet_service_search(self):
        """OnetService search should use full-text search."""
        from app.services.role_mapping_service import OnetService

        mock_repo = AsyncMock()
        mock_occupation = MagicMock(
            code="15-1252.00",
            title="Software Developers",
        )
        mock_repo.search_with_full_text.return_value = [mock_occupation]

        service = OnetService(repository=mock_repo)
        result = await service.search("software")

        assert len(result) == 1
        assert result[0]["code"] == "15-1252.00"
        mock_repo.search_with_full_text.assert_called_once_with("software")

    @pytest.mark.asyncio
    async def test_onet_service_get_occupation(self):
        """OnetService should get occupation by code."""
        from app.services.role_mapping_service import OnetService

        mock_repo = AsyncMock()
        mock_occupation = MagicMock(
            code="15-1252.00",
            title="Software Developers",
            description="Develop software applications",
        )
        mock_repo.get_by_code.return_value = mock_occupation

        service = OnetService(repository=mock_repo)
        result = await service.get_occupation("15-1252.00")

        assert result["code"] == "15-1252.00"
        assert result["title"] == "Software Developers"
        mock_repo.get_by_code.assert_called_once_with("15-1252.00")
