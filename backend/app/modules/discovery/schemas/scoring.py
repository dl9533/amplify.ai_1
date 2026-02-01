"""Scoring schemas for discovery opportunity analysis.

This module provides dataclasses for representing scoring results:
- AnalysisScores: Individual role scores (exposure, impact, complexity, priority)
- DimensionAggregation: Aggregated scores for a dimension value
- SessionScoringResult: Complete scoring result for a discovery session
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.modules.discovery.enums import AnalysisDimension


@dataclass
class AnalysisScores:
    """Scores for a single role mapping.

    All scores are normalized to the 0-1 range.

    Attributes:
        exposure: AI exposure score (0-1), how automatable the role's tasks are.
        impact: Impact score (0-1), role_count * exposure normalized.
        complexity: Complexity score (0-1), inverse of exposure.
        priority: Priority score (0-1), weighted combination of all factors.
    """

    exposure: float
    impact: float
    complexity: float
    priority: float


@dataclass
class DimensionAggregation:
    """Aggregated scores for a dimension value.

    Represents weighted average scores for all roles grouped by a dimension
    value (e.g., all roles in the "Technology" department).

    Attributes:
        dimension: The analysis dimension (ROLE, TASK, LOB, GEOGRAPHY, DEPARTMENT).
        dimension_value: The grouping key (e.g., "Technology" for DEPARTMENT).
        ai_exposure_score: Weighted average exposure score.
        impact_score: Weighted average impact score.
        complexity_score: Weighted average complexity score.
        priority_score: Weighted average priority score.
        total_headcount: Sum of row_count for all roles in this group.
        role_count: Number of roles in this group.
        breakdown: Detailed breakdown of contributing roles.
    """

    dimension: AnalysisDimension
    dimension_value: str
    ai_exposure_score: float
    impact_score: float
    complexity_score: float
    priority_score: float
    total_headcount: int
    role_count: int
    breakdown: dict[str, Any]


@dataclass
class SessionScoringResult:
    """Complete scoring result for a discovery session.

    Contains all calculated scores for roles and dimension aggregations.

    Attributes:
        session_id: UUID of the discovery session.
        role_scores: Dictionary mapping role_mapping.id to AnalysisScores.
        dimension_aggregations: List of aggregations for all dimensions.
        max_headcount: Maximum headcount across all roles (for normalization).
        total_headcount: Total headcount across all roles.
        total_roles: Number of roles scored.
    """

    session_id: UUID
    role_scores: dict[str, AnalysisScores]
    dimension_aggregations: list[DimensionAggregation]
    max_headcount: int
    total_headcount: int
    total_roles: int
