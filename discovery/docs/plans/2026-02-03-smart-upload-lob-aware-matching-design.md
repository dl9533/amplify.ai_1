# Smart Upload with LOB-Aware Role Matching

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve role-to-O*NET matching accuracy by auto-detecting column mappings during upload and using Line of Business context to boost industry-relevant occupation matches.

**Architecture:** Combined upload step with intelligent column detection (keyword matching + LLM fallback), LOB-to-NAICS mapping via curated lookup table with LLM fallback, and industry-aware occupation scoring that boosts matches common in the user's business sector.

**Tech Stack:** FastAPI, PostgreSQL (with ARRAY types), Claude API for fallback detection, React/TypeScript frontend

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER UPLOADS HR FILE                               │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Upload & Configure (Combined)                                       │
│                                                                              │
│  1. Parse file, extract columns + sample rows                                │
│  2. Auto-detect column mappings (ColumnDetectionService)                     │
│  3. Return detected mappings + preview to frontend                           │
│  4. User confirms/adjusts mappings in single UI                              │
│  5. Extract unique (Role, LOB) pairs for matching                            │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOB → NAICS MAPPING (Background)                                            │
│                                                                              │
│  1. Look up each unique LOB in curated mapping table                         │
│  2. For unmatched LOBs, call LLM to determine NAICS codes                    │
│  3. Cache LLM results for future use                                         │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Role Mapping (Industry-Aware)                                       │
│                                                                              │
│  For each unique (Role, LOB) pair:                                           │
│  1. Search O*NET occupations by role title                                   │
│  2. Get NAICS codes for the LOB                                              │
│  3. Cross-reference with onet_occupation_industries table                    │
│  4. Boost occupations common in user's industry                              │
│  5. Present ranked matches to user for confirmation                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key changes from current system:**
- Upload + Column Mapping merged into single step
- LOB is now a first-class field (not optional)
- Role matching considers industry context, not just title similarity

---

## 2. Data Models

### 2.1 New Tables

```sql
-- Maps occupations to the industries where they're employed
CREATE TABLE onet_occupation_industries (
    id SERIAL PRIMARY KEY,
    occupation_code VARCHAR(10) NOT NULL REFERENCES onet_occupations(code) ON DELETE CASCADE,
    naics_code VARCHAR(6) NOT NULL,
    naics_title VARCHAR(255) NOT NULL,
    employment_percent FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(occupation_code, naics_code)
);

CREATE INDEX idx_onet_occ_ind_occupation ON onet_occupation_industries(occupation_code);
CREATE INDEX idx_onet_occ_ind_naics ON onet_occupation_industries(naics_code);

-- Curated lookup table for common LOB values
CREATE TABLE lob_naics_mappings (
    id SERIAL PRIMARY KEY,
    lob_pattern VARCHAR(255) NOT NULL UNIQUE,
    naics_codes VARCHAR(6)[] NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(50) DEFAULT 'curated',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lob_pattern ON lob_naics_mappings(lob_pattern);

-- NAICS reference for display names and hierarchy
CREATE TABLE naics_codes (
    code VARCHAR(6) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    level INT NOT NULL,
    parent_code VARCHAR(6) REFERENCES naics_codes(code),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 Updates to Existing Tables

```sql
ALTER TABLE discovery_uploads
ADD COLUMN IF NOT EXISTS lob_column VARCHAR(255);

