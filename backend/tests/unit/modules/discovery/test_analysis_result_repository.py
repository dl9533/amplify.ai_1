# backend/tests/unit/modules/discovery/test_analysis_result_repository.py
"""Unit tests for DiscoveryAnalysisResultRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.analysis_result_repository import (
    DiscoveryAnalysisResultRepository,
)
from app.modules.discovery.models.session import DiscoveryAnalysisResult
from app.modules.discovery.enums import AnalysisDimension


@pytest.mark.asyncio
async def test_create_analysis_result(mock_db_session):
    """Should create analysis result with all fields."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dimension = AnalysisDimension.ROLE
    dimension_value = "Software Engineer"
    ai_exposure_score = 0.75
    impact_score = 0.85
    complexity_score = 0.65
    priority_score = 0.80
    breakdown = {"tasks": ["coding", "review"], "weights": [0.6, 0.4]}

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=dimension,
        dimension_value=dimension_value,
        ai_exposure_score=ai_exposure_score,
        impact_score=impact_score,
        complexity_score=complexity_score,
        priority_score=priority_score,
        breakdown=breakdown,
    )

    assert result.session_id == session_id
    assert result.role_mapping_id == role_mapping_id
    assert result.dimension == dimension
    assert result.dimension_value == dimension_value
    assert result.ai_exposure_score == ai_exposure_score
    assert result.impact_score == impact_score
    assert result.complexity_score == complexity_score
    assert result.priority_score == priority_score
    assert result.breakdown == breakdown
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_analysis_result_minimal(mock_db_session):
    """Should create analysis result with only required fields."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dimension = AnalysisDimension.TASK
    dimension_value = "Data Analysis"
    ai_exposure_score = 0.60

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=dimension,
        dimension_value=dimension_value,
        ai_exposure_score=ai_exposure_score,
    )

    assert result.session_id == session_id
    assert result.role_mapping_id == role_mapping_id
    assert result.dimension == dimension
    assert result.dimension_value == dimension_value
    assert result.ai_exposure_score == ai_exposure_score
    assert result.impact_score is None
    assert result.complexity_score is None
    assert result.priority_score is None
    assert result.breakdown is None


@pytest.mark.asyncio
async def test_get_analysis_result_by_id(mock_db_session):
    """Should retrieve analysis result by ID."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock result
    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Project Manager",
        ai_exposure_score=0.70,
    )

    # Configure mock to return result
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    retrieved = await repo.get_by_id(result_id)

    assert retrieved is not None
    assert retrieved.id == result_id
    assert retrieved.dimension_value == "Project Manager"


@pytest.mark.asyncio
async def test_get_analysis_result_by_id_not_found(mock_db_session):
    """Should return None when result not found."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return None
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_results_by_session_id(mock_db_session):
    """Should retrieve all results for a session."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock results
    result1 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Developer",
        ai_exposure_score=0.75,
    )
    result2 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.TASK,
        dimension_value="Coding",
        ai_exposure_score=0.80,
    )

    # Configure mock to return results
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [result1, result2]
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_session_id(session_id)

    assert len(results) == 2
    assert results[0].session_id == session_id
    assert results[1].session_id == session_id


@pytest.mark.asyncio
async def test_get_results_by_session_id_empty(mock_db_session):
    """Should return empty list when session has no results."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return empty list
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_session_id(uuid4())

    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_results_by_dimension(mock_db_session):
    """Should retrieve results filtered by dimension."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock results for ROLE dimension
    result1 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Developer",
        ai_exposure_score=0.75,
    )
    result2 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Manager",
        ai_exposure_score=0.65,
    )

    # Configure mock to return role dimension results
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [result1, result2]
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_dimension(session_id, AnalysisDimension.ROLE)

    assert len(results) == 2
    assert all(r.dimension == AnalysisDimension.ROLE for r in results)


