# Discovery Module - Backend Workflow Overview

> **Reference Document**: This document describes the complete backend workflow for the Discovery module's 5-step wizard.

**Last Updated:** 2026-02-01

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           DISCOVERY ORCHESTRATOR                              │
│  • Manages single conversation thread                                         │
│  • Routes to appropriate subagent based on current_step                      │
│  • Maintains session state and context                                        │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐     ┌───────────────┐         ┌───────────────┐
│ Upload Agent  │     │ Mapping Agent │   ...   │ Roadmap Agent │
│ (Step 1)      │     │ (Step 2)      │         │ (Step 5)      │
└───────┬───────┘     └───────┬───────┘         └───────┬───────┘
        │                     │                         │
        ▼                     ▼                         ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                      │
│  PostgreSQL (Sessions, Mappings, Scores) + S3 (Files) + Redis (Cache)        │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Upload - Backend Flow

```
User Request: POST /api/v1/discovery/sessions/{id}/upload
              multipart/form-data: file

┌─────────────────────────────────────────────────────────────────┐
│ 1. FILE VALIDATION                                              │
│    • Check file type (.xlsx, .csv)                             │
│    • Check file size (< 10MB)                                  │
│    • Virus scan (if enabled)                                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FILE STORAGE                                                 │
│    • Upload to S3: s3://discovery-uploads/{session_id}/{file}  │
│    • Store metadata in discovery_uploads table                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SCHEMA DETECTION (Upload Agent)                              │
│    • Parse file with pandas/openpyxl                           │
│    • Detect column types (string, number, date)                │
│    • Identify potential role/department columns                │
│    • Store detected_schema in JSONB                            │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CLARIFICATION (Chat)                                         │
│    • Agent asks: "Which column contains job titles?"           │
│    • Present options as quick action chips                     │
│    • User confirms column_mappings                             │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CHECKPOINT COMPLETE                                          │
│    • Store: column_mappings: {role: "Col B", dept: "Col C"}    │
│    • Transition to Step 2                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```sql
INSERT INTO discovery_uploads (id, session_id, file_name, file_url,
    row_count, column_mappings, detected_schema, created_at)
VALUES (uuid, session_id, 'workforce.xlsx', 's3://...',
    1500, '{"role": "Column B", "department": "Column C"}',
    '{"columns": [...]}', now());

UPDATE discovery_sessions SET current_step = 2 WHERE id = session_id;
```

---

## Step 2: Map Roles - Backend Flow

```
Trigger: Step 1 complete OR User navigates to step 2

┌─────────────────────────────────────────────────────────────────┐
│ 1. EXTRACT UNIQUE ROLES                                         │
│    • Parse uploaded file using column_mappings                 │
│    • Get distinct values from role column                      │
│    • Count occurrences (row_count per role)                    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. O*NET MATCHING (Mapping Agent)                               │
│    For each unique role:                                        │
│    • Call O*NET API: /mnm/search?keyword={role_title}          │
│    • Get top 3-5 occupation matches                            │
│    • Calculate confidence_score based on match quality         │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CONFIDENCE SCORING                                           │
│    • Exact match: 0.95                                         │
│    • Fuzzy match (>80% similarity): 0.80                       │
│    • Partial match: 0.60-0.79                                  │
│    • Weak match: <0.60                                         │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. USER REVIEW (Chat + UI)                                      │
│    • Display two-column view: Your Roles → O*NET Matches       │
│    • User can: Confirm, Search manually, Skip                  │
│    • Bulk action: "Accept all >85% confidence"                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. LEARN FROM CORRECTIONS (Agent Memory)                        │
│    If user corrects a mapping:                                  │
│    • Store in episodic memory: {original: X, corrected: Y}     │
│    • Update semantic memory patterns                           │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CHECKPOINT COMPLETE                                          │
│    • All roles mapped (or explicitly skipped)                  │
│    • Transition to Step 3                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```sql
INSERT INTO discovery_role_mappings
    (id, session_id, source_role, onet_code, confidence_score, user_confirmed, row_count)
VALUES
    (uuid, session_id, 'Software Engineer', '15-1252.00', 0.92, true, 45),
    (uuid, session_id, 'Accountant', '13-2011.00', 0.95, true, 12),
    (uuid, session_id, 'Data Analyst', '15-2051.00', 0.88, true, 23);
```

