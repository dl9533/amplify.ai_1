"""Unit tests for O*NET tables migration structure."""

from pathlib import Path


def test_migration_file_exists():
    """O*NET migration file should exist."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    assert path.exists()


def test_migration_has_upgrade_function():
    """Migration should have upgrade function."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert "def upgrade()" in content


def test_migration_has_downgrade_function():
    """Migration should have downgrade function."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert "def downgrade()" in content


def test_migration_has_correct_revision():
    """Migration should have correct revision identifier."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert 'revision: str = "070_discovery_onet_tables"' in content


def test_migration_has_correct_down_revision():
    """Migration should reference previous migration."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert 'down_revision: str | None = "103_pipeline_module"' in content


def test_migration_creates_onet_occupations_table():
    """Migration should create onet_occupations table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_occupations"' in content
    assert "op.create_table" in content


def test_migration_creates_onet_gwas_table():
    """Migration should create onet_gwas table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_gwas"' in content


def test_migration_creates_onet_iwas_table():
    """Migration should create onet_iwas table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_iwas"' in content


def test_migration_creates_onet_dwas_table():
    """Migration should create onet_dwas table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_dwas"' in content


def test_migration_creates_onet_tasks_table():
    """Migration should create onet_tasks table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_tasks"' in content


def test_migration_creates_onet_skills_table():
    """Migration should create onet_skills table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_skills"' in content


def test_migration_creates_onet_technology_skills_table():
    """Migration should create onet_technology_skills table."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert '"onet_technology_skills"' in content


def test_migration_has_foreign_keys():
    """Migration should define foreign key relationships."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    # IWA -> GWA
    assert 'ForeignKey("onet_gwas.id"' in content
    # DWA -> IWA
    assert 'ForeignKey("onet_iwas.id"' in content
    # Task -> Occupation
    assert 'ForeignKey("onet_occupations.code"' in content


def test_migration_has_indexes():
    """Migration should create indexes for foreign keys."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert "ix_onet_iwas_gwa_id" in content
    assert "ix_onet_dwas_iwa_id" in content
    assert "ix_onet_tasks_occupation_code" in content
    assert "ix_onet_technology_skills_occupation_code" in content


def test_migration_has_ai_exposure_fields():
    """Migration should include AI exposure score fields."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    assert "ai_exposure_score" in content
    assert "ai_exposure_override" in content


def test_downgrade_drops_tables_in_correct_order():
    """Downgrade should drop tables respecting foreign key constraints."""
    path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "070_discovery_onet_tables.py"
    )
    content = path.read_text()
    # Find the downgrade function
    downgrade_start = content.find("def downgrade()")
    downgrade_content = content[downgrade_start:]

    # Tables with FKs should be dropped before their referenced tables
    tech_skills_drop = downgrade_content.find('drop_table("onet_technology_skills")')
    skills_drop = downgrade_content.find('drop_table("onet_skills")')
    tasks_drop = downgrade_content.find('drop_table("onet_tasks")')
    dwas_drop = downgrade_content.find('drop_table("onet_dwas")')
    iwas_drop = downgrade_content.find('drop_table("onet_iwas")')
    gwas_drop = downgrade_content.find('drop_table("onet_gwas")')
    occupations_drop = downgrade_content.find('drop_table("onet_occupations")')

    # Verify order: child tables before parent tables
    assert dwas_drop < iwas_drop < gwas_drop  # DWA -> IWA -> GWA hierarchy
    assert tasks_drop < occupations_drop  # Tasks before occupations
    assert tech_skills_drop < occupations_drop  # Tech skills before occupations