ALTER TABLE discovery_role_mappings
ADD COLUMN IF NOT EXISTS lob_value VARCHAR(255),
ADD COLUMN IF NOT EXISTS naics_codes VARCHAR(6)[];
```

### 2.3 Record Estimates

| Table | Records | Source |
|-------|---------|--------|
| `onet_occupation_industries` | ~15,000 | O*NET Industry.txt |
| `naics_codes` | ~1,000 | Census Bureau NAICS |
| `lob_naics_mappings` | ~100 initial | Curated + LLM additions |

---

## 3. Backend Services

### 3.1 Column Detection Service

**File:** `app/services/column_detection_service.py`

```python
class ColumnDetectionService:
    """Auto-detect column mappings using heuristics + LLM fallback."""

    FIELD_DEFINITIONS = {
        "role": {
            "description": "Job title, position, or role name",
            "keywords": ["title", "position", "role", "job", "occupation", "designation"],
            "sample_patterns": ["Software Engineer", "Analyst", "Manager"],
            "required": True,
        },
        "lob": {
            "description": "Line of business, business unit, segment, or division",
            "keywords": ["lob", "line of business", "business unit", "segment", "division"],
            "sample_patterns": ["Retail Banking", "Wealth Management", "Commercial"],
            "required": False,
        },
        "department": {
            "description": "Department, cost center, or team",
            "keywords": ["department", "dept", "cost center", "team", "group", "function"],
            "sample_patterns": ["Finance", "Engineering", "HR", "Operations"],
            "required": False,
        },
        "geography": {
            "description": "Office location, city, region, or site",
            "keywords": ["location", "office", "site", "region", "city", "geo", "country"],
            "sample_patterns": ["New York", "London", "APAC", "US-East"],
            "required": False,
        },
    }

    async def detect_mappings(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Detect likely column mappings with confidence scores."""

        mappings = []
        used_columns = set()

        for field, definition in self.FIELD_DEFINITIONS.items():
            # Step 1: Keyword matching on column names
            match = self._keyword_match(columns, definition["keywords"], used_columns)

            if match and match.confidence >= 0.8:
                mappings.append(match)
                used_columns.add(match.column)
            else:
                # Step 2: Analyze sample data patterns
                match = self._pattern_match(columns, sample_rows, definition, used_columns)

                if match and match.confidence >= 0.6:
                    mappings.append(match)
                    used_columns.add(match.column)
                else:
                    # Step 3: LLM fallback for ambiguous cases
                    match = await self._llm_detect(field, definition, columns, sample_rows, used_columns)
                    mappings.append(match)
                    if match.column:
                        used_columns.add(match.column)

        return mappings
```

### 3.2 LOB Mapping Service

**File:** `app/services/lob_mapping_service.py`

```python
class LobMappingService:
    """Map Line of Business values to NAICS industry codes."""

    def __init__(self, repository: LobMappingRepository, llm_service: LLMService):
        self.repository = repository
        self.llm = llm_service

    async def map_lob_to_naics(self, lob: str) -> LobNaicsResult:
        """
        Map LOB string to NAICS codes.

        1. Normalize input (lowercase, trim)
        2. Check curated lookup table (exact + fuzzy match)
        3. Fall back to LLM if no match
        4. Cache LLM results for future use
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

        # Try fuzzy match (similarity > 0.85)
        mapping = await self.repository.find_fuzzy(normalized, threshold=0.85)
        if mapping:
            return LobNaicsResult(
                lob=lob,
                naics_codes=mapping.naics_codes,
                confidence=mapping.confidence * 0.9,
                source="fuzzy",
            )

        # LLM fallback
        naics_codes = await self._llm_map(lob)

        # Cache the result for future use
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
```

### 3.3 Enhanced Role Mapping Service

**File:** `app/services/role_mapping_service.py` (enhanced)

```python
class RoleMappingService:
    """Industry-aware role to O*NET occupation matching."""

    INDUSTRY_BOOST_FACTOR = 0.25  # Max 25% boost for industry match

    async def match_role(
        self,
        job_title: str,
        lob: str | None = None,
    ) -> list[OccupationMatch]:
        """Match job title to O*NET occupations with industry context."""

        # Step 1: Get candidate occupations from title search
        candidates = await self.onet_repository.search_occupations(job_title)

        if not lob or not candidates:
            return candidates

        # Step 2: Get NAICS codes for the LOB
        lob_result = await self.lob_service.map_lob_to_naics(lob)
        naics_codes = lob_result.naics_codes

        if not naics_codes:
            return candidates

        # Step 3: Score candidates with industry boost
        for candidate in candidates:
            industry_score = await self._calculate_industry_score(
                candidate.code, naics_codes
            )
            candidate.score *= (1 + self.INDUSTRY_BOOST_FACTOR * industry_score)
            candidate.industry_match = industry_score

        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def _naics_match_score(self, code1: str, code2: str) -> float:
        """Score NAICS code similarity (0-1)."""
        if code1 == code2:
            return 1.0
        if code1[:4] == code2[:4]:
            return 0.8
        if code1[:3] == code2[:3]:
            return 0.6
        if code1[:2] == code2[:2]:
            return 0.4
        return 0.0
```

---

## 4. API Endpoints & Schemas

### 4.1 Updated Upload Endpoint

```python
@router.post(
    "/sessions/{session_id}/upload",
    response_model=UploadWithDetectionResponse,
)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
) -> UploadWithDetectionResponse:
    """Upload workforce file and auto-detect column mappings."""
    ...


@router.post(
    "/sessions/{session_id}/upload/{upload_id}/confirm",
    response_model=UploadConfirmResponse,
)
async def confirm_mappings(
    session_id: UUID,
    upload_id: UUID,
    request: ConfirmMappingsRequest,
) -> UploadConfirmResponse:
    """Confirm column mappings and extract unique roles with LOB context."""
    ...
```

### 4.2 Schemas

```python
class DetectedMapping(BaseModel):
    field: str
    column: str | None
    confidence: float
    alternatives: list[str]
    required: bool


