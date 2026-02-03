"""
Standalone Mock API Server for E2E Testing

This server implements the Discovery API endpoints using in-memory mock services.
Run it to enable E2E testing without requiring Docker or a full database setup.

Usage:
    python tests/e2e/mock_api_server.py

The server will start on http://localhost:8001
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional
import csv
import io
from difflib import SequenceMatcher
import uvicorn

app = FastAPI(title="Discovery API (Mock)", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# In-Memory Storage
# =============================================================================

sessions = {}
uploads = {}
role_mappings = {}
activity_selections = {}
analysis_results = {}
candidates = {}

# O*NET occupation database
ONET_OCCUPATIONS = {
    "43-4051.00": "Customer Service Representatives",
    "43-9021.00": "Data Entry Keyers",
    "43-3031.00": "Bookkeeping, Accounting, and Auditing Clerks",
    "13-1071.00": "Human Resources Specialists",
    "15-1232.00": "Computer User Support Specialists",
    "13-1161.00": "Market Research Analysts and Marketing Specialists",
    "11-1021.00": "General and Operations Managers",
    "15-1252.00": "Software Developers",
}

# Sample DWAs
SAMPLE_DWAS = [
    {"id": "dwa-001", "name": "Gathering information from customers", "gwa": "Getting Information", "ai_exposure": 0.75},
    {"id": "dwa-002", "name": "Reading documents and reports", "gwa": "Getting Information", "ai_exposure": 0.82},
    {"id": "dwa-003", "name": "Responding to customer inquiries", "gwa": "Communicating", "ai_exposure": 0.70},
    {"id": "dwa-004", "name": "Writing emails and correspondence", "gwa": "Communicating", "ai_exposure": 0.85},
    {"id": "dwa-005", "name": "Entering data into systems", "gwa": "Processing Information", "ai_exposure": 0.90},
    {"id": "dwa-006", "name": "Verifying accuracy of information", "gwa": "Processing Information", "ai_exposure": 0.65},
]


# =============================================================================
# Pydantic Models
# =============================================================================

class SessionCreate(BaseModel):
    organization_id: str
    user_id: Optional[str] = None


class SessionUpdate(BaseModel):
    current_step: Optional[int] = None
    status: Optional[str] = None


class BulkConfirm(BaseModel):
    min_confidence: float = 0.85


class MappingUpdate(BaseModel):
    onet_code: Optional[str] = None
    user_confirmed: Optional[bool] = None


class AutoSelect(BaseModel):
    min_exposure: float = 0.6


class SelectForBuild(BaseModel):
    candidate_ids: list[str]


class ChatMessage(BaseModel):
    message: str


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_confidence(role: str, onet_title: str) -> float:
    """Calculate similarity score between role and O*NET title."""
    role_lower = role.lower()
    title_lower = onet_title.lower()

    if role_lower == title_lower:
        return 1.0

    ratio = SequenceMatcher(None, role_lower, title_lower).ratio()
    if role_lower in title_lower or title_lower in role_lower:
        ratio = min(1.0, ratio + 0.1)

    return round(ratio, 2)


def find_best_match(role: str) -> tuple[str, str, float]:
    """Find best O*NET match for a role."""
    best_code, best_title, best_score = None, None, 0.0

    for code, title in ONET_OCCUPATIONS.items():
        score = calculate_confidence(role, title)
        if score > best_score:
            best_score = score
            best_code = code
            best_title = title

    return best_code, best_title, best_score


# =============================================================================
# Health Endpoints
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Discovery API (Mock)", "version": "0.1.0"}


# =============================================================================
# Session Endpoints
# =============================================================================

@app.get("/discovery/sessions")
async def list_sessions(page: int = 1, per_page: int = 20):
    """List all sessions (for frontend compatibility)."""
    session_list = list(sessions.values())
    return {
        "items": session_list,
        "total": len(session_list),
        "page": page,
        "per_page": per_page
    }


@app.post("/discovery/sessions", status_code=201)
@app.post("/api/v1/discovery/sessions", status_code=201)
async def create_session(data: SessionCreate):
    session_id = str(uuid4())
    session = {
        "id": session_id,
        "organization_id": data.organization_id,
        "user_id": data.user_id or "default-user",
        "status": "draft",
        "current_step": 1,
        "name": f"Discovery Session {len(sessions) + 1}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    sessions[session_id] = session
    return session


@app.get("/discovery/sessions/{session_id}")
@app.get("/api/v1/discovery/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.patch("/discovery/sessions/{session_id}")
@app.patch("/api/v1/discovery/sessions/{session_id}")
async def update_session(session_id: str, data: SessionUpdate):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Check for unconfirmed mappings when advancing to step 3
    if data.current_step and data.current_step == 3:
        session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]
        unconfirmed = [m for m in session_mappings if not m["user_confirmed"]]
        if unconfirmed:
            raise HTTPException(
                status_code=400,
                detail=f"{len(unconfirmed)} role mappings are unconfirmed. Please review and confirm all mappings before proceeding."
            )

    if data.current_step:
        session["current_step"] = data.current_step
        if data.current_step > 1:
            session["status"] = "in_progress"

    if data.status:
        session["status"] = data.status

    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    return session


@app.delete("/discovery/sessions/{session_id}")
@app.delete("/api/v1/discovery/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


# =============================================================================
# Upload Endpoints
# =============================================================================

@app.post("/discovery/sessions/{session_id}/upload", status_code=201)
@app.post("/api/v1/discovery/sessions/{session_id}/uploads", status_code=201)
async def upload_file(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload CSV or Excel files.")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse CSV
    try:
        decoded = content.decode('utf-8')
        reader = csv.reader(io.StringIO(decoded))
        rows = list(reader)

        if len(rows) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        if len(rows) == 1:
            raise HTTPException(status_code=400, detail="File contains only headers, no data rows")

        headers = rows[0]
        data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]

        if len(data_rows) == 0:
            raise HTTPException(status_code=400, detail="File contains only headers, no data rows")

    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Please ensure it's valid UTF-8.")

    # Auto-detect column mappings
    column_mappings = {}
    for header in headers:
        header_lower = header.lower()
        if any(term in header_lower for term in ["job", "title", "role", "position"]):
            column_mappings["role"] = header
        elif "department" in header_lower or "dept" in header_lower:
            column_mappings["department"] = header
        elif any(term in header_lower for term in ["location", "geography", "geo", "city", "region"]):
            column_mappings["geography"] = header

    upload_id = str(uuid4())
    upload = {
        "id": upload_id,
        "session_id": session_id,
        "file_name": file.filename,
        "file_url": f"s3://test-bucket/{session_id}/{upload_id}/{file.filename}",
        "row_count": len(data_rows),
        "column_mappings": column_mappings,
        "detected_schema": {
            "columns": [{"name": h, "type": "string"} for h in headers]
        },
        "data_rows": data_rows,
        "headers": headers,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Update schema types
    for i, header in enumerate(headers):
        if "headcount" in header.lower() or "count" in header.lower():
            upload["detected_schema"]["columns"][i]["type"] = "integer"

    uploads[upload_id] = upload

    # Return in format expected by frontend
    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "row_count": len(data_rows),
        "detected_schema": headers,
        "column_types": {h: "string" for h in headers},
        # Also include original fields for API compatibility
        "id": upload_id,
        "session_id": session_id,
        "file_name": file.filename,
        "column_mappings": column_mappings,
    }


@app.get("/api/v1/discovery/sessions/{session_id}/uploads/{upload_id}/schema")
async def get_schema(session_id: str, upload_id: str):
    if upload_id not in uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    return uploads[upload_id]["detected_schema"]


# =============================================================================
# Role Mapping Endpoints
# =============================================================================

@app.get("/discovery/sessions/{session_id}/role-mappings")
async def get_role_mappings(session_id: str):
    """Get role mappings for a session (frontend endpoint)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]

    # If no mappings exist, auto-generate them from the upload
    if not session_mappings:
        session_uploads = [u for u in uploads.values() if u["session_id"] == session_id]
        if session_uploads:
            upload = session_uploads[-1]
            # Try to find role column from column_mappings or detect it
            role_column = upload["column_mappings"].get("role")

            if not role_column:
                # Try to detect role column from headers
                for header in upload["headers"]:
                    if any(term in header.lower() for term in ["job", "title", "role", "position"]):
                        role_column = header
                        break

            if role_column:
                role_idx = upload["headers"].index(role_column)
                unique_roles = set()
                for row in upload["data_rows"]:
                    if len(row) > role_idx and row[role_idx].strip():
                        unique_roles.add(row[role_idx].strip())

                for role in unique_roles:
                    code, title, confidence = find_best_match(role)
                    mapping_id = str(uuid4())
                    mapping = {
                        "id": mapping_id,
                        "session_id": session_id,
                        "source_role": role,
                        "onet_code": code,
                        "onet_title": title,
                        "confidence_score": confidence,
                        "is_confirmed": False,
                        "user_confirmed": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    role_mappings[mapping_id] = mapping
                    session_mappings.append(mapping)

    return session_mappings


@app.put("/discovery/role-mappings/{mapping_id}")
async def update_role_mapping(mapping_id: str, data: dict):
    """Update a role mapping (frontend endpoint)."""
    if mapping_id not in role_mappings:
        raise HTTPException(status_code=404, detail="Mapping not found")

    mapping = role_mappings[mapping_id]

    if "onet_code" in data:
        mapping["onet_code"] = data["onet_code"]
        mapping["onet_title"] = data.get("onet_title", ONET_OCCUPATIONS.get(data["onet_code"], "Unknown"))

    if "is_confirmed" in data:
        mapping["is_confirmed"] = data["is_confirmed"]
        mapping["user_confirmed"] = data["is_confirmed"]

    return mapping


@app.post("/discovery/sessions/{session_id}/role-mappings/confirm")
async def bulk_confirm_frontend(session_id: str, data: dict):
    """Bulk confirm role mappings (frontend endpoint)."""
    threshold = data.get("threshold", 0.85)
    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]
    confirmed_count = 0

    for mapping in session_mappings:
        if mapping["confidence_score"] >= threshold:
            mapping["is_confirmed"] = True
            mapping["user_confirmed"] = True
            confirmed_count += 1

    return {"confirmed_count": confirmed_count}


