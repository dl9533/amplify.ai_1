# Smart Upload with LOB-Aware Role Matching - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve role-to-O*NET matching accuracy by auto-detecting column mappings during upload and using Line of Business context to boost industry-relevant occupation matches, with aggregated UX for scale.

**Architecture:** Combined upload step with intelligent column detection (keyword matching + LLM fallback), LOB-to-NAICS mapping via curated lookup table with LLM fallback, industry-aware occupation scoring, and grouped review interfaces for 1000+ employee scale.

**Tech Stack:** FastAPI, PostgreSQL (with ARRAY types), Claude API for fallback detection, React/TypeScript frontend with TanStack Query

---

## Phase 1: Database & Data Import (Tasks 1-8)

### Task 1: Create NAICS Reference Table Migration

**Files:**
- Create: `migrations/versions/011_naics_codes.py`
- Test: `tests/unit/migrations/test_011_naics_codes.py`

**Step 1: Write the failing test**

```python
# tests/unit/migrations/test_011_naics_codes.py
"""Test 011_naics_codes migration."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text


def test_naics_codes_table_exists_after_upgrade(test_engine):
    """Test that naics_codes table is created on upgrade."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "011_naics_codes")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "naics_codes" in tables


def test_naics_codes_table_columns(test_engine):
    """Test naics_codes table has correct columns."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "011_naics_codes")

    inspector = inspect(test_engine)
    columns = {c["name"] for c in inspector.get_columns("naics_codes")}

    assert "code" in columns
    assert "title" in columns
    assert "level" in columns
    assert "parent_code" in columns
    assert "created_at" in columns


def test_naics_codes_downgrade(test_engine):
    """Test that downgrade removes the table."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "011_naics_codes")
    command.downgrade(alembic_cfg, "010_chat_messages")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "naics_codes" not in tables
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/migrations/test_011_naics_codes.py -v`
Expected: FAIL with "migration 011_naics_codes not found"

**Step 3: Write minimal implementation**

```python
# migrations/versions/011_naics_codes.py
"""NAICS reference codes table.

Revision ID: 011_naics_codes
Revises: 010_chat_messages
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_naics_codes"
down_revision: Union[str, None] = "010_chat_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create naics_codes reference table."""
    op.create_table(
        "naics_codes",
        sa.Column("code", sa.String(6), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("parent_code", sa.String(6), sa.ForeignKey("naics_codes.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop naics_codes table."""
    op.drop_table("naics_codes")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/migrations/test_011_naics_codes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add migrations/versions/011_naics_codes.py tests/unit/migrations/test_011_naics_codes.py
git commit -m "feat(db): add NAICS reference codes table migration"
```

---

### Task 2: Create LOB-NAICS Mapping Table Migration

**Files:**
- Create: `migrations/versions/012_lob_naics_mappings.py`
- Test: `tests/unit/migrations/test_012_lob_naics_mappings.py`

**Step 1: Write the failing test**

```python
# tests/unit/migrations/test_012_lob_naics_mappings.py
"""Test 012_lob_naics_mappings migration."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_lob_naics_mappings_table_exists_after_upgrade(test_engine):
    """Test that lob_naics_mappings table is created on upgrade."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "012_lob_naics_mappings")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "lob_naics_mappings" in tables


def test_lob_naics_mappings_columns(test_engine):
    """Test lob_naics_mappings has correct columns including array type."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "012_lob_naics_mappings")

    inspector = inspect(test_engine)
    columns = {c["name"]: c["type"] for c in inspector.get_columns("lob_naics_mappings")}

    assert "id" in columns
    assert "lob_pattern" in columns
    assert "naics_codes" in columns  # ARRAY type
    assert "confidence" in columns
    assert "source" in columns


def test_lob_naics_mappings_downgrade(test_engine):
    """Test downgrade removes the table."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "012_lob_naics_mappings")
    command.downgrade(alembic_cfg, "011_naics_codes")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "lob_naics_mappings" not in tables
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/migrations/test_012_lob_naics_mappings.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# migrations/versions/012_lob_naics_mappings.py
"""LOB to NAICS code mappings table.

Revision ID: 012_lob_naics_mappings
Revises: 011_naics_codes
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "012_lob_naics_mappings"
down_revision: Union[str, None] = "011_naics_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create lob_naics_mappings table."""
    op.create_table(
        "lob_naics_mappings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lob_pattern", sa.String(255), nullable=False, unique=True),
        sa.Column("naics_codes", postgresql.ARRAY(sa.String(6)), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(50), nullable=False, server_default="'curated'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_lob_pattern", "lob_naics_mappings", ["lob_pattern"])


def downgrade() -> None:
    """Drop lob_naics_mappings table."""
    op.drop_index("idx_lob_pattern", table_name="lob_naics_mappings")
    op.drop_table("lob_naics_mappings")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/migrations/test_012_lob_naics_mappings.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add migrations/versions/012_lob_naics_mappings.py tests/unit/migrations/test_012_lob_naics_mappings.py
git commit -m "feat(db): add LOB-NAICS mappings table with array support"
```

---

### Task 3: Create O*NET Occupation Industries Table Migration

**Files:**
- Create: `migrations/versions/013_onet_occupation_industries.py`
- Test: `tests/unit/migrations/test_013_onet_occupation_industries.py`

**Step 1: Write the failing test**

```python
# tests/unit/migrations/test_013_onet_occupation_industries.py
"""Test 013_onet_occupation_industries migration."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_onet_occupation_industries_table_exists(test_engine):
    """Test table is created on upgrade."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "013_onet_occupation_industries")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "onet_occupation_industries" in tables


def test_onet_occupation_industries_columns(test_engine):
    """Test correct columns exist."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "013_onet_occupation_industries")

    inspector = inspect(test_engine)
    columns = {c["name"] for c in inspector.get_columns("onet_occupation_industries")}

    assert "id" in columns
    assert "occupation_code" in columns
    assert "naics_code" in columns
    assert "naics_title" in columns
    assert "employment_percent" in columns


def test_onet_occupation_industries_indexes(test_engine):
    """Test indexes are created."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "013_onet_occupation_industries")

    inspector = inspect(test_engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("onet_occupation_industries")}

    assert "idx_onet_occ_ind_occupation" in indexes
    assert "idx_onet_occ_ind_naics" in indexes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/migrations/test_013_onet_occupation_industries.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# migrations/versions/013_onet_occupation_industries.py
"""O*NET occupation-industry mappings table.

Revision ID: 013_onet_occupation_industries
Revises: 012_lob_naics_mappings
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "013_onet_occupation_industries"
down_revision: Union[str, None] = "012_lob_naics_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create onet_occupation_industries table."""
    op.create_table(
        "onet_occupation_industries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "occupation_code",
            sa.String(10),
            sa.ForeignKey("onet_occupations.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("naics_code", sa.String(6), nullable=False),
        sa.Column("naics_title", sa.String(255), nullable=False),
        sa.Column("employment_percent", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("occupation_code", "naics_code", name="uq_occ_naics"),
    )
    op.create_index("idx_onet_occ_ind_occupation", "onet_occupation_industries", ["occupation_code"])
    op.create_index("idx_onet_occ_ind_naics", "onet_occupation_industries", ["naics_code"])


def downgrade() -> None:
    """Drop onet_occupation_industries table."""
    op.drop_index("idx_onet_occ_ind_naics", table_name="onet_occupation_industries")
    op.drop_index("idx_onet_occ_ind_occupation", table_name="onet_occupation_industries")
    op.drop_table("onet_occupation_industries")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/migrations/test_013_onet_occupation_industries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add migrations/versions/013_onet_occupation_industries.py tests/unit/migrations/test_013_onet_occupation_industries.py
git commit -m "feat(db): add O*NET occupation-industry mapping table"
```

---

### Task 4: Add LOB Columns to Existing Tables Migration

**Files:**
- Create: `migrations/versions/014_add_lob_columns.py`
- Test: `tests/unit/migrations/test_014_add_lob_columns.py`

**Step 1: Write the failing test**

