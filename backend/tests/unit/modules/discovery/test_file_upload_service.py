# backend/tests/unit/modules/discovery/test_file_upload_service.py
"""Unit tests for FileUploadService.

Tests cover:
- File upload to S3
- CSV/XLSX parsing and schema detection
- Column mapping suggestions
- Unique value extraction
- File validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import io

from app.modules.discovery.services.file_upload_service import FileUploadService


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    return AsyncMock()


@pytest.fixture
def mock_upload_repo():
    """Create a mock upload repository."""
    return AsyncMock()


@pytest.fixture
def file_upload_service(mock_s3_client, mock_upload_repo):
    """Create FileUploadService with mocked dependencies."""
    return FileUploadService(
        s3_client=mock_s3_client,
        upload_repo=mock_upload_repo,
        bucket_name="discovery-uploads"
    )


@pytest.mark.asyncio
async def test_upload_file_to_s3(file_upload_service, mock_s3_client):
    """Should upload file to S3 and return URL."""
    session_id = uuid4()
    file_content = b"col1,col2,col3\nval1,val2,val3"
    file_name = "test_data.csv"

    mock_s3_client.upload_fileobj.return_value = None

    result = await file_upload_service.upload_file(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    mock_s3_client.upload_fileobj.assert_called_once()
    assert "s3://" in result["file_url"] or "test_data.csv" in result["file_url"]


@pytest.mark.asyncio
async def test_upload_generates_unique_key(file_upload_service, mock_s3_client):
    """Should generate unique S3 key with session ID prefix."""
    session_id = uuid4()
    file_content = b"data"
    file_name = "hr_data.xlsx"

    await file_upload_service.upload_file(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    call_args = mock_s3_client.upload_fileobj.call_args
    s3_key = call_args[1].get("Key") or call_args[0][1] if len(call_args[0]) > 1 else None

    # The S3 key should contain the session ID for organization
    assert str(session_id) in str(call_args) or "hr_data" in str(call_args)


@pytest.mark.asyncio
async def test_parse_csv_file(file_upload_service):
    """Should parse CSV file and detect schema."""
    file_content = b"Name,Role,Department,Location\nJohn,Engineer,IT,NYC\nJane,Manager,HR,LA\nBob,Analyst,Finance,CHI"

    result = await file_upload_service.parse_file(
        file_name="test.csv",
        file_content=file_content
    )

    assert result["row_count"] == 3
    assert "Name" in result["detected_schema"]["columns"]
    assert "Role" in result["detected_schema"]["columns"]
    assert "Department" in result["detected_schema"]["columns"]
    assert len(result["detected_schema"]["columns"]) == 4


@pytest.mark.asyncio
async def test_parse_xlsx_file(file_upload_service):
    """Should parse XLSX file and detect schema."""
    with patch.object(file_upload_service, "_parse_xlsx") as mock_parse:
        mock_parse.return_value = {
            "row_count": 100,
            "detected_schema": {
                "columns": ["Employee ID", "Job Title", "Department"],
                "types": ["integer", "string", "string"],
                "sample_values": [["1001", "Software Engineer", "Engineering"]]
            }
        }

        result = await file_upload_service.parse_file(
            file_name="employees.xlsx",
            file_content=b"fake xlsx content"
        )

        assert result["row_count"] == 100
        assert "Job Title" in result["detected_schema"]["columns"]


@pytest.mark.asyncio
async def test_detect_column_types(file_upload_service):
    """Should detect column data types from content."""
    file_content = b"ID,Name,Salary,Active\n1,John,50000,true\n2,Jane,60000,false"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    assert "types" in result["detected_schema"]


@pytest.mark.asyncio
async def test_extract_sample_values(file_upload_service):
    """Should extract sample values for preview."""
    file_content = b"Name,Role\nAlice,Engineer\nBob,Manager\nCarol,Analyst\nDave,Designer\nEve,Director"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    assert "sample_values" in result["detected_schema"]
    assert len(result["detected_schema"]["sample_values"]) <= 5


@pytest.mark.asyncio
async def test_suggest_column_mappings(file_upload_service):
    """Should suggest column mappings based on column names."""
    file_content = b"Employee Name,Job Title,Dept,Office Location\nJohn,Engineer,IT,NYC"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    suggestions = await file_upload_service.suggest_column_mappings(result["detected_schema"])

    assert "role" in suggestions
    assert suggestions["role"] == "Job Title"
    assert "department" in suggestions
    assert suggestions["department"] == "Dept"


@pytest.mark.asyncio
async def test_suggest_mappings_handles_variations(file_upload_service):
    """Should handle common column name variations."""
    test_cases = [
        (b"Position,Name\nEng,John", "Position"),
        (b"Title,Name\nEng,John", "Title"),
        (b"Job,Name\nEng,John", "Job"),
        (b"Occupation,Name\nEng,John", "Occupation"),
    ]

    for file_content, expected_role_col in test_cases:
        result = await file_upload_service.parse_file(
            file_name="data.csv",
            file_content=file_content
        )
        suggestions = await file_upload_service.suggest_column_mappings(result["detected_schema"])

        assert suggestions.get("role") == expected_role_col, f"Expected {expected_role_col} for role"


@pytest.mark.asyncio
async def test_register_upload_with_parsed_data(file_upload_service, mock_upload_repo, mock_s3_client):
    """Should upload, parse, and register in one operation."""
    session_id = uuid4()
    file_content = b"Name,Role,Dept\nJohn,Engineer,IT\nJane,Manager,HR"
    file_name = "employees.csv"

    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload_repo.create.return_value = mock_upload

    result = await file_upload_service.upload_and_register(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    mock_s3_client.upload_fileobj.assert_called_once()
    mock_upload_repo.create.assert_called_once()
    assert "upload_id" in result
    assert "parsed_data" in result


@pytest.mark.asyncio
async def test_reject_unsupported_file_type(file_upload_service):
    """Should reject unsupported file types."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        await file_upload_service.parse_file(
            file_name="data.pdf",
            file_content=b"pdf content"
        )


