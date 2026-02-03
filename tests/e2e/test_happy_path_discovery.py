"""
End-to-End Test: Happy Path - Standard Discovery Workflow

This test validates the complete discovery workflow with clean, well-formatted
workforce data that maps cleanly to O*NET occupations.

Scenario:
- User uploads a clean workforce CSV with standard job titles
- Roles map to O*NET occupations with high confidence (>85%)
- Activities are selected based on AI exposure scores
- Analysis generates scores across multiple dimensions
- Roadmap produces prioritized agentification candidates

Expected Outcome: Full workflow completes successfully with meaningful results.
"""

import pytest
from pathlib import Path
from uuid import UUID
import io

# Test data path
TEST_DATA_DIR = Path(__file__).parent / "test_data"
HAPPY_PATH_CSV = TEST_DATA_DIR / "happy_path_workforce.csv"


class TestHappyPathDiscovery:
    """
    Happy path end-to-end test for the Discovery workflow.

    Tests the complete 5-step wizard:
    1. Upload - Ingest workforce CSV
    2. Map Roles - Match to O*NET occupations
    3. Select Activities - Choose relevant DWAs
    4. Analyze - Calculate scores
    5. Roadmap - Generate candidates
    """

    @pytest.fixture
    def test_csv_content(self) -> bytes:
        """Load the happy path test CSV."""
        with open(HAPPY_PATH_CSV, "rb") as f:
            return f.read()

    @pytest.fixture
    def expected_roles(self) -> list[str]:
        """Expected unique roles from the test data."""
        return [
            "Customer Service Representative",
            "Data Entry Clerk",
            "Accounts Payable Specialist",
            "HR Coordinator",
            "IT Help Desk Technician",
            "Marketing Coordinator",
        ]

    @pytest.fixture
    def expected_onet_mappings(self) -> dict[str, str]:
        """Expected O*NET occupation codes for each role."""
        return {
            "Customer Service Representative": "43-4051.00",  # Customer Service Representatives
            "Data Entry Clerk": "43-9021.00",  # Data Entry Keyers
            "Accounts Payable Specialist": "43-3031.00",  # Bookkeeping, Accounting, and Auditing Clerks
            "HR Coordinator": "13-1071.00",  # Human Resources Specialists
            "IT Help Desk Technician": "15-1232.00",  # Computer User Support Specialists
            "Marketing Coordinator": "13-1161.00",  # Market Research Analysts
        }

    # =========================================================================
    # STEP 1: Session Creation
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step1_create_session(self, async_client):
        """
        Step 1a: Create a new discovery session.

        Expected:
        - HTTP 201 Created
        - Session ID returned (UUID)
        - Status = DRAFT
        - Current step = 1
        """
        response = await async_client.post(
            "/api/v1/discovery/sessions",
            json={
                "organization_id": "00000000-0000-0000-0000-000000000001",
                "user_id": "00000000-0000-0000-0000-000000000002",
            }
        )

        assert response.status_code == 201, f"Failed to create session: {response.text}"

        data = response.json()
        assert "id" in data
        assert UUID(data["id"])  # Valid UUID
        assert data["status"] == "draft"
        assert data["current_step"] == 1

        return data["id"]

    # =========================================================================
    # STEP 2: File Upload
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step2_upload_csv(self, async_client, session_id, test_csv_content):
        """
        Step 2a: Upload workforce CSV file.

        Expected:
        - HTTP 201 Created
        - File stored in S3
        - Column mappings auto-detected
        - Schema detected with correct types
        """
        files = {
            "file": ("workforce.csv", io.BytesIO(test_csv_content), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 201, f"Failed to upload: {response.text}"

        data = response.json()
        assert data["file_name"] == "workforce.csv"
        assert data["row_count"] == 10
        assert "column_mappings" in data

        # Verify auto-detection of columns
        mappings = data["column_mappings"]
        assert mappings.get("role") == "job_title"
        assert mappings.get("department") == "department"
        assert mappings.get("geography") == "location"

        return data["id"]

    @pytest.mark.asyncio
    async def test_step2_verify_schema_detection(self, async_client, session_id, upload_id):
        """
        Step 2b: Verify schema was correctly detected.

        Expected:
        - Columns detected with correct types
        - Unique values extracted for role column
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/uploads/{upload_id}/schema"
        )

        assert response.status_code == 200

        schema = response.json()
        assert "columns" in schema

        # Verify column types
        column_types = {col["name"]: col["type"] for col in schema["columns"]}
        assert column_types["employee_id"] == "string"
        assert column_types["headcount"] == "integer"

    # =========================================================================
    # STEP 3: Role Mapping
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step3_auto_map_roles(
        self, async_client, session_id, expected_roles, expected_onet_mappings
    ):
        """
        Step 3a: Automatically map roles to O*NET occupations.

        Expected:
        - All 6 unique roles detected
        - High confidence matches (>85%) for standard job titles
        - Correct O*NET codes suggested
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/role-mappings/auto-map"
        )

        assert response.status_code == 200, f"Auto-map failed: {response.text}"

        data = response.json()
        mappings = data["mappings"]

        # Verify all roles were detected
        mapped_roles = {m["source_role"] for m in mappings}
        assert mapped_roles == set(expected_roles)

        # Verify high confidence for standard job titles
        for mapping in mappings:
            role = mapping["source_role"]
            assert mapping["confidence_score"] >= 0.85, \
                f"Low confidence for '{role}': {mapping['confidence_score']}"

            # Verify correct O*NET code (if available)
            if role in expected_onet_mappings:
                assert mapping["onet_code"] == expected_onet_mappings[role], \
                    f"Wrong O*NET code for '{role}'"

    @pytest.mark.asyncio
    async def test_step3_confirm_all_mappings(self, async_client, session_id):
        """
        Step 3b: Bulk confirm all high-confidence mappings.

        Expected:
        - All mappings with confidence >= 0.85 are confirmed
        - user_confirmed = true for confirmed mappings
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/role-mappings/bulk-confirm",
            json={"min_confidence": 0.85}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["confirmed_count"] == 6  # All roles should be high confidence

    @pytest.mark.asyncio
    async def test_step3_advance_to_activities(self, async_client, session_id):
        """
        Step 3c: Advance session to Step 3 (Activities).

        Expected:
        - Session advances to step 3
        - Status changes to IN_PROGRESS
        """
        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id}",
            json={"current_step": 3}
        )

        assert response.status_code == 200
        assert response.json()["current_step"] == 3
        assert response.json()["status"] == "in_progress"

    # =========================================================================
    # STEP 4: Activity Selection
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step4_load_activities(self, async_client, session_id):
        """
        Step 4a: Load Detailed Work Activities (DWAs) for mapped roles.

        Expected:
        - DWAs loaded for each O*NET occupation
        - Activities grouped by GWA (Generalized Work Activity)
        - Default selections based on AI exposure scores
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/activities"
        )

        assert response.status_code == 200

        data = response.json()
        assert "activities_by_role" in data

        # Verify activities loaded for each role
        for role, activities in data["activities_by_role"].items():
            assert len(activities) > 0, f"No activities for role '{role}'"

            # Verify structure
            for activity in activities:
                assert "dwa_id" in activity
                assert "dwa_name" in activity
                assert "gwa_name" in activity
                assert "ai_exposure_score" in activity
                assert 0 <= activity["ai_exposure_score"] <= 1

    @pytest.mark.asyncio
    async def test_step4_select_high_exposure_activities(self, async_client, session_id):
        """
        Step 4b: Select activities with high AI exposure scores.

        Expected:
        - Activities with exposure >= 0.6 are selected
        - Selection persisted to database
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/activities/auto-select",
            json={"min_exposure": 0.6}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["selected_count"] > 0
        assert data["total_count"] >= data["selected_count"]

    # =========================================================================
    # STEP 5: Analysis
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step5_trigger_analysis(self, async_client, session_id):
        """
        Step 5a: Trigger analysis to calculate scores.

        Expected:
        - Analysis runs successfully
        - Scores calculated for all dimensions
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/analyze"
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_step5_verify_role_scores(self, async_client, session_id):
        """
        Step 5b: Verify scores calculated by role dimension.

        Expected:
        - Each role has ai_exposure, impact, complexity, priority scores
        - All scores in range [0, 1]
        - Higher exposure roles have higher priority
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/analysis",
            params={"dimension": "role"}
        )

        assert response.status_code == 200

        results = response.json()["results"]
        assert len(results) == 6  # 6 unique roles

        for result in results:
            # Verify all scores present and in range
            assert 0 <= result["ai_exposure_score"] <= 1
            assert 0 <= result["impact_score"] <= 1
            assert 0 <= result["complexity_score"] <= 1
            assert 0 <= result["priority_score"] <= 1

            # Verify breakdown details
            assert "breakdown" in result

    @pytest.mark.asyncio
    async def test_step5_verify_department_aggregation(self, async_client, session_id):
        """
        Step 5c: Verify scores aggregated by department.

        Expected:
        - Departments from CSV are represented
        - Scores weighted by headcount
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/analysis",
            params={"dimension": "department"}
        )

        assert response.status_code == 200

        results = response.json()["results"]
        departments = {r["dimension_value"] for r in results}

        expected_departments = {
            "Customer Support", "Operations", "Finance",
            "Human Resources", "IT", "Marketing"
        }
        assert departments == expected_departments

    # =========================================================================
    # STEP 6: Roadmap
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step6_generate_roadmap(self, async_client, session_id):
        """
        Step 6a: Generate agentification candidates from analysis.

        Expected:
        - Candidates created based on priority scores
        - Priority tiers assigned (NOW/NEXT_QUARTER/FUTURE)
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/roadmap/generate"
        )

        assert response.status_code == 200

        data = response.json()
        assert "candidates" in data
        assert len(data["candidates"]) > 0

    @pytest.mark.asyncio
    async def test_step6_verify_priority_tiers(self, async_client, session_id):
        """
        Step 6b: Verify candidates are properly tiered.

        Expected:
        - NOW: priority >= 0.75, complexity < 0.3
        - NEXT_QUARTER: priority >= 0.60
        - FUTURE: priority < 0.60
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/roadmap"
        )

        assert response.status_code == 200

        candidates = response.json()["candidates"]

        for candidate in candidates:
            tier = candidate["priority_tier"]
            priority = candidate["priority_score"]

            if tier == "now":
                assert priority >= 0.75
            elif tier == "next_quarter":
                assert priority >= 0.60
            else:
                assert tier == "future"

    @pytest.mark.asyncio
    async def test_step6_select_for_build(self, async_client, session_id):
        """
        Step 6c: Select top candidates for Build handoff.

        Expected:
        - Candidates can be selected for build
        - selected_for_build flag updated
        """
        # Get candidates
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/roadmap"
        )
        candidates = response.json()["candidates"]

        # Select top 3 candidates
        top_candidates = [c["id"] for c in candidates[:3]]

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/roadmap/select",
            json={"candidate_ids": top_candidates}
        )

        assert response.status_code == 200
        assert response.json()["selected_count"] == 3

    # =========================================================================
    # STEP 7: Handoff & Export
    # =========================================================================

    @pytest.mark.asyncio
    async def test_step7_create_handoff_bundle(self, async_client, session_id):
        """
        Step 7a: Create handoff bundle for Build system.

        Expected:
        - Bundle contains all session data
        - Selected candidates included
        - Ready for intake process
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/handoff"
        )

        assert response.status_code == 200

        bundle = response.json()
        assert "session_id" in bundle
        assert "candidates" in bundle
        assert "analysis_summary" in bundle
        assert len(bundle["candidates"]) == 3  # Selected candidates

    @pytest.mark.asyncio
    async def test_step7_export_results(self, async_client, session_id):
        """
        Step 7b: Export results as CSV.

        Expected:
        - CSV export contains all analysis results
        - Properly formatted for external use
        """
        response = await async_client.get(
            f"/api/v1/discovery/sessions/{session_id}/exports/csv"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"

    @pytest.mark.asyncio
    async def test_step7_complete_session(self, async_client, session_id):
        """
        Step 7c: Mark session as completed.

        Expected:
        - Session status = COMPLETED
        - All steps marked complete
        """
        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id}",
            json={"status": "completed"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


# =============================================================================
# Fixtures for test orchestration
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


@pytest.fixture
async def upload_id(async_client, session_id, test_csv_content) -> str:
    """Upload test file and return upload ID."""
    files = {
        "file": ("workforce.csv", io.BytesIO(test_csv_content), "text/csv")
    }
    response = await async_client.post(
        f"/api/v1/discovery/sessions/{session_id}/uploads",
        files=files
    )
    return response.json()["id"]
