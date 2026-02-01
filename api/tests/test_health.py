# discovery/api/tests/test_health.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health check should return service status."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_checks_dependencies():
    """Health check should report dependency status."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health?detailed=true")

    assert response.status_code == 200
    data = response.json()
    assert "dependencies" in data
    assert "postgres" in data["dependencies"]
    assert "redis" in data["dependencies"]
    assert "s3" in data["dependencies"]


@pytest.mark.asyncio
async def test_readiness_endpoint():
    """Readiness probe should check if service can handle requests."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/ready")

    # May return 503 if dependencies down, but endpoint should exist
    assert response.status_code in [200, 503]
