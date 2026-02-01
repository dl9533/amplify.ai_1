# backend/tests/unit/modules/discovery/test_dimension_aggregator.py
"""Tests for multi-dimension score aggregation in the discovery module.

These tests verify the ScoringService's ability to aggregate scores across
different dimensions (ROLE, DEPARTMENT, LOB, GEOGRAPHY, TASK) using weighted
averages based on role headcount (row_count).
"""
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.services.scoring import ScoringService
from app.modules.discovery.enums import AnalysisDimension


@pytest.fixture
def scoring_service():
    """Create a ScoringService instance for testing."""
    return ScoringService()


@pytest.fixture
def sample_role_mappings():
    """Create sample role mappings with various dimensions.

    Returns a list of mock role mappings representing:
    - Software Engineer: Technology dept, Engineering LOB, US geography, 100 headcount
    - Data Analyst: Technology dept, Analytics LOB, US geography, 50 headcount
    - HR Manager: HR dept, People LOB, UK geography, 30 headcount
    - Recruiter: HR dept, People LOB, UK geography, 20 headcount
    """
    return [
        MagicMock(
            id="role-1",
            source_role="Software Engineer",
            row_count=100,
            metadata={
                "department": "Technology",
                "lob": "Engineering",
                "geography": "US",
            },
        ),
        MagicMock(
            id="role-2",
            source_role="Data Analyst",
            row_count=50,
            metadata={
                "department": "Technology",
                "lob": "Analytics",
                "geography": "US",
            },
        ),
        MagicMock(
            id="role-3",
            source_role="HR Manager",
            row_count=30,
            metadata={
                "department": "HR",
                "lob": "People",
                "geography": "UK",
            },
        ),
        MagicMock(
            id="role-4",
            source_role="Recruiter",
            row_count=20,
            metadata={
                "department": "HR",
                "lob": "People",
                "geography": "UK",
            },
        ),
    ]


@pytest.fixture
def sample_scores():
    """Create sample scores for each role.

    Scores dict maps role_mapping.id to a dict containing:
    - exposure: How automatable the role is (0-1)
    - impact: Business impact of automation (0-1)
    - complexity: How complex to automate (0-1)
    - priority: Overall priority (0-1)

    Note: Uses short keys to match calculate_all_scores_for_role() output.
    """
    return {
        "role-1": {
            "exposure": 0.85,
            "impact": 0.70,
            "complexity": 0.15,
            "priority": 0.80,
        },
        "role-2": {
            "exposure": 0.90,
            "impact": 0.60,
            "complexity": 0.10,
            "priority": 0.75,
        },
        "role-3": {
            "exposure": 0.40,
            "impact": 0.30,
            "complexity": 0.60,
            "priority": 0.35,
        },
        "role-4": {
            "exposure": 0.65,
            "impact": 0.35,
            "complexity": 0.35,
            "priority": 0.55,
        },
    }


class TestAggregateDimensionRole:
    """Tests for aggregating by ROLE dimension."""

    def test_aggregate_by_role_dimension(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Aggregating by ROLE should return one result per unique role."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.ROLE,
        )

        # Should have 4 results (one per role)
        assert len(results) == 4

        # Check role names are preserved
        role_names = [r["dimension_value"] for r in results]
        assert "Software Engineer" in role_names
        assert "Data Analyst" in role_names
        assert "HR Manager" in role_names
        assert "Recruiter" in role_names


class TestAggregateDimensionDepartment:
    """Tests for aggregating by DEPARTMENT dimension."""

    def test_aggregate_by_department_dimension(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Aggregating by DEPARTMENT should group roles by department."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT,
        )

        # Should have 2 results (Technology and HR)
        assert len(results) == 2

        dept_names = [r["dimension_value"] for r in results]
        assert "Technology" in dept_names
        assert "HR" in dept_names

        # Find Technology department result
        tech_result = next(r for r in results if r["dimension_value"] == "Technology")
        assert tech_result["total_headcount"] == 150  # 100 + 50
        assert tech_result["role_count"] == 2


class TestAggregateDimensionLob:
    """Tests for aggregating by LOB (Line of Business) dimension."""

    def test_aggregate_by_lob_dimension(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Aggregating by LOB should group roles by line of business."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.LOB,
        )

        # Should have 3 results (Engineering, Analytics, People)
        assert len(results) == 3

        lob_names = [r["dimension_value"] for r in results]
        assert "Engineering" in lob_names
        assert "Analytics" in lob_names
        assert "People" in lob_names


class TestAggregateDimensionGeography:
    """Tests for aggregating by GEOGRAPHY dimension."""

    def test_aggregate_by_geography_dimension(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Aggregating by GEOGRAPHY should group roles by location."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.GEOGRAPHY,
        )

        # Should have 2 results (US and UK)
        assert len(results) == 2

        geo_names = [r["dimension_value"] for r in results]
        assert "US" in geo_names
        assert "UK" in geo_names

        # Find US result
        us_result = next(r for r in results if r["dimension_value"] == "US")
        assert us_result["total_headcount"] == 150  # 100 + 50