---

## Step 3: Activities - Backend Flow

```
Trigger: Step 2 complete OR User navigates to step 3

┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD DWAs FOR EACH MAPPED OCCUPATION                         │
│    For each role_mapping.onet_code:                            │
│    • Query onet_dwa via onet_task_to_dwa junction              │
│    • Group by IWA parent → GWA grandparent                     │
│    • Include inherited ai_exposure_score from GWA              │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. APPLY DEFAULT SELECTIONS (Activity Agent)                    │
│    • Pre-select DWAs with ai_exposure > 0.6                    │
│    • Use organization's past selections if available           │
│    • Mark as user_modified = false (default)                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. USER REVIEW (Chat + UI)                                      │
│    • Expandable accordion by role                              │
│    • DWA checklist grouped by IWA category                     │
│    • Quick actions: "Select high exposure", "Clear all"        │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. TRACK USER MODIFICATIONS                                     │
│    • If user toggles selection: user_modified = true           │
│    • Store in agent memory for future defaults                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CHECKPOINT COMPLETE                                          │
│    • Selections confirmed                                       │
│    • Transition to Step 4                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```sql
INSERT INTO discovery_activity_selections
    (id, session_id, role_mapping_id, dwa_id, selected, user_modified)
VALUES
    (uuid, session_id, role_map_id, '4.A.1.a.1', true, false),
    (uuid, session_id, role_map_id, '4.A.2.a.1', true, true),  -- User changed
    (uuid, session_id, role_map_id, '4.A.3.a.1', false, false);
```

---

## Step 4: Analysis - Backend Flow

```
Trigger: Step 3 complete OR User navigates to step 4

┌─────────────────────────────────────────────────────────────────┐
│ 1. CALCULATE SCORES (Analysis Agent)                            │
│    For each role_mapping:                                       │
│    • ai_exposure = avg(selected_dwa.ai_exposure_score)         │
│    • impact = exposure × row_count × salary_factor             │
│    • complexity = 1 - exposure (harder to automate)            │
│    • priority = (exposure×0.4) + (impact×0.4) + ((1-complexity)×0.2) │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. AGGREGATE BY DIMENSION                                       │
│    Calculate scores for each view:                              │
│    • By Role: Individual role scores                           │
│    • By Task: DWA-level analysis                               │
│    • By LoB: Group by line_of_business from upload             │
│    • By Geography: Group by location column                    │
│    • By Department: Group by department column                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. GENERATE INSIGHTS (LLM-Powered)                              │
│    • Identify top opportunities                                 │
│    • Flag anomalies (high exposure + low complexity)           │
│    • Prepare chart data (sparklines, breakdowns)               │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. USER EXPLORATION (Chat + UI)                                 │
│    • Tab bar: By Role | By Task | By LoB | By Geo | By Dept   │
│    • Sortable data tables with scores                         │
│    • Click-to-expand detail panels                            │
│    • Agent answers questions about the data                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CHECKPOINT COMPLETE                                          │
│    • User acknowledges analysis                                 │
│    • Transition to Step 5                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```sql
INSERT INTO discovery_analysis_results
    (id, session_id, role_mapping_id, dimension, dimension_value,
     ai_exposure_score, impact_score, complexity_score, priority_score, breakdown)
VALUES
    (uuid, session_id, role_id, 'role', 'Software Engineer',
     0.78, 0.85, 0.22, 0.82, '{"dwas": [...], "tasks": [...]}'),
    (uuid, session_id, NULL, 'department', 'Engineering',
     0.75, 0.90, 0.25, 0.80, '{"roles": [...], "count": 68}');
```

---

## Step 5: Roadmap - Backend Flow

