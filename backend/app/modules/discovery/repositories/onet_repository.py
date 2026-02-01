"""O*NET repository for database operations.

Provides repositories for O*NET data including:
- OnetOccupationRepository: CRUD for occupation records
- OnetGwaRepository: Generalized Work Activity operations
- OnetIwaRepository: Intermediate Work Activity operations
- OnetDwaRepository: Detailed Work Activity operations with exposure score inheritance
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.discovery.models.onet import (
    OnetDwa,
    OnetGwa,
    OnetIwa,
    OnetOccupation,
)


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


class OnetGwaRepository:
    """Repository for Generalized Work Activity (GWA) operations.

    Provides async database operations for top-level work activities
    including retrieval by ID and listing all GWAs with AI exposure scores.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def get_by_id(self, gwa_id: str) -> OnetGwa | None:
        """Retrieve a GWA by its ID.

        Args:
            gwa_id: GWA identifier (e.g., "4.A.1.a.1").

        Returns:
            OnetGwa if found, None otherwise.
        """
        stmt = select(OnetGwa).where(OnetGwa.id == gwa_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[OnetGwa]:
        """List all Generalized Work Activities.

        Returns:
            List of all OnetGwa instances.
        """
        stmt = select(OnetGwa)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OnetIwaRepository:
    """Repository for Intermediate Work Activity (IWA) operations.

    Provides async database operations for mid-level work activities,
    including retrieval by ID and querying by parent GWA.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def get_by_id(self, iwa_id: str) -> OnetIwa | None:
        """Retrieve an IWA by its ID.

        Args:
            iwa_id: IWA identifier.

        Returns:
            OnetIwa if found, None otherwise.
        """
        stmt = select(OnetIwa).where(OnetIwa.id == iwa_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_gwa_id(self, gwa_id: str) -> list[OnetIwa]:
        """Retrieve all IWAs for a given GWA.

        Args:
            gwa_id: Parent GWA identifier.

        Returns:
            List of OnetIwa instances belonging to the GWA.
        """
        stmt = select(OnetIwa).where(OnetIwa.gwa_id == gwa_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OnetDwaRepository:
    """Repository for Detailed Work Activity (DWA) operations.

    Provides async database operations for detailed work activities,
    including retrieval by ID, querying by parent IWA or occupation,
    and computing effective AI exposure scores with inheritance.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def get_by_id(self, dwa_id: str) -> OnetDwa | None:
        """Retrieve a DWA by its ID.

        Args:
            dwa_id: DWA identifier.

        Returns:
            OnetDwa if found, None otherwise.
        """
        stmt = (
            select(OnetDwa)
            .options(selectinload(OnetDwa.iwa).selectinload(OnetIwa.gwa))
            .where(OnetDwa.id == dwa_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_iwa_id(self, iwa_id: str) -> list[OnetDwa]:
        """Retrieve all DWAs for a given IWA.

        Args:
            iwa_id: Parent IWA identifier.

        Returns:
            List of OnetDwa instances belonging to the IWA.
        """
        stmt = select(OnetDwa).where(OnetDwa.iwa_id == iwa_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_occupation_code(self, occupation_code: str) -> list[OnetDwa]:
        """Retrieve all DWAs associated with an occupation.

        Note: This currently returns an empty list as there is no direct
        relationship between occupations and DWAs in the database schema.
        The association would need to be established through an association
        table or via the O*NET API work activities endpoint.

        Args:
            occupation_code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of OnetDwa instances associated with the occupation.
        """
        # TODO: Implement when occupation-DWA association table is added
        # For now, return empty list as there's no direct relationship
        return []

    async def get_effective_exposure_score(self, dwa_id: str) -> float | None:
        """Get the effective AI exposure score for a DWA.

        If the DWA has an override score, returns that value.
        Otherwise, returns the parent GWA's exposure score.

        Args:
            dwa_id: DWA identifier.

        Returns:
            The effective exposure score (0.0-1.0), or None if the DWA
            is not found or has no score available.
        """
        dwa = await self.get_by_id(dwa_id)

        if dwa is None:
            return None

        # If DWA has an override, use it
        if dwa.ai_exposure_override is not None:
            return dwa.ai_exposure_override

        # Otherwise, inherit from GWA via IWA relationship
        if dwa.iwa and dwa.iwa.gwa:
            return dwa.iwa.gwa.ai_exposure_score

        return None
