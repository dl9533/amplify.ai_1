"""Discovery session service for orchestrating discovery workflow.

Provides the DiscoverySessionService which coordinates the various repositories
to manage the complete discovery session lifecycle including:
- Session creation and status management
- Step navigation and validation
- Upload registration
- Role mapping and activity selection
- Analysis results storage
- Candidate management and handoff bundle generation
"""

from uuid import UUID

from app.modules.discovery.enums import AnalysisDimension, PriorityTier, SessionStatus
from app.modules.discovery.models.session import (
    AgentificationCandidate,
    DiscoveryActivitySelection,
    DiscoveryAnalysisResult,
    DiscoveryRoleMapping,
    DiscoverySession,
    DiscoveryUpload,
)
from app.modules.discovery.repositories.activity_selection_repository import (
    DiscoveryActivitySelectionRepository,
)
from app.modules.discovery.repositories.analysis_result_repository import (
    DiscoveryAnalysisResultRepository,
)
from app.modules.discovery.repositories.candidate_repository import (
    AgentificationCandidateRepository,
)
from app.modules.discovery.repositories.role_mapping_repository import (
    DiscoveryRoleMappingRepository,
)
from app.modules.discovery.repositories.session_repository import (
    DiscoverySessionRepository,
)
from app.modules.discovery.repositories.upload_repository import (
    DiscoveryUploadRepository,
)


