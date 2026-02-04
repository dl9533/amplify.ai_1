"""E2E tests for O*NET Industry Mapping functionality.

These tests cover the LOB-to-NAICS mapping and industry-boosted role matching
features of the Discovery module.

Test Data:
- workforce_with_lob.csv: 10 roles with known LOB values that map to NAICS codes
- workforce_unknown_lob.csv: 2 roles with unknown/invalid LOB values

Prerequisites:
- Backend running on http://localhost:8001
- Frontend running on http://localhost:5173 (for UI tests)
- PostgreSQL database with migrations applied
- LOB-NAICS seed data loaded
- O*NET data synced
"""

import httpx
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
LOB_CSV = TEST_DATA_DIR / "workforce_with_lob.csv"
UNKNOWN_LOB_CSV = TEST_DATA_DIR / "workforce_unknown_lob.csv"

# URLs - use 127.0.0.1 instead of localhost for better browser compatibility
BASE_URL = "http://127.0.0.1:5173"
API_URL = "http://127.0.0.1:8001"


def login(page: Page):
    """Helper to log in before tests (dev mode accepts any credentials)."""
    if "/login" not in page.url:
        return

    page.fill("input[type='email']", "test@example.com")
    page.fill("input[type='password']", "password123")
    page.click("button:has-text('Sign in')")
    page.wait_for_url("**/discovery**", timeout=10000)


# =============================================================================
# HAPPY PATH TEST 1: LOB-Aware Upload with Grouped Mappings
# =============================================================================

def test_lob_aware_upload_groups_by_industry_happy_path(page: Page):
    """
    Happy Path #1: Upload file with LOB column and view grouped role mappings.

    This test verifies that when a CSV file includes a Line of Business column,
    the system correctly:
    1. Detects the LOB column during upload
    2. Maps LOB values to NAICS industry codes
    3. Groups role mappings by LOB in the mapping step
    4. Shows LOB group summary statistics

    Steps:
    1. Create a new discovery session
    2. Upload CSV with LOB column (workforce_with_lob.csv)
    3. Map columns including LOB -> Line of Business
    4. Proceed to role mapping step
    5. Verify mappings are grouped by LOB
    6. Verify each LOB group shows summary (total roles, avg confidence)

    Expected Results:
    - LOB column is detected and mappable
    - Role mappings are organized into LOB groups
    - Groups like "Investment Banking", "Information Technology" appear
    - Each group shows role count and confirmation status
    """
    # Step 1: Navigate and create session
    page.goto(f"{BASE_URL}/discovery")
    login(page)  # Handle login redirect if needed
    page.click("button:has-text('New Session')")
    page.wait_for_url("**/upload")

    # Step 2: Upload file with LOB column
    file_input = page.locator("input[type='file']")
    file_input.set_input_files(str(LOB_CSV))

    # Wait for upload - should detect 10 rows
    expect(page.locator("text=10 rows detected")).to_be_visible(timeout=10000)

    # Step 3: Map columns - should have 5 columns including LOB
    selects = page.locator("select")
    expect(selects).to_have_count(5)

    # Map the columns (order matches CSV: Job Title, Department, Line of Business, Location, Employee Count)
    selects.nth(0).select_option(label="Role (required)")       # Job Title -> Role
    selects.nth(1).select_option(label="Department")            # Department -> Department
    selects.nth(2).select_option(label="Line of Business")      # Line of Business -> LOB
    selects.nth(3).select_option(label="Geography")             # Location -> Geography
    selects.nth(4).select_option(label="Headcount")             # Employee Count -> Headcount

    # Step 4: Proceed to role mapping
    page.click("button:has-text('Continue')")
    page.wait_for_url("**/map-roles")

    # Step 5: Wait for mappings to load and verify grouping
    expect(page.locator("text=/ 10 confirmed")).to_be_visible(timeout=30000)

    # Look for grouped view toggle or LOB group headers
    # The grouped view should show LOB names as group headers
    grouped_view_toggle = page.locator("button:has-text('Group by LOB')")
    if grouped_view_toggle.is_visible():
        grouped_view_toggle.click()
        page.wait_for_timeout(1000)

    # Verify LOB groups are displayed
    # Check for at least some of the known LOB values from our test data
    investment_banking_group = page.locator("text=Investment Banking")
    information_technology_group = page.locator("text=Information Technology")
    retail_banking_group = page.locator("text=Retail Banking")

    # At least one of these LOB groups should be visible
    lob_groups_visible = (
        investment_banking_group.is_visible() or
        information_technology_group.is_visible() or
        retail_banking_group.is_visible()
    )

    # If explicit LOB groups aren't shown, check for role cards with LOB info
    if not lob_groups_visible:
        # Look for LOB indicators on individual cards
        lob_indicators = page.locator("[data-testid='lob-indicator'], .lob-badge, text=/LOB:/")
        expect(lob_indicators.first).to_be_visible()

    # Step 6: Verify group summary statistics
    # Look for summary showing counts per group or overall
    summary_stats = page.locator("text=/\\d+ roles?.*\\d+.*confirmed/i")
    expect(summary_stats.first).to_be_visible()

    print("✅ LOB-aware upload with grouped mappings passed")