@pytest.mark.asyncio
async def test_get_results_by_dimension_empty(mock_db_session):
    """Should return empty list when no results for dimension."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return empty list
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_dimension(uuid4(), AnalysisDimension.GEOGRAPHY)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_results_by_role_mapping(mock_db_session):
    """Should retrieve all results for a role mapping."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock results for role mapping
    result1 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Developer",
        ai_exposure_score=0.75,
    )
    result2 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.TASK,
        dimension_value="Coding",
        ai_exposure_score=0.80,
    )

    # Configure mock to return results
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [result1, result2]
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_role_mapping_id(role_mapping_id)

    assert len(results) == 2
    assert all(r.role_mapping_id == role_mapping_id for r in results)


@pytest.mark.asyncio
async def test_get_results_by_role_mapping_empty(mock_db_session):
    """Should return empty list when role mapping has no results."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return empty list
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_by_role_mapping_id(uuid4())

    assert len(results) == 0


@pytest.mark.asyncio
async def test_update_scores(mock_db_session):
    """Should update score fields."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()

    # Create mock result
    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.ROLE,
        dimension_value="Analyst",
        ai_exposure_score=0.70,
        impact_score=0.60,
        complexity_score=0.50,
        priority_score=0.55,
    )

    # Configure mock to return result
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    updated = await repo.update_scores(
        result_id,
        ai_exposure_score=0.85,
        impact_score=0.90,
        complexity_score=0.75,
        priority_score=0.88,
    )

    assert updated.ai_exposure_score == 0.85
    assert updated.impact_score == 0.90
    assert updated.complexity_score == 0.75
    assert updated.priority_score == 0.88
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_scores_partial(mock_db_session):
    """Should update only specified scores."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()

    # Create mock result
    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.ROLE,
        dimension_value="Manager",
        ai_exposure_score=0.70,
        impact_score=0.60,
        complexity_score=0.50,
        priority_score=0.55,
    )

    # Configure mock to return result
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    # Only update ai_exposure_score and priority_score
    updated = await repo.update_scores(
        result_id,
        ai_exposure_score=0.80,
        priority_score=0.95,
    )

    assert updated.ai_exposure_score == 0.80
    assert updated.impact_score == 0.60  # unchanged
    assert updated.complexity_score == 0.50  # unchanged
    assert updated.priority_score == 0.95


@pytest.mark.asyncio
async def test_update_scores_not_found(mock_db_session):
    """Should return None when result not found."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return None
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = None

    result = await repo.update_scores(uuid4(), ai_exposure_score=0.90)
    assert result is None


@pytest.mark.asyncio
async def test_update_breakdown(mock_db_session):
    """Should update breakdown JSON field."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()

    # Create mock result
    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.TASK,
        dimension_value="Analysis",
        ai_exposure_score=0.75,
        breakdown=None,
    )

    # Configure mock to return result
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    new_breakdown = {
        "components": ["data_extraction", "report_generation"],
        "scores": {"data_extraction": 0.8, "report_generation": 0.9},
    }
    updated = await repo.update_breakdown(result_id, new_breakdown)

    assert updated.breakdown == new_breakdown
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_breakdown_not_found(mock_db_session):
    """Should return None when result not found."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return None
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = None

    result = await repo.update_breakdown(uuid4(), {"key": "value"})
    assert result is None


@pytest.mark.asyncio
async def test_get_top_by_priority_score(mock_db_session):
    """Should get top N results by priority_score descending."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock results ordered by priority_score desc
    result1 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Developer",
        ai_exposure_score=0.75,
        priority_score=0.95,
    )
    result2 = DiscoveryAnalysisResult(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Designer",
        ai_exposure_score=0.70,
        priority_score=0.85,
    )

    # Configure mock to return top 2
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [result1, result2]
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_top_by_priority(session_id, limit=2)

    assert len(results) == 2
    assert results[0].priority_score == 0.95
    assert results[1].priority_score == 0.85


@pytest.mark.asyncio
async def test_get_top_by_priority_score_empty(mock_db_session):
    """Should return empty list when no results."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return empty list
    mock_db_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db_result.scalars.return_value = mock_scalars

    results = await repo.get_top_by_priority(uuid4(), limit=5)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_analysis_result(mock_db_session):
    """Should delete analysis result record."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()

    # Create mock result
    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.ROLE,
        dimension_value="Manager",
        ai_exposure_score=0.65,
    )

    # Configure mock to return result
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    success = await repo.delete(result_id)

    assert success is True
    mock_db_session.delete.assert_called_once_with(mock_result)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_analysis_result_not_found(mock_db_session):
    """Should return False when result not found."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return None
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = None

    success = await repo.delete(uuid4())

    assert success is False
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_by_session(mock_db_session):
    """Should delete all results for a session using bulk delete."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    session_id = uuid4()

    # Configure mock to return rowcount from bulk delete
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.rowcount = 5

    count = await repo.delete_by_session_id(session_id)

    assert count == 5
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_by_session_none_found(mock_db_session):
    """Should return 0 when no results found for session."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    # Configure mock to return rowcount of 0 from bulk delete
    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.rowcount = 0

    count = await repo.delete_by_session_id(uuid4())

    assert count == 0
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called()


