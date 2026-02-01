"""Integration tests for GWA seed data migration.

These tests verify that the onet_gwas table is correctly populated with
the 41 Generalized Work Activities and their Pew Research AI exposure scores.
"""

import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_gwa_seed_data_populated(db_engine):
    """GWA table should have 41 records with AI exposure scores."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM onet_gwas"))
        count = result.scalar()
        assert count == 41


@pytest.mark.asyncio
async def test_gwa_has_ai_exposure_scores(db_engine):
    """Each GWA should have an ai_exposure_score between 0 and 1."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT id, ai_exposure_score FROM onet_gwas "
                "WHERE ai_exposure_score IS NULL "
                "OR ai_exposure_score < 0 "
                "OR ai_exposure_score > 1"
            )
        )
        invalid_rows = result.fetchall()
        assert len(invalid_rows) == 0, f"Invalid GWA scores: {invalid_rows}"


@pytest.mark.asyncio
async def test_gwa_getting_information_high_score(db_engine):
    """'Getting Information' GWA should have high AI exposure."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT ai_exposure_score FROM onet_gwas WHERE id = '4.A.1.a.1'")
        )
        score = result.scalar()
        assert score is not None
        assert score >= 0.8  # High exposure activity


@pytest.mark.asyncio
async def test_gwa_analyzing_data_highest_exposure(db_engine):
    """'Analyzing Data or Information' should have one of the highest AI exposure scores."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT ai_exposure_score FROM onet_gwas WHERE id = '4.A.2.a.1'")
        )
        score = result.scalar()
        assert score is not None
        assert score >= 0.9  # Highest exposure activity


@pytest.mark.asyncio
async def test_gwa_physical_activities_low_exposure(db_engine):
    """Physical activities should have low AI exposure scores."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT ai_exposure_score FROM onet_gwas WHERE id = '4.A.3.a.1'")
        )
        score = result.scalar()
        assert score is not None
        assert score <= 0.3  # Low exposure for physical activities


@pytest.mark.asyncio
async def test_gwa_all_records_have_names(db_engine):
    """All GWA records should have non-empty names."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT id FROM onet_gwas WHERE name IS NULL OR name = ''"
            )
        )
        invalid_rows = result.fetchall()
        assert len(invalid_rows) == 0, f"GWAs without names: {invalid_rows}"


@pytest.mark.asyncio
async def test_gwa_all_records_have_descriptions(db_engine):
    """All GWA records should have descriptions."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT id FROM onet_gwas WHERE description IS NULL OR description = ''"
            )
        )
        invalid_rows = result.fetchall()
        assert len(invalid_rows) == 0, f"GWAs without descriptions: {invalid_rows}"


@pytest.mark.asyncio
async def test_gwa_id_format_valid(db_engine):
    """All GWA IDs should follow the O*NET format (4.A.X.X.X)."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT id FROM onet_gwas WHERE id NOT LIKE '4.A.%'"
            )
        )
        invalid_rows = result.fetchall()
        assert len(invalid_rows) == 0, f"Invalid GWA ID formats: {invalid_rows}"


@pytest.mark.asyncio
async def test_gwa_categories_represented(db_engine):
    """All major GWA categories should be represented."""
    async with db_engine.connect() as conn:
        # Check for Information Input (4.A.1)
        result = await conn.execute(
            text("SELECT COUNT(*) FROM onet_gwas WHERE id LIKE '4.A.1.%'")
        )
        count_input = result.scalar()
        assert count_input >= 3, "Information Input category should have at least 3 GWAs"

        # Check for Mental Processes (4.A.2)
        result = await conn.execute(
            text("SELECT COUNT(*) FROM onet_gwas WHERE id LIKE '4.A.2.%'")
        )
        count_mental = result.scalar()
        assert count_mental >= 5, "Mental Processes category should have at least 5 GWAs"

        # Check for Work Output (4.A.3)
        result = await conn.execute(
            text("SELECT COUNT(*) FROM onet_gwas WHERE id LIKE '4.A.3.%'")
        )
        count_output = result.scalar()
        assert count_output >= 5, "Work Output category should have at least 5 GWAs"

        # Check for Interacting with Others (4.A.4)
        result = await conn.execute(
            text("SELECT COUNT(*) FROM onet_gwas WHERE id LIKE '4.A.4.%'")
        )
        count_interact = result.scalar()
        assert count_interact >= 10, "Interacting with Others category should have at least 10 GWAs"


@pytest.mark.asyncio
async def test_gwa_documenting_recording_high_exposure(db_engine):
    """'Documenting/Recording Information' should have high AI exposure."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT ai_exposure_score FROM onet_gwas WHERE id = '4.A.3.b.6'")
        )
        score = result.scalar()
        assert score is not None
        assert score >= 0.9  # High exposure for documentation tasks