class DiscoverySessionService:
    """Service layer for orchestrating discovery session operations.

    This service coordinates the various repositories to manage the complete
    discovery session lifecycle. It acts as a thin layer delegating to
    repositories while handling cross-cutting concerns like:
    - Step validation (1-5)
    - Status transitions (DRAFT -> IN_PROGRESS -> COMPLETED -> ARCHIVED)
    - Aggregating data for session summaries and handoff bundles

    Attributes:
        session_repo: Repository for discovery session CRUD operations.
        upload_repo: Repository for file upload management.
        role_mapping_repo: Repository for O*NET role mapping operations.
        activity_selection_repo: Repository for DWA activity selections.
        analysis_result_repo: Repository for analysis result storage.
        candidate_repo: Repository for agentification candidate management.
    """

    MIN_STEP = 1
    MAX_STEP = 5

    def __init__(
        self,
        session_repo: DiscoverySessionRepository,
        upload_repo: DiscoveryUploadRepository,
        role_mapping_repo: DiscoveryRoleMappingRepository,
        activity_selection_repo: DiscoveryActivitySelectionRepository,
        analysis_result_repo: DiscoveryAnalysisResultRepository,
        candidate_repo: AgentificationCandidateRepository,
    ) -> None:
        """Initialize the service with all required repositories.

        Args:
            session_repo: Repository for discovery session operations.
            upload_repo: Repository for upload operations.
            role_mapping_repo: Repository for role mapping operations.
            activity_selection_repo: Repository for activity selection operations.
            analysis_result_repo: Repository for analysis result operations.
            candidate_repo: Repository for candidate operations.
        """
        self.session_repo = session_repo
        self.upload_repo = upload_repo
        self.role_mapping_repo = role_mapping_repo
        self.activity_selection_repo = activity_selection_repo
        self.analysis_result_repo = analysis_result_repo
        self.candidate_repo = candidate_repo

    async def create_session(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> DiscoverySession:
        """Create a new discovery session.

        Creates a session with default DRAFT status and step 1.

        Args:
            user_id: UUID of the user creating the session.
            organization_id: UUID of the organization for the session.

        Returns:
            The created DiscoverySession instance.
        """
        return await self.session_repo.create(
            user_id=user_id,
            organization_id=organization_id,
        )

    async def get_session(self, session_id: UUID) -> DiscoverySession | None:
        """Retrieve a session by its ID.

        Args:
            session_id: UUID of the session to retrieve.

        Returns:
            DiscoverySession if found, None otherwise.
        """
        return await self.session_repo.get_by_id(session_id)

    async def advance_step(self, session_id: UUID) -> DiscoverySession | None:
        """Advance the session to the next step.

        Increments the current step by 1 and updates status to IN_PROGRESS
        if advancing from step 1 (DRAFT state).

        Args:
            session_id: UUID of the session to advance.

        Returns:
            Updated DiscoverySession if found, None otherwise.
        """
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            return None

        # Update status to IN_PROGRESS when leaving step 1
        if session.current_step == 1 and session.status == SessionStatus.DRAFT:
            await self.session_repo.update_status(session_id, SessionStatus.IN_PROGRESS)

        new_step = session.current_step + 1
        return await self.session_repo.update_step(session_id, step=new_step)

    async def go_to_step(self, session_id: UUID, step: int) -> DiscoverySession | None:
        """Navigate to a specific step in the session.

        Allows navigating to any valid step (1-5), including going back
        to previous steps.

        Args:
            session_id: UUID of the session to update.
            step: The step number to navigate to (1-5).

        Returns:
            Updated DiscoverySession if found, None otherwise.

        Raises:
            ValueError: If step is not between 1 and 5.
        """
        if step < self.MIN_STEP or step > self.MAX_STEP:
            raise ValueError(f"Step must be between {self.MIN_STEP} and {self.MAX_STEP}")

        # Ensure session exists before attempting update
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            return None

        return await self.session_repo.update_step(session_id, step=step)

    async def complete_session(self, session_id: UUID) -> DiscoverySession | None:
        """Mark a session as completed.

        Args:
            session_id: UUID of the session to complete.

        Returns:
            Updated DiscoverySession if found, None otherwise.
        """
        return await self.session_repo.update_status(session_id, SessionStatus.COMPLETED)

    async def archive_session(self, session_id: UUID) -> DiscoverySession | None:
        """Archive a session.

        Args:
            session_id: UUID of the session to archive.

        Returns:
            Updated DiscoverySession if found, None otherwise.
        """
        return await self.session_repo.update_status(session_id, SessionStatus.ARCHIVED)

    async def get_session_summary(self, session_id: UUID) -> dict:
        """Get a summary of the session state.

        Aggregates data from multiple repositories to provide a comprehensive
        overview of the session including upload info, role mappings, and candidates.

        Args:
            session_id: UUID of the session to summarize.

        Returns:
            Dictionary containing:
            - session_id: UUID of the session
            - exists: Boolean indicating if session was found
            - current_step: Current step number (only if exists)
            - status: Current session status (only if exists)
            - row_count: Number of rows in latest upload (only if exists)
            - role_mapping_count: Number of role mappings (only if exists)
            - candidate_count: Number of candidates (only if exists)
        """
        session = await self.session_repo.get_by_id(session_id)

        # Return early if session doesn't exist
        if session is None:
            return {
                "session_id": session_id,
                "exists": False,
            }

        # Get latest upload for row count
        upload = await self.upload_repo.get_latest_for_session(session_id)
        row_count = upload.row_count if upload else 0

        # Get role mappings count
        role_mappings = await self.role_mapping_repo.get_by_session_id(session_id)

        # Get candidates count
        candidates = await self.candidate_repo.get_by_session_id(session_id)

        return {
            "session_id": session_id,
            "exists": True,
            "current_step": session.current_step,
            "status": session.status,
            "row_count": row_count,
            "role_mapping_count": len(role_mappings),
            "candidate_count": len(candidates),
        }

    async def register_upload(
        self,
        session_id: UUID,
        file_name: str,
        file_url: str,
        row_count: int,
        detected_schema: dict | None = None,
    ) -> DiscoveryUpload:
        """Register a file upload for a session.

        Args:
            session_id: UUID of the session this upload belongs to.
            file_name: Name of the uploaded file.
            file_url: URL where the file is stored.
            row_count: Number of rows in the uploaded file.
            detected_schema: Optional dict describing the detected file schema.

        Returns:
            The created DiscoveryUpload instance.
        """
        return await self.upload_repo.create(
            session_id=session_id,
            file_name=file_name,
            file_url=file_url,
            row_count=row_count,
            detected_schema=detected_schema,
        )

    async def create_role_mapping(
        self,
        session_id: UUID,
        source_role: str,
        onet_code: str | None,
        confidence_score: float | None = None,
        row_count: int | None = None,
    ) -> DiscoveryRoleMapping:
        """Create a role mapping for a session.

        Maps a customer role to an O*NET occupation code.

        Args:
            session_id: UUID of the session this mapping belongs to.
            source_role: The customer's role name from their data.
            onet_code: O*NET occupation code (e.g., "15-1252.00"), or None.
            confidence_score: AI confidence score for the mapping (0.0-1.0).
            row_count: Number of rows in source data with this role.

        Returns:
            The created DiscoveryRoleMapping instance.
        """
        return await self.role_mapping_repo.create(
            session_id=session_id,
            source_role=source_role,
            onet_code=onet_code,
            confidence_score=confidence_score,
            row_count=row_count,
        )

    async def bulk_create_activity_selections(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        dwa_ids: list[str],
    ) -> list[DiscoveryActivitySelection]:
        """Bulk create activity selections for a role mapping.

        Creates selection records for multiple Detailed Work Activities (DWAs).

        Args:
            session_id: UUID of the session.
            role_mapping_id: UUID of the role mapping.
            dwa_ids: List of DWA IDs to create selections for.

        Returns:
            List of created DiscoveryActivitySelection instances.
        """
        return await self.activity_selection_repo.bulk_create(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            dwa_ids=dwa_ids,
        )

    async def store_analysis_results(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        results: list[dict],
    ) -> list[DiscoveryAnalysisResult]:
        """Store analysis results for multiple dimensions.

        Each result dictionary should contain:
        - dimension: AnalysisDimension enum value
        - dimension_value: String value for the dimension
        - ai_exposure_score: Optional float (0.0-1.0)
        - priority_score: Optional float (0.0-1.0)
        - And optionally: impact_score, complexity_score, breakdown

        Args:
            session_id: UUID of the session.
            role_mapping_id: UUID of the role mapping.
            results: List of result dictionaries to store.

        Returns:
            List of created DiscoveryAnalysisResult instances.
            Returns empty list if results is empty.
        """
        if not results:
            return []

        created_results = []
        for result_data in results:
            result = await self.analysis_result_repo.create(
                session_id=session_id,
                role_mapping_id=role_mapping_id,
                dimension=result_data["dimension"],
                dimension_value=result_data["dimension_value"],
                ai_exposure_score=result_data.get("ai_exposure_score"),
                impact_score=result_data.get("impact_score"),
                complexity_score=result_data.get("complexity_score"),
                priority_score=result_data.get("priority_score"),
                breakdown=result_data.get("breakdown"),
            )
            created_results.append(result)
        return created_results

    async def create_candidate(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        name: str,
        description: str | None,
        priority_tier: PriorityTier,
        estimated_impact: float,
    ) -> AgentificationCandidate:
        """Create an agentification candidate.

        Args:
            session_id: UUID of the session this candidate belongs to.
            role_mapping_id: UUID of the role mapping this candidate is based on.
            name: Name of the candidate agent.
            description: Optional description of the candidate.
            priority_tier: Timeline bucket (NOW, NEXT_QUARTER, FUTURE).
            estimated_impact: Estimated impact score (0.0-1.0).

        Returns:
            The created AgentificationCandidate instance.
        """
        return await self.candidate_repo.create(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            name=name,
            description=description,
            priority_tier=priority_tier,
            estimated_impact=estimated_impact,
        )

    async def select_candidates_for_build(
        self,
        candidate_ids: list[UUID],
    ) -> list[AgentificationCandidate]:
        """Select multiple candidates for build.

        Marks each candidate as selected_for_build=True.

        Note: This method makes N database calls where N is the number of candidates.
        This is a known trade-off since the repository's select_for_build method
        updates a single record. Bulk optimization could be added to the repository
        layer in the future if performance becomes a concern.

        Args:
            candidate_ids: List of candidate UUIDs to select.

        Returns:
            List of updated AgentificationCandidate instances.
        """
        if not candidate_ids:
            return []

        selected = []
        for candidate_id in candidate_ids:
            candidate = await self.candidate_repo.select_for_build(candidate_id)
            if candidate:
                selected.append(candidate)
        return selected

    async def get_handoff_bundle(self, session_id: UUID) -> dict:
        """Prepare a handoff bundle for intake.

        Aggregates all selected candidates with their role mappings and
        analysis results for handoff to the intake process.

        Note: This method makes 2*N database calls where N is the number of
        selected candidates (one for role mapping, one for analysis results per
        candidate). This is a known trade-off as bulk fetching would require
        repository-level changes. Consider optimizing if performance becomes
        a concern with large numbers of candidates.

        Args:
            session_id: UUID of the session to create bundle for.

        Returns:
            Dictionary containing:
            - session_id: UUID of the session
            - candidates: List of candidate data with role mappings and analysis
        """
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            return {"session_id": session_id, "candidates": []}

        selected_candidates = await self.candidate_repo.get_selected_for_build(session_id)

        candidates_data = []
        for candidate in selected_candidates:
            role_mapping = await self.role_mapping_repo.get_by_id(candidate.role_mapping_id)
            analysis_results = await self.analysis_result_repo.get_by_role_mapping_id(
                candidate.role_mapping_id
            )

            candidate_bundle = {
                "id": candidate.id,
                "name": candidate.name,
                "description": candidate.description,
                "priority_tier": candidate.priority_tier,
                "estimated_impact": candidate.estimated_impact,
                "role_mapping": {
                    "source_role": role_mapping.source_role if role_mapping else None,
                    "onet_code": role_mapping.onet_code if role_mapping else None,
                },
                "analysis_results": [
                    {
                        "dimension": r.dimension,
                        "dimension_value": r.dimension_value,
                        "ai_exposure_score": r.ai_exposure_score,
                        "impact_score": r.impact_score,
                        "complexity_score": r.complexity_score,
                        "priority_score": r.priority_score,
                        "breakdown": r.breakdown,
                    }
                    for r in analysis_results
                ],
            }
            candidates_data.append(candidate_bundle)

        return {
            "session_id": session_id,
            "candidates": candidates_data,
        }

    async def list_user_sessions(self, user_id: UUID) -> list[DiscoverySession]:
        """List all sessions for a user.

        Args:
            user_id: UUID of the user whose sessions to list.

        Returns:
            List of DiscoverySession instances for the user.
        """
        return await self.session_repo.list_for_user(user_id)
