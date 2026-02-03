"""
E2E Test Configuration and Fixtures

This module provides shared fixtures for end-to-end testing of the
Discovery Module workflow.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import os
import sys

# Add the discovery app to the path
DISCOVERY_PATH = Path(__file__).parent.parent.parent / "discovery"
sys.path.insert(0, str(DISCOVERY_PATH))


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest_asyncio.fixture
async def async_client():
    """
    Create an async HTTP client for testing.

    This fixture supports two modes:
    1. Mock mode (default): Uses in-memory mock services
    2. Live mode: Tests against running API server

    Set E2E_BASE_URL environment variable to test against a live server.
    """
    base_url = os.environ.get("E2E_BASE_URL")

    if base_url:
        # Live server testing
        async with AsyncClient(base_url=base_url, timeout=30.0) as client:
            yield client
    else:
        # Mock testing with FastAPI TestClient
        try:
            from discovery.app.main import app
            from discovery.app.dependencies import (
                get_session_service,
                get_upload_service,
                get_role_mapping_service,
                get_activity_service,
                get_analysis_service,
                get_roadmap_service,
                get_chat_service,
            )
            from tests.e2e.mocks import (
                MockSessionService,
                MockUploadService,
                MockRoleMappingService,
                MockActivityService,
                MockAnalysisService,
                MockRoadmapService,
                MockChatService,
            )

            # Override dependencies with mocks
            app.dependency_overrides[get_session_service] = lambda: MockSessionService()
            app.dependency_overrides[get_upload_service] = lambda: MockUploadService()
            app.dependency_overrides[get_role_mapping_service] = lambda: MockRoleMappingService()
            app.dependency_overrides[get_activity_service] = lambda: MockActivityService()
            app.dependency_overrides[get_analysis_service] = lambda: MockAnalysisService()
            app.dependency_overrides[get_roadmap_service] = lambda: MockRoadmapService()
            app.dependency_overrides[get_chat_service] = lambda: MockChatService()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client

            # Clean up overrides
            app.dependency_overrides.clear()

        except ImportError:
            # If app can't be imported, skip tests
            pytest.skip("Discovery app not available for testing")


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def happy_path_csv(test_data_dir) -> bytes:
    """Load the happy path test CSV."""
    csv_path = test_data_dir / "happy_path_workforce.csv"
    with open(csv_path, "rb") as f:
        return f.read()


@pytest.fixture
def malformed_csv(test_data_dir) -> bytes:
    """Load the malformed test CSV."""
    csv_path = test_data_dir / "unhappy_path_malformed.csv"
    with open(csv_path, "rb") as f:
        return f.read()


@pytest.fixture
def unmappable_roles_csv(test_data_dir) -> bytes:
    """Load the unmappable roles test CSV."""
    csv_path = test_data_dir / "unhappy_path_unmappable_roles.csv"
    with open(csv_path, "rb") as f:
        return f.read()


# =============================================================================
# Test Data Constants
# =============================================================================

TEST_ORG_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID = "00000000-0000-0000-0000-000000000002"

# Expected O*NET mappings for happy path roles
EXPECTED_ONET_MAPPINGS = {
    "Customer Service Representative": "43-4051.00",
    "Data Entry Clerk": "43-9021.00",
    "Accounts Payable Specialist": "43-3031.00",
    "HR Coordinator": "13-1071.00",
    "IT Help Desk Technician": "15-1232.00",
    "Marketing Coordinator": "13-1161.00",
}

# Roles expected to have low confidence (< 0.60)
LOW_CONFIDENCE_ROLES = [
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