@app.post("/api/v1/discovery/sessions/{session_id}/role-mappings/auto-map")
async def auto_map_roles(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get roles from upload
    session_uploads = [u for u in uploads.values() if u["session_id"] == session_id]
    if not session_uploads:
        raise HTTPException(status_code=400, detail="No upload found for session")

    upload = session_uploads[-1]
    role_column = upload["column_mappings"].get("role")

    if not role_column:
        raise HTTPException(status_code=400, detail="Role column not mapped")

    # Get role column index
    role_idx = upload["headers"].index(role_column)

    # Extract unique roles
    unique_roles = set()
    for row in upload["data_rows"]:
        if len(row) > role_idx and row[role_idx].strip():
            unique_roles.add(row[role_idx].strip())

    mappings = []
    low_confidence_count = 0

    for role in unique_roles:
        code, title, confidence = find_best_match(role)

        mapping_id = str(uuid4())
        mapping = {
            "id": mapping_id,
            "session_id": session_id,
            "source_role": role,
            "onet_code": code,
            "onet_title": title,
            "confidence_score": confidence,
            "user_confirmed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        role_mappings[mapping_id] = mapping
        mappings.append(mapping)

        if confidence < 0.60:
            low_confidence_count += 1

    return {
        "mappings": mappings,
        "low_confidence_count": low_confidence_count,
        "requires_review": low_confidence_count > 0,
        "warnings": [f"{low_confidence_count} roles have low confidence matches and require review"] if low_confidence_count > 0 else []
    }


@app.post("/api/v1/discovery/sessions/{session_id}/role-mappings/bulk-confirm")
async def bulk_confirm(session_id: str, data: BulkConfirm):
    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]
    confirmed_count = 0

    for mapping in session_mappings:
        if mapping["confidence_score"] >= data.min_confidence:
            mapping["user_confirmed"] = True
            confirmed_count += 1

    return {"confirmed_count": confirmed_count}


@app.patch("/api/v1/discovery/sessions/{session_id}/role-mappings/{mapping_id}")
async def update_mapping(session_id: str, mapping_id: str, data: MappingUpdate):
    if mapping_id not in role_mappings:
        raise HTTPException(status_code=404, detail="Mapping not found")

    mapping = role_mappings[mapping_id]

    if data.onet_code:
        mapping["onet_code"] = data.onet_code
        mapping["onet_title"] = ONET_OCCUPATIONS.get(data.onet_code, "Unknown")

    if data.user_confirmed is not None:
        mapping["user_confirmed"] = data.user_confirmed

    return mapping


@app.get("/api/v1/discovery/onet/search")
async def search_onet(query: str = Query(...)):
    query_lower = query.lower()
    results = [
        {"code": code, "title": title}
        for code, title in ONET_OCCUPATIONS.items()
        if query_lower in title.lower()
    ]
    return {"results": results}


# =============================================================================
# Activity Endpoints
# =============================================================================

@app.get("/discovery/sessions/{session_id}/activities")
async def get_activities_frontend(session_id: str, include_unselected: bool = True):
    """Get activities for a session (frontend endpoint)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Group activities by GWA (General Work Activity)
    # Format expected by frontend: array of GWA objects with dwas array
    gwa_data = {
        "getting-info": {
            "gwa_code": "getting-info",
            "gwa_title": "Getting Information",
            "ai_exposure_score": 0.78,
            "dwas": []
        },
        "communicating": {
            "gwa_code": "communicating",
            "gwa_title": "Communicating",
            "ai_exposure_score": 0.75,
            "dwas": []
        },
        "processing-info": {
            "gwa_code": "processing-info",
            "gwa_title": "Processing Information",
            "ai_exposure_score": 0.82,
            "dwas": []
        }
    }

    # Map GWA names to codes
    gwa_map = {
        "Getting Information": "getting-info",
        "Communicating": "communicating",
        "Processing Information": "processing-info"
    }

    # Add DWAs to their GWA groups
    for dwa in SAMPLE_DWAS:
        gwa_code = gwa_map.get(dwa["gwa"])
        if gwa_code and gwa_code in gwa_data:
            dwa_entry = {
                "id": dwa["id"],
                "title": dwa["name"],
                "description": f"Activity related to {dwa['gwa'].lower()}",
                "selected": activity_selections.get(dwa["id"], False),
            }
            gwa_data[gwa_code]["dwas"].append(dwa_entry)

    # Return as array (frontend expects response.map())
    return list(gwa_data.values())


@app.put("/discovery/activities/{activity_id}")
async def update_activity_frontend(activity_id: str, data: dict):
    """Update activity selection (frontend endpoint)."""
    activity_selections[activity_id] = data.get("selected", False)
    return {"id": activity_id, "selected": activity_selections[activity_id]}


@app.post("/discovery/sessions/{session_id}/activities/select")
async def bulk_select_activities_frontend(session_id: str, data: dict):
    """Bulk select activities (frontend endpoint)."""
    activity_ids = data.get("activity_ids", [])
    select = data.get("select", True)

    for aid in activity_ids:
        activity_selections[aid] = select

    return {"selected_count": len(activity_ids)}


@app.get("/discovery/sessions/{session_id}/activities/count")
async def get_activity_count_frontend(session_id: str):
    """Get activity selection count (frontend endpoint)."""
    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]
    total = len(session_mappings) * len(SAMPLE_DWAS)
    selected = sum(1 for k, v in activity_selections.items() if v and any(m["id"] in k for m in session_mappings))
    return {"total": total, "selected": selected}


@app.get("/api/v1/discovery/sessions/{session_id}/activities")
async def get_activities(session_id: str):
    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]

    activities_by_role = {}
    for mapping in session_mappings:
        activities = []
        for dwa in SAMPLE_DWAS:
            activities.append({
                "dwa_id": dwa["id"],
                "dwa_name": dwa["name"],
                "gwa_name": dwa["gwa"],
                "ai_exposure_score": dwa["ai_exposure"],
                "selected": False,
            })
        activities_by_role[mapping["source_role"]] = activities

    return {"activities_by_role": activities_by_role}


@app.post("/api/v1/discovery/sessions/{session_id}/activities/auto-select")
async def auto_select_activities(session_id: str, data: AutoSelect):
    selected_count = sum(1 for dwa in SAMPLE_DWAS if dwa["ai_exposure"] >= data.min_exposure)
    return {"selected_count": selected_count, "total_count": len(SAMPLE_DWAS)}


# =============================================================================
# Analysis Endpoints
# =============================================================================

@app.get("/discovery/sessions/{session_id}/analysis")
async def get_all_analysis_frontend(session_id: str):
    """Get all analysis results (frontend endpoint)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]

    # Generate analysis results for each role
    results = []
    for i, mapping in enumerate(session_mappings):
        results.append({
            "id": f"analysis-{mapping['id']}",
            "dimension": "role",
            "dimension_value": mapping["source_role"],
            "ai_exposure_score": 0.65 + (i * 0.05),
            "impact_score": 0.70 + (i * 0.03),
            "complexity_score": 0.25 + (i * 0.05),
            "priority_score": 0.72 + (i * 0.04),
            "priority_tier": "high" if i < 2 else "medium" if i < 4 else "low",
        })

    return {
        "results": results,
        "summary": {
            "total_items": len(results),
            "high_priority_count": sum(1 for r in results if r["priority_tier"] == "high"),
            "avg_exposure": sum(r["ai_exposure_score"] for r in results) / len(results) if results else 0,
            "avg_priority": sum(r["priority_score"] for r in results) / len(results) if results else 0,
        }
    }


