"""Scoring service for discovery opportunity analysis.

Provides the ScoringService for calculating impact scores based on
role headcount and AI exposure scores. Impact scores help prioritize
which roles have the highest potential for AI agent automation.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.modules.discovery.enums import AnalysisDimension
from app.modules.discovery.schemas.scoring import (
    AnalysisScores,
    DimensionAggregation,
    SessionScoringResult,
)

if TYPE_CHECKING:
    from app.modules.discovery.models.session import DiscoverySession
    from app.modules.discovery.repositories.activity_selection_repository import (
        DiscoveryActivitySelectionRepository,
    )
    from app.modules.discovery.repositories.analysis_result_repository import (
        DiscoveryAnalysisResultRepository,
    )
    from app.modules.discovery.repositories.onet_repository import OnetDwaRepository
    from app.modules.discovery.repositories.role_mapping_repository import (
        DiscoveryRoleMappingRepository,
    )


@dataclass
class _DwaWithExposure:
    """Internal class for holding DWA with effective exposure score."""

    ai_exposure_override: float
    dwa_id: str
    dwa_name: str


class ScoringService:
    """Service for calculating impact and priority scores.

    This service calculates impact scores for role mappings based on:
    - Role headcount (row_count): Number of employees in a role
    - AI exposure score: How automatable the role's tasks are (0.0-1.0)

    Impact is calculated as: (role_count * exposure) / max_headcount
    This normalizes the score to a 0-1 range for consistent comparison.

    Attributes:
        DEFAULT_MAX_HEADCOUNT: Default maximum headcount for normalization (1000).
    """

    DEFAULT_MAX_HEADCOUNT = 1000

    def calculate_impact_score(
        self,
        role_mapping: Any,
        exposure_score: float,
        max_headcount: int = DEFAULT_MAX_HEADCOUNT,
    ) -> float:
        """Calculate the impact score for a single role mapping.

        Impact is calculated as (role_count * exposure_score) / max_headcount,
        capped at 1.0 to ensure the result is always in the 0-1 range.

        Args:
            role_mapping: A role mapping object with a row_count attribute
                representing the number of employees in this role.
            exposure_score: AI exposure score for the role (0.0-1.0).
            max_headcount: Maximum headcount for normalization. Defaults to 1000.
                Higher values mean individual roles contribute less to the score.

        Returns:
            Impact score normalized to 0.0-1.0 range. Returns 0.0 if either
            row_count is 0 or exposure_score is 0.0.

        Example:
            >>> service = ScoringService()
            >>> role = MagicMock(row_count=100)
            >>> service.calculate_impact_score(role, exposure_score=0.8)
            0.08
        """
        row_count = role_mapping.row_count or 0

        # Early return for zero values
        if row_count == 0 or exposure_score == 0.0:
            return 0.0

        # Calculate raw impact and normalize
        raw_impact = row_count * exposure_score
        normalized_impact = raw_impact / max_headcount

        # Cap at 1.0 to ensure result is always in 0-1 range
        return min(normalized_impact, 1.0)

    def calculate_impact_scores_for_session(
        self,
        role_mappings: list[Any],
        exposure_scores: dict[str, float],
    ) -> dict[str, float]:
        """Calculate impact scores for all role mappings in a session.

        Uses the maximum row_count from the provided role mappings as the
        normalization factor, ensuring scores are relative to the session's
        largest role.

        Args:
            role_mappings: List of role mapping objects, each with id and
                row_count attributes.
            exposure_scores: Dictionary mapping role_mapping.id to exposure
                score (0.0-1.0).

        Returns:
            Dictionary mapping role_mapping.id to calculated impact score.
            Roles without a matching exposure score are skipped.

        Example:
            >>> service = ScoringService()
            >>> mappings = [MagicMock(id="role-1", row_count=100)]
            >>> exposures = {"role-1": 0.8}
            >>> service.calculate_impact_scores_for_session(mappings, exposures)
            {"role-1": 0.8}
        """
        if not role_mappings:
            return {}

        # Find max headcount for normalization
        max_headcount = max(
            (rm.row_count or 0 for rm in role_mappings),
            default=self.DEFAULT_MAX_HEADCOUNT,
        )

        # Use default if max is 0 to avoid division issues
        if max_headcount == 0:
            max_headcount = self.DEFAULT_MAX_HEADCOUNT

        impacts: dict[str, float] = {}
        for role_mapping in role_mappings:
            role_id = role_mapping.id
            if role_id in exposure_scores:
                exposure = exposure_scores[role_id]
                impacts[role_id] = self.calculate_impact_score(
                    role_mapping=role_mapping,
                    exposure_score=exposure,
                    max_headcount=max_headcount,
                )

        return impacts

    def calculate_priority_score(
        self,
        exposure: float,
        impact: float,
        complexity: float,
        weights: dict[str, float] | None = None,
    ) -> float:
        """Calculate the priority score for a role based on weighted factors.

        Priority is calculated using a weighted formula that considers exposure,
        impact, and inverse complexity. Higher priority means the role should
        be addressed sooner for AI automation opportunities.

        Formula: (exposure * w_e) + (impact * w_i) + ((1 - complexity) * w_c)

        The inverse of complexity is used because lower complexity makes a role
        easier to automate, thus higher priority.

        Args:
            exposure: AI exposure score for the role (0.0-1.0). Higher means
                more tasks can be automated by AI.
            impact: Impact score for the role (0.0-1.0). Higher means more
                business value from automation.
            complexity: Complexity score for the role (0.0-1.0). Higher means
                the role is harder to automate.
            weights: Optional custom weights dictionary with keys 'exposure',
                'impact', and 'complexity'. Values should sum to 1.0.
                Defaults to exposure=0.4, impact=0.4, complexity=0.2.

        Returns:
            Priority score normalized to 0.0-1.0 range.

        Example:
            >>> service = ScoringService()
            >>> service.calculate_priority_score(0.8, 0.6, 0.3)
            0.70
        """
        # Default weights: exposure=40%, impact=40%, inverse_complexity=20%
        default_weights = {"exposure": 0.4, "impact": 0.4, "complexity": 0.2}
        w = weights if weights is not None else default_weights

        # Calculate weighted priority
        # Note: complexity contribution is inverted (1 - complexity)
        priority = (
            (exposure * w["exposure"])
            + (impact * w["impact"])
            + ((1 - complexity) * w["complexity"])
        )

        # Ensure result is bounded to 0-1 range
        return max(0.0, min(1.0, priority))

    def calculate_complexity_score(self, exposure: float) -> float:
        """Calculate complexity score as the inverse of exposure.

        This provides a simple approximation where tasks with high AI exposure
        (easily automated) have low complexity, and tasks with low AI exposure
        (hard to automate) have high complexity.

        Args:
            exposure: AI exposure score (0.0-1.0).

        Returns:
            Complexity score (0.0-1.0), calculated as 1 - exposure.

        Example:
            >>> service = ScoringService()
            >>> service.calculate_complexity_score(0.75)
            0.25
        """
        return 1.0 - exposure

    def calculate_all_scores_for_role(
        self,
        role_mapping: Any,
        selected_dwas: list[Any],
        max_headcount: int = DEFAULT_MAX_HEADCOUNT,
    ) -> dict[str, float]:
        """Calculate all scores (exposure, impact, complexity, priority) for a role.

        This method aggregates exposure from selected DWAs (Detailed Work Activities),
        derives complexity from exposure, calculates impact from role headcount
        and exposure, and finally computes the overall priority score.

        Args:
            role_mapping: A role mapping object with id and row_count attributes.
            selected_dwas: List of DWA objects with ai_exposure_override attribute.
                The average of these values becomes the role's exposure score.
            max_headcount: Maximum headcount for impact normalization.
                Defaults to 1000.

        Returns:
            Dictionary with keys 'exposure', 'impact', 'complexity', 'priority',
            each containing a float score in the 0.0-1.0 range.

        Example:
            >>> service = ScoringService()
            >>> role = MagicMock(id="role-1", row_count=200)
            >>> dwas = [MagicMock(ai_exposure_override=0.8)]
            >>> service.calculate_all_scores_for_role(role, dwas, 1000)
            {'exposure': 0.8, 'impact': 0.16, 'complexity': 0.2, 'priority': ...}
        """
        # Calculate exposure as average of DWA exposures
        if selected_dwas:
            total_exposure = sum(dwa.ai_exposure_override for dwa in selected_dwas)
            exposure = total_exposure / len(selected_dwas)
        else:
            exposure = 0.0

        # Derive complexity from exposure (inverse relationship)
        complexity = self.calculate_complexity_score(exposure)

        # Calculate impact using existing method
        impact = self.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=exposure,
            max_headcount=max_headcount,
        )

        # Calculate priority from all three scores
        priority = self.calculate_priority_score(
            exposure=exposure,
            impact=impact,
            complexity=complexity,
        )

        return {
            "exposure": exposure,
            "impact": impact,
            "complexity": complexity,
            "priority": priority,
        }

    def _get_dimension_value(
        self,
        role_mapping: Any,
        dimension: AnalysisDimension,
    ) -> str:
        """Extract dimension value from a role mapping.

        Args:
            role_mapping: A role mapping object with source_role attribute and
                metadata dict containing department, lob, and geography keys.
            dimension: The dimension to extract the value for.

        Returns:
            The dimension value, or "Unknown" if the value is None or missing.
        """
        if dimension == AnalysisDimension.TASK:
            # TASK dimension is handled separately via dwa_selections
            return "Unknown"

        if dimension == AnalysisDimension.ROLE:
            # ROLE uses source_role directly
            value = role_mapping.source_role
            return value if value is not None else "Unknown"

        # DEPARTMENT, LOB, GEOGRAPHY use metadata dict
        metadata_key_map = {
            AnalysisDimension.DEPARTMENT: "department",
            AnalysisDimension.LOB: "lob",
            AnalysisDimension.GEOGRAPHY: "geography",
        }

        key = metadata_key_map.get(dimension)
        if key is None:
            return "Unknown"

        value = role_mapping.metadata.get(key)
        return value if value is not None else "Unknown"

    def _calculate_weighted_average(
        self,
        values_with_weights: list[tuple[float, int]],
    ) -> float:
        """Calculate weighted average of values.

        Args:
            values_with_weights: List of (value, weight) tuples.

        Returns:
            Weighted average, or 0.0 if total weight is 0.
        """
        total_weight = sum(weight for _, weight in values_with_weights)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(value * weight for value, weight in values_with_weights)
        return weighted_sum / total_weight

    def aggregate_by_dimension(
        self,
        role_mappings: list[Any],
        scores: dict[str, dict[str, float]],
        dimension: AnalysisDimension,
        dwa_selections: dict[str, list[Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Aggregate scores by a specified dimension using weighted averages.

        Groups role mappings by the specified dimension and calculates
        weighted average scores based on headcount (row_count).

        Args:
            role_mappings: List of role mapping objects with id, source_role,
                row_count, and metadata dict containing department, lob, geography.
            scores: Dictionary mapping role_mapping.id to a dict containing
                ai_exposure_score, impact_score, complexity_score, priority_score.
            dimension: The AnalysisDimension to aggregate by (ROLE, DEPARTMENT,
                LOB, GEOGRAPHY, or TASK).
            dwa_selections: Optional dictionary keyed by role_mapping.id for TASK
                dimension aggregation. Each value is a list of DWA objects with
                dwa_id and dwa_name attributes.

        Returns:
            List of aggregation result dictionaries, each containing:
            - dimension: The AnalysisDimension enum value
            - dimension_value: The grouping key (e.g., "Technology" for DEPARTMENT)
            - ai_exposure_score: Weighted average exposure score
            - impact_score: Weighted average impact score
            - complexity_score: Weighted average complexity score
            - priority_score: Weighted average priority score
            - total_headcount: Sum of row_count for all roles in this group
            - role_count: Number of roles in this group
            - breakdown: List of contributing role details

        Example:
            >>> service = ScoringService()
            >>> service.aggregate_by_dimension(
            ...     role_mappings=[...],
            ...     scores={"role-1": {...}},
            ...     dimension=AnalysisDimension.DEPARTMENT,
            ... )
            [{"dimension": DEPARTMENT, "dimension_value": "Technology", ...}]
        """
        if not role_mappings:
            return []

        # Handle TASK dimension separately
        if dimension == AnalysisDimension.TASK:
            return self._aggregate_by_task(role_mappings, scores, dwa_selections or {})

        # Group roles by dimension value
        groups: dict[str, list[Any]] = defaultdict(list)
        for role_mapping in role_mappings:
            dim_value = self._get_dimension_value(role_mapping, dimension)
            groups[dim_value].append(role_mapping)

        # Calculate aggregated scores for each group
        results: list[dict[str, Any]] = []
        for dim_value, group_mappings in groups.items():
            result = self._aggregate_group(
                dimension=dimension,
                dimension_value=dim_value,
                role_mappings=group_mappings,
                scores=scores,
            )
            results.append(result)

        return results

    def _aggregate_by_task(
        self,
        role_mappings: list[Any],
        scores: dict[str, dict[str, float]],
        dwa_selections: dict[str, list[Any]],
    ) -> list[dict[str, Any]]:
        """Aggregate scores by TASK dimension using DWA selections.

        Args:
            role_mappings: List of role mapping objects.
            scores: Dictionary mapping role_mapping.id to score dict.
            dwa_selections: Dictionary keyed by role_mapping.id, where each value
                is a list of DWA objects with dwa_id and dwa_name attributes.

        Returns:
            List of aggregation results grouped by task (dwa_name).
        """
        # Create a lookup for role mappings by id
        role_mapping_lookup: dict[str, Any] = {
            rm.id: rm for rm in role_mappings
        }

        # Group by task (dwa_name) - iterate over all DWAs for each role
        task_groups: dict[str, list[str]] = defaultdict(list)
        for role_id, dwas in dwa_selections.items():
            for dwa in dwas:
                task_groups[dwa.dwa_name].append(role_id)

        # Calculate aggregated scores for each task
        results: list[dict[str, Any]] = []
        for task_name, role_ids in task_groups.items():
            # Get role mappings for this task
            task_mappings = [
                role_mapping_lookup[rid]
                for rid in role_ids
                if rid in role_mapping_lookup
            ]

            if not task_mappings:
                continue

            result = self._aggregate_group(
                dimension=AnalysisDimension.TASK,
                dimension_value=task_name,
                role_mappings=task_mappings,
                scores=scores,
            )
            results.append(result)

        return results

    def _aggregate_group(
        self,
        dimension: AnalysisDimension,
        dimension_value: str,
        role_mappings: list[Any],
        scores: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        """Calculate aggregated scores for a group of role mappings.

        Args:
            dimension: The AnalysisDimension being aggregated.
            dimension_value: The grouping key value.
            role_mappings: List of role mappings in this group.
            scores: Dictionary mapping role_mapping.id to score dict.

        Returns:
            Aggregation result dictionary with all required fields.
        """
        # Collect values and weights for weighted averaging
        exposure_values: list[tuple[float, int]] = []
        impact_values: list[tuple[float, int]] = []
        complexity_values: list[tuple[float, int]] = []
        priority_values: list[tuple[float, int]] = []

        breakdown: list[dict[str, Any]] = []
        total_headcount = 0
        role_count = 0

        for rm in role_mappings:
            role_id = rm.id
            if role_id not in scores:
                continue

            role_scores = scores[role_id]
            headcount = rm.row_count or 0
            total_headcount += headcount
            role_count += 1

            # Collect values with headcount weights
            exposure_values.append(
                (role_scores.get("exposure", 0.0), headcount)
            )
            impact_values.append(
                (role_scores.get("impact", 0.0), headcount)
            )
            complexity_values.append(
                (role_scores.get("complexity", 0.0), headcount)
            )
            priority_values.append(
                (role_scores.get("priority", 0.0), headcount)
            )

            # Add to breakdown
            breakdown.append({
                "role_id": role_id,
                "role_name": rm.source_role,
                "headcount": headcount,
                "ai_exposure_score": role_scores.get("exposure", 0.0),
                "impact_score": role_scores.get("impact", 0.0),
                "complexity_score": role_scores.get("complexity", 0.0),
                "priority_score": role_scores.get("priority", 0.0),
            })

        return {
            "dimension": dimension,
            "dimension_value": dimension_value,
            "ai_exposure_score": self._calculate_weighted_average(exposure_values),
            "impact_score": self._calculate_weighted_average(impact_values),
            "complexity_score": self._calculate_weighted_average(complexity_values),
            "priority_score": self._calculate_weighted_average(priority_values),
            "total_headcount": total_headcount,
            "role_count": role_count,
            "breakdown": {"roles": breakdown},
        }

    def aggregate_all_dimensions(
        self,
        role_mappings: list[Any],
        scores: dict[str, dict[str, float]],
        dwa_selections: dict[str, list[Any]] | None = None,
    ) -> dict[AnalysisDimension, list[dict[str, Any]]]:
        """Aggregate scores across all 5 dimensions in one call.

        Convenience method that calls aggregate_by_dimension for each
        AnalysisDimension value.

        Args:
            role_mappings: List of role mapping objects with id, source_role,
                row_count, and metadata dict containing department, lob, geography.
            scores: Dictionary mapping role_mapping.id to a dict containing
                ai_exposure_score, impact_score, complexity_score, priority_score.
            dwa_selections: Optional dictionary keyed by role_mapping.id for TASK
                dimension aggregation.

        Returns:
            Dictionary keyed by AnalysisDimension enum, where each value is
            the list of aggregation results for that dimension.

        Example:
            >>> service = ScoringService()
            >>> results = service.aggregate_all_dimensions(role_mappings, scores)
            >>> results[AnalysisDimension.DEPARTMENT]
            [{"dimension": DEPARTMENT, "dimension_value": "Technology", ...}]
        """
        return {
            dim: self.aggregate_by_dimension(
                role_mappings=role_mappings,
                scores=scores,
                dimension=dim,
                dwa_selections=dwa_selections,
            )
            for dim in AnalysisDimension
        }

    async def score_session(
        self,
        session: "DiscoverySession",
        role_mapping_repo: "DiscoveryRoleMappingRepository",
        activity_selection_repo: "DiscoveryActivitySelectionRepository",
        dwa_repo: "OnetDwaRepository",
        analysis_result_repo: "DiscoveryAnalysisResultRepository | None" = None,
        persist: bool = False,
    ) -> SessionScoringResult:
        """Score all role mappings for a discovery session.

        This method orchestrates the complete scoring workflow:
        1. Get all role mappings for the session
        2. For each role, get selected activity DWAs
        3. Get DWA objects to compute exposure scores
        4. Calculate all scores for each role
        5. Aggregate by all dimensions
        6. Optionally persist results to the database

        Exposure score calculation:
        - Uses dwa.ai_exposure_override if set
        - Falls back to dwa.iwa.gwa.ai_exposure_score otherwise
        - Averages across all selected DWAs for the role

        Args:
            session: The discovery session to score.
            role_mapping_repo: Repository for role mapping queries.
            activity_selection_repo: Repository for activity selection queries.
            dwa_repo: Repository for DWA queries with IWA/GWA relationships.
            analysis_result_repo: Optional repository for persisting results.
                Required if persist=True.
            persist: Whether to persist results to the database. If True,
                clears existing results and bulk creates new ones.

        Returns:
            SessionScoringResult containing all scores and aggregations.

        Raises:
            ValueError: If persist=True but analysis_result_repo is None.

        Example:
            >>> service = ScoringService()
            >>> result = await service.score_session(
            ...     session=session,
            ...     role_mapping_repo=role_mapping_repo,
            ...     activity_selection_repo=activity_selection_repo,
            ...     dwa_repo=dwa_repo,
            ...     persist=False,
            ... )
            >>> result.role_scores["role-1"].exposure
            0.75
        """
        if persist and analysis_result_repo is None:
            raise ValueError("analysis_result_repo is required when persist=True")

        # Get all role mappings for the session
        role_mappings = await role_mapping_repo.get_by_session_id(session.id)

        if not role_mappings:
            return SessionScoringResult(
                session_id=session.id,
                role_scores={},
                dimension_aggregations=[],
                max_headcount=0,
                total_headcount=0,
                total_roles=0,
            )

        # Calculate max headcount for normalization
        max_headcount = max(
            (rm.row_count or 0 for rm in role_mappings),
            default=self.DEFAULT_MAX_HEADCOUNT,
        )
        if max_headcount == 0:
            max_headcount = self.DEFAULT_MAX_HEADCOUNT

        # Calculate total headcount
        total_headcount = sum(rm.row_count or 0 for rm in role_mappings)

        # For each role, get selected DWAs and calculate scores
        role_scores: dict[str, AnalysisScores] = {}
        scores_for_aggregation: dict[str, dict[str, float]] = {}
        dwa_selections_for_aggregation: dict[str, list[Any]] = {}

        for role_mapping in role_mappings:
            role_id = str(role_mapping.id)

            # Get selected activities for this role
            selections = await activity_selection_repo.get_selected_for_role_mapping(
                role_mapping.id
            )

            # Get DWA objects for exposure calculation
            dwas = []
            dwa_info_list = []
            for selection in selections:
                dwa = await dwa_repo.get_by_id(selection.dwa_id)
                if dwa:
                    # Calculate effective exposure score
                    if dwa.ai_exposure_override is not None:
                        effective_exposure = dwa.ai_exposure_override
                    elif dwa.iwa and dwa.iwa.gwa and dwa.iwa.gwa.ai_exposure_score is not None:
                        effective_exposure = dwa.iwa.gwa.ai_exposure_score
                    else:
                        effective_exposure = 0.0

                    # Create a dataclass instance with the effective exposure
                    dwa_with_exposure = _DwaWithExposure(
                        ai_exposure_override=effective_exposure,
                        dwa_id=dwa.id,
                        dwa_name=dwa.name,
                    )
                    dwas.append(dwa_with_exposure)
                    dwa_info_list.append(dwa_with_exposure)

            # Calculate all scores for this role
            scores = self.calculate_all_scores_for_role(
                role_mapping=role_mapping,
                selected_dwas=dwas,
                max_headcount=max_headcount,
            )

            # Store as AnalysisScores dataclass
            role_scores[role_id] = AnalysisScores(
                exposure=scores["exposure"],
                impact=scores["impact"],
                complexity=scores["complexity"],
                priority=scores["priority"],
            )

            # Store for aggregation
            scores_for_aggregation[role_id] = scores
            dwa_selections_for_aggregation[role_id] = dwa_info_list

        # Aggregate by all dimensions
        all_aggregations = self.aggregate_all_dimensions(
            role_mappings=role_mappings,
            scores=scores_for_aggregation,
            dwa_selections=dwa_selections_for_aggregation,
        )

        # Convert aggregation dicts to DimensionAggregation dataclasses
        dimension_aggregations: list[DimensionAggregation] = []
        for dim, agg_list in all_aggregations.items():
            for agg in agg_list:
                dimension_aggregations.append(
                    DimensionAggregation(
                        dimension=agg["dimension"],
                        dimension_value=agg["dimension_value"],
                        ai_exposure_score=agg["ai_exposure_score"],
                        impact_score=agg["impact_score"],
                        complexity_score=agg["complexity_score"],
                        priority_score=agg["priority_score"],
                        total_headcount=agg["total_headcount"],
                        role_count=agg["role_count"],
                        breakdown=agg["breakdown"],
                    )
                )

        # Persist results if requested
        if persist and analysis_result_repo is not None:
            # Clear old results
            await analysis_result_repo.delete_by_session_id(session.id)

            # Prepare results for bulk create
            results_to_create: list[dict] = []

            # Add role-level results (ROLE dimension)
            for role_mapping in role_mappings:
                role_id = str(role_mapping.id)
                if role_id in role_scores:
                    scores = role_scores[role_id]
                    results_to_create.append({
                        "session_id": session.id,
                        "role_mapping_id": role_mapping.id,
                        "dimension": AnalysisDimension.ROLE,
                        "dimension_value": role_mapping.source_role or "Unknown",
                        "ai_exposure_score": scores.exposure,
                        "impact_score": scores.impact,
                        "complexity_score": scores.complexity,
                        "priority_score": scores.priority,
                        "breakdown": None,
                    })

            # Note: We only persist role-level results (ROLE dimension) to the database.
            # Aggregations for other dimensions (DEPARTMENT, LOB, GEOGRAPHY, TASK)
            # are computed on-the-fly from role results and returned in the response,
            # but not persisted. This avoids the semantic issue of linking aggregated
            # dimension results to an arbitrary role_mapping_id.

            if results_to_create:
                await analysis_result_repo.bulk_create(results_to_create)

        return SessionScoringResult(
            session_id=session.id,
            role_scores=role_scores,
            dimension_aggregations=dimension_aggregations,
            max_headcount=max_headcount,
            total_headcount=total_headcount,
            total_roles=len(role_mappings),
        )
