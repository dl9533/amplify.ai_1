"""Test grouped role mappings endpoint."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


class TestGroupedRoleMappingsSchemas:
    """Test schemas for grouped role mappings."""

    def test_grouped_mapping_summary_exists(self):
        """Test GroupedMappingSummary schema is defined."""
        from app.schemas.role_mapping import GroupedMappingSummary

        assert GroupedMappingSummary is not None

    def test_grouped_mapping_summary_fields(self):
        """Test GroupedMappingSummary has expected fields."""
        from app.schemas.role_mapping import GroupedMappingSummary

        summary = GroupedMappingSummary(
            total_roles=10,
            confirmed_count=5,
            pending_count=3,
            low_confidence_count=2,
            total_employees=1000,
        )

        assert summary.total_roles == 10
        assert summary.confirmed_count == 5
        assert summary.pending_count == 3
        assert summary.low_confidence_count == 2
        assert summary.total_employees == 1000

    def test_role_mapping_compact_exists(self):
        """Test RoleMappingCompact schema is defined."""
        from app.schemas.role_mapping import RoleMappingCompact

        assert RoleMappingCompact is not None

    def test_role_mapping_compact_fields(self):
        """Test RoleMappingCompact has expected fields."""
        from app.schemas.role_mapping import RoleMappingCompact

        mapping = RoleMappingCompact(
            id=uuid4(),
            source_role="Software Engineer",
            onet_code="15-1252.00",
            onet_title="Software Developers",
            confidence_score=0.92,
            is_confirmed=True,
            employee_count=25,
        )

        assert mapping.source_role == "Software Engineer"
        assert mapping.onet_code == "15-1252.00"
        assert mapping.confidence_score == 0.92
        assert mapping.employee_count == 25

    def test_lob_group_exists(self):
        """Test LobGroup schema is defined."""
        from app.schemas.role_mapping import LobGroup

        assert LobGroup is not None

    def test_lob_group_fields(self):
        """Test LobGroup has expected fields."""
        from app.schemas.role_mapping import LobGroup, RoleMappingCompact, GroupedMappingSummary

        summary = GroupedMappingSummary(
            total_roles=2,
            confirmed_count=1,
            pending_count=1,
            low_confidence_count=0,
            total_employees=50,
        )

        mapping = RoleMappingCompact(
            id=uuid4(),
            source_role="Analyst",
            onet_code="13-2051.00",
            onet_title="Financial Analysts",
            confidence_score=0.85,
            is_confirmed=False,
            employee_count=25,
        )

        group = LobGroup(
            lob="Investment Banking",
            summary=summary,
            mappings=[mapping],
        )

        assert group.lob == "Investment Banking"
        assert group.summary.total_roles == 2
        assert len(group.mappings) == 1

    def test_grouped_role_mappings_response_exists(self):
        """Test GroupedRoleMappingsResponse schema is defined."""
        from app.schemas.role_mapping import GroupedRoleMappingsResponse

        assert GroupedRoleMappingsResponse is not None

    def test_grouped_role_mappings_response_fields(self):
        """Test GroupedRoleMappingsResponse has expected fields."""
        from app.schemas.role_mapping import (
            GroupedRoleMappingsResponse,
            GroupedMappingSummary,
            LobGroup,
            RoleMappingCompact,
        )

        overall_summary = GroupedMappingSummary(
            total_roles=10,
            confirmed_count=5,
            pending_count=3,
            low_confidence_count=2,
            total_employees=1000,
        )

        response = GroupedRoleMappingsResponse(
            session_id=uuid4(),
            overall_summary=overall_summary,
            lob_groups=[],
            ungrouped_mappings=[],
        )

        assert response.overall_summary.total_roles == 10
        assert response.lob_groups == []
        assert response.ungrouped_mappings == []


class TestGroupedRoleMappingsEndpoint:
    """Test grouped role mappings endpoint."""

    @pytest.mark.asyncio
    async def test_get_grouped_mappings_endpoint_exists(self):
        """Test that grouped mappings endpoint is defined."""
        from app.routers.role_mappings import get_grouped_mappings

        assert get_grouped_mappings is not None
        assert callable(get_grouped_mappings)

    @pytest.mark.asyncio
    async def test_get_grouped_mappings_returns_response(self):
        """Test endpoint returns GroupedRoleMappingsResponse."""
        from app.routers.role_mappings import get_grouped_mappings
        from app.schemas.role_mapping import GroupedRoleMappingsResponse

        session_id = uuid4()

        # Create mock service
        mock_service = AsyncMock()
        mock_service.get_grouped_mappings.return_value = {
            "session_id": str(session_id),
            "overall_summary": {
                "total_roles": 5,
                "confirmed_count": 2,
                "pending_count": 2,
                "low_confidence_count": 1,
                "total_employees": 500,
            },
            "lob_groups": [],
            "ungrouped_mappings": [],
        }

        result = await get_grouped_mappings(
            session_id=session_id,
            service=mock_service,
        )

        assert isinstance(result, GroupedRoleMappingsResponse)
        assert result.overall_summary.total_roles == 5


class TestRoleMappingServiceGroupedMappings:
    """Test RoleMappingService.get_grouped_mappings method."""

    def test_get_grouped_mappings_method_exists(self):
        """Test that get_grouped_mappings method exists on service."""
        from app.services.role_mapping_service import RoleMappingService

        assert hasattr(RoleMappingService, "get_grouped_mappings")
        assert callable(getattr(RoleMappingService, "get_grouped_mappings"))
