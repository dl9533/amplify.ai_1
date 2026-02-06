"""Role mapping service for managing role-to-O*NET mappings.

Uses LLM-powered semantic mapping via RoleMappingAgent.
"""
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from app.config import get_settings
from app.repositories.onet_repository import OnetRepository
from app.repositories.role_mapping_repository import RoleMappingRepository
from app.services.file_parser import FileParser
from app.services.upload_service import UploadService

if TYPE_CHECKING:
    from app.agents.role_mapping_agent import RoleMappingAgent
    from app.services.lob_mapping_service import LobMappingService

logger = logging.getLogger(__name__)


class RoleMappingService:
    """Service for role-to-O*NET occupation mapping.

    Uses LLM-powered RoleMappingAgent for semantic role matching.
    Supports industry-aware matching when LOB context is available.

    Attributes:
        repository: Repository for role mapping persistence.
        upload_service: Service for file uploads.
        role_mapping_agent: LLM-powered mapping agent.
        onet_repository: Repository for O*NET data (optional).
        lob_service: Service for LOB-to-NAICS mapping (optional).
    """

    INDUSTRY_BOOST_FACTOR = 0.25  # Max 25% boost for industry match

    def __init__(
        self,
        repository: RoleMappingRepository,
        role_mapping_agent: "RoleMappingAgent",
        upload_service: UploadService | None = None,
        onet_repository: OnetRepository | None = None,
        lob_service: "LobMappingService | None" = None,
    ) -> None:
        """Initialize the role mapping service.

        Args:
            repository: Repository for role mapping persistence.
            role_mapping_agent: LLM-powered mapping agent.
            upload_service: Service for file uploads.
            onet_repository: Repository for O*NET data (optional, for industry matching).
            lob_service: Service for LOB-to-NAICS mapping (optional).
        """
        self.repository = repository
        self.role_mapping_agent = role_mapping_agent
        self.upload_service = upload_service
        self.onet_repository = onet_repository
        self.lob_service = lob_service
        self._file_parser = FileParser()

    async def create_mappings_from_upload(
        self,
        session_id: UUID,
        upload_id: UUID,
        role_column: str,
        lob_column: str | None = None,
        headcount_column: str | None = None,
        industry_naics_sector: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create role mappings from uploaded file.

        Uses the LLM-powered agent for semantic role matching.
        Optionally applies industry boosting based on session's industry.

        Note: This method deletes any existing mappings for the session
        before creating new ones to ensure clean state.

        Args:
            session_id: Discovery session ID.
            upload_id: Upload ID containing the file.
            role_column: Column name containing roles.
            lob_column: Optional column name containing LOB values for grouping.
            headcount_column: Optional column name containing employee counts to sum.
            industry_naics_sector: Optional 2-digit NAICS sector for industry boosting.

        Returns:
            List of created mapping dicts.
        """
        if not self.upload_service:
            raise ValueError("upload_service required")

        # Delete existing mappings for this session to ensure clean state
        # This prevents duplicates if the upload is re-processed
        deleted_count = await self.repository.delete_for_session(session_id)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} existing mappings for session {session_id}")

        # Get file content
        content = await self.upload_service.get_file_content(upload_id)
        if not content:
            return []

        # Extract unique roles with optional LOB grouping and headcount summing
        upload = await self.upload_service.repository.get_by_id(upload_id)
        role_lob_data = self._file_parser.extract_role_lob_values(
            content, upload.file_name, role_column, lob_column, headcount_column
        )

        if not role_lob_data:
            return []

        # Build role->LOB mapping and aggregate counts per unique role
        # (A role may appear in multiple LOBs, but we map once per unique role+LOB)
        role_entries = []
        for entry in role_lob_data:
            role_entries.append({
                "role": entry["role"],
                "lob": entry["lob"],
                "count": entry["count"],
            })

        # Get unique role names for LLM mapping (deduplicated)
        unique_role_names = list(set(e["role"] for e in role_entries))

        logger.info(f"Using LLM agent to map {len(unique_role_names)} unique roles")

        # Call agent to map all unique roles
        results = await self.role_mapping_agent.map_roles(unique_role_names)

        # Build lookup from role name to mapping result
        result_by_role = {r.source_role: r for r in results}

        # Create mapping records for each role+LOB combination
        mappings = []
        for entry in role_entries:
            role_name = entry["role"]
            lob_value = entry["lob"]
            row_count = entry["count"]

            result = result_by_role.get(role_name)
            if not result:
                continue

            # Calculate industry match score if industry is specified
            industry_match_score = None
            final_confidence = result.confidence_score

            if industry_naics_sector and result.onet_code and self.onet_repository:
                industry_match_score = await self.onet_repository.calculate_industry_score(
                    result.onet_code,
                    [industry_naics_sector],  # 2-digit prefix matching
                )
                # Apply boost to confidence score
                if industry_match_score > 0:
                    final_confidence = min(
                        1.0,
                        result.confidence_score * (1 + self.INDUSTRY_BOOST_FACTOR * industry_match_score)
                    )
                    logger.debug(
                        f"Industry boost for {result.source_role}: "
                        f"{result.confidence_score:.2f} -> {final_confidence:.2f} "
                        f"(industry_score={industry_match_score:.2f})"
                    )

            mapping = await self.repository.create(
                session_id=session_id,
                source_role=result.source_role,
                onet_code=result.onet_code,
                confidence_score=final_confidence,
                row_count=row_count,
                industry_match_score=industry_match_score,
                lob_value=lob_value,
            )

            mappings.append({
                "id": str(mapping.id),
                "source_role": mapping.source_role,
                "onet_code": mapping.onet_code,
                "onet_title": result.onet_title,
                "confidence_score": mapping.confidence_score,
                "confidence_tier": result.confidence.value,
                "reasoning": result.reasoning,
                "row_count": mapping.row_count,
                "is_confirmed": mapping.user_confirmed,
                "industry_match_score": industry_match_score,
                "lob_value": lob_value,
            })

        return mappings

    async def map_roles(self, role_names: list[str]) -> list[dict[str, Any]]:
        """Map a list of role names to O*NET occupations.

        Args:
            role_names: List of role titles to map.

        Returns:
            List of mapping result dicts with onet_code, onet_title,
            confidence_score, confidence_tier, and reasoning.
        """
        results = await self.role_mapping_agent.map_roles(role_names)
        return [
            {
                "source_role": r.source_role,
                "onet_code": r.onet_code,
                "onet_title": r.onet_title,
                "confidence_score": r.confidence_score,
                "confidence_tier": r.confidence.value,
                "reasoning": r.reasoning,
            }
            for r in results
        ]

    async def get_by_session_id(self, session_id: UUID) -> list[dict[str, Any]]:
        """Get all mappings for a session."""
        mappings = await self.repository.get_for_session(session_id)
        return [
            {
                "id": str(m.id),
                "source_role": m.source_role,
                "onet_code": m.onet_code,
                "onet_title": getattr(m, "onet_title", None),
                "confidence_score": m.confidence_score,
                "row_count": m.row_count,
                "is_confirmed": m.user_confirmed,
            }
            for m in mappings
        ]

    async def update(
        self,
        mapping_id: UUID,
        onet_code: Optional[str] = None,
        onet_title: Optional[str] = None,
        is_confirmed: Optional[bool] = None,
    ) -> Optional[dict]:
        """Update a role mapping.

        Args:
            mapping_id: The mapping ID to update.
            onet_code: New O*NET code (optional).
            onet_title: New O*NET title (optional).
            is_confirmed: New confirmation status (optional).

        Returns:
            Updated role mapping dictionary, or None if not found.
        """
        mapping = await self.repository.update(
            mapping_id, onet_code=onet_code, user_confirmed=is_confirmed
        )
        if not mapping:
            return None
        return {
            "id": str(mapping.id),
            "source_role": mapping.source_role,
            "onet_code": mapping.onet_code,
            "onet_title": getattr(mapping, "onet_title", None) or onet_title,
            "confidence_score": mapping.confidence_score,
            "is_confirmed": mapping.user_confirmed,
        }

    async def confirm_mapping(
        self,
        mapping_id: UUID,
        onet_code: str,
    ) -> dict[str, Any] | None:
        """Confirm a mapping with selected O*NET code."""
        mapping = await self.repository.confirm(mapping_id, onet_code)
        if not mapping:
            return None
        return {
            "id": str(mapping.id),
            "source_role": mapping.source_role,
            "onet_code": mapping.onet_code,
            "is_confirmed": mapping.user_confirmed,
        }

    async def bulk_confirm(
        self,
        session_id: UUID,
        threshold: float = 0.85,
        lob: str | None = None,
        mapping_ids: list[UUID] | None = None,
    ) -> dict[str, Any]:
        """Bulk confirm mappings above confidence threshold.

        Args:
            session_id: Discovery session ID.
            threshold: Minimum confidence threshold for auto-confirmation.
            lob: Optional LOB filter to confirm only mappings in this LOB.
            mapping_ids: Optional specific mapping IDs to confirm.

        Returns:
            Dict with confirmed_count.
        """
        mappings = await self.repository.get_for_session(session_id)
        confirmed = 0

        for mapping in mappings:
            # Skip if specific mapping_ids provided and this isn't one of them
            if mapping_ids is not None and mapping.id not in mapping_ids:
                continue

            # Skip if LOB filter provided and mapping doesn't match
            mapping_lob = getattr(mapping, "lob_value", None)
            if lob is not None and mapping_lob != lob:
                continue

            if (
                not mapping.user_confirmed
                and mapping.onet_code
                and mapping.confidence_score >= threshold
            ):
                await self.repository.confirm(mapping.id, mapping.onet_code)
                confirmed += 1

        return {"confirmed_count": confirmed}

    async def bulk_remap(
        self,
        session_id: UUID,
        threshold: float = 0.6,
        mapping_ids: list[UUID] | None = None,
    ) -> dict[str, Any]:
        """Re-map low-confidence roles using LLM agent.

        Args:
            session_id: Discovery session ID.
            threshold: Maximum confidence threshold - roles at or below this will be re-mapped.
            mapping_ids: Optional specific mapping IDs to re-map.

        Returns:
            Dict with remapped_count and updated mappings.
        """
        mappings = await self.repository.get_for_session(session_id)

        # Filter to mappings that need re-mapping
        if mapping_ids:
            to_remap = [m for m in mappings if m.id in mapping_ids]
        else:
            to_remap = [
                m for m in mappings
                if not m.user_confirmed and m.confidence_score <= threshold
            ]

        if not to_remap:
            return {"remapped_count": 0, "mappings": []}

        # Extract role names for re-mapping
        role_names = [m.source_role for m in to_remap]
        mapping_by_role = {m.source_role: m for m in to_remap}

        logger.info(f"Re-mapping {len(role_names)} low-confidence roles via LLM agent")

        # Call agent to re-map roles
        results = await self.role_mapping_agent.map_roles(role_names)

        # Update mappings with new results
        updated_mappings = []
        for result in results:
            mapping = mapping_by_role.get(result.source_role)
            if mapping:
                # Update the mapping in the database
                updated = await self.repository.update(
                    mapping.id,
                    onet_code=result.onet_code,
                    confidence_score=result.confidence_score,
                )

                if updated:
                    updated_mappings.append({
                        "id": str(updated.id),
                        "source_role": updated.source_role,
                        "onet_code": result.onet_code,
                        "onet_title": result.onet_title,
                        "confidence_score": result.confidence_score,
                        "confidence_tier": result.confidence.value,
                        "reasoning": result.reasoning,
                        "is_confirmed": updated.user_confirmed,
                    })

        return {
            "remapped_count": len(updated_mappings),
            "mappings": updated_mappings,
        }

    async def match_role_with_industry(
        self,
        job_title: str,
        lob: str | None = None,
    ) -> list[dict[str, Any]]:
        """Match job title to O*NET occupations with industry context.

        Uses LOB-to-NAICS mapping to boost occupations that are more
        commonly employed in the target industry.

        Args:
            job_title: The job title to match.
            lob: Optional Line of Business for industry-aware boosting.

        Returns:
            List of occupation matches with scores and industry data.
        """
        if not self.onet_repository:
            return []

        # Get candidate occupations from title search
        candidates = await self.onet_repository.search_occupations(job_title)

        if not candidates:
            return []

        # Convert to dict format
        results = [
            {
                "code": occ.code,
                "title": occ.title,
                "score": 1.0,  # Base score
            }
            for occ in candidates
        ]

        if not lob or not self.lob_service:
            return results

        # Get NAICS codes for the LOB
        lob_result = await self.lob_service.map_lob_to_naics(lob)
        naics_codes = lob_result.naics_codes

        if not naics_codes:
            return results

        # Score candidates with industry boost
        for result in results:
            industry_score = await self.onet_repository.calculate_industry_score(
                result["code"],
                naics_codes,
            )

            original_score = result["score"]
            boosted_score = original_score * (1 + self.INDUSTRY_BOOST_FACTOR * industry_score)

            result["score"] = boosted_score
            result["industry_match"] = industry_score
            result["original_score"] = original_score

        # Re-sort by boosted score
        return sorted(results, key=lambda x: x["score"], reverse=True)

    async def get_grouped_mappings(
        self,
        session_id: UUID,
        low_confidence_threshold: float = 0.6,
    ) -> dict[str, Any]:
        """Get role mappings grouped by Line of Business.

        Organizes role mappings by LOB with summary statistics for each group.
        Mappings without LOB assignment are returned separately.
        Duplicate roles within the same LOB are aggregated.

        Args:
            session_id: Discovery session ID.
            low_confidence_threshold: Threshold below which mappings are considered low confidence.

        Returns:
            Dict with session_id, overall_summary, lob_groups, and ungrouped_mappings.
        """
        mappings = await self.repository.get_for_session(session_id)

        # Build mapping data with employee counts
        mapping_data = []
        for m in mappings:
            mapping_data.append({
                "id": str(m.id),
                "source_role": m.source_role,
                "onet_code": m.onet_code,
                "onet_title": getattr(m, "onet_title", None),
                "confidence_score": m.confidence_score or 0,
                "is_confirmed": m.user_confirmed,
                "employee_count": getattr(m, "row_count", 1) or 1,
                "lob": getattr(m, "lob_value", None),
            })

        # Group by LOB first, then aggregate by source_role within each LOB
        lob_groups_dict: dict[str | None, list[dict]] = {}

        for m in mapping_data:
            lob = m.get("lob")
            if lob not in lob_groups_dict:
                lob_groups_dict[lob] = []
            lob_groups_dict[lob].append(m)

        def aggregate_by_role(mappings_list: list[dict]) -> list[dict]:
            """Aggregate mappings with the same source_role."""
            role_groups: dict[str, list[dict]] = {}
            for m in mappings_list:
                role = m["source_role"]
                if role not in role_groups:
                    role_groups[role] = []
                role_groups[role].append(m)

            aggregated = []
            for role, role_mappings in role_groups.items():
                if len(role_mappings) == 1:
                    # No aggregation needed
                    aggregated.append(role_mappings[0])
                else:
                    # Aggregate multiple mappings with same role
                    # Prefer confirmed mapping for O*NET info, otherwise highest confidence
                    confirmed = [m for m in role_mappings if m["is_confirmed"]]
                    if confirmed:
                        primary = confirmed[0]
                    else:
                        # Sort by confidence score descending
                        sorted_by_conf = sorted(
                            role_mappings,
                            key=lambda x: x["confidence_score"],
                            reverse=True
                        )
                        primary = sorted_by_conf[0]

                    aggregated.append({
                        "id": primary["id"],  # Use primary ID for API operations
                        "source_role": role,
                        "onet_code": primary["onet_code"],
                        "onet_title": primary["onet_title"],
                        "confidence_score": primary["confidence_score"],
                        "is_confirmed": any(m["is_confirmed"] for m in role_mappings),
                        "employee_count": sum(m["employee_count"] for m in role_mappings),
                        "lob": primary["lob"],
                    })
            return aggregated

        # Aggregate within each LOB and build groups
        lob_groups = []
        ungrouped = []

        for lob, group_mappings in sorted(
            lob_groups_dict.items(),
            key=lambda x: (x[0] is None, x[0] or ""),  # None goes last
        ):
            aggregated_mappings = aggregate_by_role(group_mappings)

            if lob is None:
                ungrouped.extend(aggregated_mappings)
            else:
                group_summary = {
                    "total_roles": len(aggregated_mappings),
                    "confirmed_count": sum(1 for m in aggregated_mappings if m["is_confirmed"]),
                    "pending_count": sum(1 for m in aggregated_mappings if not m["is_confirmed"]),
                    "low_confidence_count": sum(
                        1 for m in aggregated_mappings
                        if m["confidence_score"] < low_confidence_threshold and not m["is_confirmed"]
                    ),
                    "total_employees": sum(m["employee_count"] for m in aggregated_mappings),
                }
                lob_groups.append({
                    "lob": lob,
                    "summary": group_summary,
                    "mappings": aggregated_mappings,
                })

        # Aggregate ungrouped as well
        ungrouped = aggregate_by_role(ungrouped) if ungrouped else []

        # Calculate overall summary from aggregated data
        all_aggregated = []
        for g in lob_groups:
            all_aggregated.extend(g["mappings"])
        all_aggregated.extend(ungrouped)

        overall_summary = {
            "total_roles": len(all_aggregated),
            "confirmed_count": sum(1 for m in all_aggregated if m["is_confirmed"]),
            "pending_count": sum(1 for m in all_aggregated if not m["is_confirmed"]),
            "low_confidence_count": sum(
                1 for m in all_aggregated
                if m["confidence_score"] < low_confidence_threshold and not m["is_confirmed"]
            ),
            "total_employees": sum(m["employee_count"] for m in all_aggregated),
        }

        return {
            "session_id": str(session_id),
            "overall_summary": overall_summary,
            "lob_groups": lob_groups,
            "ungrouped_mappings": ungrouped,
        }


class OnetService:
    """O*NET service for searching and retrieving occupation data.

    Uses the local O*NET repository for data access.

    Attributes:
        repository: OnetRepository for database access.
    """

    def __init__(self, repository: OnetRepository) -> None:
        """Initialize the O*NET service.

        Args:
            repository: OnetRepository instance for database access.
        """
        self.repository = repository

    async def search(self, query: str) -> list[dict]:
        """Search O*NET occupations by query.

        Args:
            query: Search query string.

        Returns:
            List of matching occupations with code, title, and score.
        """
        occupations = await self.repository.search_with_full_text(query)
        return [
            {
                "code": occ.code,
                "title": occ.title,
                "score": 1.0,  # Full-text search doesn't return scores
            }
            for occ in occupations
        ]

    async def get_occupation(self, code: str) -> Optional[dict]:
        """Get O*NET occupation details by code.

        Args:
            code: O*NET SOC code.

        Returns:
            Occupation details dictionary, or None if not found.
        """
        occupation = await self.repository.get_by_code(code)
        if not occupation:
            return None
        return {
            "code": occupation.code,
            "title": occupation.title,
            "description": occupation.description,
        }


async def get_role_mapping_service() -> AsyncGenerator[RoleMappingService, None]:
    """Get role mapping service dependency for FastAPI.

    Yields a fully configured RoleMappingService with the LLM-powered
    RoleMappingAgent for semantic role matching and industry-aware boosting.
    """
    from app.agents.role_mapping_agent import RoleMappingAgent
    from app.models.base import async_session_maker
    from app.repositories.lob_mapping_repository import LobMappingRepository
    from app.repositories.upload_repository import UploadRepository
    from app.services.llm_service import get_llm_service
    from app.services.lob_mapping_service import LobMappingService
    from app.services.s3_client import S3Client
    from app.services.upload_service import UploadService

    settings = get_settings()

    async with async_session_maker() as db:
        repository = RoleMappingRepository(db)
        onet_repo = OnetRepository(db)
        lob_repo = LobMappingRepository(db)
        upload_repo = UploadRepository(db)

        # Get LLM service
        llm_service = get_llm_service(settings)

        # Create S3 client for upload content retrieval
        s3_client = S3Client(
            endpoint_url=settings.s3_endpoint_url,
            bucket=settings.s3_bucket,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key.get_secret_value() if settings.aws_secret_access_key else None,
            region=settings.aws_region,
        )

        # Create upload service for role extraction
        upload_service = UploadService(
            repository=upload_repo,
            s3_client=s3_client,
        )

        # Create LOB mapping service for industry-aware matching
        lob_service = LobMappingService(
            repository=lob_repo,
            llm_service=llm_service,
        )

        # Create role mapping agent
        agent = RoleMappingAgent(
            llm_service=llm_service,
            onet_repository=onet_repo,
        )

        service = RoleMappingService(
            repository=repository,
            role_mapping_agent=agent,
            upload_service=upload_service,
            onet_repository=onet_repo,
            lob_service=lob_service,
        )
        yield service


async def get_onet_service() -> AsyncGenerator[OnetService, None]:
    """Get O*NET service dependency for FastAPI.

    Yields an OnetService configured with the local repository.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        repository = OnetRepository(db)
        yield OnetService(repository=repository)
