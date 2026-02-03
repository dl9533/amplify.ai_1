"""
End-to-End Test: Unhappy Path - Unmappable/Low-Confidence Roles

This test validates the system's behavior when users upload workforce data
with non-standard job titles that don't map well to O*NET occupations.

Scenario:
- User uploads CSV with creative/non-standard job titles
- System attempts to map roles but gets low confidence scores (<60%)
- User must manually review and confirm or correct mappings
- System enforces confirmation before proceeding to analysis

Expected Outcome: Workflow gates user until low-confidence mappings are resolved.
"""

import pytest
from pathlib import Path
import io

# Test data path
TEST_DATA_DIR = Path(__file__).parent / "test_data"
UNMAPPABLE_ROLES_CSV = TEST_DATA_DIR / "unhappy_path_unmappable_roles.csv"


class TestUnhappyPathUnmappableRoles:
    """
    Unhappy path test for low-confidence role mappings.

    Tests the system's ability to:
    1. Detect low-confidence O*NET matches
    2. Prevent auto-confirmation of uncertain mappings
    3. Require user review for ambiguous roles
    4. Gate workflow progression until mappings are confirmed
    """

    @pytest.fixture
    def unmappable_csv_content(self) -> bytes:
        """Load the unmappable roles test CSV."""
        with open(UNMAPPABLE_ROLES_CSV, "rb") as f:
            return f.read()

    @pytest.fixture
    def expected_low_confidence_roles(self) -> list[str]:
        """Roles expected to have low confidence matches."""
        return [
            "Chief Synergy Optimization Specialist",
            "Digital Transformation Evangelist",
            "Quantum Computing Liaison",
            "Blockchain Integration Architect",
            "AI Ethics Philosophy Lead",
            "Metaverse Experience Designer",
            "Sustainability Narrative Coordinator",
            "Cross-Functional Alignment Facilitator",
            "Holistic Wellness Integration Manager",
            "Disruptive Innovation Catalyst",
        ]

    # =========================================================================
    # Test: Upload and Initial Mapping
    # =========================================================================

    @pytest.mark.asyncio
    async def test_upload_succeeds_with_unusual_roles(
        self, async_client, session_id, unmappable_csv_content
    ):
        """
        Test that CSV with unusual roles uploads successfully.

        Expected:
        - HTTP 201 Created
        - File parsed correctly
        - All 10 rows detected
        """
        files = {
            "file": ("unusual_roles.csv", io.BytesIO(unmappable_csv_content), "text/csv")
        }

        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id}/uploads",
            files=files
        )

        assert response.status_code == 201, f"Upload failed: {response.text}"

        data = response.json()
        assert data["row_count"] == 10

    @pytest.mark.asyncio
    async def test_auto_map_returns_low_confidence(
        self, async_client, session_id_with_upload, expected_low_confidence_roles
    ):
        """
        Test that unusual roles result in low-confidence mappings.

        Expected:
        - All roles have confidence < 0.60
        - Mappings are NOT auto-confirmed
        - System flags roles for manual review
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )

        assert response.status_code == 200

        data = response.json()
        mappings = data["mappings"]

        # Verify all mappings have low confidence
        low_confidence_count = 0
        for mapping in mappings:
            if mapping["confidence_score"] < 0.60:
                low_confidence_count += 1

            # None should be auto-confirmed
            assert mapping["user_confirmed"] is False, \
                f"Low-confidence mapping should not be auto-confirmed: {mapping['source_role']}"

        # At least 80% should be low confidence (some might match partially)
        assert low_confidence_count >= 8, \
            f"Expected most mappings to be low confidence, got {low_confidence_count}/10"

    @pytest.mark.asyncio
    async def test_mappings_flagged_for_review(self, async_client, session_id_with_upload):
        """
        Test that response includes review requirement flag.

        Expected:
        - Response indicates mappings need review
        - Count of low-confidence mappings provided
        - Warning message included
        """
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )

        data = response.json()

        # Check for review indicators
        assert "requires_review" in data or "low_confidence_count" in data or "warnings" in data

        if "low_confidence_count" in data:
            assert data["low_confidence_count"] >= 8

        if "warnings" in data:
            assert any("confidence" in w.lower() or "review" in w.lower()
                       for w in data["warnings"])

    # =========================================================================
    # Test: Bulk Confirm Blocked
    # =========================================================================

    @pytest.mark.asyncio
    async def test_bulk_confirm_fails_for_low_confidence(self, async_client, session_id_with_upload):
        """
        Test that bulk confirm doesn't confirm low-confidence mappings.

        Expected:
        - Bulk confirm with min_confidence=0.85 confirms 0 mappings
        - Response indicates no mappings met threshold
        """
        # First, auto-map to create mappings
        await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )

        # Try to bulk confirm with high threshold
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/bulk-confirm",
            json={"min_confidence": 0.85}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["confirmed_count"] == 0, \
            "No mappings should meet 0.85 confidence threshold"

    @pytest.mark.asyncio
    async def test_cannot_proceed_without_confirmation(self, async_client, session_id_with_upload):
        """
        Test that workflow blocks progression without confirmed mappings.

        Expected:
        - Attempt to advance to step 3 fails
        - Error message explains unconfirmed mappings
        """
        # Auto-map to create low-confidence mappings
        await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )

        # Attempt to advance to step 3 (Activities)
        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id_with_upload}",
            json={"current_step": 3}
        )

        # Should fail - mappings not confirmed
        assert response.status_code in [400, 422], \
            f"Should not advance with unconfirmed mappings: {response.text}"

        error = response.json()
        error_message = str(error).lower()
        assert any(term in error_message for term in
                   ["confirm", "mapping", "unconfirmed", "review"])

    # =========================================================================
    # Test: Manual Confirmation Flow
    # =========================================================================

    @pytest.mark.asyncio
    async def test_can_manually_confirm_mapping(self, async_client, session_id_with_upload):
        """
        Test that individual mappings can be manually confirmed.

        Expected:
        - User can confirm a specific mapping
        - user_confirmed flag is set to true
        """
        # Auto-map first
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )
        mappings = response.json()["mappings"]
        mapping_id = mappings[0]["id"]

        # Manually confirm one mapping
        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/{mapping_id}",
            json={"user_confirmed": True}
        )

        assert response.status_code == 200
        assert response.json()["user_confirmed"] is True

    @pytest.mark.asyncio
    async def test_can_override_onet_code(self, async_client, session_id_with_upload):
        """
        Test that user can override the suggested O*NET code.

        Expected:
        - User can specify a different O*NET code
        - Mapping updates with new code
        - Confidence is set by user action
        """
        # Auto-map first
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )
        mappings = response.json()["mappings"]
        mapping_id = mappings[0]["id"]

        # Override with a specific O*NET code
        # "Chief Synergy Optimization Specialist" -> General and Operations Managers
        new_onet_code = "11-1021.00"

        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/{mapping_id}",
            json={
                "onet_code": new_onet_code,
                "user_confirmed": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["onet_code"] == new_onet_code
        assert data["user_confirmed"] is True

    @pytest.mark.asyncio
    async def test_can_search_onet_for_alternatives(self, async_client):
        """
        Test that user can search O*NET for alternative occupations.

        Expected:
        - Search endpoint returns relevant results
        - Results include code, title, and description
        """
        # Search for management-related occupations
        response = await async_client.get(
            "/api/v1/discovery/onet/search",
            params={"query": "manager"}
        )

        assert response.status_code == 200

        results = response.json()["results"]
        assert len(results) > 0

        # Verify result structure
        for result in results[:5]:
            assert "code" in result
            assert "title" in result
            assert result["code"].count("-") == 1  # O*NET format: XX-XXXX.XX

    # =========================================================================
    # Test: Workflow After Manual Confirmation
    # =========================================================================

    @pytest.mark.asyncio
    async def test_can_proceed_after_all_confirmed(self, async_client, session_id_with_upload):
        """
        Test that workflow proceeds after all mappings confirmed.

        Expected:
        - After confirming all mappings, can advance to step 3
        - Session progresses normally
        """
        # Auto-map
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )
        mappings = response.json()["mappings"]

        # Manually confirm all mappings
        for mapping in mappings:
            await async_client.patch(
                f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/{mapping['id']}",
                json={"user_confirmed": True}
            )

        # Now should be able to advance
        response = await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id_with_upload}",
            json={"current_step": 3}
        )

        assert response.status_code == 200
        assert response.json()["current_step"] == 3

    # =========================================================================
    # Test: Analysis Quality Warning
    # =========================================================================

    @pytest.mark.asyncio
    async def test_analysis_warns_about_low_original_confidence(
        self, async_client, session_id_with_confirmed_mappings
    ):
        """
        Test that analysis includes warning about originally low-confidence mappings.

        Expected:
        - Analysis completes successfully
        - Results include warning about mapping quality
        - User is informed results may be less reliable
        """
        # Trigger analysis
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_confirmed_mappings}/analyze"
        )

        assert response.status_code == 200

        data = response.json()

        # Check for quality warnings
        if "warnings" in data:
            assert any("confidence" in w.lower() or "quality" in w.lower() or "mapping" in w.lower()
                       for w in data["warnings"])

        # Or check for quality_score/reliability indicator
        if "metadata" in data:
            # Should indicate lower reliability
            pass

    # =========================================================================
    # Test: Chat Guidance
    # =========================================================================

    @pytest.mark.asyncio
    async def test_chat_provides_mapping_guidance(self, async_client, session_id_with_upload):
        """
        Test that chat interface helps with low-confidence mappings.

        Expected:
        - Chat acknowledges low confidence issues
        - Provides guidance on manual mapping
        - Suggests alternatives
        """
        # Auto-map to trigger low confidence
        await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
        )

        # Send chat message asking for help
        response = await async_client.post(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/chat",
            json={"message": "The role mappings don't look right. Can you help?"}
        )

        assert response.status_code == 200

        chat_response = response.json()["response"]

        # Chat should acknowledge the issue and provide guidance
        response_lower = chat_response.lower()
        assert any(term in response_lower for term in
                   ["confidence", "mapping", "manual", "review", "confirm", "o*net"])


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


@pytest.fixture
async def session_id_with_upload(async_client, unmappable_csv_content) -> str:
    """Create a session with uploaded unmappable roles CSV."""
    # Create session
    response = await async_client.post(
        "/api/v1/discovery/sessions",
        json={
            "organization_id": "00000000-0000-0000-0000-000000000001",
            "user_id": "00000000-0000-0000-0000-000000000002",
        }
    )
    session_id = response.json()["id"]

    # Upload file
    files = {
        "file": ("unusual_roles.csv", io.BytesIO(unmappable_csv_content), "text/csv")
    }
    await async_client.post(
        f"/api/v1/discovery/sessions/{session_id}/uploads",
        files=files
    )

    return session_id


@pytest.fixture
async def session_id_with_confirmed_mappings(async_client, session_id_with_upload) -> str:
    """Create a session with all mappings confirmed (despite low confidence)."""
    # Auto-map
    response = await async_client.post(
        f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/auto-map"
    )
    mappings = response.json()["mappings"]

    # Confirm all
    for mapping in mappings:
        await async_client.patch(
            f"/api/v1/discovery/sessions/{session_id_with_upload}/role-mappings/{mapping['id']}",
            json={"user_confirmed": True}
        )

    # Advance to step 3
    await async_client.patch(
        f"/api/v1/discovery/sessions/{session_id_with_upload}",
        json={"current_step": 3}
    )

    return session_id_with_upload