class UploadWithDetectionResponse(BaseModel):
    upload_id: UUID
    file_name: str
    row_count: int
    columns: list[str]
    detected_mappings: list[DetectedMapping]
    preview_rows: list[dict]


class ConfirmMappingsRequest(BaseModel):
    mappings: dict[str, str | None]


class RoleMappingResponse(BaseModel):
    id: UUID
    source_role: str
    lob_value: str | None
    onet_code: str | None
    onet_title: str | None
    confidence_score: float
    industry_match: float | None
    reasoning: str | None
    is_confirmed: bool
    row_count: int
```

---

## 5. Frontend Changes

### 5.1 Combined Upload Step

The upload step now shows:
1. File drop zone
2. File summary after upload
3. Auto-detected column mappings with confidence indicators
4. Data preview table
5. Single "Confirm & Continue" action

### 5.2 Updated Role Mapping Step

Role mapping cards now display:
- Source role name
- LOB context (if available)
- O*NET match with confidence score
- Industry boost indicator (e.g., "+15% industry match")

---

## 6. Data Import

### 6.1 O*NET Industry Data

Extend `OnetFileSyncService` to parse `Industry.txt` from O*NET database.

### 6.2 NAICS Reference Data

Import ~1,000 NAICS codes from Census Bureau data.

### 6.3 Curated LOB Mappings

Seed ~100 common LOB patterns:
- Banking & Financial Services (retail banking, wealth management, etc.)
- Insurance (life, property, health)
- Technology (software, IT services, cloud)
- Healthcare (pharma, medical devices)
- And more...

---

## 7. Error Handling

- Column detection failures return empty match with alternatives
- LOB mapping failures return empty NAICS (role matching proceeds without boost)
- All errors logged for monitoring
- Graceful degradation at each step

---

## 8. Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Column detection, LOB mapping, industry scoring |
| Integration tests | Upload flow, role mapping with industry context |
| E2E tests | Complete wizard flow with column detection |

---

---

## 9. Frontend - Aggregated Role Mapping UX

### 9.1 Scale Problem

With 1,000+ employees uploading, one-by-one role validation doesn't scale:
- 1,000 employees → 75 unique (Role, LOB) combinations
- Need efficient bulk review and confirmation

### 9.2 Grouped Review Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Review Role Mappings                                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Summary: 75 roles • 847 auto-matched (93%) • 12 need review             ││
│  │                                                                          ││
│  │ [✓ Confirm All High Confidence]  [Filter ▼]  [Group by: LOB ▼]         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ▼ Retail Banking (28 roles • 412 employees)                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ ☑ Financial Analyst (45 emp)     → Financial Analysts         ✓ 96%    ││
│  │ ☑ Relationship Manager (38 emp)  → Personal Financial Adv...  ✓ 91%    ││
│  │ ☐ Client Associate (22 emp)      → Brokerage Clerks           ? 67%    ││
│  │   └─ [Review] [Search O*NET]                                            ││
│  │ ☑ Branch Manager (18 emp)        → Financial Managers          ✓ 89%   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ▶ Wealth Management (19 roles • 215 employees)                             │
│  ▶ Technology (15 roles • 198 employees)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Key UX Features

| Feature | Purpose |
|---------|---------|
| **Group by LOB** | Logical organization, review similar roles together |
| **Employee count** | Prioritize high-impact roles |
| **Bulk confirm** | One click to confirm all HIGH confidence matches |
| **Confidence tiers** | ✓ HIGH (>85%), ? MEDIUM (60-85%), ✗ LOW (<60%) |
| **Expand on demand** | Only show details for roles needing attention |
| **Filter by status** | "Show only needs review" to focus on problems |

### 9.4 Bulk Actions API

```python
@router.post("/sessions/{session_id}/role-mappings/bulk-confirm")
async def bulk_confirm_mappings(
    session_id: UUID,
    request: BulkConfirmRequest,
) -> BulkConfirmResponse:
    """Confirm multiple role mappings at once."""

class BulkConfirmRequest(BaseModel):
    mapping_ids: list[UUID] | None = None
    min_confidence: float | None = None
    lob: str | None = None
```

---

## 10. Frontend - Aggregated DWA Selection UX

### 10.1 DWA Selection Model

DWA selections are at the **(Role + LOB)** level:
- Same job title in different LOBs → different O*NET match → different DWAs
- All employees with same (Role, LOB) share the same DWA selections

### 10.2 Three-Level Hierarchy

```
LOB Group (collapsible)
  └── Role + LOB (collapsible)
        └── GWA Category (collapsible)
              └── DWA Checkboxes (selectable)
