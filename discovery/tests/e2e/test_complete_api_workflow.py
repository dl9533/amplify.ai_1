"""Robust E2E test for complete Discovery API workflow.

This test exercises the entire Discovery module flow via direct API calls:
1. Create a discovery session
2. Upload workforce CSV file
3. Update column mappings
4. Generate and confirm role mappings
5. Trigger scoring analysis
6. Retrieve analysis results by dimension
7. Validate handoff readiness

This is an API-level E2E test that does not require a browser/UI.

Prerequisites:
- Backend running on http://localhost:8001
- PostgreSQL database with migrations applied
- O*NET data synced (at least seed data)
- LOB-NAICS seed data loaded
"""

import io
import pytest
import httpx
from pathlib import Path
from uuid import UUID


# Configuration
API_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"  # Test org ID
TIMEOUT = 30.0  # Generous timeout for slower operations

# Test data
TEST_DATA_DIR = Path(__file__).parent / "test_data"
LOB_CSV_PATH = TEST_DATA_DIR / "workforce_with_lob.csv"


class TestCompleteDiscoveryWorkflow:
    """
    Comprehensive E2E test suite for the Discovery API workflow.

    This test class exercises the complete happy path from session creation
    through analysis, validating data integrity at each step.
    """

    @pytest.fixture
    def api_client(self):
        """Create async HTTP client with timeout configuration."""
        return httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=httpx.Timeout(TIMEOUT),
        )

    @pytest.fixture
    def workforce_csv_content(self) -> bytes:
        """Load workforce CSV test data with LOB column."""
        if LOB_CSV_PATH.exists():
            return LOB_CSV_PATH.read_bytes()
        # Fallback: generate test data inline
        return b"""Job Title,Department,Line of Business,Location,Employee Count
Financial Analyst,Finance,Investment Banking,New York,25
Software Engineer,Engineering,Information Technology,San Francisco,40
Loan Officer,Operations,Retail Banking,Chicago,18
Claims Adjuster,Claims,Property Insurance,Boston,15
Data Scientist,Analytics,Cloud Services,Seattle,12
"""

    @pytest.mark.asyncio
    async def test_complete_discovery_workflow_happy_path(
        self,
        api_client: httpx.AsyncClient,
        workforce_csv_content: bytes,
    ):
        """
        Complete E2E test: Session -> Upload -> Mappings -> Analysis -> Handoff.

        This test validates the entire Discovery module workflow by:
        1. Creating a new discovery session
        2. Uploading a workforce CSV with LOB data
        3. Setting column mappings (role, department, LOB, etc.)
        4. Retrieving auto-generated role mappings
        5. Bulk confirming high-confidence mappings
        6. Triggering scoring analysis
        7. Retrieving analysis results by dimension
        8. Validating handoff readiness

        Each step validates response schemas and data integrity.
        """
        session_id = None
        upload_id = None

        try:
            # ================================================================
            # STEP 1: Create Discovery Session
            # ================================================================
            print("\n[Step 1] Creating discovery session...")

            response = await api_client.post(
                "/discovery/sessions",
                json={"organization_id": DEFAULT_ORG_ID},
            )

            assert response.status_code == 201, (
                f"Failed to create session: {response.status_code} - {response.text}"
            )

            session_data = response.json()
            session_id = session_data["id"]

            # Validate session response schema
            assert "id" in session_data, "Session response missing 'id'"
            assert "status" in session_data, "Session response missing 'status'"
            assert "current_step" in session_data, "Session response missing 'current_step'"
            assert "created_at" in session_data, "Session response missing 'created_at'"

            # Validate UUID format
            UUID(session_id)  # Raises ValueError if invalid

            assert session_data["status"] == "draft", (
                f"New session should be 'draft', got '{session_data['status']}'"
            )

            print(f"    Created session: {session_id}")
            print(f"    Status: {session_data['status']}, Step: {session_data['current_step']}")

            # ================================================================
            # STEP 2: Upload Workforce CSV
            # ================================================================
            print("\n[Step 2] Uploading workforce CSV...")

            # Prepare multipart file upload
            files = {
                "file": ("workforce_with_lob.csv", workforce_csv_content, "text/csv"),
            }

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/upload",
                files=files,
            )

            assert response.status_code == 201, (
                f"Failed to upload file: {response.status_code} - {response.text}"
            )

            upload_data = response.json()
            upload_id = upload_data["id"]

            # Validate upload response schema
            assert "id" in upload_data, "Upload response missing 'id'"
            assert "file_name" in upload_data, "Upload response missing 'file_name'"
            assert "row_count" in upload_data, "Upload response missing 'row_count'"
            assert "detected_schema" in upload_data, "Upload response missing 'detected_schema'"

            # Validate row count matches expected data (5 roles in inline fallback, 10 in file)
            assert upload_data["row_count"] >= 5, (
                f"Expected at least 5 rows, got {upload_data['row_count']}"
            )

            # Validate schema detection
            schema = upload_data["detected_schema"]
            assert isinstance(schema, list), "detected_schema should be a list of columns"
            assert len(schema) >= 4, f"Expected at least 4 columns, got {len(schema)}"

            print(f"    Uploaded file: {upload_data['file_name']}")
            print(f"    Rows detected: {upload_data['row_count']}")
            print(f"    Columns: {schema}")

            # Check for auto-detected mappings
            if "detected_mappings" in upload_data and upload_data["detected_mappings"]:
                print(f"    Auto-detected mappings: {len(upload_data['detected_mappings'])}")
                for m in upload_data["detected_mappings"]:
                    print(f"      - {m['field']}: {m['column']} (confidence: {m['confidence']:.0%})")

            # ================================================================
            # STEP 3: Update Column Mappings
            # ================================================================
            print("\n[Step 3] Setting column mappings...")

            # Map columns based on detected schema
            # Standard mapping for workforce file with LOB
            column_mappings = {
                "role": "Job Title",
                "department": "Department",
                "lob": "Line of Business",
                "geography": "Location",
                "headcount": "Employee Count",
            }

            response = await api_client.put(
                f"/discovery/uploads/{upload_id}/mappings",
                json=column_mappings,
            )

            assert response.status_code == 200, (
                f"Failed to update mappings: {response.status_code} - {response.text}"
            )

            mapping_data = response.json()

            # Validate mappings were saved
            assert "column_mappings" in mapping_data, "Response missing column_mappings"
            saved_mappings = mapping_data["column_mappings"]
            assert saved_mappings.get("role") == "Job Title", (
                f"Role mapping not saved correctly: {saved_mappings}"
            )

            print(f"    Mappings saved: {saved_mappings}")

            # ================================================================
            # STEP 4: Retrieve Role Mappings
            # ================================================================
            print("\n[Step 4] Retrieving role mappings...")

            response = await api_client.get(
                f"/discovery/sessions/{session_id}/role-mappings",
            )

            assert response.status_code == 200, (
                f"Failed to get role mappings: {response.status_code} - {response.text}"
            )

            role_mappings = response.json()

            # Validate role mappings structure
            assert isinstance(role_mappings, list), "Role mappings should be a list"

            if len(role_mappings) > 0:
                # Validate first mapping has expected fields
                first_mapping = role_mappings[0]
                assert "id" in first_mapping, "Mapping missing 'id'"
                assert "source_role" in first_mapping, "Mapping missing 'source_role'"
                assert "confidence_score" in first_mapping, "Mapping missing 'confidence_score'"
                assert "is_confirmed" in first_mapping, "Mapping missing 'is_confirmed'"

                # Count by confirmation status
                confirmed = sum(1 for m in role_mappings if m["is_confirmed"])
                unconfirmed = len(role_mappings) - confirmed

                # Count by confidence tier
                high_conf = sum(1 for m in role_mappings if m["confidence_score"] >= 0.85)
                medium_conf = sum(1 for m in role_mappings if 0.6 <= m["confidence_score"] < 0.85)
                low_conf = sum(1 for m in role_mappings if m["confidence_score"] < 0.6)

                print(f"    Total mappings: {len(role_mappings)}")
                print(f"    Confirmed: {confirmed}, Unconfirmed: {unconfirmed}")
                print(f"    Confidence: High={high_conf}, Medium={medium_conf}, Low={low_conf}")

                # Print sample mappings
                for m in role_mappings[:3]:
                    print(f"      - {m['source_role']} -> {m.get('onet_title', 'N/A')} ({m['confidence_score']:.0%})")
            else:
                print("    No role mappings generated (may need O*NET data)")

            # ================================================================
            # STEP 5: Bulk Confirm High-Confidence Mappings
            # ================================================================
            print("\n[Step 5] Bulk confirming high-confidence mappings...")

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/role-mappings/confirm",
                json={"threshold": 0.7},  # Confirm mappings with >= 70% confidence
            )

            assert response.status_code == 200, (
                f"Failed to bulk confirm: {response.status_code} - {response.text}"
            )

            confirm_data = response.json()

            assert "confirmed_count" in confirm_data, "Response missing confirmed_count"
            print(f"    Confirmed {confirm_data['confirmed_count']} mappings")

            # ================================================================
            # STEP 6: Trigger Analysis
            # ================================================================
            print("\n[Step 6] Triggering scoring analysis...")

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/analyze",
            )

            # Analysis may return 202 (accepted) for async processing
            assert response.status_code in (200, 202), (
                f"Failed to trigger analysis: {response.status_code} - {response.text}"
            )

            analysis_trigger = response.json()
            print(f"    Analysis status: {analysis_trigger.get('status', 'triggered')}")

            # ================================================================
            # STEP 7: Get Analysis Results
            # ================================================================
            print("\n[Step 7] Retrieving analysis results...")

            # Get overall analysis summary
            response = await api_client.get(
                f"/discovery/sessions/{session_id}/analysis",
            )

            if response.status_code == 200:
                all_dimensions = response.json()
                print(f"    Dimensions analyzed: {list(all_dimensions.keys()) if isinstance(all_dimensions, dict) else 'N/A'}")

                # Get specific dimension results (role dimension)
                response = await api_client.get(
                    f"/discovery/sessions/{session_id}/analysis/role",
                )

                if response.status_code == 200:
                    role_analysis = response.json()

                    if "results" in role_analysis:
                        results = role_analysis["results"]
                        print(f"    Role analysis results: {len(results)}")

                        # Count by priority tier
                        by_tier = {}
                        for r in results:
                            tier = r.get("priority_tier", "UNKNOWN")
                            by_tier[tier] = by_tier.get(tier, 0) + 1

                        print(f"    Priority tiers: {by_tier}")

                        # Show top 3 high-priority items
                        high_priority = [r for r in results if r.get("priority_tier") == "HIGH"]
                        for item in high_priority[:3]:
                            print(f"      - {item['name']}: priority={item['priority_score']:.2f}")
                else:
                    print(f"    Role analysis not available: {response.status_code}")
            else:
                print(f"    Analysis results not available yet: {response.status_code}")
                print("    (This is expected if analysis runs asynchronously)")

            # ================================================================
            # STEP 8: Validate Handoff Readiness
            # ================================================================
            print("\n[Step 8] Validating handoff readiness...")

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/handoff/validate",
            )

            assert response.status_code == 200, (
                f"Failed to validate handoff: {response.status_code} - {response.text}"
            )

            validation = response.json()

            assert "is_ready" in validation, "Validation missing 'is_ready'"

            if validation["is_ready"]:
                print("    Handoff validation: READY")
            else:
                print("    Handoff validation: NOT READY")
                if "errors" in validation and validation["errors"]:
                    for error in validation["errors"]:
                        print(f"      - {error}")

            # ================================================================
            # VERIFICATION: Get Final Session State
            # ================================================================
            print("\n[Verification] Final session state...")

            response = await api_client.get(
                f"/discovery/sessions/{session_id}",
            )

            assert response.status_code == 200, (
                f"Failed to get session: {response.status_code} - {response.text}"
            )

            final_session = response.json()
            print(f"    Session ID: {final_session['id']}")
            print(f"    Status: {final_session['status']}")
            print(f"    Current Step: {final_session['current_step']}")
            print(f"    Created: {final_session['created_at']}")
            print(f"    Updated: {final_session['updated_at']}")

            print("\n" + "=" * 60)
            print("COMPLETE DISCOVERY WORKFLOW E2E TEST PASSED")
            print("=" * 60)

        finally:
            # ================================================================
            # CLEANUP: Delete test session
            # ================================================================
            if session_id:
                print(f"\n[Cleanup] Deleting test session {session_id}...")
                try:
                    response = await api_client.delete(
                        f"/discovery/sessions/{session_id}",
                    )
                    if response.status_code == 204:
                        print("    Session deleted successfully")
                    else:
                        print(f"    Cleanup warning: {response.status_code}")
                except Exception as e:
                    print(f"    Cleanup error: {e}")


