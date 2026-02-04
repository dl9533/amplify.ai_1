"""Test upload endpoint with column detection."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


def test_detected_mapping_response_schema_exists():
    """Test DetectedMappingResponse schema is defined."""
    from app.schemas.upload import DetectedMappingResponse
    assert DetectedMappingResponse is not None


def test_detected_mapping_response_fields():
    """Test DetectedMappingResponse has expected fields."""
    from app.schemas.upload import DetectedMappingResponse

    mapping = DetectedMappingResponse(
        field="role",
        column="Job Title",
        confidence=0.95,
        alternatives=["Position", "Title"],
        required=True,
    )

    assert mapping.field == "role"
    assert mapping.column == "Job Title"
    assert mapping.confidence == 0.95
    assert mapping.alternatives == ["Position", "Title"]
    assert mapping.required is True


def test_detected_mapping_response_allows_null_column():
    """Test DetectedMappingResponse allows null column."""
    from app.schemas.upload import DetectedMappingResponse

    mapping = DetectedMappingResponse(
        field="lob",
        column=None,
        confidence=0.0,
        alternatives=["Department", "Division"],
        required=False,
    )

    assert mapping.column is None


def test_upload_response_has_detected_mappings_field():
    """Test UploadResponse includes detected_mappings field."""
    from app.schemas.upload import UploadResponse
    from datetime import datetime

    # Check the field exists in the model
    fields = UploadResponse.model_fields
    assert "detected_mappings" in fields


class TestUploadWithColumnDetection:
    """Test upload endpoint returns detected columns."""

    @pytest.mark.asyncio
    async def test_upload_returns_detected_mappings(self):
        """Test that upload response includes detected column mappings."""
        from app.routers.uploads import upload_file
        from app.schemas.upload import UploadResponse
        from io import BytesIO

        # Create mock service
        mock_service = AsyncMock()
        mock_service.process_upload.return_value = {
            "id": str(uuid4()),
            "file_name": "workforce.csv",
            "row_count": 100,
            "detected_schema": ["Employee ID", "Job Title", "Department", "LOB"],
            "created_at": "2026-02-03T00:00:00",
            "preview": [
                {"Employee ID": "1", "Job Title": "Analyst", "Department": "IT", "LOB": "Tech"}
            ],
        }

        # Create mock file
        mock_file = MagicMock()
        mock_file.content_type = "text/csv"
        mock_file.filename = "test.csv"
        mock_file.read = AsyncMock(return_value=b"a,b,c\n1,2,3")

        # Call endpoint
        result = await upload_file(
            session_id=uuid4(),
            file=mock_file,
            service=mock_service,
        )

        # Verify detected_mappings in response
        assert hasattr(result, "detected_mappings")
        assert len(result.detected_mappings) == 4  # role, lob, department, geography