class TestAggregateDimensionTask:
    """Tests for aggregating by TASK dimension."""

    def test_aggregate_by_task_dimension(self, scoring_service):
        """Aggregating by TASK should group by DWA selections."""
        # Create role mappings with task info via dwa_selections
        role_mappings = [
            MagicMock(
                id="role-1",
                source_role="Developer",
                row_count=100,
                metadata={
                    "department": "Tech",
                    "lob": "Eng",
                    "geography": "US",
                },
            ),
            MagicMock(
                id="role-2",
                source_role="Analyst",
                row_count=50,
                metadata={
                    "department": "Tech",
                    "lob": "Eng",
                    "geography": "US",
                },
            ),
        ]

        scores = {
            "role-1": {
                "exposure": 0.80,
                "impact": 0.60,
                "complexity": 0.20,
                "priority": 0.70,
            },
            "role-2": {
                "exposure": 0.70,
                "impact": 0.50,
                "complexity": 0.30,
                "priority": 0.60,
            },
        }

        # DWA selections keyed by role_mapping.id
        dwa_selections = {
            "role-1": [
                MagicMock(dwa_id="4.A.1.a.1", dwa_name="Write code"),
                MagicMock(dwa_id="4.A.2.a.1", dwa_name="Review documents"),
            ],
            "role-2": [
                MagicMock(dwa_id="4.A.2.a.1", dwa_name="Review documents"),
            ],
        }

        results = scoring_service.aggregate_by_dimension(
            role_mappings=role_mappings,
            scores=scores,
            dimension=AnalysisDimension.TASK,
            dwa_selections=dwa_selections,
        )

        # Should have 2 tasks: "Write code" and "Review documents"
        assert len(results) == 2

        task_names = [r["dimension_value"] for r in results]
        assert "Write code" in task_names
        assert "Review documents" in task_names


class TestWeightedAverageScores:
    """Tests for weighted average score calculations."""

    def test_aggregation_includes_weighted_average_scores(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Aggregated scores should use weighted average by headcount.

        Technology department has:
        - Software Engineer: 100 headcount, exposure=0.85
        - Data Analyst: 50 headcount, exposure=0.90

        Weighted average = (100 * 0.85 + 50 * 0.90) / (100 + 50)
                        = (85 + 45) / 150 = 130 / 150 = 0.867
        """
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT,
        )

        tech_result = next(r for r in results if r["dimension_value"] == "Technology")

        # Verify weighted average for exposure score
        # (100 * 0.85 + 50 * 0.90) / 150 = 0.867
        expected_exposure = (100 * 0.85 + 50 * 0.90) / 150
        assert tech_result["ai_exposure_score"] == pytest.approx(
            expected_exposure, rel=0.01
        )

        # Verify weighted average for impact score
        # (100 * 0.70 + 50 * 0.60) / 150 = 0.667
        expected_impact = (100 * 0.70 + 50 * 0.60) / 150
        assert tech_result["impact_score"] == pytest.approx(expected_impact, rel=0.01)


class TestAggregationResultStructure:
    """Tests for aggregation result structure."""

    def test_aggregation_result_structure(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Each aggregation result should have all 9 required fields."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT,
        )

        required_fields = [
            "dimension",
            "dimension_value",
            "ai_exposure_score",
            "impact_score",
            "complexity_score",
            "priority_score",
            "total_headcount",
            "role_count",
            "breakdown",
        ]

        for result in results:
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"


class TestAggregationBreakdown:
    """Tests for aggregation breakdown details."""

    def test_breakdown_includes_contributing_roles(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """Breakdown should list all roles contributing to the aggregation."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT,
        )

        tech_result = next(r for r in results if r["dimension_value"] == "Technology")

        # Breakdown should list contributing roles
        assert "breakdown" in tech_result
        breakdown = tech_result["breakdown"]["roles"]
        assert len(breakdown) == 2

        # Each breakdown entry should have role details
        role_names = [entry["role_name"] for entry in breakdown]
        assert "Software Engineer" in role_names
        assert "Data Analyst" in role_names


class TestAggregateAllDimensions:
    """Tests for aggregate_all_dimensions method."""

    def test_aggregate_all_dimensions(
        self, scoring_service, sample_role_mappings, sample_scores
    ):
        """aggregate_all_dimensions should return dict keyed by dimension."""
        results = scoring_service.aggregate_all_dimensions(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
        )

        # Should have all 5 dimensions
        assert AnalysisDimension.ROLE in results
        assert AnalysisDimension.DEPARTMENT in results
        assert AnalysisDimension.LOB in results
        assert AnalysisDimension.GEOGRAPHY in results
        assert AnalysisDimension.TASK in results

        # Each dimension should have aggregation results
        assert len(results[AnalysisDimension.ROLE]) == 4
        assert len(results[AnalysisDimension.DEPARTMENT]) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_role_mappings_returns_empty_results(self, scoring_service):
        """Empty role_mappings should return empty results."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=[],
            scores={},
            dimension=AnalysisDimension.ROLE,
        )

        assert results == []

    def test_missing_dimension_metadata_handled_gracefully(self, scoring_service):
        """Roles with missing dimension metadata should default to 'Unknown'."""
        role_mappings = [
            MagicMock(
                id="role-1",
                source_role="Developer",
                row_count=100,
                metadata={
                    "department": None,  # Missing department
                    "lob": "Engineering",
                    "geography": "US",
                },
            ),
            MagicMock(
                id="role-2",
                source_role="Analyst",
                row_count=50,
                metadata={
                    "department": "Technology",
                    "lob": None,  # Missing LOB
                    "geography": "US",
                },
            ),
        ]

        scores = {
            "role-1": {
                "exposure": 0.80,
                "impact": 0.60,
                "complexity": 0.20,
                "priority": 0.70,
            },
            "role-2": {
                "exposure": 0.70,
                "impact": 0.50,
                "complexity": 0.30,
                "priority": 0.60,
            },
        }

        # Should not raise an error for missing department
        results = scoring_service.aggregate_by_dimension(
            role_mappings=role_mappings,
            scores=scores,
            dimension=AnalysisDimension.DEPARTMENT,
        )

        # Should have 2 results: "Unknown" and "Technology"
        assert len(results) == 2
        dept_names = [r["dimension_value"] for r in results]
        assert "Unknown" in dept_names
        assert "Technology" in dept_names