# --- Score Validation Tests ---


@pytest.mark.asyncio
async def test_create_with_negative_ai_exposure_score_raises_error(mock_db_session):
    """Should raise ValueError when ai_exposure_score is negative."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            dimension=AnalysisDimension.ROLE,
            dimension_value="Developer",
            ai_exposure_score=-0.1,
        )

    assert "ai_exposure_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_ai_exposure_score_greater_than_one_raises_error(mock_db_session):
    """Should raise ValueError when ai_exposure_score is greater than 1.0."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            dimension=AnalysisDimension.ROLE,
            dimension_value="Developer",
            ai_exposure_score=1.5,
        )

    assert "ai_exposure_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_negative_impact_score_raises_error(mock_db_session):
    """Should raise ValueError when impact_score is negative."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            dimension=AnalysisDimension.ROLE,
            dimension_value="Developer",
            ai_exposure_score=0.5,
            impact_score=-0.2,
        )

    assert "impact_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_negative_complexity_score_raises_error(mock_db_session):
    """Should raise ValueError when complexity_score is negative."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            dimension=AnalysisDimension.ROLE,
            dimension_value="Developer",
            ai_exposure_score=0.5,
            complexity_score=-0.3,
        )

    assert "complexity_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_negative_priority_score_raises_error(mock_db_session):
    """Should raise ValueError when priority_score is negative."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            dimension=AnalysisDimension.ROLE,
            dimension_value="Developer",
            ai_exposure_score=0.5,
            priority_score=-0.1,
        )

    assert "priority_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_scores_at_boundaries(mock_db_session):
    """Should accept scores at 0.0 and 1.0 boundaries."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    result = await repo.create(
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.ROLE,
        dimension_value="Developer",
        ai_exposure_score=0.0,
        impact_score=1.0,
        complexity_score=0.0,
        priority_score=1.0,
    )

    assert result.ai_exposure_score == 0.0
    assert result.impact_score == 1.0
    assert result.complexity_score == 0.0
    assert result.priority_score == 1.0
    mock_db_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_update_scores_with_negative_value_raises_error(mock_db_session):
    """Should raise ValueError when updating with negative score."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.update_scores(uuid4(), ai_exposure_score=-0.5)

    assert "ai_exposure_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_update_scores_with_value_greater_than_one_raises_error(mock_db_session):
    """Should raise ValueError when updating with score > 1.0."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.update_scores(uuid4(), impact_score=1.5)

    assert "impact_score must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_update_scores_at_boundaries(mock_db_session):
    """Should accept updating scores to 0.0 and 1.0 boundaries."""
    repo = DiscoveryAnalysisResultRepository(mock_db_session)
    result_id = uuid4()

    mock_result = DiscoveryAnalysisResult(
        id=result_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dimension=AnalysisDimension.ROLE,
        dimension_value="Manager",
        ai_exposure_score=0.5,
    )

    mock_db_result = mock_db_session.execute.return_value
    mock_db_result.scalar_one_or_none.return_value = mock_result

    updated = await repo.update_scores(
        result_id,
        ai_exposure_score=0.0,
        impact_score=1.0,
    )

    assert updated.ai_exposure_score == 0.0
    assert updated.impact_score == 1.0