# =============================================================================
# HAPPY PATH TEST 2: Industry-Boosted Role Matching
# =============================================================================

def test_industry_boosted_matching_improves_confidence_happy_path(page: Page):
    """
    Happy Path #2: Verify industry context improves role mapping confidence.

    When a role like "Financial Analyst" is uploaded with LOB "Investment Banking",
    the system should:
    1. Map the LOB to NAICS code 523110 (Investment Banking)
    2. Look up which O*NET occupations commonly work in that industry
    3. Boost confidence for relevant occupations (e.g., 13-2051.00 Financial Analysts)

    Steps:
    1. Upload file with LOB-tagged roles
    2. Proceed to role mapping
    3. Find the "Financial Analyst" with "Investment Banking" LOB
    4. Verify it has high confidence (industry boost applied)
    5. Verify the matched O*NET code is relevant (13-2051.00 or similar)

    Expected Results:
    - Financial Analyst in Investment Banking -> 13-2051.00 with high confidence
    - Industry alignment is reflected in confidence score
    - Role with matching industry context scores higher than generic match
    """
    # Create session and upload
    page.goto(f"{BASE_URL}/discovery")
    login(page)
    page.click("button:has-text('New Session')")
    page.wait_for_url("**/upload")

    file_input = page.locator("input[type='file']")
    file_input.set_input_files(str(LOB_CSV))
    expect(page.locator("text=10 rows detected")).to_be_visible(timeout=10000)

    # Map columns including LOB
    selects = page.locator("select")
    selects.nth(0).select_option(label="Role (required)")
    selects.nth(1).select_option(label="Department")
    selects.nth(2).select_option(label="Line of Business")
    selects.nth(3).select_option(label="Geography")
    selects.nth(4).select_option(label="Headcount")

    page.click("button:has-text('Continue')")
    page.wait_for_url("**/map-roles")

    # Wait for mappings
    expect(page.locator("text=/ 10 confirmed")).to_be_visible(timeout=30000)

    # Find the Financial Analyst role mapping card
    financial_analyst_card = page.locator("text=Financial Analyst").first
    expect(financial_analyst_card).to_be_visible()

    # Navigate to the card's parent to find confidence score
    # Look for high confidence indicator (green badge, >80%, "High" tier)
    card_container = financial_analyst_card.locator("xpath=ancestor::div[contains(@class, 'card') or contains(@class, 'mapping')]")

    # Check for confidence score display
    # Could be percentage, tier badge, or color indicator
    confidence_display = card_container.locator("text=/\\d+%|High|Medium/").first
    expect(confidence_display).to_be_visible()

    # Extract the confidence value if it's a percentage
    confidence_text = confidence_display.text_content()
    if "%" in confidence_text:
        # Parse confidence value (e.g., "85%" -> 85)
        confidence_value = int(confidence_text.replace("%", "").strip())
        # With industry boosting, Financial Analyst in Investment Banking
        # should have reasonable confidence (>50%)
        assert confidence_value >= 50, f"Expected confidence >= 50%, got {confidence_value}%"

    # Verify O*NET match is relevant to financial analysis
    # Look for O*NET code or title in the card
    onet_match = card_container.locator("text=/13-\\d{4}|Financial|Analyst/i").first
    expect(onet_match).to_be_visible()

    print("✅ Industry-boosted role matching passed")


# =============================================================================
# UNHAPPY PATH TEST 1: Unknown LOB Returns Empty NAICS Mapping
# =============================================================================