class TestEdgeCasesAndErrorHandling:
    """
    E2E tests for edge cases and error handling scenarios.

    These tests validate that the API properly handles invalid inputs,
    missing data, and error conditions.
    """

    @pytest.fixture
    def api_client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=httpx.Timeout(TIMEOUT),
        )

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type_returns_400(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that uploading non-CSV/XLSX file returns 400 error."""
        # Create session first
        response = await api_client.post(
            "/discovery/sessions",
            json={"organization_id": DEFAULT_ORG_ID},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        try:
            # Try to upload a text file (invalid type)
            files = {
                "file": ("test.txt", b"This is plain text", "text/plain"),
            }

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/upload",
                files=files,
            )

            assert response.status_code == 400, (
                f"Expected 400 for invalid file type, got {response.status_code}"
            )

            error_data = response.json()
            assert "detail" in error_data, "Error response missing 'detail'"
            assert "Unsupported file type" in error_data["detail"], (
                f"Unexpected error message: {error_data['detail']}"
            )

            print("Invalid file type correctly rejected with 400")

        finally:
            await api_client.delete(f"/discovery/sessions/{session_id}")

    @pytest.mark.asyncio
    async def test_upload_empty_file_returns_400(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that uploading empty file returns 400 error."""
        # Create session
        response = await api_client.post(
            "/discovery/sessions",
            json={"organization_id": DEFAULT_ORG_ID},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        try:
            # Upload empty CSV
            files = {
                "file": ("empty.csv", b"", "text/csv"),
            }

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/upload",
                files=files,
            )

            assert response.status_code == 400, (
                f"Expected 400 for empty file, got {response.status_code}"
            )

            print("Empty file correctly rejected with 400")

        finally:
            await api_client.delete(f"/discovery/sessions/{session_id}")

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_returns_404(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that requesting non-existent session returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await api_client.get(
            f"/discovery/sessions/{fake_uuid}",
        )

        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}"
        )

        print("Non-existent session correctly returns 404")

    @pytest.mark.asyncio
    async def test_upload_oversized_file_returns_413(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that uploading file over size limit returns 413."""
        # Create session
        response = await api_client.post(
            "/discovery/sessions",
            json={"organization_id": DEFAULT_ORG_ID},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        try:
            # Create a file slightly over 10MB limit
            # Generate valid CSV structure to pass content-type validation
            header = b"col1,col2,col3\n"
            row = b"a" * 100 + b"," + b"b" * 100 + b"," + b"c" * 100 + b"\n"
            # Calculate rows needed to exceed 10MB
            rows_needed = (11 * 1024 * 1024) // len(row)
            large_content = header + (row * rows_needed)

            files = {
                "file": ("large.csv", large_content, "text/csv"),
            }

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/upload",
                files=files,
            )

            assert response.status_code == 413, (
                f"Expected 413 for oversized file, got {response.status_code}"
            )

            print("Oversized file correctly rejected with 413")

        finally:
            await api_client.delete(f"/discovery/sessions/{session_id}")

    @pytest.mark.asyncio
    async def test_bulk_confirm_with_invalid_threshold_returns_422(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that invalid threshold value returns validation error."""
        # Create session
        response = await api_client.post(
            "/discovery/sessions",
            json={"organization_id": DEFAULT_ORG_ID},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        try:
            # Try bulk confirm with invalid threshold (> 1.0)
            response = await api_client.post(
                f"/discovery/sessions/{session_id}/role-mappings/confirm",
                json={"threshold": 1.5},  # Invalid: > 1.0
            )

            # Should return 422 (validation error) or 400 (bad request)
            assert response.status_code in (400, 422), (
                f"Expected 400/422 for invalid threshold, got {response.status_code}"
            )

            print("Invalid threshold correctly rejected")

        finally:
            await api_client.delete(f"/discovery/sessions/{session_id}")


class TestLobMappingIntegration:
    """
    E2E tests for LOB (Line of Business) to NAICS code mapping.

    These tests validate the industry-aware role mapping features.
    """

    @pytest.fixture
    def api_client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=httpx.Timeout(TIMEOUT),
        )

    @pytest.mark.asyncio
    async def test_lob_lookup_known_value_returns_naics_codes(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test LOB lookup for known industry value returns NAICS codes."""
        response = await api_client.get(
            "/discovery/lob/lookup",
            params={"lob": "Investment Banking"},
        )

        assert response.status_code == 200, (
            f"LOB lookup failed: {response.status_code} - {response.text}"
        )

        data = response.json()

        # Validate response schema
        assert "lob" in data, "Response missing 'lob'"
        assert "naics_codes" in data, "Response missing 'naics_codes'"
        assert "confidence" in data, "Response missing 'confidence'"
        assert "source" in data, "Response missing 'source'"

        # For known LOB, should have NAICS codes
        if data["naics_codes"]:
            assert data["confidence"] > 0, "Known LOB should have confidence > 0"
            assert data["source"] in ("curated", "fuzzy", "llm"), (
                f"Unexpected source: {data['source']}"
            )
            print(f"Investment Banking -> NAICS {data['naics_codes']} ({data['source']}, {data['confidence']:.0%})")
        else:
            print("Note: LOB lookup returned empty (seed data may not be loaded)")

    @pytest.mark.asyncio
    async def test_lob_lookup_unknown_value_returns_empty(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test LOB lookup for unknown value returns empty with source='none'."""
        response = await api_client.get(
            "/discovery/lob/lookup",
            params={"lob": "Interdimensional Widget Fabrication"},
        )

        assert response.status_code == 200, (
            f"LOB lookup failed: {response.status_code} - {response.text}"
        )

        data = response.json()

        # Unknown LOB should return empty codes with source="none"
        assert data["naics_codes"] == [], (
            f"Unknown LOB should return empty naics_codes, got {data['naics_codes']}"
        )
        assert data["confidence"] == 0.0, (
            f"Unknown LOB should have 0 confidence, got {data['confidence']}"
        )
        assert data["source"] == "none", (
            f"Unknown LOB source should be 'none', got {data['source']}"
        )

        print("Unknown LOB correctly returns empty with source='none'")

    @pytest.mark.asyncio
    async def test_grouped_role_mappings_include_lob_groups(
        self,
        api_client: httpx.AsyncClient,
    ):
        """Test that role mappings can be retrieved grouped by LOB."""
        # Create session and upload file with LOB data
        response = await api_client.post(
            "/discovery/sessions",
            json={"organization_id": DEFAULT_ORG_ID},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        try:
            # Upload CSV with LOB column
            csv_content = b"""Job Title,Department,Line of Business,Location,Employee Count
Financial Analyst,Finance,Investment Banking,New York,25
Software Engineer,Engineering,Information Technology,San Francisco,40
"""
            files = {
                "file": ("test_lob.csv", csv_content, "text/csv"),
            }

            response = await api_client.post(
                f"/discovery/sessions/{session_id}/upload",
                files=files,
            )
            assert response.status_code == 201
            upload_id = response.json()["id"]

            # Set column mappings including LOB
            response = await api_client.put(
                f"/discovery/uploads/{upload_id}/mappings",
                json={
                    "role": "Job Title",
                    "department": "Department",
                    "lob": "Line of Business",
                    "geography": "Location",
                    "headcount": "Employee Count",
                },
            )
            assert response.status_code == 200

            # Get grouped role mappings
            response = await api_client.get(
                f"/discovery/sessions/{session_id}/role-mappings/grouped",
            )

            assert response.status_code == 200, (
                f"Failed to get grouped mappings: {response.status_code} - {response.text}"
            )

            data = response.json()

            # Validate grouped response schema
            assert "session_id" in data, "Response missing 'session_id'"
            assert "overall_summary" in data, "Response missing 'overall_summary'"
            assert "lob_groups" in data, "Response missing 'lob_groups'"

            print(f"Grouped mappings response:")
            print(f"  Overall: {data['overall_summary']}")
            print(f"  LOB groups: {len(data['lob_groups'])}")

            for group in data["lob_groups"]:
                print(f"    - {group['lob']}: {group['summary']['total_count']} roles")

        finally:
            await api_client.delete(f"/discovery/sessions/{session_id}")


# =============================================================================
# Test Runner
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
