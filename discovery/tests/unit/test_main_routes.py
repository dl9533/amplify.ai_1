"""Tests for main FastAPI application route registration."""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self):
        """Health check endpoint returns 200 OK."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self):
        """Health check endpoint returns status healthy."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.json() == {"status": "healthy"}


class TestCORSConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_allows_localhost_origin(self):
        """CORS allows requests from localhost:3000."""
        from app.main import app

        client = TestClient(app)
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should succeed
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_allows_credentials(self):
        """CORS allows credentials."""
        from app.main import app

        client = TestClient(app)
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestRouterRegistration:
    """Tests for router registration in the main app."""

    @pytest.fixture
    def openapi_paths(self):
        """Get all paths from OpenAPI schema."""
        from app.main import app

        return app.openapi()["paths"]

    def test_sessions_routes_registered(self, openapi_paths):
        """Sessions router routes are registered."""
        # Create session
        assert "/discovery/sessions" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions"]

        # Get session by ID
        assert "/discovery/sessions/{session_id}" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}"]

        # List sessions
        assert "get" in openapi_paths["/discovery/sessions"]

        # Delete session
        assert "delete" in openapi_paths["/discovery/sessions/{session_id}"]

    def test_uploads_routes_registered(self, openapi_paths):
        """Uploads router routes are registered."""
        # Upload file
        assert "/discovery/sessions/{session_id}/upload" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/upload"]

        # List uploads
        assert "/discovery/sessions/{session_id}/uploads" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/uploads"]

    def test_role_mappings_routes_registered(self, openapi_paths):
        """Role mappings router routes are registered."""
        # Get role mappings
        assert "/discovery/sessions/{session_id}/role-mappings" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/role-mappings"]

        # Bulk confirm
        assert "/discovery/sessions/{session_id}/role-mappings/confirm" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/role-mappings/confirm"]

        # Update role mapping
        assert "/discovery/role-mappings/{mapping_id}" in openapi_paths
        assert "put" in openapi_paths["/discovery/role-mappings/{mapping_id}"]

        # O*NET search
        assert "/discovery/onet/search" in openapi_paths
        assert "get" in openapi_paths["/discovery/onet/search"]

        # O*NET occupation details
        assert "/discovery/onet/{code}" in openapi_paths
        assert "get" in openapi_paths["/discovery/onet/{code}"]

    def test_activities_routes_registered(self, openapi_paths):
        """Activities router routes are registered."""
        # Get activities
        assert "/discovery/sessions/{session_id}/activities" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/activities"]

        # Bulk select
        assert "/discovery/sessions/{session_id}/activities/select" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/activities/select"]

        # Selection count
        assert "/discovery/sessions/{session_id}/activities/count" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/activities/count"]

        # Update single activity
        assert "/discovery/activities/{activity_id}" in openapi_paths
        assert "put" in openapi_paths["/discovery/activities/{activity_id}"]

    def test_analysis_routes_registered(self, openapi_paths):
        """Analysis router routes are registered."""
        # Trigger analysis
        assert "/discovery/sessions/{session_id}/analyze" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/analyze"]

        # Get all dimensions
        assert "/discovery/sessions/{session_id}/analysis" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/analysis"]

        # Get by dimension
        assert "/discovery/sessions/{session_id}/analysis/{dimension}" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/analysis/{dimension}"]

    def test_roadmap_routes_registered(self, openapi_paths):
        """Roadmap router routes are registered."""
        # Get roadmap
        assert "/discovery/sessions/{session_id}/roadmap" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/roadmap"]

        # Reorder
        assert "/discovery/sessions/{session_id}/roadmap/reorder" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/roadmap/reorder"]

        # Bulk update
        assert "/discovery/sessions/{session_id}/roadmap/bulk-update" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/roadmap/bulk-update"]

        # Update single item phase
        assert "/discovery/roadmap/{item_id}" in openapi_paths
        assert "put" in openapi_paths["/discovery/roadmap/{item_id}"]

    def test_chat_routes_registered(self, openapi_paths):
        """Chat router routes are registered."""
        # Send message (POST)
        assert "/discovery/sessions/{session_id}/chat" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/chat"]

        # Get history (GET)
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/chat"]

        # Stream
        assert "/discovery/sessions/{session_id}/chat/stream" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/chat/stream"]

        # Execute action
        assert "/discovery/sessions/{session_id}/chat/action" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/chat/action"]

    def test_exports_routes_registered(self, openapi_paths):
        """Exports router routes are registered."""
        # CSV export
        assert "/discovery/sessions/{session_id}/export/csv" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/export/csv"]

        # XLSX export
        assert "/discovery/sessions/{session_id}/export/xlsx" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/export/xlsx"]

        # PDF export
        assert "/discovery/sessions/{session_id}/export/pdf" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/export/pdf"]

        # Handoff bundle export
        assert "/discovery/sessions/{session_id}/export/handoff" in openapi_paths
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/export/handoff"]

    def test_handoff_routes_registered(self, openapi_paths):
        """Handoff router routes are registered."""
        # Submit handoff (POST)
        assert "/discovery/sessions/{session_id}/handoff" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/handoff"]

        # Get handoff status (GET)
        assert "get" in openapi_paths["/discovery/sessions/{session_id}/handoff"]

        # Validate handoff
        assert "/discovery/sessions/{session_id}/handoff/validate" in openapi_paths
        assert "post" in openapi_paths["/discovery/sessions/{session_id}/handoff/validate"]


