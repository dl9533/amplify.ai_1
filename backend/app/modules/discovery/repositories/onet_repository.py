"""O*NET Occupation repository for database operations."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.models.onet import OnetOccupation


class OnetOccupationRepository:
    """Repository for OnetOccupation CRUD and search operations.

    Provides async database operations for O*NET occupations including:
    - CRUD operations (create, read, delete)
    - Search by title/description
    - Upsert (insert or update) for data synchronization
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        code: str,
        title: str,
        description: str | None = None,
    ) -> OnetOccupation:
        """Create a new O*NET occupation record.

        Args:
            code: O*NET SOC code (e.g., "15-1252.00").
            title: Occupation title.
            description: Optional occupation description.

        Returns:
            The created OnetOccupation instance.
        """
        occupation = OnetOccupation(
            code=code,
            title=title,
            description=description,
        )
        self.session.add(occupation)
        await self.session.commit()
        await self.session.refresh(occupation)
        return occupation

    async def get_by_code(self, code: str) -> OnetOccupation | None:
        """Retrieve an occupation by its O*NET code.

        Args:
            code: O*NET SOC code (e.g., "15-1252.00").

        Returns:
            OnetOccupation if found, None otherwise.
        """
        stmt = select(OnetOccupation).where(OnetOccupation.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: str) -> list[OnetOccupation]:
        """Search occupations by title or description.

        Performs a case-insensitive search on both title and description fields.

        Args:
            query: Search query string.

        Returns:
            List of matching OnetOccupation instances.
        """
        search_pattern = f"%{query}%"
        stmt = select(OnetOccupation).where(
            or_(
                OnetOccupation.title.ilike(search_pattern),
                OnetOccupation.description.ilike(search_pattern),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        code: str,
        title: str,
        description: str | None = None,
    ) -> OnetOccupation:
        """Insert or update an O*NET occupation.

        If an occupation with the given code exists, updates its title and description.
        Otherwise, creates a new occupation record.

        Args:
            code: O*NET SOC code (e.g., "15-1252.00").
            title: Occupation title.
            description: Optional occupation description.

        Returns:
            The created or updated OnetOccupation instance.
        """
        existing = await self.get_by_code(code)

        if existing is not None:
            existing.title = title
            if description is not None:
                existing.description = description
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        return await self.create(code=code, title=title, description=description)

    async def list_all(self) -> list[OnetOccupation]:
        """List all O*NET occupations.

        Returns:
            List of all OnetOccupation instances.
        """
        stmt = select(OnetOccupation)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_code(self, code: str) -> bool:
        """Delete an occupation by its O*NET code.

        Args:
            code: O*NET SOC code (e.g., "15-1252.00").

        Returns:
            True if the occupation was deleted, False if not found.
        """
        occupation = await self.get_by_code(code)
        if occupation is None:
            return False

        await self.session.delete(occupation)
        await self.session.commit()
        return True
