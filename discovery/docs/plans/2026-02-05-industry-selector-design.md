# Industry Selector Feature - Implementation Plan

**Date**: 2026-02-05
**Feature**: Two-level Industry Selection (Supersector → NAICS Sector)

## Overview

Allow users to select their company's industry via cascading dropdowns:
1. **Supersector** (11 BLS categories) - narrows choices
2. **NAICS Sector** (2-digit code) - specific industry

This metadata enhances role mapping accuracy by boosting O*NET occupations with higher employment percentages in the selected industry.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  UPLOAD STEP                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Supersector:  [Financial Activities        ▼]                   │    │
│  │  Sector:       [52 - Finance & Insurance    ▼]                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓                                           │
│  Stored on: discovery_sessions.industry_naics_sector = "52"             │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  ROLE MAPPING SERVICE                                                    │
│                                                                          │
│  For each role "Senior Accountant":                                     │
│    1. Get O*NET candidates via LLM agent                                │
│    2. Query onet_occupation_industries WHERE naics_code LIKE '52%'      │
│    3. Calculate industry_score from employment_percent                  │
│    4. Apply boost: final_score = base_score * (1 + 0.25 * industry_score)│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Supersector → NAICS Sector Mapping

| Supersector | NAICS Sectors |
|-------------|---------------|
| Natural Resources & Mining | 11 - Agriculture, Forestry, Fishing, Hunting |
| | 21 - Mining, Quarrying, Oil & Gas |
| Construction | 23 - Construction |
| Manufacturing | 31 - Manufacturing (Food, Beverage, Textile) |
| | 32 - Manufacturing (Wood, Paper, Chemical, Plastics) |
| | 33 - Manufacturing (Metal, Machinery, Electronics) |
| Trade, Transportation & Utilities | 22 - Utilities |
| | 42 - Wholesale Trade |
| | 44 - Retail Trade (Motor Vehicles, Furniture, Electronics) |
| | 45 - Retail Trade (Sporting Goods, General Merchandise) |
| | 48 - Transportation |
| | 49 - Warehousing & Postal |
| Information | 51 - Information |
| Financial Activities | 52 - Finance & Insurance |
| | 53 - Real Estate & Rental |
| Professional & Business Services | 54 - Professional, Scientific & Technical Services |
| | 55 - Management of Companies |
| | 56 - Administrative & Support Services |
| Education & Health Services | 61 - Educational Services |
| | 62 - Health Care & Social Assistance |
| Leisure & Hospitality | 71 - Arts, Entertainment & Recreation |
| | 72 - Accommodation & Food Services |
| Other Services | 81 - Other Services |
| Government | 92 - Public Administration |

---

## Implementation Tasks

### Phase 1: Backend - Data Layer

#### 1.1 Add Constants File
**File**: `app/data/industry_sectors.py`

```python
SUPERSECTORS = [
    {
        "code": "NATURAL_RESOURCES",
        "label": "Natural Resources & Mining",
        "sectors": [
            {"code": "11", "label": "Agriculture, Forestry, Fishing & Hunting"},
            {"code": "21", "label": "Mining, Quarrying & Oil/Gas Extraction"},
        ],
    },
    # ... all 11 supersectors
]
```

#### 1.2 Database Migration
**File**: `migrations/versions/015_session_industry.py`

Add to `discovery_sessions`:
- `industry_naics_sector` (String(2), nullable)

Note: We only need to store the 2-digit NAICS sector. Supersector can be derived client-side.

#### 1.3 Update Session Model
**File**: `app/models/discovery_session.py`

```python
industry_naics_sector: Mapped[str | None] = mapped_column(
    String(2), nullable=True
)
```

#### 1.4 Update Session Schemas
**File**: `app/schemas/session.py`

```python
class SessionUpdate(BaseModel):
    industry_naics_sector: str | None = None

class SessionResponse(BaseModel):
    industry_naics_sector: str | None
```

### Phase 2: Backend - API Layer

#### 2.1 Add Industry Endpoints
**File**: `app/routers/industry.py` (new)

```python
@router.get("/industries")
async def list_industries() -> list[SupersectorResponse]:
    """Return all supersectors with their NAICS sectors."""

@router.patch("/sessions/{session_id}/industry")
async def update_session_industry(
    session_id: UUID,
    update: IndustryUpdate,
) -> SessionResponse:
    """Update session's industry selection."""
```

#### 2.2 Update Role Mapping Service
**File**: `app/services/role_mapping_service.py`

Modify `create_mappings_from_upload()`:
1. Retrieve session's `industry_naics_sector`
2. Pass to `match_role_with_industry()` for boosting
3. Store `industry_match_score` on each mapping

```python
async def create_mappings_from_upload(
    self,
    session_id: UUID,
    upload_id: UUID,
) -> list[RoleMappingResponse]:
    # Get session industry
    session = await session_repo.get(session_id)
    naics_sector = session.industry_naics_sector

    # For each role...
    if naics_sector:
        industry_score = await onet_repo.calculate_industry_score(
            occupation_code=onet_code,
            naics_codes=[naics_sector],  # 2-digit prefix match
        )
        # Apply boost
        boosted_score = base_score * (1 + INDUSTRY_BOOST_FACTOR * industry_score)
```

### Phase 3: Frontend - UI Components

#### 3.1 Industry Selector Component
**File**: `frontend/src/components/features/discovery/IndustrySelector.tsx`

