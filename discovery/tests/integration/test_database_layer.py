"""Integration tests for database layer.

These tests require a running PostgreSQL database.
Skip if database not available.
"""
import os
import pytest
from uuid import uuid4

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") and not os.getenv("POSTGRES_HOST"),
    reason="Database not configured"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_repository_crud():
    """Test session repository CRUD operations."""
    from app.models.base import async_session_maker
    from app.repositories.session_repository import SessionRepository

    async with async_session_maker() as db:
        repo = SessionRepository(db)

        # Create
        user_id = uuid4()
        org_id = uuid4()
        session = await repo.create(user_id=user_id, organization_id=org_id)
        assert session.id is not None
        assert session.current_step == 1

        # Read
        retrieved = await repo.get_by_id(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id

        # Update
        updated = await repo.update_step(session.id, 2)
        assert updated.current_step == 2

        # Delete
        deleted = await repo.delete(session.id)
        assert deleted is True

        # Verify deletion
        retrieved = await repo.get_by_id(session.id)
        assert retrieved is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_service_integration():
    """Test session service with real database."""
    from app.models.base import async_session_maker
    from app.repositories.session_repository import SessionRepository
    from app.services.session_service import SessionService

    async with async_session_maker() as db:
        repo = SessionRepository(db)
        user_id = uuid4()
        service = SessionService(repository=repo, user_id=user_id)

        # Create session
        org_id = uuid4()
        result = await service.create(organization_id=org_id)

        assert "id" in result
        assert result["status"] == "draft"
        assert result["current_step"] == 1

        # Clean up
        from uuid import UUID
        await repo.delete(UUID(result["id"]))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onet_repository_search():
    """Test O*NET repository search (requires seeded data)."""
    from app.models.base import async_session_maker
    from app.repositories.onet_repository import OnetRepository

    async with async_session_maker() as db:
        repo = OnetRepository(db)

        # Search should return empty if no data seeded
        # In production, would have seeded O*NET data
        results = await repo.search_occupations("software")

        # Just verify method works without error
        assert isinstance(results, (list, tuple))