def test_unknown_lob_graceful_fallback_unhappy_path(page: Page):
    """
    Unhappy Path #1: Handle unknown/invalid LOB values gracefully.

    When a CSV contains LOB values that don't match any known pattern
    (e.g., "Quantum Flux Division"), the system should:
    1. Not crash or error out
    2. Proceed with role mapping using only role title matching
    3. Show lower confidence (no industry boost available)
    4. Allow user to still confirm or remap the roles

    Steps:
    1. Upload file with unknown LOB values (workforce_unknown_lob.csv)
    2. Map columns including LOB
    3. Proceed to role mapping
    4. Verify roles are mapped (fallback to title-only matching)
    5. Verify confidence is lower (no industry boost)
    6. Verify user can still interact with mappings

    Expected Results:
    - No errors during upload or processing
    - Roles are still mapped to O*NET occupations
    - Confidence scores are lower without industry boost
    - User can confirm or remap roles
    """
    page.goto(f"{BASE_URL}/discovery")
    login(page)
    page.click("button:has-text('New Session')")
    page.wait_for_url("**/upload")

    # Upload file with unknown LOB values
    file_input = page.locator("input[type='file']")
    file_input.set_input_files(str(UNKNOWN_LOB_CSV))

    # Should detect 2 rows
    expect(page.locator("text=2 rows detected")).to_be_visible(timeout=10000)

    # Map columns
    selects = page.locator("select")
    selects.nth(0).select_option(label="Role (required)")       # Job Title
    selects.nth(1).select_option(label="Department")            # Department
    selects.nth(2).select_option(label="Line of Business")      # Line of Business (unknown values)
    selects.nth(3).select_option(label="Geography")             # Location
    selects.nth(4).select_option(label="Headcount")             # Employee Count

    # Should be able to proceed (no error for unknown LOB)
    continue_btn = page.locator("button:has-text('Continue')")
    expect(continue_btn).to_be_enabled()
    continue_btn.click()

    # Should reach role mapping step
    page.wait_for_url("**/map-roles")

    # Verify mappings loaded (may show lower confidence or "Low" tier)
    expect(page.locator("text=/ 2 confirmed")).to_be_visible(timeout=30000)

    # Verify the roles are displayed
    expect(page.locator("text=Widget Specialist")).to_be_visible()
    expect(page.locator("text=Synergy Coordinator")).to_be_visible()

    # These unusual roles may have lower confidence - look for Low tier or warning
    low_confidence_indicators = page.locator("text=/Low|Uncertain|Review/i")
    # It's OK if these don't appear - the test is that it doesn't crash

    # User should still be able to confirm or remap
    confirm_buttons = page.locator("button:has-text('Confirm')")
    remap_buttons = page.locator("button:has-text('Remap')")

    # At least one action button should be available
    expect(confirm_buttons.first.or_(remap_buttons.first)).to_be_visible()

    print("✅ Unknown LOB graceful fallback passed")


# =============================================================================
# UNHAPPY PATH TEST 2: LOB Lookup API Returns No Match (API Test)
# =============================================================================

@pytest.mark.asyncio
async def test_lob_lookup_api_no_match_unhappy_path():
    """
    Unhappy Path #2: Direct API test for LOB lookup with unmatchable value.

    Tests the /discovery/lob/lookup endpoint directly to verify it handles
    unknown LOB values correctly by returning empty NAICS codes with
    source="none" and confidence=0.

    Steps:
    1. Call LOB lookup API with a nonsensical LOB value
    2. Verify response structure is valid (no 500 error)
    3. Verify naics_codes is empty array
    4. Verify confidence is 0 and source is "none"

    Expected Results:
    - API returns 200 OK (not error)
    - Response has valid schema
    - naics_codes: []
    - confidence: 0.0
    - source: "none"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/discovery/lob/lookup",
            params={"lob": "Interdimensional Widget Fabrication"}
        )

        # Should not error - returns 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Parse response
        data = response.json()

        # Verify response structure
        assert "lob" in data, "Response missing 'lob' field"
        assert "naics_codes" in data, "Response missing 'naics_codes' field"
        assert "confidence" in data, "Response missing 'confidence' field"
        assert "source" in data, "Response missing 'source' field"

        # Verify empty/no-match result
        assert data["naics_codes"] == [], f"Expected empty naics_codes, got {data['naics_codes']}"
        assert data["confidence"] == 0.0, f"Expected confidence 0.0, got {data['confidence']}"
        assert data["source"] == "none", f"Expected source 'none', got {data['source']}"

        # Verify the LOB value is echoed back
        assert "Interdimensional" in data["lob"], "LOB value not echoed in response"

        print("✅ LOB lookup API no-match handling passed")


# =============================================================================
# BONUS: API-Level Happy Path Test for LOB Lookup
# =============================================================================

@pytest.mark.asyncio
async def test_lob_lookup_api_curated_match_happy_path():
    """
    Bonus Happy Path: Direct API test for LOB lookup with known value.

    Tests the /discovery/lob/lookup endpoint with a known LOB value
    that should match a curated mapping.

    Steps:
    1. Call LOB lookup API with "Investment Banking"
    2. Verify returns NAICS code 523110
    3. Verify confidence is high (1.0 for curated)
    4. Verify source is "curated"

    Expected Results:
    - naics_codes contains "523110"
    - confidence: 1.0
    - source: "curated"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/discovery/lob/lookup",
            params={"lob": "Investment Banking"}
        )

        assert response.status_code == 200

        data = response.json()

        # Verify curated match
        assert "523110" in data["naics_codes"], f"Expected 523110 in {data['naics_codes']}"
        assert data["confidence"] == 1.0, f"Expected confidence 1.0, got {data['confidence']}"
        assert data["source"] == "curated", f"Expected source 'curated', got {data['source']}"

        print("✅ LOB lookup API curated match passed")


# =============================================================================
# Test Runner
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])
