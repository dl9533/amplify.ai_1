"""Unit tests for role mapping service with agent integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier


class TestRoleMappingServiceWithAgent:
    """Tests for RoleMappingService with agent integration."""

    def test_init_accepts_role_mapping_agent(self):
        """Service should accept role_mapping_agent parameter."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = MagicMock()
        mock_agent = MagicMock()

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
        )

        assert service.role_mapping_agent is mock_agent

    def test_init_defaults_to_none_agent(self):
        """Service should default role_mapping_agent to None."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = MagicMock()

        service = RoleMappingService(repository=mock_repo)

        assert service.role_mapping_agent is None

    def test_init_still_accepts_fuzzy_matcher(self):
        """Service should still accept fuzzy_matcher for backwards compat."""
        from app.services.role_mapping_service import RoleMappingService
        from app.services.fuzzy_matcher import FuzzyMatcher

        mock_repo = MagicMock()
        mock_matcher = FuzzyMatcher()

        service = RoleMappingService(
            repository=mock_repo,
            fuzzy_matcher=mock_matcher,
        )

        assert service.fuzzy_matcher is mock_matcher

    @pytest.mark.asyncio
    async def test_create_mappings_uses_agent_when_available(self):
        """Service should use agent for mapping when available."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_agent = AsyncMock()
        mock_upload_service = AsyncMock()

        # Setup mock returns
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
            upload_service=mock_upload_service,
            role_mapping_agent=mock_agent,
        )

        # Patch file parser
        with patch.object(service, "_file_parser") as mock_parser:
            mock_parser.extract_unique_values.return_value = [
                {"value": "Software Engineer", "count": 1}
            ]

            import uuid
            await service.create_mappings_from_upload(
                session_id=uuid.uuid4(),
                upload_id=uuid.uuid4(),
                role_column="role",
            )

        # Agent should be called
        mock_agent.map_roles.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_mappings_falls_back_to_fuzzy_when_no_agent(self):
        """Service should use fuzzy matcher when no agent is available."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_onet_client = AsyncMock()
        mock_fuzzy_matcher = MagicMock()
        mock_upload_service = AsyncMock()

        # Setup mock returns
        mock_upload_service.get_file_content.return_value = b"role\nSoftware Engineer\n"
        mock_upload = MagicMock()
        mock_upload.file_name = "test.csv"
        mock_upload_service.repository.get_by_id.return_value = mock_upload

        mock_onet_client.search_occupations.return_value = [
            {"code": "15-1252.00", "title": "Software Developers"}
        ]
        mock_fuzzy_matcher.find_best_matches.return_value = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.85}
        ]

        mock_repo.create.return_value = MagicMock(
            id="123",
            source_role="Software Engineer",
            onet_code="15-1252.00",
            confidence_score=0.85,
            row_count=1,
            user_confirmed=False,
        )

        service = RoleMappingService(
            repository=mock_repo,
            onet_client=mock_onet_client,
            upload_service=mock_upload_service,
            fuzzy_matcher=mock_fuzzy_matcher,
            role_mapping_agent=None,  # No agent
        )

        # Patch file parser
        with patch.object(service, "_file_parser") as mock_parser:
            mock_parser.extract_unique_values.return_value = [
                {"value": "Software Engineer", "count": 1}
            ]

            import uuid
            await service.create_mappings_from_upload(
                session_id=uuid.uuid4(),
                upload_id=uuid.uuid4(),
                role_column="role",
            )

        # Fuzzy matcher should be called
        mock_fuzzy_matcher.find_best_matches.assert_called_once()


class TestGetRoleMappingServiceWithAgent:
    """Tests for get_role_mapping_service_with_agent dependency."""

    def test_get_role_mapping_service_with_agent_exists(self):
        """Should have dependency function that creates service with agent."""
        from app.services.role_mapping_service import get_role_mapping_service_with_agent

        assert callable(get_role_mapping_service_with_agent)