```python
# tests/unit/migrations/test_014_add_lob_columns.py
"""Test 014_add_lob_columns migration."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_discovery_uploads_has_lob_column(test_engine):
    """Test discovery_uploads gets lob_column field."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "014_add_lob_columns")

    inspector = inspect(test_engine)
    columns = {c["name"] for c in inspector.get_columns("discovery_uploads")}

    assert "lob_column" in columns


def test_discovery_role_mappings_has_lob_columns(test_engine):
    """Test discovery_role_mappings gets LOB-related columns."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "014_add_lob_columns")

    inspector = inspect(test_engine)
    columns = {c["name"] for c in inspector.get_columns("discovery_role_mappings")}

    assert "lob_value" in columns
    assert "naics_codes" in columns
    assert "industry_match_score" in columns


def test_downgrade_removes_columns(test_engine):
    """Test downgrade removes the added columns."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "014_add_lob_columns")
    command.downgrade(alembic_cfg, "013_onet_occupation_industries")

    inspector = inspect(test_engine)
    upload_columns = {c["name"] for c in inspector.get_columns("discovery_uploads")}
    mapping_columns = {c["name"] for c in inspector.get_columns("discovery_role_mappings")}

    assert "lob_column" not in upload_columns
    assert "lob_value" not in mapping_columns
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/migrations/test_014_add_lob_columns.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# migrations/versions/014_add_lob_columns.py
"""Add LOB columns to upload and role mapping tables.

Revision ID: 014_add_lob_columns
Revises: 013_onet_occupation_industries
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "014_add_lob_columns"
down_revision: Union[str, None] = "013_onet_occupation_industries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LOB-related columns to existing tables."""
    # Add lob_column to discovery_uploads
    op.add_column(
        "discovery_uploads",
        sa.Column("lob_column", sa.String(255), nullable=True),
    )

    # Add LOB columns to discovery_role_mappings
    op.add_column(
        "discovery_role_mappings",
        sa.Column("lob_value", sa.String(255), nullable=True),
    )
    op.add_column(
        "discovery_role_mappings",
        sa.Column("naics_codes", postgresql.ARRAY(sa.String(6)), nullable=True),
    )
    op.add_column(
        "discovery_role_mappings",
        sa.Column("industry_match_score", sa.Float, nullable=True),
    )

    # Add index for LOB grouping queries
    op.create_index(
        "idx_role_mappings_lob",
        "discovery_role_mappings",
        ["session_id", "lob_value"],
    )


def downgrade() -> None:
    """Remove LOB columns."""
    op.drop_index("idx_role_mappings_lob", table_name="discovery_role_mappings")
    op.drop_column("discovery_role_mappings", "industry_match_score")
    op.drop_column("discovery_role_mappings", "naics_codes")
    op.drop_column("discovery_role_mappings", "lob_value")
    op.drop_column("discovery_uploads", "lob_column")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/migrations/test_014_add_lob_columns.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add migrations/versions/014_add_lob_columns.py tests/unit/migrations/test_014_add_lob_columns.py
git commit -m "feat(db): add LOB columns to uploads and role mappings"
```

---

### Task 5: Create NAICS SQLAlchemy Model

**Files:**
- Create: `app/models/naics_code.py`
- Modify: `app/models/__init__.py`
- Test: `tests/unit/models/test_naics_code.py`

**Step 1: Write the failing test**

```python
# tests/unit/models/test_naics_code.py
"""Test NaicsCode model."""
import pytest
from app.models.naics_code import NaicsCode


def test_naics_code_model_fields():
    """Test NaicsCode has expected fields."""
    assert hasattr(NaicsCode, "code")
    assert hasattr(NaicsCode, "title")
    assert hasattr(NaicsCode, "level")
    assert hasattr(NaicsCode, "parent_code")
    assert hasattr(NaicsCode, "created_at")


def test_naics_code_tablename():
    """Test table name is correct."""
    assert NaicsCode.__tablename__ == "naics_codes"


def test_naics_code_repr():
    """Test string representation."""
    code = NaicsCode(code="52", title="Finance and Insurance", level=2)
    assert "52" in repr(code)
    assert "Finance" in repr(code)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/models/test_naics_code.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.naics_code'"

**Step 3: Write minimal implementation**

```python
# app/models/naics_code.py
"""NAICS code reference model."""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NaicsCode(Base):
    """North American Industry Classification System reference data."""
    __tablename__ = "naics_codes"

    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_code: Mapped[str | None] = mapped_column(
        String(6),
        ForeignKey("naics_codes.code"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Self-referential relationship
    parent: Mapped["NaicsCode | None"] = relationship(
        "NaicsCode",
        remote_side=[code],
        backref="children",
    )

    def __repr__(self) -> str:
        return f"<NaicsCode(code={self.code}, title={self.title})>"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/models/test_naics_code.py -v`
Expected: PASS

**Step 5: Update __init__.py and commit**

Add to `app/models/__init__.py`:
```python
from app.models.naics_code import NaicsCode
```

```bash
git add app/models/naics_code.py app/models/__init__.py tests/unit/models/test_naics_code.py
git commit -m "feat(models): add NaicsCode model"
```

---

### Task 6: Create LobNaicsMapping SQLAlchemy Model

**Files:**
- Create: `app/models/lob_naics_mapping.py`
- Modify: `app/models/__init__.py`
- Test: `tests/unit/models/test_lob_naics_mapping.py`

**Step 1: Write the failing test**

```python
# tests/unit/models/test_lob_naics_mapping.py
"""Test LobNaicsMapping model."""
import pytest
from app.models.lob_naics_mapping import LobNaicsMapping


def test_lob_naics_mapping_fields():
    """Test model has expected fields."""
    assert hasattr(LobNaicsMapping, "id")
    assert hasattr(LobNaicsMapping, "lob_pattern")
    assert hasattr(LobNaicsMapping, "naics_codes")  # Array type
    assert hasattr(LobNaicsMapping, "confidence")
    assert hasattr(LobNaicsMapping, "source")


def test_lob_naics_mapping_tablename():
    """Test table name."""
    assert LobNaicsMapping.__tablename__ == "lob_naics_mappings"


def test_lob_naics_mapping_repr():
    """Test string representation."""
    mapping = LobNaicsMapping(
        lob_pattern="retail banking",
        naics_codes=["522110"],
        confidence=1.0,
        source="curated",
    )
    assert "retail banking" in repr(mapping)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/models/test_lob_naics_mapping.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/models/lob_naics_mapping.py
"""LOB to NAICS mapping model."""
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LobNaicsMapping(Base):
    """Mapping from Line of Business patterns to NAICS codes."""
    __tablename__ = "lob_naics_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lob_pattern: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    naics_codes: Mapped[list[str]] = mapped_column(ARRAY(String(6)), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="curated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<LobNaicsMapping(pattern={self.lob_pattern}, codes={self.naics_codes})>"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/models/test_lob_naics_mapping.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/lob_naics_mapping.py app/models/__init__.py tests/unit/models/test_lob_naics_mapping.py
git commit -m "feat(models): add LobNaicsMapping model with array support"
```

---

### Task 7: Create OnetOccupationIndustry SQLAlchemy Model

**Files:**
- Create: `app/models/onet_occupation_industry.py`
- Modify: `app/models/__init__.py`
- Test: `tests/unit/models/test_onet_occupation_industry.py`

**Step 1: Write the failing test**

```python
# tests/unit/models/test_onet_occupation_industry.py
"""Test OnetOccupationIndustry model."""
import pytest
from app.models.onet_occupation_industry import OnetOccupationIndustry


def test_onet_occupation_industry_fields():
    """Test model has expected fields."""
    assert hasattr(OnetOccupationIndustry, "id")
    assert hasattr(OnetOccupationIndustry, "occupation_code")
    assert hasattr(OnetOccupationIndustry, "naics_code")
    assert hasattr(OnetOccupationIndustry, "naics_title")
    assert hasattr(OnetOccupationIndustry, "employment_percent")


def test_onet_occupation_industry_tablename():
    """Test table name."""
    assert OnetOccupationIndustry.__tablename__ == "onet_occupation_industries"


def test_onet_occupation_industry_repr():
    """Test string representation."""
    ind = OnetOccupationIndustry(
        occupation_code="13-2051.00",
        naics_code="522110",
        naics_title="Commercial Banking",
        employment_percent=15.5,
    )
    assert "13-2051.00" in repr(ind)
    assert "522110" in repr(ind)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/models/test_onet_occupation_industry.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/models/onet_occupation_industry.py
"""O*NET occupation-industry mapping model."""
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OnetOccupationIndustry(Base):
    """Maps O*NET occupations to industries where they're employed."""
    __tablename__ = "onet_occupation_industries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    naics_code: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    naics_title: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationship to occupation
    occupation: Mapped["OnetOccupation"] = relationship(back_populates="industries")

    def __repr__(self) -> str:
        return f"<OnetOccupationIndustry(occ={self.occupation_code}, naics={self.naics_code})>"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/models/test_onet_occupation_industry.py -v`
Expected: PASS

**Step 5: Update OnetOccupation model and commit**

Add to `app/models/onet_occupation.py`:
```python
industries: Mapped[list["OnetOccupationIndustry"]] = relationship(
    back_populates="occupation", cascade="all, delete-orphan"
)
```

```bash
git add app/models/onet_occupation_industry.py app/models/onet_occupation.py app/models/__init__.py tests/unit/models/test_onet_occupation_industry.py
git commit -m "feat(models): add OnetOccupationIndustry model"
```

---

### Task 8: Update DiscoveryRoleMapping Model with LOB Fields

**Files:**
- Modify: `app/models/discovery_role_mapping.py`
- Test: `tests/unit/models/test_discovery_role_mapping_lob.py`

**Step 1: Write the failing test**

```python
# tests/unit/models/test_discovery_role_mapping_lob.py
"""Test DiscoveryRoleMapping LOB fields."""
import pytest
from app.models.discovery_role_mapping import DiscoveryRoleMapping


def test_discovery_role_mapping_has_lob_value():
    """Test model has lob_value field."""
    assert hasattr(DiscoveryRoleMapping, "lob_value")


def test_discovery_role_mapping_has_naics_codes():
    """Test model has naics_codes array field."""
    assert hasattr(DiscoveryRoleMapping, "naics_codes")


def test_discovery_role_mapping_has_industry_match_score():
    """Test model has industry_match_score field."""
    assert hasattr(DiscoveryRoleMapping, "industry_match_score")


def test_discovery_role_mapping_with_lob():
    """Test creating mapping with LOB data."""
    mapping = DiscoveryRoleMapping(
        source_role="Financial Analyst",
        lob_value="Retail Banking",
        naics_codes=["522110", "523110"],
        industry_match_score=0.85,
    )
    assert mapping.lob_value == "Retail Banking"
    assert mapping.naics_codes == ["522110", "523110"]
    assert mapping.industry_match_score == 0.85
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/models/test_discovery_role_mapping_lob.py -v`
Expected: FAIL with "AttributeError: 'DiscoveryRoleMapping' has no attribute 'lob_value'"

**Step 3: Write minimal implementation**

Update `app/models/discovery_role_mapping.py`:

```python
# Add these imports at the top
from sqlalchemy.dialects.postgresql import ARRAY

# Add these columns after existing columns
lob_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
naics_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String(6)), nullable=True)
industry_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/models/test_discovery_role_mapping_lob.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/discovery_role_mapping.py tests/unit/models/test_discovery_role_mapping_lob.py
git commit -m "feat(models): add LOB fields to DiscoveryRoleMapping"
```

---

## Phase 2: Backend Services (Tasks 9-16)

### Task 9: Create Column Detection Service

**Files:**
- Create: `app/services/column_detection_service.py`
- Test: `tests/unit/services/test_column_detection_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/services/test_column_detection_service.py
"""Test ColumnDetectionService."""
import pytest
from app.services.column_detection_service import ColumnDetectionService, DetectedMapping


