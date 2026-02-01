"""Integration tests for the complete discovery flow.

These tests verify the end-to-end API contracts work correctly
by mocking the service layer and testing actual HTTP endpoints.
"""
import io
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.handoff import HandoffResponse, HandoffStatus, ValidationResult
from app.services.session_service import SessionService, get_session_service
from app.services.upload_service import UploadService, get_upload_service
from app.services.role_mapping_service import (
    RoleMappingService,
    OnetService,
    get_role_mapping_service,
    get_onet_service,
)
from app.services.activity_service import ActivityService, get_activity_service
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.services.roadmap_service import RoadmapService, get_roadmap_service
from app.services.handoff_service import HandoffService, get_handoff_service
from app.services.chat_service import ChatService, get_chat_service
from app.services.export_service import ExportService, get_export_service


# Test data constants
TEST_ORG_ID = uuid4()
TEST_SESSION_ID = uuid4()
TEST_UPLOAD_ID = uuid4()
TEST_MAPPING_ID = uuid4()
TEST_ACTIVITY_ID = uuid4()
TEST_ROADMAP_ITEM_ID = uuid4()
TEST_INTAKE_REQUEST_ID = uuid4()


def _now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class MockSessionService(SessionService):
    """Mock session service for testing."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    async def create(self, organization_id: UUID) -> dict:
        session_id = str(uuid4())
        now = _now_iso()
        session = {
            "id": session_id,
            "organization_id": str(organization_id),
            "status": "draft",
            "current_step": 1,
            "created_at": now,
            "updated_at": now,
        }
        self._sessions[session_id] = session
        return session

    async def get_by_id(self, session_id: UUID) -> Optional[dict]:
        return self._sessions.get(str(session_id))

    async def list_for_user(self, page: int = 1, per_page: int = 20) -> dict:
        items = list(self._sessions.values())
        start = (page - 1) * per_page
        end = start + per_page
        return {
            "items": items[start:end],
            "total": len(items),
            "page": page,
            "per_page": per_page,
        }

    async def update_step(self, session_id: UUID, step: int) -> Optional[dict]:
        session = self._sessions.get(str(session_id))
        if session:
            session["current_step"] = step
            session["updated_at"] = _now_iso()
            if step > 1:
                session["status"] = "in_progress"
        return session

    async def delete(self, session_id: UUID) -> bool:
        sid = str(session_id)
        if sid in self._sessions:
            del self._sessions[sid]
            return True
        return False


class MockUploadService(UploadService):
    """Mock upload service for testing."""

    def __init__(self):
        self._uploads: dict[str, dict] = {}

    async def process_upload(
        self,
        session_id: UUID,
        file_name: str,
        content: bytes,
    ) -> dict:
        upload_id = str(uuid4())
        # Parse CSV content to detect schema
        lines = content.decode("utf-8").strip().split("\n")
        headers = lines[0].split(",") if lines else []
        row_count = len(lines) - 1 if len(lines) > 1 else 0

        upload = {
            "id": upload_id,
            "session_id": str(session_id),
            "file_name": file_name,
            "row_count": row_count,
            "detected_schema": headers,
            "created_at": _now_iso(),
            "column_mappings": None,
        }
        self._uploads[upload_id] = upload
        return upload

    async def get_by_session_id(self, session_id: UUID) -> list[dict]:
        return [
            u for u in self._uploads.values()
            if u.get("session_id") == str(session_id)
        ]

    async def update_column_mappings(
        self,
        upload_id: UUID,
        mappings: dict[str, Optional[str]],
    ) -> Optional[dict]:
        upload = self._uploads.get(str(upload_id))
        if upload:
            upload["column_mappings"] = mappings
        return upload


class MockRoleMappingService(RoleMappingService):
    """Mock role mapping service for testing."""

    def __init__(self):
        self._mappings: dict[str, dict] = {}
        # Pre-populate with test data
        mapping_id = str(TEST_MAPPING_ID)
        self._mappings[mapping_id] = {
            "id": mapping_id,
            "session_id": str(TEST_SESSION_ID),
            "source_role": "Software Engineer",
            "onet_code": "15-1252.00",
            "onet_title": "Software Developers",
            "confidence_score": 0.92,
            "is_confirmed": False,
        }

    async def get_by_session_id(self, session_id: UUID) -> list[dict]:
        return [
            m for m in self._mappings.values()
            if m.get("session_id") == str(session_id)
        ]

    async def update(
        self,
        mapping_id: UUID,
        onet_code: Optional[str] = None,
        onet_title: Optional[str] = None,
        is_confirmed: Optional[bool] = None,
    ) -> Optional[dict]:
        mapping = self._mappings.get(str(mapping_id))
        if mapping:
            if onet_code is not None:
                mapping["onet_code"] = onet_code
            if onet_title is not None:
                mapping["onet_title"] = onet_title
            if is_confirmed is not None:
                mapping["is_confirmed"] = is_confirmed
        return mapping

    async def bulk_confirm(self, session_id: UUID, threshold: float) -> dict:
        count = 0
        for mapping in self._mappings.values():
            if (
                mapping.get("session_id") == str(session_id)
                and mapping.get("confidence_score", 0) >= threshold
            ):
                mapping["is_confirmed"] = True
                count += 1
        return {"confirmed_count": count}


class MockOnetService(OnetService):
    """Mock O*NET service for testing."""

    async def search(self, query: str) -> list[dict]:
        return [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.95},
            {"code": "15-1253.00", "title": "Software Quality Assurance Analysts", "score": 0.85},
        ]

    async def get_occupation(self, code: str) -> Optional[dict]:
        if code == "15-1252.00":
            return {
                "code": "15-1252.00",
                "title": "Software Developers",
                "description": "Develop and test software applications.",
                "gwas": ["4.A.2.a.4", "4.A.2.b.2"],
            }
        return None


class MockActivityService(ActivityService):
    """Mock activity service for testing."""

    def __init__(self):
        self._activities: dict[str, dict] = {}
        # Pre-populate with test data
        activity_id = str(TEST_ACTIVITY_ID)
        self._activities[activity_id] = {
            "id": activity_id,
            "session_id": str(TEST_SESSION_ID),
            "code": "4.A.2.a.4",
            "title": "Analyzing Data",
            "description": "Identify patterns and trends",
            "selected": True,
            "gwa_code": "4.A.2.a",
        }

    async def get_activities_by_session(
        self,
        session_id: UUID,
        include_unselected: bool = True,
    ) -> Optional[list[dict]]:
        activities = [
            a for a in self._activities.values()
            if a.get("session_id") == str(session_id)
            and (include_unselected or a.get("selected"))
        ]
        # Group by GWA
        gwa_groups: dict[str, dict] = {}
        for act in activities:
            gwa_code = act["gwa_code"]
            if gwa_code not in gwa_groups:
                gwa_groups[gwa_code] = {
                    "gwa_code": gwa_code,
                    "gwa_title": f"GWA {gwa_code}",
                    "dwas": [],
                    "ai_exposure_score": 0.75,
                }
            gwa_groups[gwa_code]["dwas"].append(act)
        return list(gwa_groups.values()) if gwa_groups else []

    async def update_selection(
        self,
        activity_id: UUID,
        selected: bool,
    ) -> Optional[dict]:
        activity = self._activities.get(str(activity_id))
        if activity:
            activity["selected"] = selected
        return activity

    async def bulk_update_selection(
        self,
        session_id: UUID,
        activity_ids: list[UUID],
        selected: bool,
    ) -> Optional[dict]:
        count = 0
        for aid in activity_ids:
            activity = self._activities.get(str(aid))
            if activity and activity.get("session_id") == str(session_id):
                activity["selected"] = selected
                count += 1
        return {"updated_count": count}

    async def get_selection_count(self, session_id: UUID) -> Optional[dict]:
        activities = [
            a for a in self._activities.values()
            if a.get("session_id") == str(session_id)
        ]
        selected = sum(1 for a in activities if a.get("selected"))
        gwa_codes = set(a["gwa_code"] for a in activities if a.get("selected"))
        return {
            "total": len(activities),
            "selected": selected,
            "unselected": len(activities) - selected,
            "gwas_with_selections": len(gwa_codes),
        }


class MockAnalysisService(AnalysisService):
    """Mock analysis service for testing."""

    async def trigger_analysis(self, session_id: UUID) -> Optional[dict]:
        return {"status": "processing"}

    async def get_by_dimension(
        self,
        session_id: UUID,
        dimension: Any,
        priority_tier: Optional[Any] = None,
    ) -> Optional[dict]:
        results = [
            {
                "id": str(uuid4()),
                "name": "Software Engineer",
                "ai_exposure_score": 0.85,
                "impact_score": 0.9,
                "complexity_score": 0.7,
                "priority_score": 0.82,
                "priority_tier": "HIGH",
            }
        ]
        if priority_tier:
            results = [r for r in results if r["priority_tier"] == str(priority_tier.value)]
        return {
            "dimension": str(dimension.value),
            "results": results,
        }

    async def get_all_dimensions(self, session_id: UUID) -> Optional[dict]:
        return {
            "ROLE": {"count": 10, "avg_exposure": 0.75},
            "DEPARTMENT": {"count": 5, "avg_exposure": 0.68},
            "GEOGRAPHY": {"count": 3, "avg_exposure": 0.71},
        }


class MockRoadmapService(RoadmapService):
    """Mock roadmap service for testing."""

    def __init__(self):
        self._items: dict[str, dict] = {}
        # Pre-populate with test data
        item_id = str(TEST_ROADMAP_ITEM_ID)
        self._items[item_id] = {
            "id": item_id,
            "session_id": str(TEST_SESSION_ID),
            "role_name": "Software Engineer",
            "priority_score": 0.85,
            "priority_tier": "HIGH",
            "phase": "NOW",
            "estimated_effort": "medium",
            "order": 1,
        }

    async def get_roadmap(
        self,
        session_id: UUID,
        phase: Optional[Any] = None,
    ) -> Optional[list[dict]]:
        items = [
            i for i in self._items.values()
            if i.get("session_id") == str(session_id)
        ]
        if phase:
            items = [i for i in items if i["phase"] == str(phase.value)]
        return items

    async def update_phase(
        self,
        item_id: UUID,
        phase: Any,
    ) -> Optional[dict]:
        item = self._items.get(str(item_id))
        if item:
            item["phase"] = str(phase.value)
        return item

    async def reorder(
        self,
        session_id: UUID,
        item_ids: list[UUID],
    ) -> Optional[bool]:
        return True

    async def bulk_update(
        self,
        session_id: UUID,
        updates: list[Any],
    ) -> Optional[int]:
        return len(updates)


class MockHandoffService(HandoffService):
    """Mock handoff service for testing."""

    def __init__(self):
        self._handed_off = False

    async def submit_to_intake(
        self,
        session_id: UUID,
        request: Any,
    ) -> Optional[HandoffResponse]:
        self._handed_off = True
        return HandoffResponse(
            intake_request_id=TEST_INTAKE_REQUEST_ID,
            status="submitted",
            candidates_count=5,
        )

    async def validate_readiness(self, session_id: UUID) -> Optional[ValidationResult]:
        return ValidationResult(
            is_ready=True,
            warnings=["Some activities not reviewed"],
            errors=[],
        )

    async def get_status(self, session_id: UUID) -> Optional[HandoffStatus]:
        return HandoffStatus(
            session_id=session_id,
            handed_off=self._handed_off,
            intake_request_id=TEST_INTAKE_REQUEST_ID if self._handed_off else None,
            handed_off_at=datetime.now(timezone.utc) if self._handed_off else None,
        )


class MockChatService(ChatService):
    """Mock chat service for testing."""

    def __init__(self):
        self._history: list[dict] = []

    async def send_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Optional[dict]:
        self._history.append({
            "role": "user",
            "content": message,
            "timestamp": _now_iso(),
        })
        response = {
            "role": "assistant",
            "content": f"I understand you said: {message}",
            "timestamp": _now_iso(),
        }
        self._history.append(response)
        return {
            "response": response["content"],
            "quick_actions": [
                {"label": "Continue", "action": "continue"},
                {"label": "Skip", "action": "skip"},
            ],
        }

    async def get_history(self, session_id: UUID) -> Optional[list[dict]]:
        return self._history

    async def execute_action(
        self,
        session_id: UUID,
        action: str,
        params: dict[str, Any],
    ) -> Optional[dict]:
        return {
            "response": f"Executed action: {action}",
            "data": {"action": action, "params": params},
        }

    async def stream_response(self, session_id: UUID) -> Optional[AsyncIterator[str]]:
        async def generate():
            yield "data: Hello\n\n"
            yield "data: World\n\n"
        return generate()


class MockExportService(ExportService):
    """Mock export service for testing."""

    async def generate_csv(
        self,
        session_id: UUID,
        dimension: Optional[str] = None,
    ) -> Optional[bytes]:
        csv_content = "Name,Role,Score\nJohn Doe,Engineer,0.85\n"
        return csv_content.encode("utf-8")

    async def generate_xlsx(self, session_id: UUID) -> Optional[bytes]:
        # Return minimal valid XLSX magic bytes (PK header)
        return b"PK\x03\x04" + b"\x00" * 100

    async def generate_pdf(self, session_id: UUID) -> Optional[bytes]:
        # Return minimal PDF header
        return b"%PDF-1.4\n" + b"\x00" * 100

    async def generate_handoff_bundle(
        self,
        session_id: UUID,
    ) -> Optional[dict[str, Any]]:
        return {
            "session_summary": {
                "id": str(session_id),
                "created_at": _now_iso(),
                "status": "completed",
            },
            "role_mappings": [
                {
                    "source_role": "Engineer",
                    "onet_code": "15-1252.00",
                    "confidence": 0.92,
                }
            ],
            "analysis_results": [
                {
                    "dimension": "ROLE",
                    "total_roles": 10,
                    "high_priority": 3,
                }
            ],
            "roadmap": [
                {
                    "role": "Engineer",
                    "phase": "NOW",
                    "priority": "HIGH",
                }
            ],
        }


# Create mock service instances
mock_session_service = MockSessionService()
mock_upload_service = MockUploadService()
mock_role_mapping_service = MockRoleMappingService()
mock_onet_service = MockOnetService()
mock_activity_service = MockActivityService()
mock_analysis_service = MockAnalysisService()
mock_roadmap_service = MockRoadmapService()
mock_handoff_service = MockHandoffService()
mock_chat_service = MockChatService()
mock_export_service = MockExportService()


# Override dependencies
app.dependency_overrides[get_session_service] = lambda: mock_session_service
app.dependency_overrides[get_upload_service] = lambda: mock_upload_service
app.dependency_overrides[get_role_mapping_service] = lambda: mock_role_mapping_service
app.dependency_overrides[get_onet_service] = lambda: mock_onet_service
app.dependency_overrides[get_activity_service] = lambda: mock_activity_service
app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service
app.dependency_overrides[get_roadmap_service] = lambda: mock_roadmap_service
app.dependency_overrides[get_handoff_service] = lambda: mock_handoff_service
app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
app.dependency_overrides[get_export_service] = lambda: mock_export_service


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def created_session(client: AsyncClient) -> dict:
    """Create a session for tests that need one."""
    response = await client.post(
        "/discovery/sessions",
        json={"organization_id": str(TEST_ORG_ID)},
    )
    return response.json()


# =============================================================================
# Health Check Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# =============================================================================
# Session Management Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_discovery_session(client: AsyncClient):
    """Test creating a new discovery session."""
    response = await client.post(
        "/discovery/sessions",
        json={"organization_id": str(TEST_ORG_ID)},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "draft"
    assert data["current_step"] == 1
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_session_by_id(client: AsyncClient, created_session: dict):
    """Test retrieving a session by ID."""
    session_id = created_session["id"]
    response = await client.get(f"/discovery/sessions/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, created_session: dict):
    """Test listing discovery sessions with pagination."""
    response = await client.get("/discovery/sessions?page=1&per_page=10")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_session_step(client: AsyncClient, created_session: dict):
    """Test updating session step."""
    session_id = created_session["id"]
    response = await client.patch(
        f"/discovery/sessions/{session_id}/step",
        json={"step": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_step"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, created_session: dict):
    """Test deleting a session."""
    session_id = created_session["id"]
    response = await client.delete(f"/discovery/sessions/{session_id}")

    assert response.status_code == 204


# =============================================================================
# Step 1: Upload Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_csv_file(client: AsyncClient, created_session: dict):
    """Test uploading a CSV file to a session."""
    session_id = created_session["id"]
    csv_content = "Name,Department,Role\nJohn,Engineering,Developer\nJane,HR,Manager"

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["file_name"] == "test.csv"
    assert data["row_count"] == 2
    assert "Name" in data["detected_schema"]
    assert "Department" in data["detected_schema"]
    assert "Role" in data["detected_schema"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_uploads_for_session(client: AsyncClient, created_session: dict):
    """Test listing uploads for a session."""
    session_id = created_session["id"]
    # First upload a file
    csv_content = "Col1,Col2\nA,B"
    await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )

    response = await client.get(f"/discovery/sessions/{session_id}/uploads")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(client: AsyncClient, created_session: dict):
    """Test that unsupported file types are rejected."""
    session_id = created_session["id"]

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")},
    )

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_rejects_empty_file(client: AsyncClient, created_session: dict):
    """Test that empty files are rejected."""
    session_id = created_session["id"]

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )

    assert response.status_code == 400


# =============================================================================
# Step 2: Role Mapping Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_role_mappings(client: AsyncClient):
    """Test getting role mappings for a session."""
    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/role-mappings")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        mapping = data[0]
        assert "id" in mapping
        assert "source_role" in mapping
        assert "onet_code" in mapping
        assert "onet_title" in mapping
        assert "confidence_score" in mapping
        assert "is_confirmed" in mapping


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_role_mapping(client: AsyncClient):
    """Test updating a role mapping."""
    response = await client.put(
        f"/discovery/role-mappings/{TEST_MAPPING_ID}",
        json={
            "onet_code": "15-1253.00",
            "onet_title": "Software Quality Assurance Analysts",
            "is_confirmed": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["onet_code"] == "15-1253.00"
    assert data["is_confirmed"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_confirm_role_mappings(client: AsyncClient):
    """Test bulk confirming role mappings above threshold."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/role-mappings/confirm",
        json={"threshold": 0.85},
    )

    assert response.status_code == 200
    data = response.json()
    assert "confirmed_count" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_onet_occupations(client: AsyncClient):
    """Test searching O*NET occupations."""
    response = await client.get("/discovery/onet/search?q=software")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        result = data[0]
        assert "code" in result
        assert "title" in result
        assert "score" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_onet_occupation_details(client: AsyncClient):
    """Test getting O*NET occupation details."""
    response = await client.get("/discovery/onet/15-1252.00")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "15-1252.00"
    assert "title" in data
    assert "description" in data