@app.get("/discovery/sessions/{session_id}/analysis/{dimension}")
async def get_dimension_analysis_frontend(session_id: str, dimension: str, tier: str = None):
    """Get analysis by dimension (frontend endpoint)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]

    results = []
    for i, mapping in enumerate(session_mappings):
        priority_tier = "high" if i < 2 else "medium" if i < 4 else "low"
        if tier and tier != priority_tier:
            continue

        results.append({
            "id": f"analysis-{mapping['id']}",
            "dimension": dimension,
            "dimension_value": mapping["source_role"],
            "ai_exposure_score": 0.65 + (i * 0.05),
            "impact_score": 0.70 + (i * 0.03),
            "complexity_score": 0.25 + (i * 0.05),
            "priority_score": 0.72 + (i * 0.04),
            "priority_tier": priority_tier,
        })

    return {
        "results": results,
        "dimension": dimension,
    }


@app.post("/api/v1/discovery/sessions/{session_id}/analyze")
async def trigger_analysis(session_id: str):
    session_mappings = [m for m in role_mappings.values() if m["session_id"] == session_id]

    results = []
    for mapping in session_mappings:
        result = {
            "id": str(uuid4()),
            "session_id": session_id,
            "dimension": "role",
            "dimension_value": mapping["source_role"],
            "ai_exposure_score": round(0.7 + 0.2 * hash(mapping["source_role"]) % 100 / 100, 2),
            "impact_score": round(0.6 + 0.3 * hash(mapping["source_role"] + "i") % 100 / 100, 2),
            "complexity_score": round(0.1 + 0.3 * hash(mapping["source_role"] + "c") % 100 / 100, 2),
            "priority_score": round(0.6 + 0.3 * hash(mapping["source_role"] + "p") % 100 / 100, 2),
            "breakdown": {"activities_count": len(SAMPLE_DWAS)},
        }
        results.append(result)
        analysis_results[result["id"]] = result

    return {"status": "completed"}


@app.get("/api/v1/discovery/sessions/{session_id}/analysis")
async def get_analysis(session_id: str, dimension: str = Query(None)):
    session_results = [r for r in analysis_results.values() if r["session_id"] == session_id]

    if dimension:
        session_results = [r for r in session_results if r["dimension"] == dimension]

    return {"results": session_results}


# =============================================================================
# Roadmap Endpoints
# =============================================================================

@app.post("/api/v1/discovery/sessions/{session_id}/roadmap/generate")
async def generate_roadmap(session_id: str):
    session_results = [r for r in analysis_results.values() if r["session_id"] == session_id]

    generated_candidates = []
    for i, result in enumerate(session_results[:5]):
        priority = result["priority_score"]
        complexity = result["complexity_score"]

        if priority >= 0.75 and complexity < 0.3:
            tier = "now"
        elif priority >= 0.60:
            tier = "next_quarter"
        else:
            tier = "future"

        candidate = {
            "id": str(uuid4()),
            "session_id": session_id,
            "name": f"Agent for {result['dimension_value']}",
            "description": f"Automate tasks for {result['dimension_value']}",
            "priority_tier": tier,
            "priority_score": priority,
            "estimated_impact": result["impact_score"],
            "selected_for_build": False,
        }
        candidates[candidate["id"]] = candidate
        generated_candidates.append(candidate)

    return {"candidates": generated_candidates}


@app.get("/api/v1/discovery/sessions/{session_id}/roadmap")
async def get_roadmap(session_id: str):
    session_candidates = [c for c in candidates.values() if c["session_id"] == session_id]
    return {"candidates": session_candidates}


@app.post("/api/v1/discovery/sessions/{session_id}/roadmap/select")
async def select_for_build(session_id: str, data: SelectForBuild):
    selected_count = 0
    for cid in data.candidate_ids:
        if cid in candidates:
            candidates[cid]["selected_for_build"] = True
            selected_count += 1
    return {"selected_count": selected_count}


# =============================================================================
# Handoff & Export Endpoints
# =============================================================================

@app.post("/api/v1/discovery/sessions/{session_id}/handoff")
async def create_handoff(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    selected = [c for c in candidates.values() if c["session_id"] == session_id and c["selected_for_build"]]
    session_results = [r for r in analysis_results.values() if r["session_id"] == session_id]

    return {
        "session_id": session_id,
        "candidates": selected,
        "analysis_summary": {
            "total_roles": len(session_results),
            "avg_exposure": sum(r["ai_exposure_score"] for r in session_results) / len(session_results) if session_results else 0,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/discovery/sessions/{session_id}/exports/csv")
async def export_csv(session_id: str):
    from fastapi.responses import Response

    session_results = [r for r in analysis_results.values() if r["session_id"] == session_id]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["dimension", "dimension_value", "ai_exposure_score", "impact_score", "complexity_score", "priority_score"])

    for r in session_results:
        writer.writerow([r["dimension"], r["dimension_value"], r["ai_exposure_score"], r["impact_score"], r["complexity_score"], r["priority_score"]])

    return Response(content=output.getvalue(), media_type="text/csv")


# =============================================================================
# Chat Endpoints
# =============================================================================

@app.get("/discovery/sessions/{session_id}/chat")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    return {"messages": []}


@app.post("/discovery/sessions/{session_id}/chat")
@app.post("/api/v1/discovery/sessions/{session_id}/chat")
async def send_chat(session_id: str, data: ChatMessage):
    message_lower = data.message.lower()

    if any(term in message_lower for term in ["mapping", "confidence", "o*net"]):
        response = "I can help with role mapping. Some roles have low confidence matches. You can manually review and confirm each mapping."
    elif "help" in message_lower:
        response = "I'm here to help you through the discovery process. Would you like me to explain the current step?"
    else:
        response = "I understand. Let me know if you have questions about the discovery workflow."

    return {"response": response}


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Starting Discovery API Mock Server")
    print("=" * 60)
    print(f"Server will be available at: http://localhost:8001")
    print(f"API docs available at: http://localhost:8001/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