```tsx
interface IndustrySelectorProps {
  value: string | null;
  onChange: (naicsSector: string | null) => void;
}

export function IndustrySelector({ value, onChange }: IndustrySelectorProps) {
  const [supersector, setSupersector] = useState<string | null>(null);

  // Cascading dropdown logic
  return (
    <div className="space-y-4">
      <Select
        label="Industry Category"
        value={supersector}
        onChange={setSupersector}
        options={SUPERSECTORS.map(s => ({ value: s.code, label: s.label }))}
      />

      {supersector && (
        <Select
          label="Specific Industry"
          value={value}
          onChange={onChange}
          options={getSectorsForSupersector(supersector)}
        />
      )}
    </div>
  );
}
```

#### 3.2 Integrate into Upload Step
**File**: `frontend/src/pages/discovery/UploadStep.tsx`

Add IndustrySelector above file upload area:
```tsx
<StepContent title="Upload Employee Data">
  {/* NEW: Industry Selection */}
  <div className="surface p-6 mb-6">
    <h3 className="text-lg font-semibold mb-4">Company Industry</h3>
    <p className="text-sm text-muted mb-4">
      Select your company's primary industry to improve role matching accuracy.
    </p>
    <IndustrySelector
      value={industryNaicsSector}
      onChange={handleIndustryChange}
    />
  </div>

  {/* Existing file upload */}
  <FileDropzone ... />
</StepContent>
```

#### 3.3 Add API Service
**File**: `frontend/src/services/discoveryApi.ts`

```typescript
export const industryApi = {
  list: (): Promise<Supersector[]> =>
    api.get('/discovery/industries'),

  updateSession: (sessionId: string, naicsSector: string): Promise<SessionResponse> =>
    api.patch(`/discovery/sessions/${sessionId}/industry`, {
      industry_naics_sector: naicsSector
    }),
}
```

#### 3.4 Add Hook
**File**: `frontend/src/hooks/useIndustrySelector.ts`

```typescript
export function useIndustrySelector(sessionId: string) {
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const updateIndustry = async (naicsSector: string) => {
    setIsSaving(true);
    await industryApi.updateSession(sessionId, naicsSector);
    setSelectedSector(naicsSector);
    setIsSaving(false);
  };

  return { selectedSector, updateIndustry, isSaving };
}
```

### Phase 4: Agent Enhancement (Optional)

#### 4.1 Update Role Mapping Agent Prompt
**File**: `app/agents/role_mapping_agent.py`

Add industry context to system prompt when available:
```python
if industry_naics_sector:
    industry_context = f"""
    The company operates in NAICS sector {industry_naics_sector} ({sector_name}).
    Prioritize occupations commonly found in this industry when confidence is similar.
    """
```

---

## Existing Infrastructure Leveraged

| Component | Already Exists | Used For |
|-----------|---------------|----------|
| `onet_occupation_industries` | ✅ | Employment % by NAICS for each occupation |
| `naics_codes` | ✅ | NAICS hierarchy reference |
| `calculate_industry_score()` | ✅ | Score calculation with prefix matching |
| `INDUSTRY_BOOST_FACTOR` | ✅ | 0.25 max boost |
| Column mapping UI | ✅ | LOB detection (separate from industry) |

---

## Data Verification Needed

Before implementation, verify:

```sql
-- Check O*NET industries are populated
SELECT COUNT(*) FROM onet_occupation_industries;
-- Expected: 10,000+ rows

-- Check NAICS codes exist
SELECT COUNT(*) FROM naics_codes WHERE level = 2;
-- Expected: 20+ sector-level codes

-- Sample industry distribution for an occupation
SELECT naics_code, naics_title, employment_percent
FROM onet_occupation_industries
WHERE occupation_code = '13-2011.00'  -- Accountants
ORDER BY employment_percent DESC
LIMIT 10;
```

---

## Testing Strategy

1. **Unit Tests**:
   - `test_industry_sectors.py` - Verify supersector→sector mapping
   - `test_session_industry.py` - Session update with industry

2. **Integration Tests**:
   - Role mapping with industry boost vs without
   - Verify boost factor is applied correctly

3. **E2E Tests**:
   - Complete flow: Select industry → Upload → Verify boosted mappings

---

## Files to Create/Modify

| Action | File Path |
|--------|-----------|
| CREATE | `app/data/industry_sectors.py` |
| CREATE | `migrations/versions/015_session_industry.py` |
| CREATE | `app/routers/industry.py` |
| CREATE | `app/schemas/industry.py` |
| CREATE | `frontend/src/components/features/discovery/IndustrySelector.tsx` |
| CREATE | `frontend/src/hooks/useIndustrySelector.ts` |
| MODIFY | `app/models/discovery_session.py` |
| MODIFY | `app/schemas/session.py` |
| MODIFY | `app/services/role_mapping_service.py` |
| MODIFY | `app/routers/__init__.py` (register industry router) |
| MODIFY | `frontend/src/pages/discovery/UploadStep.tsx` |
| MODIFY | `frontend/src/services/discoveryApi.ts` |

---

## Open Questions

1. **Default Industry**: Should there be a default selection or require explicit choice?
2. **Change After Upload**: Allow industry change after file uploaded? (Recommend: Yes, triggers re-scoring)
3. **Multiple Industries**: Support selecting multiple NAICS sectors? (Recommend: No, keep simple v1)

---

## Estimated Scope

- **Backend**: ~4 files, ~200 lines
- **Frontend**: ~3 files, ~150 lines
- **Migration**: 1 file
- **Tests**: ~3 files