# =============================================================================
# Step 3: Activities Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_activities_grouped_by_gwa(client: AsyncClient):
    """Test getting activities grouped by GWA."""
    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        gwa_group = data[0]
        assert "gwa_code" in gwa_group
        assert "gwa_title" in gwa_group
        assert "dwas" in gwa_group
        assert isinstance(gwa_group["dwas"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_activity_selection(client: AsyncClient):
    """Test updating an activity's selection status."""
    response = await client.put(
        f"/discovery/activities/{TEST_ACTIVITY_ID}",
        json={"selected": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["selected"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_select_activities(client: AsyncClient):
    """Test bulk selecting/deselecting activities."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/activities/select",
        json={
            "activity_ids": [str(TEST_ACTIVITY_ID)],
            "selected": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_selection_count(client: AsyncClient):
    """Test getting activity selection counts."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/activities/count"
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "selected" in data
    assert "unselected" in data
    assert "gwas_with_selections" in data


# =============================================================================
# Step 4: Analysis Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_trigger_analysis(client: AsyncClient):
    """Test triggering analysis for a session."""
    response = await client.post(f"/discovery/sessions/{TEST_SESSION_ID}/analyze")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "processing"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_analysis_by_dimension(client: AsyncClient):
    """Test getting analysis results by dimension."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/analysis/ROLE"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "ROLE"
    assert "results" in data
    assert isinstance(data["results"], list)
    if len(data["results"]) > 0:
        result = data["results"][0]
        assert "id" in result
        assert "name" in result
        assert "ai_exposure_score" in result
        assert "priority_tier" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_dimensions_analysis(client: AsyncClient):
    """Test getting analysis summary for all dimensions."""
    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/analysis")

    assert response.status_code == 200
    data = response.json()
    assert "ROLE" in data
    assert "count" in data["ROLE"]
    assert "avg_exposure" in data["ROLE"]


# =============================================================================
# Step 5: Roadmap Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_roadmap(client: AsyncClient):
    """Test getting roadmap items for a session."""
    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/roadmap")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "id" in item
        assert "role_name" in item
        assert "priority_score" in item
        assert "phase" in item
        assert "estimated_effort" in item


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_roadmap_filtered_by_phase(client: AsyncClient):
    """Test getting roadmap items filtered by phase."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/roadmap?phase=NOW"
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_roadmap_phase(client: AsyncClient):
    """Test updating a roadmap item's phase."""
    response = await client.put(
        f"/discovery/roadmap/{TEST_ROADMAP_ITEM_ID}",
        json={"phase": "NEXT"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phase"] == "NEXT"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_roadmap(client: AsyncClient):
    """Test reordering roadmap items."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/roadmap/reorder",
        json={"item_ids": [str(TEST_ROADMAP_ITEM_ID)]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_update_roadmap_phases(client: AsyncClient):
    """Test bulk updating roadmap phases."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/roadmap/bulk-update",
        json={
            "updates": [
                {"id": str(TEST_ROADMAP_ITEM_ID), "phase": "LATER"},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data


# =============================================================================
# Handoff Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_handoff_readiness(client: AsyncClient):
    """Test validating handoff readiness."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/handoff/validate"
    )

    assert response.status_code == 200
    data = response.json()
    assert "is_ready" in data
    assert "warnings" in data
    assert "errors" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_submit_handoff(client: AsyncClient):
    """Test submitting candidates to intake."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/handoff",
        json={"candidate_ids": [str(uuid4())], "notes": "Test handoff"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "intake_request_id" in data
    assert data["status"] == "submitted"
    assert "candidates_count" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_handoff_status(client: AsyncClient):
    """Test getting handoff status."""
    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/handoff")

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "handed_off" in data


# =============================================================================
# Chat Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_chat_message(client: AsyncClient):
    """Test sending a chat message."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/chat",
        json={"message": "Hello, can you help me with discovery?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "quick_actions" in data
    assert isinstance(data["quick_actions"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_chat_history(client: AsyncClient):
    """Test getting chat history."""
    # First send a message
    await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/chat",
        json={"message": "Test message"},
    )

    response = await client.get(f"/discovery/sessions/{TEST_SESSION_ID}/chat")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_quick_action(client: AsyncClient):
    """Test executing a quick action."""
    response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/chat/action",
        json={"action": "continue", "params": {}},
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "data" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_chat_endpoint_exists(client: AsyncClient):
    """Test that chat streaming endpoint exists and returns SSE."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/chat/stream"
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


# =============================================================================
# Export Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_csv(client: AsyncClient):
    """Test exporting analysis as CSV."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/csv"
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_csv_with_dimension_filter(client: AsyncClient):
    """Test exporting CSV with dimension filter."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/csv?dimension=ROLE"
    )

    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_xlsx(client: AsyncClient):
    """Test exporting analysis as Excel."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/xlsx"
    )

    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "spreadsheetml" in content_type or "application/octet-stream" in content_type


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_pdf(client: AsyncClient):
    """Test exporting analysis as PDF."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/pdf"
    )

    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "pdf" in content_type or "application/octet-stream" in content_type


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_handoff_bundle(client: AsyncClient):
    """Test exporting handoff bundle as JSON."""
    response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/handoff"
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_summary" in data
    assert "role_mappings" in data
    assert "analysis_results" in data
    assert "roadmap" in data


# =============================================================================
# Complete Flow Integration Test
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_discovery_flow(client: AsyncClient):
    """
    Test the complete 5-step discovery flow end-to-end.

    This test simulates a full discovery workflow:
    1. Create session
    2. Upload file
    3. Review role mappings
    4. Select activities
    5. Trigger analysis
    6. Review roadmap
    7. Submit handoff
    8. Export results
    """
    # Step 1: Create a new discovery session
    create_response = await client.post(
        "/discovery/sessions",
        json={"organization_id": str(TEST_ORG_ID)},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    session_id = session["id"]
    assert session["status"] == "draft"
    assert session["current_step"] == 1

    # Step 2: Upload a CSV file
    csv_content = "Employee,Department,JobTitle\nAlice,Engineering,Developer\nBob,Sales,Manager"
    upload_response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("employees.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert upload_response.status_code == 201
    upload = upload_response.json()
    assert upload["row_count"] == 2
    assert "Employee" in upload["detected_schema"]

    # Update step to 2
    step_response = await client.patch(
        f"/discovery/sessions/{session_id}/step",
        json={"step": 2},
    )
    assert step_response.status_code == 200
    assert step_response.json()["current_step"] == 2

    # Step 3: Role mappings (using mock data from TEST_SESSION_ID)
    mappings_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/role-mappings"
    )
    assert mappings_response.status_code == 200

    # Bulk confirm high-confidence mappings
    confirm_response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/role-mappings/confirm",
        json={"threshold": 0.9},
    )
    assert confirm_response.status_code == 200

    # Step 4: Activities selection
    activities_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/activities"
    )
    assert activities_response.status_code == 200

    # Get selection count
    count_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/activities/count"
    )
    assert count_response.status_code == 200
    assert "total" in count_response.json()

    # Step 5: Trigger analysis
    analyze_response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/analyze"
    )
    assert analyze_response.status_code == 202
    assert analyze_response.json()["status"] == "processing"

    # Get analysis results
    analysis_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/analysis/ROLE"
    )
    assert analysis_response.status_code == 200
    assert analysis_response.json()["dimension"] == "ROLE"

    # Step 6: Review roadmap
    roadmap_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/roadmap"
    )
    assert roadmap_response.status_code == 200
    assert "items" in roadmap_response.json()

    # Step 7: Validate and submit handoff
    validate_response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/handoff/validate"
    )
    assert validate_response.status_code == 200
    validation = validate_response.json()
    assert validation["is_ready"] is True

    handoff_response = await client.post(
        f"/discovery/sessions/{TEST_SESSION_ID}/handoff",
        json={"notes": "Ready for intake"},
    )
    assert handoff_response.status_code == 201
    assert handoff_response.json()["status"] == "submitted"

    # Step 8: Export results
    csv_export = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/csv"
    )
    assert csv_export.status_code == 200

    bundle_export = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/export/handoff"
    )
    assert bundle_export.status_code == 200
    bundle = bundle_export.json()
    assert "session_summary" in bundle
    assert "roadmap" in bundle

    # Verify final status
    status_response = await client.get(
        f"/discovery/sessions/{TEST_SESSION_ID}/handoff"
    )
    assert status_response.status_code == 200
    assert status_response.json()["handed_off"] is True
