"""Test enhanced bulk confirm role mappings endpoint."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


class TestBulkConfirmRequestEnhanced:
    """Test enhanced BulkConfirmRequest schema."""

    def test_bulk_confirm_request_supports_lob(self):
        """Test BulkConfirmRequest accepts optional lob filter."""
        from app.schemas.role_mapping import BulkConfirmRequest

        request = BulkConfirmRequest(
            threshold=0.85,
            lob="Investment Banking",
        )

        assert request.threshold == 0.85
        assert request.lob == "Investment Banking"

    def test_bulk_confirm_request_supports_mapping_ids(self):
        """Test BulkConfirmRequest accepts optional mapping_ids."""
        from app.schemas.role_mapping import BulkConfirmRequest

        mapping_id = uuid4()
        request = BulkConfirmRequest(
            threshold=0.85,
            mapping_ids=[mapping_id],
        )

        assert request.threshold == 0.85
        assert request.mapping_ids == [mapping_id]

    def test_bulk_confirm_request_lob_defaults_to_none(self):
        """Test BulkConfirmRequest lob defaults to None."""
        from app.schemas.role_mapping import BulkConfirmRequest

        request = BulkConfirmRequest(threshold=0.85)

        assert request.lob is None

    def test_bulk_confirm_request_mapping_ids_defaults_to_none(self):
        """Test BulkConfirmRequest mapping_ids defaults to None."""
        from app.schemas.role_mapping import BulkConfirmRequest

        request = BulkConfirmRequest(threshold=0.85)

        assert request.mapping_ids is None


class TestBulkConfirmServiceEnhanced:
    """Test enhanced bulk_confirm service method."""

    @pytest.mark.asyncio
    async def test_bulk_confirm_filters_by_lob(self):
        """Test bulk_confirm can filter by LOB."""
        from app.services.role_mapping_service import RoleMappingService

        # Verify method signature accepts lob parameter
        import inspect
        sig = inspect.signature(RoleMappingService.bulk_confirm)
        params = list(sig.parameters.keys())

        assert "lob" in params

    @pytest.mark.asyncio
    async def test_bulk_confirm_filters_by_mapping_ids(self):
        """Test bulk_confirm can filter by mapping_ids."""
        from app.services.role_mapping_service import RoleMappingService

        # Verify method signature accepts mapping_ids parameter
        import inspect
        sig = inspect.signature(RoleMappingService.bulk_confirm)
        params = list(sig.parameters.keys())

        assert "mapping_ids" in params


class TestBulkConfirmEndpointEnhanced:
    """Test enhanced bulk confirm endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_confirm_with_lob_filter(self):
        """Test endpoint passes lob to service."""
        from app.routers.role_mappings import bulk_confirm_mappings
        from app.schemas.role_mapping import BulkConfirmRequest

        session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.bulk_confirm.return_value = {"confirmed_count": 5}

        request = BulkConfirmRequest(
            threshold=0.85,
            lob="Technology",
        )

        await bulk_confirm_mappings(
            session_id=session_id,
            request=request,
            service=mock_service,
        )

        mock_service.bulk_confirm.assert_called_once()
        call_kwargs = mock_service.bulk_confirm.call_args.kwargs
        assert call_kwargs.get("lob") == "Technology"

    @pytest.mark.asyncio
    async def test_bulk_confirm_with_mapping_ids_filter(self):
        """Test endpoint passes mapping_ids to service."""
        from app.routers.role_mappings import bulk_confirm_mappings
        from app.schemas.role_mapping import BulkConfirmRequest

        session_id = uuid4()
        mapping_ids = [uuid4(), uuid4()]

        mock_service = AsyncMock()
        mock_service.bulk_confirm.return_value = {"confirmed_count": 2}

        request = BulkConfirmRequest(
            threshold=0.85,
            mapping_ids=mapping_ids,
        )

        await bulk_confirm_mappings(
            session_id=session_id,
            request=request,
            service=mock_service,
        )

        mock_service.bulk_confirm.assert_called_once()
        call_kwargs = mock_service.bulk_confirm.call_args.kwargs
        assert call_kwargs.get("mapping_ids") == mapping_ids
