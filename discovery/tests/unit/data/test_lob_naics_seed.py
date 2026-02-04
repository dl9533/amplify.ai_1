"""Test LOB-NAICS seed data."""
import pytest
from app.data.lob_naics_seed import LOB_NAICS_MAPPINGS


class TestLobNaicsSeedData:
    """Test seed data structure and content."""

    def test_seed_data_exists(self):
        """Test that seed data is defined."""
        assert LOB_NAICS_MAPPINGS is not None
        assert len(LOB_NAICS_MAPPINGS) > 0

    def test_seed_data_has_required_fields(self):
        """Test each mapping has required fields."""
        for mapping in LOB_NAICS_MAPPINGS:
            assert "lob_pattern" in mapping
            assert "naics_codes" in mapping
            assert isinstance(mapping["naics_codes"], list)
            assert len(mapping["naics_codes"]) > 0

    def test_common_banking_mappings_exist(self):
        """Test common banking LOBs are mapped."""
        patterns = [m["lob_pattern"] for m in LOB_NAICS_MAPPINGS]

        assert "retail banking" in patterns
        assert "investment banking" in patterns
        assert "wealth management" in patterns

    def test_common_tech_mappings_exist(self):
        """Test common technology LOBs are mapped."""
        patterns = [m["lob_pattern"] for m in LOB_NAICS_MAPPINGS]

        assert "software" in patterns or "technology" in patterns
        assert "information technology" in patterns or "it services" in patterns

    def test_naics_codes_are_valid_format(self):
        """Test NAICS codes are valid format (2-6 digits)."""
        for mapping in LOB_NAICS_MAPPINGS:
            for code in mapping["naics_codes"]:
                assert isinstance(code, str)
                assert 2 <= len(code) <= 6
                assert code.isdigit()

    def test_no_duplicate_lob_patterns(self):
        """Test LOB patterns are unique."""
        patterns = [m["lob_pattern"] for m in LOB_NAICS_MAPPINGS]
        assert len(patterns) == len(set(patterns))

    def test_common_insurance_mappings_exist(self):
        """Test common insurance LOBs are mapped."""
        patterns = [m["lob_pattern"] for m in LOB_NAICS_MAPPINGS]

        assert "life insurance" in patterns
        assert "health insurance" in patterns

    def test_common_healthcare_mappings_exist(self):
        """Test common healthcare LOBs are mapped."""
        patterns = [m["lob_pattern"] for m in LOB_NAICS_MAPPINGS]

        assert "healthcare" in patterns
        assert "pharmaceuticals" in patterns

    def test_seed_data_count(self):
        """Test we have a reasonable number of mappings."""
        # Should have at least 50 common LOB mappings
        assert len(LOB_NAICS_MAPPINGS) >= 50


def test_lob_naics_mappings_exported():
    """Test LOB_NAICS_MAPPINGS is exported from data module."""
    from app.data import LOB_NAICS_MAPPINGS
    assert LOB_NAICS_MAPPINGS is not None
