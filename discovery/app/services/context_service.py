"""Context service for chat-UI coordination."""
from typing import Any, TypedDict
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_activity_selection import DiscoveryActivitySelection
from app.models.discovery_analysis import DiscoveryAnalysisResult
from app.models.onet_work_activities import OnetDWA, OnetIWA, OnetGWA


# Constants
MAX_MESSAGE_LENGTH = 10000
MIN_STEP = 1
MAX_STEP = 5


class SuggestedAction(TypedDict):
    """Structure for a suggested action."""

    action: str
    label: str
    description: str


class GWAGroup(TypedDict):
    """Structure for a GWA group."""

    id: str
    name: str
    count: int


class ActivitiesData(TypedDict):
    """Structure for activities data."""

    gwa_groups: list[GWAGroup]
    total_activities: int


class Priority(TypedDict):
    """Structure for a priority item."""

    id: str
    name: str
    score: float


class AnalysisSummary(TypedDict):
    """Structure for analysis summary."""

    top_priorities: list[Priority]
    total_opportunities: int
    high_impact_count: int


class ContextResult(TypedDict, total=False):
    """Return type for build_context method.

    Required fields are always present; optional fields depend on the current step.
    """

    current_step: int
    step_name: str
    session_id: str
    suggested_actions: list[SuggestedAction]
    # Optional fields (depend on step)
    activities: ActivitiesData
    selection_count: int
    analysis_summary: AnalysisSummary


# Step names mapping
STEP_NAMES: dict[int, str] = {
    1: "Upload",
    2: "Map Roles",
    3: "Select Activities",
    4: "Analysis",
    5: "Roadmap",
}


async def get_context_service(db: AsyncSession) -> "ContextService":
    """Dependency injection for ContextService."""
    return ContextService(db=db)


