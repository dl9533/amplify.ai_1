"""Test OnetFileSyncService industry data import."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.onet_file_sync_service import OnetFileSyncService


class TestParseIndustries:
    """Test parsing industry data from O*NET files."""

    def test_parse_industry_file(self):
        """Test parsing Industry.txt content."""
        # Sample O*NET Industry.txt format
        content = """O*NET-SOC Code\tIndustry Code\tIndustry Title\tEmployment
13-2051.00\t522110\tCommercial Banking\t0.25
13-2051.00\t523110\tInvestment Banking\t0.15
11-1011.00\t523\tSecurities and Commodity Contracts\t0.20
"""
        service = OnetFileSyncService(repository=None)
        result = service._parse_industries(content)

        assert len(result) == 3
        assert result[0]["occupation_code"] == "13-2051.00"
        assert result[0]["naics_code"] == "522110"
        assert result[0]["naics_title"] == "Commercial Banking"
        assert result[0]["employment_percent"] == 0.25

    def test_parse_industry_empty_content(self):
        """Test parsing empty content returns empty list."""
        service = OnetFileSyncService(repository=None)
        result = service._parse_industries("")

        assert result == []

    def test_parse_industry_handles_missing_employment(self):
        """Test parsing handles missing employment value."""
        content = """O*NET-SOC Code\tIndustry Code\tIndustry Title\tEmployment
13-2051.00\t522110\tCommercial Banking\t
"""
        service = OnetFileSyncService(repository=None)
        result = service._parse_industries(content)

        assert len(result) == 1
        assert result[0]["employment_percent"] is None


class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_sync_result_has_industry_count(self):
        """Test SyncResult has industry_count field."""
        from app.services.onet_file_sync_service import SyncResult

        result = SyncResult(
            version="30.1",
            occupation_count=100,
            alternate_title_count=200,
            task_count=300,
            industry_count=400,
            gwa_count=50,
            iwa_count=60,
            dwa_count=70,
            task_to_dwa_count=80,
            status="success",
        )

        assert result.industry_count == 400


class TestIndustryFileConstant:
    """Test INDUSTRY_FILE constant."""

    def test_industry_file_constant_exists(self):
        """Test INDUSTRY_FILE constant is defined."""
        assert hasattr(OnetFileSyncService, "INDUSTRY_FILE")
        assert OnetFileSyncService.INDUSTRY_FILE == "Industry.txt"


def test_parse_industries_method_exists():
    """Test _parse_industries method exists."""
    assert hasattr(OnetFileSyncService, "_parse_industries")
    assert callable(getattr(OnetFileSyncService, "_parse_industries"))
