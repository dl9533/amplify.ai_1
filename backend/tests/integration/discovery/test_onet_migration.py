"""Integration tests for O*NET database migration.

These tests verify that the O*NET tables are correctly created by the
migration script and that foreign key relationships are properly configured.
"""

import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_onet_occupations_table_exists(db_engine):
    """onet_occupations table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_occupations" in tables


@pytest.mark.asyncio
async def test_onet_gwas_table_exists(db_engine):
    """onet_gwas table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_gwas" in tables


@pytest.mark.asyncio
async def test_onet_iwas_table_exists(db_engine):
    """onet_iwas table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_iwas" in tables


@pytest.mark.asyncio
async def test_onet_dwas_table_exists(db_engine):
    """onet_dwas table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_dwas" in tables


@pytest.mark.asyncio
async def test_onet_tasks_table_exists(db_engine):
    """onet_tasks table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_tasks" in tables


@pytest.mark.asyncio
async def test_onet_skills_table_exists(db_engine):
    """onet_skills table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_skills" in tables


@pytest.mark.asyncio
async def test_onet_technology_skills_table_exists(db_engine):
    """onet_technology_skills table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_technology_skills" in tables


@pytest.mark.asyncio
async def test_iwa_gwa_foreign_key(db_engine):
    """onet_iwas.gwa_id should reference onet_gwas."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("onet_iwas")

        fks = await conn.run_sync(get_fks)
        gwa_fk = next((fk for fk in fks if "gwa_id" in fk["constrained_columns"]), None)
        assert gwa_fk is not None
        assert gwa_fk["referred_table"] == "onet_gwas"


@pytest.mark.asyncio
async def test_dwa_iwa_foreign_key(db_engine):
    """onet_dwas.iwa_id should reference onet_iwas."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("onet_dwas")

        fks = await conn.run_sync(get_fks)
        iwa_fk = next((fk for fk in fks if "iwa_id" in fk["constrained_columns"]), None)
        assert iwa_fk is not None
        assert iwa_fk["referred_table"] == "onet_iwas"


@pytest.mark.asyncio
async def test_task_occupation_foreign_key(db_engine):
    """onet_tasks.occupation_code should reference onet_occupations."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("onet_tasks")

        fks = await conn.run_sync(get_fks)
        occ_fk = next(
            (fk for fk in fks if "occupation_code" in fk["constrained_columns"]), None
        )
        assert occ_fk is not None
        assert occ_fk["referred_table"] == "onet_occupations"


@pytest.mark.asyncio
async def test_technology_skill_occupation_foreign_key(db_engine):
    """onet_technology_skills.occupation_code should reference onet_occupations."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("onet_technology_skills")

        fks = await conn.run_sync(get_fks)
        occ_fk = next(
            (fk for fk in fks if "occupation_code" in fk["constrained_columns"]), None
        )
        assert occ_fk is not None
        assert occ_fk["referred_table"] == "onet_occupations"


@pytest.mark.asyncio
async def test_onet_occupations_columns(db_engine):
    """onet_occupations should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("onet_occupations")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {"code", "title", "description", "created_at", "updated_at"}
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_onet_gwas_columns(db_engine):
    """onet_gwas should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("onet_gwas")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {"id", "name", "description", "ai_exposure_score"}
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_onet_dwas_has_ai_exposure_override(db_engine):
    """onet_dwas should have ai_exposure_override column."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("onet_dwas")}

        columns = await conn.run_sync(get_columns)
        assert "ai_exposure_override" in columns