class TestAPIMetadata:
    """Tests for API metadata configuration."""

    def test_api_title_is_set(self):
        """API title is set correctly."""
        from app.main import app

        assert app.title == "Discovery API"

    def test_api_description_is_set(self):
        """API description is set correctly."""
        from app.main import app

        assert "Opportunity Discovery" in app.description

    def test_api_version_is_set(self):
        """API version is set correctly."""
        from app.main import app

        assert app.version == "0.1.0"


class TestAllDiscoveryRoutes:
    """Integration tests to verify all discovery routes have proper prefixes."""

    def test_all_routes_have_discovery_prefix_or_health(self):
        """All registered routes either start with /discovery or are /health."""
        from app.main import app

        openapi_paths = app.openapi()["paths"]

        for path in openapi_paths.keys():
            assert path.startswith("/discovery") or path == "/health", (
                f"Route {path} does not have /discovery prefix or is not /health"
            )

    def test_route_count_is_correct(self):
        """Verify the expected number of route paths are registered."""
        from app.main import app

        openapi_paths = app.openapi()["paths"]

        # Count discovery routes (excluding /health)
        discovery_routes = [p for p in openapi_paths.keys() if p.startswith("/discovery")]

        # We expect at least these main routes:
        # - /discovery/sessions (2 methods: GET list, POST create)
        # - /discovery/sessions/{session_id} (2 methods: GET, DELETE)
        # - /discovery/sessions/{session_id}/step (1 method: PATCH)
        # - /discovery/sessions/{session_id}/upload
        # - /discovery/sessions/{session_id}/uploads
        # - /discovery/sessions/{session_id}/role-mappings
        # - /discovery/sessions/{session_id}/role-mappings/confirm
        # - /discovery/role-mappings/{mapping_id}
        # - /discovery/onet/search
        # - /discovery/onet/{code}
        # - /discovery/sessions/{session_id}/activities
        # - /discovery/sessions/{session_id}/activities/select
        # - /discovery/sessions/{session_id}/activities/count
        # - /discovery/activities/{activity_id}
        # - /discovery/sessions/{session_id}/analyze
        # - /discovery/sessions/{session_id}/analysis
        # - /discovery/sessions/{session_id}/analysis/{dimension}
        # - /discovery/sessions/{session_id}/roadmap
        # - /discovery/sessions/{session_id}/roadmap/reorder
        # - /discovery/sessions/{session_id}/roadmap/bulk-update
        # - /discovery/roadmap/{item_id}
        # - /discovery/sessions/{session_id}/chat
        # - /discovery/sessions/{session_id}/chat/stream
        # - /discovery/sessions/{session_id}/chat/action
        # - /discovery/sessions/{session_id}/export/csv
        # - /discovery/sessions/{session_id}/export/xlsx
        # - /discovery/sessions/{session_id}/export/pdf
        # - /discovery/sessions/{session_id}/export/handoff
        # - /discovery/sessions/{session_id}/handoff
        # - /discovery/sessions/{session_id}/handoff/validate
        # - /discovery/uploads/{upload_id}/mappings
        assert len(discovery_routes) >= 25, (
            f"Expected at least 25 discovery routes, found {len(discovery_routes)}: {discovery_routes}"
        )