class ContextService:
    """Service for building context for chat-UI coordination.

    This service provides context information based on the current step
    in the discovery workflow, enabling the chat interface to understand
    the user's current position and provide relevant suggestions.
    """

    def __init__(self, db: AsyncSession | None = None) -> None:
        """Initialize the context service.

        Args:
            db: Optional async database session for querying real data.
        """
        self.step_names = STEP_NAMES
        self.db = db

    async def build_context(
        self,
        session_id: UUID,
        current_step: int,
        user_message: str,
    ) -> ContextResult:
        """Build context dictionary for the current session state.

        Args:
            session_id: The unique session identifier.
            current_step: The current step number (1-5).
            user_message: The user's message to analyze for context.

        Returns:
            ContextResult TypedDict containing context information including:
            - current_step: The step number
            - step_name: Human readable step name
            - activities: Activity data (for step 3)
            - selection_count: Number of selections (for step 3)
            - analysis_summary: Analysis results (for step 4+)
            - suggested_actions: Relevant quick actions

        Raises:
            ValueError: If current_step is not in range 1-5.
            ValueError: If user_message exceeds MAX_MESSAGE_LENGTH characters.
        """
        # Validate current_step
        if not (MIN_STEP <= current_step <= MAX_STEP):
            raise ValueError(
                f"current_step must be between {MIN_STEP} and {MAX_STEP}, "
                f"got {current_step}"
            )

        # Validate user_message length
        if len(user_message) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"user_message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            )

        context: dict[str, Any] = {
            "current_step": current_step,
            "step_name": self.step_names.get(current_step, "Unknown"),
            "session_id": str(session_id),
        }

        # Add step-specific data
        if current_step == 3:
            context["activities"] = await self._get_activities_data(session_id)
            context["selection_count"] = await self._get_selection_count(session_id)

        if current_step >= 4:
            context["analysis_summary"] = await self._get_analysis_summary(session_id)

        # Add suggested actions based on context
        context["suggested_actions"] = self._get_suggested_actions(
            current_step, user_message
        )

        return context

    async def _get_activities_data(self, session_id: UUID) -> ActivitiesData:
        """Get activities data for step 3.

        Queries the database for GWA groups and their DWA counts
        based on the session's activity selections.

        Args:
            session_id: The session identifier.

        Returns:
            Dictionary containing activity groups and data.
        """
        if not self.db:
            # Return empty data if no database session
            return {"gwa_groups": [], "total_activities": 0}

        # Query to get GWA groups with counts based on session's selected activities
        # Join: ActivitySelection -> DWA -> IWA -> GWA
        stmt = (
            select(
                OnetGWA.id,
                OnetGWA.name,
                func.count(DiscoveryActivitySelection.id).label("count"),
            )
            .select_from(DiscoveryActivitySelection)
            .join(OnetDWA, DiscoveryActivitySelection.dwa_id == OnetDWA.id)
            .join(OnetIWA, OnetDWA.iwa_id == OnetIWA.id)
            .join(OnetGWA, OnetIWA.gwa_id == OnetGWA.id)
            .where(DiscoveryActivitySelection.session_id == session_id)
            .group_by(OnetGWA.id, OnetGWA.name)
            .order_by(func.count(DiscoveryActivitySelection.id).desc())
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        gwa_groups: list[GWAGroup] = []
        total_activities = 0

        for row in rows:
            gwa_groups.append({
                "id": row.id,
                "name": row.name,
                "count": row.count,
            })
            total_activities += row.count

        return {
            "gwa_groups": gwa_groups,
            "total_activities": total_activities,
        }

    async def _get_selection_count(self, session_id: UUID) -> int:
        """Get the count of selected activities.

        Queries the database for the count of selected activities
        for the given session.

        Args:
            session_id: The session identifier.

        Returns:
            Number of selected activities.
        """
        if not self.db:
            return 0

        stmt = (
            select(func.count(DiscoveryActivitySelection.id))
            .where(DiscoveryActivitySelection.session_id == session_id)
            .where(DiscoveryActivitySelection.selected == True)  # noqa: E712
        )

        result = await self.db.execute(stmt)
        count = result.scalar()
        return count or 0

    async def _get_analysis_summary(self, session_id: UUID) -> AnalysisSummary:
        """Get analysis summary for step 4+.

        Queries the database for analysis results and returns
        top priorities and summary statistics.

        Args:
            session_id: The session identifier.

        Returns:
            Dictionary containing analysis summary with top priorities.
        """
        if not self.db:
            return {
                "top_priorities": [],
                "total_opportunities": 0,
                "high_impact_count": 0,
            }

        # Get top 5 priorities by priority_score
        stmt = (
            select(DiscoveryAnalysisResult)
            .where(DiscoveryAnalysisResult.session_id == session_id)
            .order_by(DiscoveryAnalysisResult.priority_score.desc())
            .limit(5)
        )

        result = await self.db.execute(stmt)
        top_results = result.scalars().all()

        top_priorities: list[Priority] = [
            {
                "id": str(r.id),
                "name": r.dimension_value,
                "score": r.priority_score or 0.0,
            }
            for r in top_results
        ]

        # Get total count and high impact count
        count_stmt = (
            select(
                func.count(DiscoveryAnalysisResult.id).label("total"),
                func.count(
                    func.nullif(
                        DiscoveryAnalysisResult.impact_score < 0.7,
                        True,
                    )
                ).label("high_impact"),
            )
            .where(DiscoveryAnalysisResult.session_id == session_id)
        )

        count_result = await self.db.execute(count_stmt)
        counts = count_result.one_or_none()

        total_opportunities = counts.total if counts else 0

        # Count high impact separately for clarity
        high_impact_stmt = (
            select(func.count(DiscoveryAnalysisResult.id))
            .where(DiscoveryAnalysisResult.session_id == session_id)
            .where(DiscoveryAnalysisResult.impact_score >= 0.7)
        )
        high_impact_result = await self.db.execute(high_impact_stmt)
        high_impact_count = high_impact_result.scalar() or 0

        return {
            "top_priorities": top_priorities,
            "total_opportunities": total_opportunities,
            "high_impact_count": high_impact_count,
        }

    def _get_suggested_actions(
        self, current_step: int, user_message: str
    ) -> list[dict[str, Any]]:
        """Get suggested quick actions based on context.

        Args:
            current_step: The current step number.
            user_message: The user's message to analyze.

        Returns:
            List of suggested action dictionaries.
        """
        actions: list[dict[str, Any]] = []

        # Analyze message for keywords and suggest relevant actions
        message_lower = user_message.lower()

        if current_step == 2:
            # Map Roles step
            if any(
                keyword in message_lower
                for keyword in ["not sure", "unsure", "wrong", "change", "different"]
            ):
                actions.append(
                    {
                        "action": "remap_role",
                        "label": "Change Role Mapping",
                        "description": "Select a different O*NET role for this position",
                    }
                )
            actions.append(
                {
                    "action": "view_alternatives",
                    "label": "View Alternative Mappings",
                    "description": "See other possible role mappings",
                }
            )

        elif current_step == 3:
            # Select Activities step
            actions.append(
                {
                    "action": "select_all_category",
                    "label": "Select All in Category",
                    "description": "Select all activities in a category",
                }
            )
            actions.append(
                {
                    "action": "clear_selections",
                    "label": "Clear All Selections",
                    "description": "Remove all selected activities",
                }
            )

        elif current_step == 4:
            # Analysis step
            actions.append(
                {
                    "action": "export_analysis",
                    "label": "Export Analysis",
                    "description": "Download the analysis results",
                }
            )
            actions.append(
                {
                    "action": "refine_priorities",
                    "label": "Refine Priorities",
                    "description": "Adjust priority rankings",
                }
            )

        elif current_step == 5:
            # Roadmap step
            actions.append(
                {
                    "action": "export_roadmap",
                    "label": "Export Roadmap",
                    "description": "Download the implementation roadmap",
                }
            )
            actions.append(
                {
                    "action": "share_roadmap",
                    "label": "Share Roadmap",
                    "description": "Share with team members",
                }
            )

        return actions