```

### 10.3 Activities Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: Select Work Activities                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Summary: 75 roles • 2,340 activities • 1,847 selected (79%)             ││
│  │                                                                          ││
│  │ [Auto-select High Exposure]  [Filter ▼]  [Group by: LOB ▼]              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ▼ Retail Banking (28 roles • 412 employees)                    78% selected│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ▼ Financial Analyst (45 emp)                               82% selected││
│  │    ┌─────────────────────────────────────────────────────────────────┐  ││
│  │    │ ▶ Analyzing Data or Information (AI: 85%)           4/5 selected│  ││
│  │    │ ▶ Processing Information (AI: 82%)                  3/4 selected│  ││
│  │    │ ▼ Getting Information (AI: 75%)                     2/3 selected│  ││
│  │    │   ☑ Gather financial data for analysis                    88%   │  ││
│  │    │   ☑ Research market conditions                            82%   │  ││
│  │    │   ☐ Interview clients about financial needs               45%   │  ││
│  │    └─────────────────────────────────────────────────────────────────┘  ││
│  │  ▶ Relationship Manager (38 emp)                            71% selected││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ▶ Wealth Management (19 roles • 215 employees)                 81% selected│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.4 Bulk Activity Actions

```python
@router.post("/sessions/{session_id}/activities/bulk-select")
async def bulk_select_activities(
    session_id: UUID,
    request: BulkActivitySelectRequest,
) -> BulkSelectionResponse:
    """Bulk select/deselect activities with flexible targeting."""

class BulkActivitySelectRequest(BaseModel):
    selected: bool
    activity_ids: list[UUID] | None = None
    role_mapping_id: UUID | None = None
    gwa_code: str | None = None
    lob: str | None = None
    min_exposure: float | None = None
```

---

## 11. Frontend Component Inventory

### 11.1 New Components

```
frontend/src/components/features/discovery/
├── upload/
│   ├── ColumnMappingCard.tsx         # Single field mapping row
│   ├── ColumnMappingPanel.tsx        # All mappings + confidence
│   └── DataPreviewTable.tsx          # Preview with highlights
│
├── role-mapping/
│   ├── MappingSummaryBar.tsx         # Global stats + bulk actions
│   ├── MappingControls.tsx           # Filters, search, sort
│   ├── MappingGroupCard.tsx          # Collapsible LOB group
│   ├── MappingRowCompact.tsx         # Single role row
│   ├── MappingRowExpanded.tsx        # Expanded details
│   ├── ConfidenceBadge.tsx           # HIGH/MEDIUM/LOW indicator
│   └── IndustryBoostBadge.tsx        # Industry match indicator
│
├── activities/
│   ├── ActivitySummaryBar.tsx        # Global stats + auto-select
│   ├── ActivityFilters.tsx           # Search, show/hide unselected
│   ├── LobActivityGroup.tsx          # Collapsible LOB container
│   ├── RoleActivityCard.tsx          # Collapsible role container
│   ├── GwaAccordion.tsx              # GWA category accordion
│   ├── DwaCheckboxRow.tsx            # Individual DWA checkbox
│   └── ExposureBadge.tsx             # AI exposure indicator
│
└── shared/
    ├── CollapsibleSection.tsx        # Reusable expand/collapse
    ├── BulkActionBar.tsx             # Floating bulk toolbar
    └── SelectAllCheckbox.tsx         # Tri-state checkbox
```

### 11.2 Updated Pages

| Page | Change |
|------|--------|
| `UploadStep.tsx` | Major - add column mapping UI |
| `MapRolesStep.tsx` | Rewrite - grouped view with bulk actions |
| `ActivitiesStep.tsx` | Rewrite - hierarchical grouped view |
| `AnalysisStep.tsx` | Minor - no structural changes |
| `RoadmapStep.tsx` | Minor - no structural changes |

### 11.3 New Hooks

```typescript
useColumnDetection(uploadId)      // Column detection results
useGroupedRoleMappings(sessionId) // Grouped mappings with bulk actions
useGroupedActivities(sessionId)   // Grouped activities with bulk actions
```

---

## 12. Implementation Summary

| Component | Files | Scope |
|-----------|-------|-------|
| **Database** | 1 migration | 3 new tables, 3 column additions |
| **Backend Services** | 4 new, 2 modified | Column detection, LOB mapping, role mapping, activity service |
| **API Endpoints** | 4 new, 2 modified | Grouped endpoints, bulk actions |
| **Schemas** | 4 new, 2 modified | Grouped responses, bulk requests |
| **Frontend Components** | 18 new, 5 modified | Full component inventory above |
| **Frontend Hooks** | 3 new, 2 modified | Grouped data hooks |
| **Data Import** | 3 scripts | NAICS, LOB seed, O*NET industry |
| **Tests** | ~25 new tests | Unit + integration + E2E |

---

*Document created: 2026-02-03*
*Updated: 2026-02-03 - Added aggregated UX for role mapping and activities*
