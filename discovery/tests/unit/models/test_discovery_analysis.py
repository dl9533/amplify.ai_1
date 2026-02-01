"""Unit tests for DiscoveryAnalysisResult model."""
import pytest


def test_analysis_result_model_exists():
    """Test DiscoveryAnalysisResult model is importable."""
    from app.models.discovery_analysis import DiscoveryAnalysisResult, AnalysisDimension
    assert DiscoveryAnalysisResult is not None
    assert AnalysisDimension is not None


def test_analysis_result_has_required_columns():
    """Test model has required columns."""
    from app.models.discovery_analysis import DiscoveryAnalysisResult

    columns = DiscoveryAnalysisResult.__table__.columns.keys()
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dimension" in columns
    assert "dimension_value" in columns
    assert "ai_exposure_score" in columns
    assert "impact_score" in columns
    assert "complexity_score" in columns
    assert "priority_score" in columns
    assert "breakdown" in columns


def test_analysis_dimension_enum_values():
    """Test AnalysisDimension has expected values."""
    from app.models.discovery_analysis import AnalysisDimension

    assert AnalysisDimension.ROLE.value == "role"
    assert AnalysisDimension.TASK.value == "task"
    assert AnalysisDimension.LOB.value == "lob"
    assert AnalysisDimension.GEOGRAPHY.value == "geography"
    assert AnalysisDimension.DEPARTMENT.value == "department"