```
Trigger: Step 4 complete OR User navigates to step 5

┌─────────────────────────────────────────────────────────────────┐
│ 1. GENERATE PRIORITIZATION (Roadmap Agent)                      │
│    For each role with priority_score > threshold:              │
│    • NOW: priority > 0.75 AND complexity < 0.3                 │
│    • NEXT_QUARTER: priority > 0.60                             │
│    • FUTURE: everything else                                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CREATE CANDIDATES                                            │
│    For each prioritized role:                                   │
│    • Generate agent name suggestion                            │
│    • Generate description based on DWAs                        │
│    • Calculate estimated_impact                                │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. USER REVIEW (Kanban UI)                                      │
│    • Three columns: NOW | NEXT QUARTER | FUTURE                │
│    • Drag-and-drop to reprioritize                            │
│    • Select candidates to send to Build                       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. HANDOFF TO BUILD (selected_for_build = true)                 │
│    Create intake request bundle:                               │
│    • Candidate details                                         │
│    • Supporting analysis data                                  │
│    • Source role mappings                                      │
│    • Selected DWAs with scores                                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SESSION COMPLETE                                             │
│    • Mark session status = completed                           │
│    • Link to intake_request_id                                 │
│    • Available for export (PDF, Excel, JSON)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Database Changes:**
```sql
INSERT INTO agentification_candidates
    (id, session_id, role_mapping_id, name, description,
     priority_tier, estimated_impact, selected_for_build, intake_request_id)
VALUES
    (uuid, session_id, role_id, 'Invoice Processing Agent',
     'Automates invoice data extraction and validation...',
     'now', 0.85, true, NULL),
    (uuid, session_id, role_id, 'Report Generation Agent',
     'Generates weekly status reports...',
     'next_quarter', 0.72, false, NULL);

-- After handoff
UPDATE agentification_candidates
SET intake_request_id = intake_uuid
WHERE id = candidate_id AND selected_for_build = true;

UPDATE discovery_sessions
SET status = 'completed'
WHERE id = session_id;
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sessions` | POST | Create new discovery session |
| `/sessions/{id}` | GET | Get session with current state |
| `/sessions/{id}/upload` | POST | Upload workforce file |
| `/sessions/{id}/mappings` | GET/PATCH | Get/update role mappings |
| `/sessions/{id}/mappings/bulk-confirm` | POST | Bulk confirm mappings |
| `/sessions/{id}/activities` | GET/PATCH | Get/update activity selections |
| `/sessions/{id}/analysis` | GET | Get analysis results |
| `/sessions/{id}/analysis/{dimension}` | GET | Get dimension-specific analysis |
| `/sessions/{id}/candidates` | GET/PATCH | Get/update roadmap candidates |
| `/sessions/{id}/handoff` | POST | Send to Build intake |
| `/sessions/{id}/export` | GET | Export (PDF/Excel/JSON) |
| `/chat/message` | POST | Send chat message |
| `/onet/search` | GET | Search O*NET occupations |
| `/onet/occupations/{code}` | GET | Get occupation details |

---

## Key Services

| Service | Purpose |
|---------|---------|
| `OnetApiClient` | Fetches occupation data from O*NET v2 API |
| `LLMService` | Anthropic Claude for AI-powered chat |
| `ChatService` | Manages conversation context per step |
| `SessionService` | CRUD for discovery sessions |
| `UploadService` | File parsing and S3 storage |
| `RoleMappingService` | Role-to-O*NET mapping operations |
| `ActivityService` | DWA selection management |
| `AnalysisService` | Score calculations and aggregations |
| `RoadmapService` | Prioritization and candidate generation |
| `HandoffService` | Build intake bundle creation |

---

## Data Model Reference

See: `docs/plans/2026-01-31-opportunity-discovery-design.md` for complete schema definitions.

### Core Tables

- `discovery_sessions` - Session state and progress
- `discovery_uploads` - Uploaded files and schema
- `discovery_role_mappings` - Role to O*NET links
- `discovery_activity_selections` - DWA selections per role
- `discovery_analysis_results` - Calculated scores
- `agentification_candidates` - Roadmap items

### O*NET Reference Tables

- `onet_occupations` - 923 occupation codes
- `onet_gwa` - 41 Generalized Work Activities
- `onet_iwa` - ~300 Intermediate Work Activities
- `onet_dwa` - 2000+ Detailed Work Activities
- `onet_tasks` - ~19,000 occupation tasks

---

*Document created: 2026-02-01*