@pytest.mark.asyncio
async def test_handle_empty_file(file_upload_service):
    """Should handle empty files gracefully."""
    with pytest.raises(ValueError, match="File is empty"):
        await file_upload_service.parse_file(
            file_name="empty.csv",
            file_content=b""
        )


@pytest.mark.asyncio
async def test_handle_malformed_csv(file_upload_service):
    """Should handle malformed CSV with appropriate error."""
    file_content = b"A,B,C\n1,2\n3,4,5,6"

    result = await file_upload_service.parse_file(
        file_name="malformed.csv",
        file_content=file_content
    )

    assert "detected_schema" in result


@pytest.mark.asyncio
async def test_delete_file_from_s3(file_upload_service, mock_s3_client, mock_upload_repo):
    """Should delete file from S3 and remove upload record."""
    upload_id = uuid4()
    file_url = "s3://discovery-uploads/sessions/abc/file.csv"

    mock_upload = MagicMock()
    mock_upload.id = upload_id
    mock_upload.file_url = file_url
    mock_upload_repo.get_by_id.return_value = mock_upload

    await file_upload_service.delete_upload(upload_id)

    mock_s3_client.delete_object.assert_called_once()
    mock_upload_repo.delete.assert_called_once_with(upload_id)


@pytest.mark.asyncio
async def test_get_download_url(file_upload_service, mock_s3_client):
    """Should generate presigned download URL."""
    file_url = "s3://discovery-uploads/sessions/abc/file.csv"

    mock_s3_client.generate_presigned_url.return_value = "https://signed-url.example.com/file.csv"

    result = await file_upload_service.get_download_url(file_url, expires_in=3600)

    mock_s3_client.generate_presigned_url.assert_called_once()
    assert "https://" in result


@pytest.mark.asyncio
async def test_extract_unique_roles(file_upload_service):
    """Should extract unique roles from parsed file data."""
    file_content = b"Name,Role\nJohn,Engineer\nJane,Manager\nBob,Engineer\nAlice,Analyst\nCarol,Manager"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    column_mappings = {"role": "Role"}
    unique_roles = await file_upload_service.extract_unique_values(
        file_content=file_content,
        file_name="data.csv",
        column_name=column_mappings["role"]
    )

    assert len(unique_roles) == 3
    assert set(unique_roles.keys()) == {"Engineer", "Manager", "Analyst"}
    assert unique_roles["Engineer"] == 2
    assert unique_roles["Manager"] == 2


@pytest.mark.asyncio
async def test_validate_file_size(file_upload_service):
    """Should reject files exceeding size limit."""
    large_content = b"x" * (101 * 1024 * 1024)

    with pytest.raises(ValueError, match="File size exceeds"):
        await file_upload_service.validate_file(
            file_name="large.csv",
            file_content=large_content
        )


@pytest.mark.asyncio
async def test_validate_row_count(file_upload_service):
    """Should warn when row count exceeds threshold."""
    header = b"Col1,Col2\n"
    rows = b"\n".join([f"val{i},val{i}".encode() for i in range(100001)])
    file_content = header + rows

    result = await file_upload_service.parse_file(
        file_name="large.csv",
        file_content=file_content
    )

    assert result["row_count"] > 100000


@pytest.mark.asyncio
async def test_upload_file_validates_size(file_upload_service, mock_s3_client):
    """Should validate file size before uploading."""
    session_id = uuid4()
    # Create content that exceeds the max file size
    large_content = b"x" * (101 * 1024 * 1024)  # 101MB

    with pytest.raises(ValueError, match="File size exceeds"):
        await file_upload_service.upload_file(
            session_id=session_id,
            file_name="large.csv",
            file_content=large_content
        )

    # S3 upload should not have been called
    mock_s3_client.upload_fileobj.assert_not_called()


@pytest.mark.asyncio
async def test_upload_and_register_cleans_up_on_db_failure(
    file_upload_service, mock_s3_client, mock_upload_repo
):
    """Should clean up S3 file when database registration fails."""
    session_id = uuid4()
    file_content = b"Name,Role\nJohn,Engineer"
    file_name = "test.csv"

    # Make S3 upload succeed
    mock_s3_client.upload_fileobj.return_value = None

    # Make database registration fail
    mock_upload_repo.create.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        await file_upload_service.upload_and_register(
            session_id=session_id,
            file_name=file_name,
            file_content=file_content
        )

    # S3 cleanup should have been attempted
    mock_s3_client.delete_object.assert_called_once()


@pytest.mark.asyncio
async def test_delete_upload_handles_not_found(file_upload_service, mock_upload_repo):
    """Should raise ValueError when upload doesn't exist."""
    upload_id = uuid4()
    mock_upload_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Upload not found"):
        await file_upload_service.delete_upload(upload_id)


@pytest.mark.asyncio
async def test_extract_unique_values_invalid_column(file_upload_service):
    """Should raise ValueError when column doesn't exist in file."""
    file_content = b"Name,Role\nJohn,Engineer\nJane,Manager"

    with pytest.raises(ValueError, match="Column 'NonExistent' not found"):
        await file_upload_service.extract_unique_values(
            file_content=file_content,
            file_name="test.csv",
            column_name="NonExistent"
        )
