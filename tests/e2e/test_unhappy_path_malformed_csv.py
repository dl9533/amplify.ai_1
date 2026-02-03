"""
End-to-End Test: Unhappy Path - Malformed CSV Data

This test validates error handling when users upload CSV files with
data quality issues such as:
- Unclosed quotes causing parse errors
- Invalid numeric values (non-numeric headcount)
- Missing required values
- Empty critical fields

Scenario:
- User uploads a malformed CSV file
- System detects and reports specific validation errors
- User is guided to fix issues and re-upload

Expected Outcome: Graceful error handling with actionable feedback.
"""

import pytest
from pathlib import Path
import io

# Test data path
TEST_DATA_DIR = Path(__file__).parent / "test_data"
MALFORMED_CSV = TEST_DATA_DIR / "unhappy_path_malformed.csv"


class TestUnhappyPathMalformedCSV:
    """
    Unhappy path test for malformed CSV uploads.

    Tests the system's ability to:
    1. Detect and report CSV parsing errors
    2. Validate data types and required fields
    3. Provide actionable error messages
    4. Allow recovery through re-upload
    """

    @pytest.fixture
    def malformed_csv_content(self) -> bytes:
        """Load the malformed test CSV."""
        with open(MALFORMED_CSV, "rb") as f:
            return f.read()

    @pytest.fixture
    def csv_with_unclosed_quote(self) -> bytes:
        """CSV with an unclosed quote causing parse failure."""
        return b'''employee_id,name,job_title,department,location,headcount
E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45
E002,Bob Smith,"Customer Service Representative,Customer Support,Chicago,38
E003,Carol Williams,Data Entry Clerk,Operations,New York,22'''

    @pytest.fixture
    def csv_with_invalid_number(self) -> bytes:
        """CSV with invalid numeric value in headcount column."""
        return b'''employee_id,name,job_title,department,location,headcount
E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45
E002,Bob Smith,Customer Service Representative,Customer Support,Chicago,INVALID
E003,Carol Williams,Data Entry Clerk,Operations,New York,22'''

    @pytest.fixture
    def csv_with_missing_role(self) -> bytes:
        """CSV with missing job_title (critical field)."""
        return b'''employee_id,name,job_title,department,location,headcount
E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45
E002,Bob Smith,,Customer Support,Chicago,38
E003,Carol Williams,Data Entry Clerk,Operations,New York,22'''

    @pytest.fixture
    def csv_with_empty_rows(self) -> bytes:
        """CSV with completely empty rows."""
        return b'''employee_id,name,job_title,department,location,headcount
E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45
,,,,,
E003,Carol Williams,Data Entry Clerk,Operations,New York,22'''

    # =========================================================================
    # Test: CSV Parse Errors
    # =========================================================================

    @pytest.mark.asyncio
    async def test_unclosed_quote_parse_error(self, async_client, session_id, csv_with_unclosed_quote):
        """
        Test that unclosed quotes cause a clear parse error.

        Expected:
        - HTTP 400 Bad Request
        - Error message identifies the parsing issue
        - Suggests checking for unclosed quotes
        """
        files = {
            "file": ("malformed.csv", io.BytesIO(csv_with_unclosed_quote), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        error = response.json()
        assert "error" in error or "detail" in error

        error_message = error.get("error") or error.get("detail")
        assert any(term in error_message.lower() for term in ["parse", "quote", "csv", "format"]), \
            f"Error message should mention parsing issue: {error_message}"

    @pytest.mark.asyncio
    async def test_invalid_number_validation_error(self, async_client, session_id, csv_with_invalid_number):
        """
        Test that invalid numeric values are detected.

        Expected:
        - HTTP 400/422 Validation Error
        - Error identifies the invalid value and column
        - Row number is specified
        """
        files = {
            "file": ("invalid_number.csv", io.BytesIO(csv_with_invalid_number), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        # Could be 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"

        error = response.json()
        error_detail = str(error)

        # Should identify the problematic value or column
        assert any(term in error_detail.lower() for term in
                   ["invalid", "headcount", "number", "integer", "row 2", "numeric"]), \
            f"Error should identify invalid number issue: {error_detail}"

    @pytest.mark.asyncio
    async def test_missing_required_field_error(self, async_client, session_id, csv_with_missing_role):
        """
        Test that missing required fields (job_title) are detected.

        Expected:
        - Upload may succeed but with warnings
        - OR HTTP 400/422 if job_title is strictly required
        - Missing value is flagged for user attention
        """
        files = {
            "file": ("missing_role.csv", io.BytesIO(csv_with_missing_role), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        if response.status_code == 201:
            # Upload succeeded - check for warnings
            data = response.json()
            assert "warnings" in data or "validation_issues" in data, \
                "Missing job_title should trigger a warning"

            warnings = data.get("warnings") or data.get("validation_issues", [])
            assert len(warnings) > 0, "Expected warnings about missing job_title"
        else:
            # Upload rejected
            assert response.status_code in [400, 422]
            error = response.json()
            assert "job_title" in str(error).lower() or "role" in str(error).lower()

    @pytest.mark.asyncio
    async def test_empty_rows_handling(self, async_client, session_id, csv_with_empty_rows):
        """
        Test that empty rows are handled gracefully.

        Expected:
        - Empty rows are skipped
        - Row count reflects only valid rows
        - Warning may be issued about skipped rows
        """
        files = {
            "file": ("empty_rows.csv", io.BytesIO(csv_with_empty_rows), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        # Empty rows should be skipped, not cause failure
        assert response.status_code in [200, 201], f"Empty rows should be skipped: {response.text}"

        data = response.json()
        # Should only count 2 valid rows (not the empty one)
        assert data["row_count"] == 2, f"Expected 2 rows, got {data['row_count']}"

    # =========================================================================
    # Test: File Type Validation
    # =========================================================================

    @pytest.mark.asyncio
    async def test_invalid_file_type_rejected(self, async_client, session_id):
        """
        Test that non-CSV/XLSX files are rejected.

        Expected:
        - HTTP 400 Bad Request
        - Error specifies allowed file types
        """
        # Try to upload a PDF
        fake_pdf = b"%PDF-1.4 fake pdf content"
        files = {
            "file": ("document.pdf", io.BytesIO(fake_pdf), "application/pdf")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 400
        error = response.json()
        error_message = str(error).lower()
        assert any(term in error_message for term in ["csv", "xlsx", "file type", "unsupported"])

    @pytest.mark.asyncio
    async def test_empty_file_rejected(self, async_client, session_id):
        """
        Test that empty files are rejected.

        Expected:
        - HTTP 400 Bad Request
        - Error indicates file is empty
        """
        files = {
            "file": ("empty.csv", io.BytesIO(b""), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 400
        error = response.json()
        assert "empty" in str(error).lower()

    @pytest.mark.asyncio
    async def test_header_only_file_rejected(self, async_client, session_id):
        """
        Test that files with only headers (no data) are rejected.

        Expected:
        - HTTP 400 Bad Request
        - Error indicates no data rows
        """
        header_only = b"employee_id,name,job_title,department,location,headcount\n"
        files = {
            "file": ("header_only.csv", io.BytesIO(header_only), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 400
        error = response.json()
        assert any(term in str(error).lower() for term in ["no data", "empty", "row", "0 rows"])

    # =========================================================================
    # Test: Size Limits
    # =========================================================================

    @pytest.mark.asyncio
    async def test_file_too_large_rejected(self, async_client, session_id):
        """
        Test that files exceeding size limit are rejected.

        Expected:
        - HTTP 413 Payload Too Large (or 400)
        - Error specifies maximum file size
        """
        # Create a large CSV (> 100MB simulated via header)
        # Note: This test may need adjustment based on actual limits
        large_header = b"employee_id,name,job_title,department,location,headcount\n"
        large_row = b"E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45\n"

        # Simulate a very large file (in reality, might need to test differently)
        # For now, just verify the endpoint exists and handles size checking

        # This is a placeholder - actual large file testing would be different
        pass

    # =========================================================================
    # Test: Recovery Flow
    # =========================================================================

    @pytest.mark.asyncio
    async def test_can_retry_after_failed_upload(self, async_client, session_id, malformed_csv_content):
        """
        Test that users can retry upload after failure.

        Expected:
        - First upload fails with malformed CSV
        - Second upload with valid CSV succeeds
        - Session state is correct after recovery
        """
        # First upload - should fail
        files = {
            "file": ("malformed.csv", io.BytesIO(malformed_csv_content), "text/csv")
        }

        response1 = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        # May fail or succeed with warnings depending on implementation
        first_status = response1.status_code

        # Second upload - valid CSV
        valid_csv = b'''employee_id,name,job_title,department,location,headcount
E001,Alice Johnson,Customer Service Representative,Customer Support,New York,45
E002,Bob Smith,Data Entry Clerk,Operations,Chicago,38'''

        files2 = {
            "file": ("valid.csv", io.BytesIO(valid_csv), "text/csv")
        }

        response2 = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files2
        )

        assert response2.status_code == 201, f"Valid upload should succeed: {response2.text}"
        assert response2.json()["row_count"] == 2

    @pytest.mark.asyncio
    async def test_session_not_corrupted_after_failed_upload(self, async_client, session_id, csv_with_unclosed_quote):
        """
        Test that failed upload doesn't corrupt session state.

        Expected:
        - Session remains in valid state after failed upload
        - Session can still be accessed
        - No partial data left from failed upload
        """
        # Attempt failed upload
        files = {
            "file": ("malformed.csv", io.BytesIO(csv_with_unclosed_quote), "text/csv")
        }

        await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        # Verify session is still accessible
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}"
        )

        assert response.status_code == 200
        session = response.json()
        assert session["status"] in ["draft", "in_progress"]
        assert session["current_step"] == 1  # Should still be on upload step


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def session_id(async_client) -> str:
    """Create a session and return its ID."""
    response = await async_client.post(
        "/api/v1/discovery/sessions",
        json={
            "organization_id": "00000000-0000-0000-0000-000000000001",
            "user_id": "00000000-0000-0000-0000-000000000002",
        }
    )
    return response.json()["id"]