@pytest.fixture
def service():
    return ColumnDetectionService()


class TestKeywordMatching:
    """Test keyword-based column detection."""

    def test_detect_role_column_from_title(self, service):
        """Test detecting role column from 'Job Title' header."""
        columns = ["Employee ID", "Job Title", "Department"]
        sample_rows = [
            {"Employee ID": "1001", "Job Title": "Software Engineer", "Department": "IT"},
        ]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping is not None
        assert role_mapping.column == "Job Title"
        assert role_mapping.confidence >= 0.8

    def test_detect_lob_column(self, service):
        """Test detecting LOB column."""
        columns = ["Name", "Line of Business", "Title"]
        sample_rows = [
            {"Name": "John", "Line of Business": "Retail Banking", "Title": "Analyst"},
        ]

        result = service.detect_mappings_sync(columns, sample_rows)
        lob_mapping = next((m for m in result if m.field == "lob"), None)

        assert lob_mapping is not None
        assert lob_mapping.column == "Line of Business"
        assert lob_mapping.confidence >= 0.8

    def test_detect_department_column(self, service):
        """Test detecting department column."""
        columns = ["Emp", "Dept", "Role"]
        sample_rows = [{"Emp": "1", "Dept": "Finance", "Role": "Manager"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        dept_mapping = next((m for m in result if m.field == "department"), None)

        assert dept_mapping is not None
        assert dept_mapping.column == "Dept"

    def test_no_match_returns_alternatives(self, service):
        """Test that unmatched columns provide alternatives."""
        columns = ["A", "B", "C"]  # Ambiguous names
        sample_rows = [{"A": "1", "B": "2", "C": "3"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping is not None
        assert role_mapping.column is None or role_mapping.confidence < 0.6
        assert len(role_mapping.alternatives) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_column_detection_service.py::TestKeywordMatching -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/services/column_detection_service.py
"""Column detection service for auto-detecting field mappings."""
from dataclasses import dataclass
from typing import Any


@dataclass
class DetectedMapping:
    """Result of column detection for a field."""
    field: str
    column: str | None
    confidence: float
    alternatives: list[str]
    required: bool


class ColumnDetectionService:
    """Auto-detect column mappings using heuristics + LLM fallback."""

    FIELD_DEFINITIONS = {
        "role": {
            "description": "Job title, position, or role name",
            "keywords": ["title", "position", "role", "job", "occupation", "designation"],
            "required": True,
        },
        "lob": {
            "description": "Line of business, business unit, segment, or division",
            "keywords": ["lob", "line of business", "business unit", "segment", "division", "business line"],
            "required": False,
        },
        "department": {
            "description": "Department, cost center, or team",
            "keywords": ["department", "dept", "cost center", "team", "group", "function", "org"],
            "required": False,
        },
        "geography": {
            "description": "Office location, city, region, or site",
            "keywords": ["location", "office", "site", "region", "city", "geo", "country"],
            "required": False,
        },
    }

    def __init__(self, llm_service: Any = None):
        """Initialize service with optional LLM for fallback."""
        self.llm_service = llm_service

    def detect_mappings_sync(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Synchronously detect column mappings (no LLM fallback)."""
        return self._detect_with_keywords(columns, sample_rows)

    async def detect_mappings(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Detect column mappings with LLM fallback for ambiguous cases."""
        mappings = self._detect_with_keywords(columns, sample_rows)

        # Use LLM fallback for low-confidence required fields
        if self.llm_service:
            for mapping in mappings:
                if mapping.required and mapping.confidence < 0.6:
                    llm_result = await self._llm_detect(
                        mapping.field,
                        columns,
                        sample_rows,
                    )
                    if llm_result:
                        mapping.column = llm_result.column
                        mapping.confidence = llm_result.confidence

        return mappings

    def _detect_with_keywords(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Detect mappings using keyword matching."""
        mappings = []
        used_columns: set[str] = set()

        for field, definition in self.FIELD_DEFINITIONS.items():
            match = self._keyword_match(
                columns,
                definition["keywords"],
                used_columns,
            )

            alternatives = [c for c in columns if c not in used_columns]

            if match:
                mappings.append(DetectedMapping(
                    field=field,
                    column=match["column"],
                    confidence=match["confidence"],
                    alternatives=alternatives,
                    required=definition["required"],
                ))
                used_columns.add(match["column"])
            else:
                mappings.append(DetectedMapping(
                    field=field,
                    column=None,
                    confidence=0.0,
                    alternatives=alternatives,
                    required=definition["required"],
                ))

        return mappings

    def _keyword_match(
        self,
        columns: list[str],
        keywords: list[str],
        used: set[str],
    ) -> dict | None:
        """Match column to keywords."""
        best_match = None
        best_score = 0.0

        for col in columns:
            if col in used:
                continue

            col_lower = col.lower().strip()

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Exact match
                if col_lower == keyword_lower:
                    return {"column": col, "confidence": 1.0}

                # Contains keyword
                if keyword_lower in col_lower:
                    score = 0.9
                    if score > best_score:
                        best_score = score
                        best_match = {"column": col, "confidence": score}

                # Column contains in keyword (e.g., "Dept" in "department")
                elif col_lower in keyword_lower and len(col_lower) >= 3:
                    score = 0.8
                    if score > best_score:
                        best_score = score
                        best_match = {"column": col, "confidence": score}

        return best_match if best_score >= 0.8 else None

    async def _llm_detect(
        self,
        field: str,
        columns: list[str],
        sample_rows: list[dict],
    ) -> DetectedMapping | None:
        """Use LLM to detect column mapping."""
        if not self.llm_service:
            return None

        definition = self.FIELD_DEFINITIONS[field]
        prompt = f"""Given these columns and sample data, identify which column contains the {field}.

Field description: {definition['description']}

Columns: {columns}

Sample data:
{sample_rows[:3]}

Respond with just the column name, or "NONE" if no match."""

        response = await self.llm_service.complete(prompt)
        col = response.strip()

        if col in columns:
            return DetectedMapping(
                field=field,
                column=col,
                confidence=0.7,  # LLM confidence
                alternatives=[],
                required=definition["required"],
            )

        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_column_detection_service.py::TestKeywordMatching -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/column_detection_service.py tests/unit/services/test_column_detection_service.py
git commit -m "feat(services): add ColumnDetectionService with keyword matching"
```

---

### Task 10: Create LOB Mapping Repository

**Files:**
- Create: `app/repositories/lob_mapping_repository.py`
- Test: `tests/unit/repositories/test_lob_mapping_repository.py`

**Step 1: Write the failing test**

```python
# tests/unit/repositories/test_lob_mapping_repository.py
"""Test LobMappingRepository."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories.lob_mapping_repository import LobMappingRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return LobMappingRepository(mock_session)


class TestFindByPattern:
    """Test finding LOB mappings by pattern."""

    async def test_find_exact_match(self, repository, mock_session):
        """Test finding exact pattern match."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_mapping = LobNaicsMapping(
            id=1,
            lob_pattern="retail banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_mapping

        result = await repository.find_by_pattern("retail banking")

        assert result is not None
        assert result.naics_codes == ["522110"]

    async def test_find_no_match(self, repository, mock_session):
        """Test when no match found."""
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await repository.find_by_pattern("unknown lob")

        assert result is None


class TestCreate:
    """Test creating new LOB mappings."""

    async def test_create_mapping(self, repository, mock_session):
        """Test creating a new mapping."""
        result = await repository.create(
            lob_pattern="investment banking",
            naics_codes=["523110"],
            confidence=0.8,
            source="llm",
        )

        mock_session.add.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/repositories/test_lob_mapping_repository.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/repositories/lob_mapping_repository.py
"""Repository for LOB to NAICS mappings."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lob_naics_mapping import LobNaicsMapping


class LobMappingRepository:
    """Repository for LOB-NAICS mapping operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_pattern(self, pattern: str) -> LobNaicsMapping | None:
        """Find mapping by exact pattern match (case-insensitive)."""
        normalized = pattern.lower().strip()
        stmt = select(LobNaicsMapping).where(
            func.lower(LobNaicsMapping.lob_pattern) == normalized
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_fuzzy(
        self,
        pattern: str,
        threshold: float = 0.85,
    ) -> LobNaicsMapping | None:
        """Find mapping using fuzzy matching.

        Uses PostgreSQL similarity function for fuzzy matching.
        Returns best match above threshold.
        """
        normalized = pattern.lower().strip()

        # Use pg_trgm similarity if available, otherwise exact match
        stmt = select(LobNaicsMapping).where(
            func.similarity(LobNaicsMapping.lob_pattern, normalized) >= threshold
        ).order_by(
            func.similarity(LobNaicsMapping.lob_pattern, normalized).desc()
        ).limit(1)

        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            # Fall back to exact match if pg_trgm not available
            return await self.find_by_pattern(pattern)

    async def create(
        self,
        lob_pattern: str,
        naics_codes: list[str],
        confidence: float = 1.0,
        source: str = "curated",
    ) -> LobNaicsMapping:
        """Create a new LOB mapping."""
        mapping = LobNaicsMapping(
            lob_pattern=lob_pattern.lower().strip(),
            naics_codes=naics_codes,
            confidence=confidence,
            source=source,
        )
        self.session.add(mapping)
        await self.session.flush()
        return mapping

    async def get_all(self) -> list[LobNaicsMapping]:
        """Get all LOB mappings."""
        stmt = select(LobNaicsMapping).order_by(LobNaicsMapping.lob_pattern)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_upsert(
        self,
        mappings: list[dict],
    ) -> int:
        """Bulk upsert LOB mappings."""
        count = 0
        for data in mappings:
            existing = await self.find_by_pattern(data["lob_pattern"])
            if existing:
                existing.naics_codes = data["naics_codes"]
                existing.confidence = data.get("confidence", 1.0)
                existing.source = data.get("source", "curated")
            else:
                await self.create(**data)
            count += 1
        return count
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/repositories/test_lob_mapping_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/repositories/lob_mapping_repository.py tests/unit/repositories/test_lob_mapping_repository.py
git commit -m "feat(repos): add LobMappingRepository"
```

---

### Task 11: Create LOB Mapping Service

**Files:**
- Create: `app/services/lob_mapping_service.py`
- Test: `tests/unit/services/test_lob_mapping_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/services/test_lob_mapping_service.py
"""Test LobMappingService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.lob_mapping_service import LobMappingService, LobNaicsResult


@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    llm = AsyncMock()
    return llm


@pytest.fixture
def service(mock_repository, mock_llm_service):
    return LobMappingService(mock_repository, mock_llm_service)


class TestMapLobToNaics:
    """Test LOB to NAICS mapping."""

    async def test_exact_match_from_curated(self, service, mock_repository):
        """Test exact match returns curated mapping."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = LobNaicsMapping(
            lob_pattern="retail banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )

        result = await service.map_lob_to_naics("Retail Banking")

        assert result.naics_codes == ["522110"]
        assert result.confidence == 1.0
        assert result.source == "curated"

    async def test_fuzzy_match_reduces_confidence(self, service, mock_repository):
        """Test fuzzy match reduces confidence score."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = None
        mock_repository.find_fuzzy.return_value = LobNaicsMapping(
            lob_pattern="retail bank",
            naics_codes=["522110"],
            confidence=0.95,
            source="curated",
        )

        result = await service.map_lob_to_naics("Retail Banking Div")

        assert result.naics_codes == ["522110"]
        assert result.confidence < 0.95  # Reduced for fuzzy
        assert result.source == "fuzzy"

    async def test_llm_fallback_when_no_match(self, service, mock_repository, mock_llm_service):
        """Test LLM fallback when no curated match."""
        mock_repository.find_by_pattern.return_value = None
        mock_repository.find_fuzzy.return_value = None
        mock_llm_service.complete.return_value = '["523110"]'

        result = await service.map_lob_to_naics("Investment Management")

        mock_llm_service.complete.assert_called_once()
        assert result.source == "llm"
        assert result.confidence == 0.8
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_lob_mapping_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/services/lob_mapping_service.py
"""LOB to NAICS mapping service."""
import json
from dataclasses import dataclass
from typing import Any

from app.repositories.lob_mapping_repository import LobMappingRepository


@dataclass
class LobNaicsResult:
    """Result of LOB to NAICS mapping."""
    lob: str
    naics_codes: list[str]
    confidence: float
    source: str  # "curated", "fuzzy", or "llm"


class LobMappingService:
    """Map Line of Business values to NAICS industry codes."""

    def __init__(
        self,
        repository: LobMappingRepository,
        llm_service: Any = None,
    ):
        self.repository = repository
        self.llm = llm_service

    async def map_lob_to_naics(self, lob: str) -> LobNaicsResult:
        """Map LOB string to NAICS codes.

        1. Normalize input (lowercase, trim)
        2. Check curated lookup table (exact match)
        3. Try fuzzy match
        4. Fall back to LLM if no match
        5. Cache LLM results for future use
        """
        normalized = self._normalize(lob)

        # Try exact match first
        mapping = await self.repository.find_by_pattern(normalized)
        if mapping:
            return LobNaicsResult(
                lob=lob,
                naics_codes=mapping.naics_codes,
                confidence=mapping.confidence,
                source=mapping.source,
            )

        # Try fuzzy match
        mapping = await self.repository.find_fuzzy(normalized, threshold=0.85)
        if mapping:
            return LobNaicsResult(
                lob=lob,
                naics_codes=mapping.naics_codes,
                confidence=mapping.confidence * 0.9,  # Reduce for fuzzy
                source="fuzzy",
            )

        # LLM fallback
        if self.llm:
            naics_codes = await self._llm_map(lob)
            if naics_codes:
                # Cache the result
                await self.repository.create(
                    lob_pattern=normalized,
                    naics_codes=naics_codes,
                    confidence=0.8,
                    source="llm",
                )
                return LobNaicsResult(
                    lob=lob,
                    naics_codes=naics_codes,
                    confidence=0.8,
                    source="llm",
                )

        # No match found
        return LobNaicsResult(
            lob=lob,
            naics_codes=[],
            confidence=0.0,
            source="none",
        )

    async def map_batch(self, lobs: list[str]) -> dict[str, LobNaicsResult]:
        """Map multiple LOBs to NAICS codes."""
        results = {}
        for lob in set(lobs):  # Dedupe
            results[lob] = await self.map_lob_to_naics(lob)
        return results

    def _normalize(self, lob: str) -> str:
        """Normalize LOB string for matching."""
        return lob.lower().strip()

    async def _llm_map(self, lob: str) -> list[str] | None:
        """Use LLM to determine NAICS codes for LOB."""
        if not self.llm:
            return None

        prompt = f"""Map this Line of Business to NAICS industry codes.

Line of Business: "{lob}"

Return a JSON array of the most relevant 2-digit or 3-digit NAICS codes.
Common examples:
- "Retail Banking" → ["522110"]
- "Software Development" → ["541511"]
- "Healthcare" → ["62"]

Respond with ONLY a JSON array like ["52", "523110"]. No explanation."""

        try:
            response = await self.llm.complete(prompt)
            codes = json.loads(response.strip())
            if isinstance(codes, list) and all(isinstance(c, str) for c in codes):
                return codes
        except (json.JSONDecodeError, Exception):
            pass

        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_lob_mapping_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/lob_mapping_service.py tests/unit/services/test_lob_mapping_service.py
git commit -m "feat(services): add LobMappingService with LLM fallback"
```

---

### Task 12: Create Industry Repository Methods

**Files:**
- Modify: `app/repositories/onet_repository.py`
- Test: `tests/unit/repositories/test_onet_repository_industries.py`

**Step 1: Write the failing test**

```python
# tests/unit/repositories/test_onet_repository_industries.py
"""Test OnetRepository industry methods."""
import pytest
from unittest.mock import AsyncMock
from app.repositories.onet_repository import OnetRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return OnetRepository(mock_session)


class TestGetIndustriesForOccupation:
    """Test getting industries for an occupation."""

    async def test_get_industries(self, repository, mock_session):
        """Test getting industry list for occupation code."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
                employment_percent=25.0,
            ),
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="523110",
                naics_title="Investment Banking",
                employment_percent=15.0,
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        result = await repository.get_industries_for_occupation("13-2051.00")

        assert len(result) == 2
        assert result[0].naics_code == "522110"


class TestCalculateIndustryScore:
    """Test industry match score calculation."""

    async def test_exact_naics_match(self, repository, mock_session):
        """Test perfect match score for exact NAICS code."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
                employment_percent=25.0,
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        score = await repository.calculate_industry_score("13-2051.00", ["522110"])

        assert score == 1.0

    async def test_partial_naics_match(self, repository, mock_session):
        """Test partial match when NAICS prefix matches."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        # Match 2-digit prefix
        score = await repository.calculate_industry_score("13-2051.00", ["52"])

        assert 0.3 <= score <= 0.5  # Partial match

    async def test_no_match_zero_score(self, repository, mock_session):
        """Test zero score when no industry match."""
        from app.models.onet_occupation_industry import OnetOccupationIndustry

        mock_industries = [
            OnetOccupationIndustry(
                occupation_code="13-2051.00",
                naics_code="522110",
                naics_title="Commercial Banking",
            ),
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_industries

        score = await repository.calculate_industry_score("13-2051.00", ["62"])  # Healthcare

        assert score == 0.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/repositories/test_onet_repository_industries.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `app/repositories/onet_repository.py`:

```python
# Add import
from app.models.onet_occupation_industry import OnetOccupationIndustry

# Add methods to OnetRepository class
async def get_industries_for_occupation(
    self,
    occupation_code: str,
) -> list[OnetOccupationIndustry]:
    """Get all industries for an occupation."""
    stmt = select(OnetOccupationIndustry).where(
        OnetOccupationIndustry.occupation_code == occupation_code
    ).order_by(OnetOccupationIndustry.employment_percent.desc().nulls_last())

    result = await self.session.execute(stmt)
    return list(result.scalars().all())

async def calculate_industry_score(
    self,
    occupation_code: str,
    naics_codes: list[str],
) -> float:
    """Calculate industry match score for occupation and NAICS codes.

    Returns 0-1 score based on how well the occupation matches
    the provided industry codes.
    """
    if not naics_codes:
        return 0.0

    industries = await self.get_industries_for_occupation(occupation_code)
    if not industries:
        return 0.0

    best_score = 0.0
    for industry in industries:
        for target_code in naics_codes:
            score = self._naics_match_score(industry.naics_code, target_code)
            if score > best_score:
                best_score = score

    return best_score

def _naics_match_score(self, code1: str, code2: str) -> float:
    """Calculate similarity between two NAICS codes."""
    # Exact match
    if code1 == code2:
        return 1.0

    # Check prefix matching (longer prefix = better match)
    min_len = min(len(code1), len(code2))
    for i in range(min_len, 0, -1):
        if code1[:i] == code2[:i]:
            # Score based on matching prefix length
            if i >= 4:
                return 0.8
            elif i >= 3:
                return 0.6
            elif i >= 2:
                return 0.4

    return 0.0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/repositories/test_onet_repository_industries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/repositories/onet_repository.py tests/unit/repositories/test_onet_repository_industries.py
git commit -m "feat(repos): add industry matching methods to OnetRepository"
```

---

### Task 13: Enhance RoleMappingService with Industry Boost

**Files:**
- Modify: `app/services/role_mapping_service.py`
- Test: `tests/unit/services/test_role_mapping_service_industry.py`

**Step 1: Write the failing test**

```python
# tests/unit/services/test_role_mapping_service_industry.py
"""Test RoleMappingService industry-aware matching."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.role_mapping_service import RoleMappingService


@pytest.fixture
def mock_onet_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_lob_service():
    service = AsyncMock()
    return service


@pytest.fixture
def service(mock_onet_repo, mock_lob_service):
    from app.services.role_mapping_service import RoleMappingService
    return RoleMappingService(
        onet_repository=mock_onet_repo,
        lob_service=mock_lob_service,
    )


class TestMatchRoleWithIndustry:
    """Test industry-aware role matching."""

    async def test_industry_boosts_relevant_occupation(
        self, service, mock_onet_repo, mock_lob_service
    ):
        """Test that industry match boosts occupation score."""
        from app.services.lob_mapping_service import LobNaicsResult

        # Mock two occupation candidates
        mock_onet_repo.search_occupations.return_value = [
            {"code": "13-2051.00", "title": "Financial Analysts", "score": 0.90},
            {"code": "13-2011.00", "title": "Accountants", "score": 0.85},
        ]

        # Mock LOB mapping
        mock_lob_service.map_lob_to_naics.return_value = LobNaicsResult(
            lob="Retail Banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )

        # Mock industry scores - Financial Analysts matches banking better
        async def mock_industry_score(code, naics):
            if code == "13-2051.00":  # Financial Analysts
                return 0.9  # Strong banking match
            return 0.2  # Accountants - weak match

        mock_onet_repo.calculate_industry_score.side_effect = mock_industry_score

        result = await service.match_role_with_industry(
            job_title="Financial Analyst",
            lob="Retail Banking",
        )

        # Financial Analysts should be ranked higher due to industry boost
        assert result[0]["code"] == "13-2051.00"
        assert result[0]["industry_match"] > 0

    async def test_without_lob_no_industry_boost(
        self, service, mock_onet_repo, mock_lob_service
    ):
        """Test that without LOB, no industry boost is applied."""
        mock_onet_repo.search_occupations.return_value = [
            {"code": "13-2051.00", "title": "Financial Analysts", "score": 0.90},
        ]

        result = await service.match_role_with_industry(
            job_title="Financial Analyst",
            lob=None,
        )

        # Score should be unchanged
        assert result[0]["score"] == 0.90
        assert result[0].get("industry_match") is None
        mock_lob_service.map_lob_to_naics.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_role_mapping_service_industry.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/services/role_mapping_service.py`:

```python
# Add to imports
from app.services.lob_mapping_service import LobMappingService

# Update __init__ to accept lob_service
def __init__(
    self,
    onet_repository,
    lob_service: LobMappingService | None = None,
):
    self.onet_repository = onet_repository
    self.lob_service = lob_service

# Add new method
INDUSTRY_BOOST_FACTOR = 0.25  # Max 25% boost

async def match_role_with_industry(
    self,
    job_title: str,
    lob: str | None = None,
) -> list[dict]:
    """Match job title to O*NET occupations with industry context.

    Args:
        job_title: The job title to match.
        lob: Optional Line of Business for industry-aware boosting.

    Returns:
        List of occupation matches with scores.
    """
    # Get candidate occupations from title search
    candidates = await self.onet_repository.search_occupations(job_title)

    if not candidates:
        return []

    if not lob or not self.lob_service:
        return candidates

    # Get NAICS codes for the LOB
    lob_result = await self.lob_service.map_lob_to_naics(lob)
    naics_codes = lob_result.naics_codes

    if not naics_codes:
        return candidates

    # Score candidates with industry boost
    for candidate in candidates:
        industry_score = await self.onet_repository.calculate_industry_score(
            candidate["code"],
            naics_codes,
        )

        original_score = candidate["score"]
        boosted_score = original_score * (1 + self.INDUSTRY_BOOST_FACTOR * industry_score)

        candidate["score"] = boosted_score
        candidate["industry_match"] = industry_score
        candidate["original_score"] = original_score

    # Re-sort by boosted score
    return sorted(candidates, key=lambda x: x["score"], reverse=True)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_role_mapping_service_industry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/role_mapping_service.py tests/unit/services/test_role_mapping_service_industry.py
git commit -m "feat(services): add industry-aware matching to RoleMappingService"
```

---

### Task 14: Extend OnetFileSyncService for Industry Data

**Files:**
- Modify: `app/services/onet_file_sync_service.py`
- Test: `tests/unit/services/test_onet_file_sync_industries.py`

**Step 1: Write the failing test**

```python
# tests/unit/services/test_onet_file_sync_industries.py
"""Test OnetFileSyncService industry data import."""
import pytest
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


class TestSyncIndustries:
    """Test syncing industry data."""

    async def test_sync_includes_industries(self, mocker):
        """Test that sync() imports industry data."""
        mock_repo = mocker.AsyncMock()
        mock_repo.bulk_upsert_occupations.return_value = 10
        mock_repo.bulk_replace_alternate_titles.return_value = 20
        mock_repo.bulk_replace_tasks.return_value = 30
        mock_repo.bulk_upsert_industries.return_value = 100
        mock_repo.log_sync = mocker.AsyncMock()
        mock_repo.session = mocker.AsyncMock()

        service = OnetFileSyncService(repository=mock_repo)

        # Mock download to return test zip
        mocker.patch.object(service, "_download", return_value=b"fake_zip")
        mocker.patch.object(service, "_extract_and_parse", return_value=([], [], [], []))

        result = await service.sync("30_1")

        assert hasattr(result, "industry_count")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_onet_file_sync_industries.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/services/onet_file_sync_service.py`:

```python
# Add to constants
INDUSTRY_FILE = "Industry.txt"

# Update SyncResult dataclass
@dataclass
class SyncResult:
    """Result of an O*NET sync operation."""
    version: str
    occupation_count: int
    alternate_title_count: int
    task_count: int
    industry_count: int  # NEW
    status: str

# Add parse method
def _parse_industries(self, content: str) -> list[dict[str, Any]]:
    """Parse industry data from tab-separated content.

    Args:
        content: Tab-separated industry data.

    Returns:
        List of industry dicts.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    industries = []

    for row in reader:
        employment = None
        if row.get("Employment"):
            try:
                employment = float(row["Employment"])
            except (ValueError, TypeError):
                pass

        industries.append({
            "occupation_code": row["O*NET-SOC Code"],
            "naics_code": row["Industry Code"],
            "naics_title": row["Industry Title"],
            "employment_percent": employment,
        })

    return industries

# Update _extract_and_parse to include industries
def _extract_and_parse(
    self,
    zip_data: bytes,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Extract and parse O*NET data files from zip.

    Returns:
        Tuple of (occupations, alternate_titles, tasks, industries).
    """
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        names = zf.namelist()
        prefix = names[0].split("/")[0] + "/" if "/" in names[0] else ""

        occ_content = zf.read(f"{prefix}{self.OCCUPATION_FILE}").decode("utf-8")
        alt_content = zf.read(f"{prefix}{self.ALTERNATE_TITLES_FILE}").decode("utf-8")
        task_content = zf.read(f"{prefix}{self.TASKS_FILE}").decode("utf-8")

        # Try to read industry file (may not exist in all versions)
        try:
            ind_content = zf.read(f"{prefix}{self.INDUSTRY_FILE}").decode("utf-8")
        except KeyError:
            ind_content = ""

    occupations = self._parse_occupations(occ_content)
    alt_titles = self._parse_alternate_titles(alt_content)
    tasks = self._parse_tasks(task_content)
    industries = self._parse_industries(ind_content) if ind_content else []

    return occupations, alt_titles, tasks, industries

# Update sync() method to handle industries
# In the sync() method, after parsing:
occupations, alt_titles, tasks, industries = self._extract_and_parse(zip_data)

# Add industry upsert
ind_count = await self.repository.bulk_upsert_industries(industries)

# Update return
return SyncResult(
    version=display_version,
    occupation_count=occ_count,
    alternate_title_count=alt_count,
    task_count=task_count,
    industry_count=ind_count,
    status="success",
)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_onet_file_sync_industries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/onet_file_sync_service.py tests/unit/services/test_onet_file_sync_industries.py
git commit -m "feat(services): add industry data import to OnetFileSyncService"
```

---

### Task 15: Add Repository Method for Industry Bulk Upsert

**Files:**
- Modify: `app/repositories/onet_repository.py`
- Test: `tests/unit/repositories/test_onet_repository_bulk_industries.py`

**Step 1: Write the failing test**

```python
# tests/unit/repositories/test_onet_repository_bulk_industries.py
"""Test OnetRepository bulk_upsert_industries."""
import pytest
from unittest.mock import AsyncMock


class TestBulkUpsertIndustries:
    """Test bulk upserting industry data."""

    async def test_bulk_upsert_industries(self):
        """Test inserting new industry records."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        repo = OnetRepository(mock_session)

        industries = [
            {
                "occupation_code": "13-2051.00",
                "naics_code": "522110",
                "naics_title": "Commercial Banking",
                "employment_percent": 0.25,
            },
            {
                "occupation_code": "13-2051.00",
                "naics_code": "523110",
                "naics_title": "Investment Banking",
                "employment_percent": 0.15,
            },
        ]

        result = await repo.bulk_upsert_industries(industries)

        assert result == 2

    async def test_bulk_upsert_handles_empty_list(self):
        """Test handling empty industry list."""
        from app.repositories.onet_repository import OnetRepository

        mock_session = AsyncMock()
        repo = OnetRepository(mock_session)

        result = await repo.bulk_upsert_industries([])

        assert result == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/repositories/test_onet_repository_bulk_industries.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `app/repositories/onet_repository.py`:

```python
async def bulk_upsert_industries(
    self,
    industries: list[dict],
) -> int:
    """Bulk upsert occupation-industry mappings.

    Uses PostgreSQL ON CONFLICT for upsert behavior.

    Args:
        industries: List of industry dicts with occupation_code, naics_code, etc.

    Returns:
        Number of records upserted.
    """
    if not industries:
        return 0

    from sqlalchemy.dialects.postgresql import insert
    from app.models.onet_occupation_industry import OnetOccupationIndustry

    stmt = insert(OnetOccupationIndustry).values(industries)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_occ_naics",
        set_={
            "naics_title": stmt.excluded.naics_title,
            "employment_percent": stmt.excluded.employment_percent,
        }
    )

    await self.session.execute(stmt)
    return len(industries)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/repositories/test_onet_repository_bulk_industries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/repositories/onet_repository.py tests/unit/repositories/test_onet_repository_bulk_industries.py
git commit -m "feat(repos): add bulk_upsert_industries to OnetRepository"
```

---

### Task 16: Create Seed Data Script for LOB-NAICS Mappings

**Files:**
- Create: `app/data/lob_naics_seed.py`
- Test: `tests/unit/data/test_lob_naics_seed.py`

**Step 1: Write the failing test**

```python
# tests/unit/data/test_lob_naics_seed.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/data/test_lob_naics_seed.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/data/lob_naics_seed.py
"""Curated LOB to NAICS code mappings.

These mappings cover common Lines of Business in enterprise organizations.
NAICS codes are from the North American Industry Classification System.
"""

LOB_NAICS_MAPPINGS = [
    # Banking & Financial Services
    {"lob_pattern": "retail banking", "naics_codes": ["522110"]},
    {"lob_pattern": "commercial banking", "naics_codes": ["522110"]},
    {"lob_pattern": "investment banking", "naics_codes": ["523110"]},
    {"lob_pattern": "wealth management", "naics_codes": ["523930"]},
    {"lob_pattern": "private banking", "naics_codes": ["522110", "523930"]},
    {"lob_pattern": "asset management", "naics_codes": ["523920"]},
    {"lob_pattern": "capital markets", "naics_codes": ["523110", "523130"]},
    {"lob_pattern": "treasury", "naics_codes": ["522110", "523130"]},
    {"lob_pattern": "mortgage", "naics_codes": ["522310"]},
    {"lob_pattern": "credit cards", "naics_codes": ["522210"]},
    {"lob_pattern": "consumer lending", "naics_codes": ["522291"]},
    {"lob_pattern": "corporate banking", "naics_codes": ["522110"]},

    # Insurance
    {"lob_pattern": "life insurance", "naics_codes": ["524113"]},
    {"lob_pattern": "health insurance", "naics_codes": ["524114"]},
    {"lob_pattern": "property insurance", "naics_codes": ["524126"]},
    {"lob_pattern": "casualty insurance", "naics_codes": ["524126"]},
    {"lob_pattern": "reinsurance", "naics_codes": ["524130"]},
    {"lob_pattern": "insurance underwriting", "naics_codes": ["524126"]},
    {"lob_pattern": "claims", "naics_codes": ["524291"]},

    # Technology
    {"lob_pattern": "software", "naics_codes": ["541511", "541512"]},
    {"lob_pattern": "information technology", "naics_codes": ["541512"]},
    {"lob_pattern": "it services", "naics_codes": ["541512"]},
    {"lob_pattern": "cloud services", "naics_codes": ["518210"]},
    {"lob_pattern": "data services", "naics_codes": ["518210", "541511"]},
    {"lob_pattern": "cybersecurity", "naics_codes": ["541512"]},
    {"lob_pattern": "infrastructure", "naics_codes": ["541512", "517311"]},
    {"lob_pattern": "enterprise technology", "naics_codes": ["541512"]},

    # Healthcare
    {"lob_pattern": "healthcare", "naics_codes": ["62"]},
    {"lob_pattern": "pharmaceuticals", "naics_codes": ["325411"]},
    {"lob_pattern": "medical devices", "naics_codes": ["339112"]},
    {"lob_pattern": "clinical", "naics_codes": ["621111"]},
    {"lob_pattern": "hospital", "naics_codes": ["622110"]},

    # Professional Services
    {"lob_pattern": "consulting", "naics_codes": ["541611"]},
    {"lob_pattern": "legal", "naics_codes": ["541110"]},
    {"lob_pattern": "accounting", "naics_codes": ["541211"]},
    {"lob_pattern": "audit", "naics_codes": ["541211"]},
    {"lob_pattern": "tax", "naics_codes": ["541213"]},
    {"lob_pattern": "advisory", "naics_codes": ["541611"]},

    # Operations & Support
    {"lob_pattern": "operations", "naics_codes": ["561110"]},
    {"lob_pattern": "human resources", "naics_codes": ["541612"]},
    {"lob_pattern": "hr", "naics_codes": ["541612"]},
    {"lob_pattern": "finance", "naics_codes": ["523999"]},
    {"lob_pattern": "risk management", "naics_codes": ["524298"]},
    {"lob_pattern": "compliance", "naics_codes": ["541199"]},
    {"lob_pattern": "marketing", "naics_codes": ["541810"]},
    {"lob_pattern": "sales", "naics_codes": ["423"]},
    {"lob_pattern": "customer service", "naics_codes": ["561421"]},

    # Manufacturing & Industrial
    {"lob_pattern": "manufacturing", "naics_codes": ["31", "32", "33"]},
    {"lob_pattern": "supply chain", "naics_codes": ["493"]},
    {"lob_pattern": "logistics", "naics_codes": ["493110"]},
    {"lob_pattern": "procurement", "naics_codes": ["425120"]},

    # Retail & Consumer
    {"lob_pattern": "retail", "naics_codes": ["44", "45"]},
    {"lob_pattern": "e-commerce", "naics_codes": ["454110"]},
    {"lob_pattern": "consumer products", "naics_codes": ["311", "312", "316"]},

    # Real Estate
    {"lob_pattern": "real estate", "naics_codes": ["531"]},
    {"lob_pattern": "property management", "naics_codes": ["531311"]},
    {"lob_pattern": "facilities", "naics_codes": ["531312"]},

    # Energy & Utilities
    {"lob_pattern": "energy", "naics_codes": ["21", "22"]},
    {"lob_pattern": "utilities", "naics_codes": ["22"]},
    {"lob_pattern": "oil and gas", "naics_codes": ["211"]},
    {"lob_pattern": "renewables", "naics_codes": ["221114"]},

    # Media & Entertainment
    {"lob_pattern": "media", "naics_codes": ["511", "512"]},
    {"lob_pattern": "entertainment", "naics_codes": ["711", "712"]},
    {"lob_pattern": "digital media", "naics_codes": ["519130"]},
]


async def seed_lob_naics_mappings(repository) -> int:
    """Seed the LOB-NAICS mappings table.

    Args:
        repository: LobMappingRepository instance.

    Returns:
        Number of mappings seeded.
    """
    return await repository.bulk_upsert(LOB_NAICS_MAPPINGS)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/data/test_lob_naics_seed.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/data/lob_naics_seed.py app/data/__init__.py tests/unit/data/test_lob_naics_seed.py
git commit -m "feat(data): add curated LOB-NAICS seed mappings"
```

---

## Phase 3: API Endpoints (Tasks 17-22)

### Task 17: Update Upload Endpoint with Column Detection

**Files:**
- Modify: `app/routers/uploads.py`
- Modify: `app/schemas/upload.py`
- Test: `tests/unit/routers/test_uploads_column_detection.py`

**Step 1: Write the failing test**

```python
# tests/unit/routers/test_uploads_column_detection.py
"""Test upload endpoint with column detection."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from io import BytesIO


class TestUploadWithColumnDetection:
    """Test upload endpoint returns detected columns."""

    def test_upload_returns_detected_mappings(self, client, mock_upload_service):
        """Test that upload response includes detected column mappings."""
        mock_upload_service.process_upload.return_value = {
            "id": "test-upload-id",
            "file_name": "workforce.csv",
            "row_count": 100,
            "detected_schema": ["Employee ID", "Job Title", "Department", "LOB"],
            "column_suggestions": {},
            "preview": [{"Employee ID": "1", "Job Title": "Analyst", "Department": "IT", "LOB": "Tech"}],
            "detected_mappings": [
                {"field": "role", "column": "Job Title", "confidence": 0.95, "alternatives": [], "required": True},
                {"field": "lob", "column": "LOB", "confidence": 0.90, "alternatives": [], "required": False},
            ],
        }

        response = client.post(
            "/discovery/sessions/test-session/upload",
            files={"file": ("test.csv", BytesIO(b"a,b,c"), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "detected_mappings" in data
        assert len(data["detected_mappings"]) > 0
        assert data["detected_mappings"][0]["field"] == "role"


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_upload_service():
    with patch("app.routers.uploads.get_upload_service") as mock:
        service = AsyncMock()
        mock.return_value.__aenter__.return_value = service
        yield service
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/routers/test_uploads_column_detection.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/schemas/upload.py`:

```python
# Add new schema
class DetectedMappingResponse(BaseModel):
    """Column detection result for a field."""
    field: str
    column: str | None
    confidence: float
    alternatives: list[str]
    required: bool


class UploadWithDetectionResponse(BaseModel):
    """Upload response with column detection."""
    id: str
    file_name: str
    row_count: int
    detected_schema: list[str]
    preview: list[dict]
    detected_mappings: list[DetectedMappingResponse]
```

Update `app/routers/uploads.py`:

```python
# Add import
from app.services.column_detection_service import ColumnDetectionService

# Update upload endpoint
@router.post(
    "/sessions/{session_id}/upload",
    response_model=UploadWithDetectionResponse,
)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadWithDetectionResponse:
    """Upload workforce file and auto-detect column mappings."""
    content = await file.read()

    # Process upload
    result = await upload_service.process_upload(
        session_id=session_id,
        file_name=file.filename or "upload",
        content=content,
    )

    # Detect column mappings
    column_detector = ColumnDetectionService()
    detected = column_detector.detect_mappings_sync(
        columns=result["detected_schema"],
        sample_rows=result.get("preview", []),
    )

    return UploadWithDetectionResponse(
        id=result["id"],
        file_name=result["file_name"],
        row_count=result["row_count"],
        detected_schema=result["detected_schema"],
        preview=result.get("preview", []),
        detected_mappings=[
            DetectedMappingResponse(
                field=m.field,
                column=m.column,
                confidence=m.confidence,
                alternatives=m.alternatives,
                required=m.required,
            )
            for m in detected
        ],
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/routers/test_uploads_column_detection.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routers/uploads.py app/schemas/upload.py tests/unit/routers/test_uploads_column_detection.py
git commit -m "feat(api): add column detection to upload endpoint"
```

---

### Task 18: Add Grouped Role Mappings Endpoint

**Files:**
- Modify: `app/routers/role_mappings.py`
- Modify: `app/schemas/role_mapping.py`
- Test: `tests/unit/routers/test_role_mappings_grouped.py`

**Step 1: Write the failing test**

```python
# tests/unit/routers/test_role_mappings_grouped.py
"""Test grouped role mappings endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


class TestGroupedRoleMappings:
    """Test grouped role mappings endpoint."""

    def test_get_grouped_mappings_by_lob(self, client, mock_role_service):
        """Test getting role mappings grouped by LOB."""
        mock_role_service.get_grouped_mappings.return_value = {
            "summary": {
                "total_roles": 75,
                "total_employees": 1000,
                "confirmed_count": 60,
                "needs_review_count": 15,
            },
            "groups": [
                {
                    "lob": "Retail Banking",
                    "role_count": 28,
                    "employee_count": 412,
                    "confirmed_count": 25,
                    "mappings": [
                        {
                            "id": "mapping-1",
                            "source_role": "Financial Analyst",
                            "onet_code": "13-2051.00",
                            "onet_title": "Financial Analysts",
                            "confidence": 0.96,
                            "row_count": 45,
                            "is_confirmed": True,
                        },
                    ],
                },
            ],
        }

        response = client.get("/discovery/sessions/test-session/role-mappings/grouped")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "groups" in data
        assert data["summary"]["total_roles"] == 75

    def test_grouped_mappings_filters_by_confidence(self, client, mock_role_service):
        """Test filtering by confidence threshold."""
        mock_role_service.get_grouped_mappings.return_value = {
            "summary": {"total_roles": 10},
            "groups": [],
        }

        response = client.get(
            "/discovery/sessions/test-session/role-mappings/grouped",
            params={"min_confidence": 0.85, "show_only": "needs_review"},
        )

        assert response.status_code == 200
        mock_role_service.get_grouped_mappings.assert_called_once()


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_role_service():
    with patch("app.routers.role_mappings.get_role_mapping_service") as mock:
        service = AsyncMock()
        mock.return_value.__aenter__.return_value = service
        yield service
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/routers/test_role_mappings_grouped.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/schemas/role_mapping.py`:

```python
# Add new schemas
class GroupedMappingSummary(BaseModel):
    """Summary statistics for grouped mappings."""
    total_roles: int
    total_employees: int
    confirmed_count: int
    needs_review_count: int


class RoleMappingCompact(BaseModel):
    """Compact role mapping for list views."""
    id: str
    source_role: str
    lob_value: str | None
    onet_code: str | None
    onet_title: str | None
    confidence: float
    industry_match: float | None
    row_count: int
    is_confirmed: bool


class LobGroup(BaseModel):
    """Group of role mappings by LOB."""
    lob: str | None
    role_count: int
    employee_count: int
    confirmed_count: int
    mappings: list[RoleMappingCompact]


class GroupedRoleMappingsResponse(BaseModel):
    """Response with role mappings grouped by LOB."""
    summary: GroupedMappingSummary
    groups: list[LobGroup]
```

Update `app/routers/role_mappings.py`:

```python
@router.get(
    "/sessions/{session_id}/role-mappings/grouped",
    response_model=GroupedRoleMappingsResponse,
)
async def get_grouped_role_mappings(
    session_id: UUID,
    min_confidence: float | None = Query(None, ge=0, le=1),
    show_only: str | None = Query(None, regex="^(all|needs_review|confirmed)$"),
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> GroupedRoleMappingsResponse:
    """Get role mappings grouped by LOB with summary statistics."""
    result = await service.get_grouped_mappings(
        session_id=session_id,
        min_confidence=min_confidence,
        show_only=show_only,
    )
    return GroupedRoleMappingsResponse(**result)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/routers/test_role_mappings_grouped.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routers/role_mappings.py app/schemas/role_mapping.py tests/unit/routers/test_role_mappings_grouped.py
git commit -m "feat(api): add grouped role mappings endpoint"
```

---

### Task 19: Add Bulk Confirm Role Mappings Endpoint

**Files:**
- Modify: `app/routers/role_mappings.py`
- Modify: `app/schemas/role_mapping.py`
- Test: `tests/unit/routers/test_role_mappings_bulk_confirm.py`

**Step 1: Write the failing test**

```python
# tests/unit/routers/test_role_mappings_bulk_confirm.py
"""Test bulk confirm role mappings endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


class TestBulkConfirmRoleMappings:
    """Test bulk confirm endpoint."""

    def test_bulk_confirm_by_ids(self, client, mock_role_service):
        """Test confirming multiple mappings by ID."""
        mock_role_service.bulk_confirm.return_value = {
            "confirmed_count": 5,
            "mapping_ids": ["id1", "id2", "id3", "id4", "id5"],
        }

        response = client.post(
            "/discovery/sessions/test-session/role-mappings/bulk-confirm",
            json={"mapping_ids": ["id1", "id2", "id3", "id4", "id5"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confirmed_count"] == 5

    def test_bulk_confirm_by_confidence_threshold(self, client, mock_role_service):
        """Test confirming all mappings above confidence threshold."""
        mock_role_service.bulk_confirm.return_value = {
            "confirmed_count": 50,
            "mapping_ids": [],
        }

        response = client.post(
            "/discovery/sessions/test-session/role-mappings/bulk-confirm",
            json={"min_confidence": 0.85},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confirmed_count"] == 50

    def test_bulk_confirm_by_lob(self, client, mock_role_service):
        """Test confirming all mappings for a specific LOB."""
        mock_role_service.bulk_confirm.return_value = {
            "confirmed_count": 28,
            "mapping_ids": [],
        }

        response = client.post(
            "/discovery/sessions/test-session/role-mappings/bulk-confirm",
            json={"lob": "Retail Banking", "min_confidence": 0.8},
        )

        assert response.status_code == 200


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_role_service():
    with patch("app.routers.role_mappings.get_role_mapping_service") as mock:
        service = AsyncMock()
        mock.return_value.__aenter__.return_value = service
        yield service
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/routers/test_role_mappings_bulk_confirm.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/schemas/role_mapping.py`:

```python
class BulkConfirmRequest(BaseModel):
    """Request to bulk confirm role mappings."""
    mapping_ids: list[str] | None = None
    min_confidence: float | None = Field(None, ge=0, le=1)
    lob: str | None = None


class BulkConfirmResponse(BaseModel):
    """Response from bulk confirm operation."""
    confirmed_count: int
    mapping_ids: list[str]
```

Update `app/routers/role_mappings.py`:

```python
@router.post(
    "/sessions/{session_id}/role-mappings/bulk-confirm",
    response_model=BulkConfirmResponse,
)
async def bulk_confirm_mappings(
    session_id: UUID,
    request: BulkConfirmRequest,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> BulkConfirmResponse:
    """Confirm multiple role mappings at once."""
    result = await service.bulk_confirm(
        session_id=session_id,
        mapping_ids=request.mapping_ids,
        min_confidence=request.min_confidence,
        lob=request.lob,
    )
    return BulkConfirmResponse(**result)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/routers/test_role_mappings_bulk_confirm.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routers/role_mappings.py app/schemas/role_mapping.py tests/unit/routers/test_role_mappings_bulk_confirm.py
git commit -m "feat(api): add bulk confirm role mappings endpoint"
```

---

### Task 20-22: Additional API Endpoints

Tasks 20-22 follow the same TDD pattern for:
- **Task 20**: Grouped Activities endpoint (`GET /sessions/{id}/activities/grouped`)
- **Task 21**: Bulk Select Activities endpoint (`POST /sessions/{id}/activities/bulk-select`)
- **Task 22**: LOB mapping lookup endpoint (`GET /lob-mappings/{pattern}`)

Each task follows the same structure: test → implement → verify → commit.

---

## Phase 4: Frontend Components (Tasks 23-40)

### Task 23: Create ColumnMappingCard Component

**Files:**
- Create: `frontend/src/components/features/discovery/upload/ColumnMappingCard.tsx`
- Test: `frontend/tests/unit/discovery/upload/ColumnMappingCard.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/tests/unit/discovery/upload/ColumnMappingCard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ColumnMappingCard } from '../../../../src/components/features/discovery/upload/ColumnMappingCard'

describe('ColumnMappingCard', () => {
  const defaultProps = {
    field: 'role',
    label: 'Job Title/Role',
    description: 'The column containing job titles',
    required: true,
    detectedColumn: 'Job Title',
    confidence: 0.95,
    alternatives: ['Position', 'Title'],
    columns: ['Employee ID', 'Job Title', 'Department', 'LOB'],
    selectedColumn: 'Job Title',
    onColumnSelect: vi.fn(),
  }

  it('renders field label', () => {
    render(<ColumnMappingCard {...defaultProps} />)
    expect(screen.getByText('Job Title/Role')).toBeInTheDocument()
  })

  it('shows required badge for required fields', () => {
    render(<ColumnMappingCard {...defaultProps} />)
    expect(screen.getByText('Required')).toBeInTheDocument()
  })

  it('shows confidence indicator', () => {
    render(<ColumnMappingCard {...defaultProps} />)
    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  it('calls onColumnSelect when selection changes', () => {
    render(<ColumnMappingCard {...defaultProps} />)
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'Position' } })
    expect(defaultProps.onColumnSelect).toHaveBeenCalledWith('role', 'Position')
  })

  it('shows auto-detected indicator when column was auto-detected', () => {
    render(<ColumnMappingCard {...defaultProps} />)
    expect(screen.getByText(/auto-detected/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- frontend/tests/unit/discovery/upload/ColumnMappingCard.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/components/features/discovery/upload/ColumnMappingCard.tsx
import { IconCheck, IconAlertCircle } from '../../../ui/Icons'

interface ColumnMappingCardProps {
  field: string
  label: string
  description: string
  required: boolean
  detectedColumn: string | null
  confidence: number
  alternatives: string[]
  columns: string[]
  selectedColumn: string | null
  onColumnSelect: (field: string, column: string | null) => void
}

export function ColumnMappingCard({
  field,
  label,
  description,
  required,
  detectedColumn,
  confidence,
  alternatives,
  columns,
  selectedColumn,
  onColumnSelect,
}: ColumnMappingCardProps) {
  const isAutoDetected = detectedColumn && detectedColumn === selectedColumn
  const confidencePercent = Math.round(confidence * 100)
  const confidenceColor = confidence >= 0.85 ? 'text-success' : confidence >= 0.6 ? 'text-warning' : 'text-muted'

  return (
    <div className="surface p-4 rounded-lg">
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-default">{label}</h4>
            {required && (
              <span className="text-xs px-1.5 py-0.5 bg-destructive/10 text-destructive rounded">
                Required
              </span>
            )}
          </div>
          <p className="text-sm text-muted mt-0.5">{description}</p>
        </div>

        {isAutoDetected && confidence > 0 && (
          <div className="flex items-center gap-1">
            <IconCheck size={14} className="text-success" />
            <span className={`text-sm font-medium ${confidenceColor}`}>
              {confidencePercent}%
            </span>
            <span className="text-xs text-muted">auto-detected</span>
          </div>
        )}
      </div>

      <select
        value={selectedColumn || ''}
        onChange={(e) => onColumnSelect(field, e.target.value || null)}
        className="
          w-full px-3 py-2 text-sm
          bg-bg-surface text-default
          border border-border rounded-md
          focus:border-accent focus:ring-1 focus:ring-accent/30
        "
      >
        <option value="">Skip this field</option>
        {columns.map((col) => (
          <option key={col} value={col}>
            {col}
            {col === detectedColumn && confidence > 0 ? ` (suggested)` : ''}
          </option>
        ))}
      </select>

      {required && !selectedColumn && (
        <div className="flex items-center gap-1.5 mt-2 text-warning">
          <IconAlertCircle size={14} />
          <span className="text-xs">This field is required</span>
        </div>
      )}
    </div>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -- frontend/tests/unit/discovery/upload/ColumnMappingCard.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/upload/ColumnMappingCard.tsx frontend/tests/unit/discovery/upload/ColumnMappingCard.test.tsx
git commit -m "feat(ui): add ColumnMappingCard component"
```

---

### Tasks 24-40: Remaining Frontend Components

The remaining frontend tasks follow the same TDD pattern. Each creates one component with its test:

| Task | Component | Purpose |
|------|-----------|---------|
| 24 | ColumnMappingPanel | Container for all column mapping cards |
| 25 | DataPreviewTable | Preview uploaded data with column highlights |
| 26 | MappingSummaryBar | Global stats + bulk action buttons |
| 27 | MappingGroupCard | Collapsible LOB group container |
| 28 | MappingRowCompact | Single role mapping row |
| 29 | MappingRowExpanded | Expanded role with O*NET search |
| 30 | ConfidenceBadge | HIGH/MEDIUM/LOW confidence indicator |
| 31 | IndustryBoostBadge | Industry match percentage badge |
| 32 | ActivitySummaryBar | Activity selection stats |
| 33 | LobActivityGroup | LOB container for activities |
| 34 | RoleActivityCard | Role container with GWA accordions |
| 35 | GwaAccordion | GWA category with DWA checkboxes |
| 36 | DwaCheckboxRow | Individual DWA checkbox |
| 37 | ExposureBadge | AI exposure percentage |
| 38 | CollapsibleSection | Reusable expand/collapse |
| 39 | BulkActionBar | Floating toolbar for bulk actions |
| 40 | SelectAllCheckbox | Tri-state checkbox component |

Each task uses the same structure as Task 23.

---

## Phase 5: Frontend Hooks & Integration (Tasks 41-45)

### Task 41: Create useColumnDetection Hook

**Files:**
- Create: `frontend/src/hooks/useColumnDetection.ts`
- Test: `frontend/tests/unit/hooks/useColumnDetection.test.tsx`

### Task 42: Create useGroupedRoleMappings Hook

**Files:**
- Create: `frontend/src/hooks/useGroupedRoleMappings.ts`
- Test: `frontend/tests/unit/hooks/useGroupedRoleMappings.test.tsx`

### Task 43: Create useGroupedActivities Hook

**Files:**
- Create: `frontend/src/hooks/useGroupedActivities.ts`
- Test: `frontend/tests/unit/hooks/useGroupedActivities.test.tsx`

### Task 44: Update UploadStep Page

**Files:**
- Modify: `frontend/src/pages/discovery/UploadStep.tsx`
- Test: `frontend/tests/unit/discovery/UploadStep.test.tsx`

### Task 45: Update MapRolesStep Page

**Files:**
- Modify: `frontend/src/pages/discovery/MapRolesStep.tsx`
- Test: `frontend/tests/unit/discovery/MapRolesStep.test.tsx`

---

## Phase 6: Integration Testing (Tasks 46-48)

### Task 46: E2E Test - Upload with Column Detection

**Files:**
- Create: `frontend/tests/e2e/discovery/upload-column-detection.spec.ts`

### Task 47: E2E Test - Grouped Role Mapping Flow

**Files:**
- Create: `frontend/tests/e2e/discovery/grouped-role-mapping.spec.ts`

### Task 48: E2E Test - Bulk Activity Selection

**Files:**
- Create: `frontend/tests/e2e/discovery/bulk-activity-selection.spec.ts`

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-8 | Database migrations and models |
| 2 | 9-16 | Backend services |
| 3 | 17-22 | API endpoints |
| 4 | 23-40 | Frontend components |
| 5 | 41-45 | Frontend hooks and page integration |
| 6 | 46-48 | End-to-end testing |

**Total: 48 tasks**

Each task follows strict TDD:
1. Write failing test
2. Run test to confirm failure
3. Write minimal implementation
4. Run test to confirm success
5. Commit with descriptive message

---

*Document created: 2026-02-03*
*Design reference: 2026-02-03-smart-upload-lob-aware-matching-design.md*
