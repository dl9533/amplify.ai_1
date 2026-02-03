"""
Mock Service Implementations for E2E Testing

These mocks simulate the behavior of real services without
requiring database or external API access.
"""

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any
import csv
import io
from difflib import SequenceMatcher


class MockSessionService:
    """In-memory mock for DiscoverySessionService."""

    def __init__(self):
        self.sessions: dict[str, dict] = {}

    async def create(self, organization_id: str, user_id: str) -> dict:
        session_id = str(uuid4())
        session = {
            "id": session_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "status": "draft",
            "current_step": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sessions[session_id] = session
        return session

    async def get(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    async def update(self, session_id: str, **kwargs) -> dict:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Validate step advancement
        if "current_step" in kwargs:
            new_step = kwargs["current_step"]
            if new_step > session["current_step"] + 1:
                raise ValueError("Cannot skip steps")

            # Check if mappings are confirmed before advancing to step 3
            if new_step == 3:
                # This would be checked against actual mapping data
                pass

        session.update(kwargs)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()

        if session["current_step"] > 1 and session["status"] == "draft":
            session["status"] = "in_progress"

        return session

    async def delete(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class MockUploadService:
    """In-memory mock for UploadService."""

    def __init__(self):
        self.uploads: dict[str, dict] = {}
        self.session_uploads: dict[str, list[str]] = {}

    async def upload(self, session_id: str, file_name: str, content: bytes) -> dict:
        # Validate file type
        if not file_name.endswith(('.csv', '.xlsx', '.xls')):
            raise ValueError("Unsupported file type. Please upload CSV or Excel files.")

        # Validate not empty
        if len(content) == 0:
            raise ValueError("File is empty")

        # Try to parse CSV
        if file_name.endswith('.csv'):
            try:
                decoded = content.decode('utf-8')
                reader = csv.reader(io.StringIO(decoded))
                rows = list(reader)

                if len(rows) == 0:
                    raise ValueError("File is empty")

                if len(rows) == 1:
                    raise ValueError("File contains only headers, no data rows")

                headers = rows[0]
                data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]

                if len(data_rows) == 0:
                    raise ValueError("File contains only headers, no data rows")

            except csv.Error as e:
                raise ValueError(f"CSV parse error: {e}")
            except UnicodeDecodeError:
                raise ValueError("Unable to decode file. Please ensure it's valid UTF-8.")
        else:
            # Simulate Excel parsing
            headers = ["employee_id", "name", "job_title", "department", "location", "headcount"]
            data_rows = []

        upload_id = str(uuid4())

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

        upload = {
            "id": upload_id,
            "session_id": session_id,
            "file_name": file_name,
            "file_url": f"s3://test-bucket/{session_id}/{upload_id}/{file_name}",
            "row_count": len(data_rows),
            "column_mappings": column_mappings,
            "detected_schema": {
                "columns": [{"name": h, "type": "string"} for h in headers]
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update schema types based on content
        for i, header in enumerate(headers):
            if "headcount" in header.lower() or "count" in header.lower():
                upload["detected_schema"]["columns"][i]["type"] = "integer"

        self.uploads[upload_id] = upload

        if session_id not in self.session_uploads:
            self.session_uploads[session_id] = []
        self.session_uploads[session_id].append(upload_id)

        return upload

    async def get(self, upload_id: str) -> dict | None:
        return self.uploads.get(upload_id)

    async def get_schema(self, upload_id: str) -> dict | None:
        upload = self.uploads.get(upload_id)
        if upload:
            return upload.get("detected_schema")
        return None


class MockRoleMappingService:
    """In-memory mock for RoleMappingService."""

    # O*NET occupation database (subset)
    ONET_OCCUPATIONS = {
        "43-4051.00": "Customer Service Representatives",
        "43-9021.00": "Data Entry Keyers",
        "43-3031.00": "Bookkeeping, Accounting, and Auditing Clerks",
        "13-1071.00": "Human Resources Specialists",
        "15-1232.00": "Computer User Support Specialists",
        "13-1161.00": "Market Research Analysts and Marketing Specialists",
        "11-1021.00": "General and Operations Managers",
        "15-1252.00": "Software Developers",
        "13-2011.00": "Accountants and Auditors",
        "11-3031.00": "Financial Managers",
    }

    def __init__(self):
        self.mappings: dict[str, dict] = {}
        self.session_mappings: dict[str, list[str]] = {}

    def _calculate_confidence(self, role: str, onet_title: str) -> float:
        """Calculate similarity score between role and O*NET title."""
        role_lower = role.lower()
        title_lower = onet_title.lower()

        # Exact match
        if role_lower == title_lower:
            return 1.0

        # Substring bonus
        ratio = SequenceMatcher(None, role_lower, title_lower).ratio()
        if role_lower in title_lower or title_lower in role_lower:
            ratio = min(1.0, ratio + 0.1)

        return round(ratio, 2)

    def _find_best_match(self, role: str) -> tuple[str, str, float]:
        """Find best O*NET match for a role."""
        best_code = None
        best_title = None
        best_score = 0.0

        for code, title in self.ONET_OCCUPATIONS.items():
            score = self._calculate_confidence(role, title)
            if score > best_score:
                best_score = score
                best_code = code
                best_title = title

        return best_code, best_title, best_score

    async def auto_map(self, session_id: str, roles: list[str]) -> dict:
        """Auto-map roles to O*NET occupations."""
        mappings = []
        low_confidence_count = 0

        for role in roles:
            code, title, confidence = self._find_best_match(role)

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

            self.mappings[mapping_id] = mapping

            if session_id not in self.session_mappings:
                self.session_mappings[session_id] = []
            self.session_mappings[session_id].append(mapping_id)

            mappings.append(mapping)

            if confidence < 0.60:
                low_confidence_count += 1

        return {
            "mappings": mappings,
            "low_confidence_count": low_confidence_count,
            "requires_review": low_confidence_count > 0,
            "warnings": [
                f"{low_confidence_count} roles have low confidence matches and require review"
            ] if low_confidence_count > 0 else []
        }

    async def bulk_confirm(self, session_id: str, min_confidence: float) -> dict:
        """Bulk confirm mappings meeting confidence threshold."""
        confirmed_count = 0

        mapping_ids = self.session_mappings.get(session_id, [])
        for mapping_id in mapping_ids:
            mapping = self.mappings.get(mapping_id)
            if mapping and mapping["confidence_score"] >= min_confidence:
                mapping["user_confirmed"] = True
                confirmed_count += 1

        return {"confirmed_count": confirmed_count}

    async def update(self, mapping_id: str, **kwargs) -> dict:
        """Update a single mapping."""
        if mapping_id not in self.mappings:
            raise ValueError(f"Mapping {mapping_id} not found")

        mapping = self.mappings[mapping_id]
        mapping.update(kwargs)
        return mapping

    async def get_unconfirmed_count(self, session_id: str) -> int:
        """Get count of unconfirmed mappings."""
        mapping_ids = self.session_mappings.get(session_id, [])
        count = 0
        for mapping_id in mapping_ids:
            mapping = self.mappings.get(mapping_id)
            if mapping and not mapping["user_confirmed"]:
                count += 1
        return count


class MockActivityService:
    """In-memory mock for ActivityService."""

    # Sample DWAs organized by GWA
    SAMPLE_DWAS = {
        "Getting Information": [
            {"id": "dwa-001", "name": "Gathering information from customers", "ai_exposure_score": 0.75},
            {"id": "dwa-002", "name": "Reading documents and reports", "ai_exposure_score": 0.82},
        ],
        "Communicating": [
            {"id": "dwa-003", "name": "Responding to customer inquiries", "ai_exposure_score": 0.70},
            {"id": "dwa-004", "name": "Writing emails and correspondence", "ai_exposure_score": 0.85},
        ],
        "Processing Information": [
            {"id": "dwa-005", "name": "Entering data into systems", "ai_exposure_score": 0.90},
            {"id": "dwa-006", "name": "Verifying accuracy of information", "ai_exposure_score": 0.65},
        ],
    }

    def __init__(self):
        self.selections: dict[str, dict] = {}

    async def get_activities_by_role(self, session_id: str) -> dict:
        """Get activities grouped by role."""
        # Return sample activities for each role
        activities_by_role = {}

        roles = ["Customer Service Representative", "Data Entry Clerk"]
        for role in roles:
            activities = []
            for gwa_name, dwas in self.SAMPLE_DWAS.items():
                for dwa in dwas:
                    activities.append({
                        "dwa_id": dwa["id"],
                        "dwa_name": dwa["name"],
                        "gwa_name": gwa_name,
                        "ai_exposure_score": dwa["ai_exposure_score"],
                        "selected": False,
                    })
            activities_by_role[role] = activities

        return {"activities_by_role": activities_by_role}

    async def auto_select(self, session_id: str, min_exposure: float) -> dict:
        """Auto-select activities with high AI exposure."""
        selected_count = 0
        total_count = 0

        for gwa_name, dwas in self.SAMPLE_DWAS.items():
            for dwa in dwas:
                total_count += 1
                if dwa["ai_exposure_score"] >= min_exposure:
                    selected_count += 1

        return {
            "selected_count": selected_count,
            "total_count": total_count,
        }


class MockAnalysisService:
    """In-memory mock for AnalysisService."""

    def __init__(self):
        self.results: dict[str, list] = {}

    async def trigger_analysis(self, session_id: str) -> dict:
        """Trigger analysis calculation."""
        # Generate mock results
        self.results[session_id] = [
            {
                "dimension": "role",
                "dimension_value": "Customer Service Representative",
                "ai_exposure_score": 0.78,
                "impact_score": 0.85,
                "complexity_score": 0.22,
                "priority_score": 0.82,
                "breakdown": {"activities_count": 15, "avg_exposure": 0.78},
            },
            {
                "dimension": "role",
                "dimension_value": "Data Entry Clerk",
                "ai_exposure_score": 0.88,
                "impact_score": 0.65,
                "complexity_score": 0.12,
                "priority_score": 0.79,
                "breakdown": {"activities_count": 8, "avg_exposure": 0.88},
            },
        ]

        return {"status": "completed"}

    async def get_results(self, session_id: str, dimension: str = None) -> dict:
        """Get analysis results."""
        results = self.results.get(session_id, [])

        if dimension:
            results = [r for r in results if r["dimension"] == dimension]

        return {"results": results}


class MockRoadmapService:
    """In-memory mock for RoadmapService."""

    def __init__(self):
        self.candidates: dict[str, list] = {}

    async def generate(self, session_id: str) -> dict:
        """Generate agentification candidates."""
        candidates = [
            {
                "id": str(uuid4()),
                "name": "Customer Inquiry Handler",
                "description": "Automate customer service inquiry routing and responses",
                "priority_tier": "now",
                "priority_score": 0.82,
                "estimated_impact": 0.85,
                "selected_for_build": False,
            },
            {
                "id": str(uuid4()),
                "name": "Data Entry Automation",
                "description": "Automate repetitive data entry tasks",
                "priority_tier": "now",
                "priority_score": 0.79,
                "estimated_impact": 0.65,
                "selected_for_build": False,
            },
            {
                "id": str(uuid4()),
                "name": "Report Generation Assistant",
                "description": "Automate report generation and distribution",
                "priority_tier": "next_quarter",
                "priority_score": 0.68,
                "estimated_impact": 0.55,
                "selected_for_build": False,
            },
        ]

        self.candidates[session_id] = candidates
        return {"candidates": candidates}

    async def get_candidates(self, session_id: str) -> dict:
        """Get roadmap candidates."""
        return {"candidates": self.candidates.get(session_id, [])}

    async def select_for_build(self, session_id: str, candidate_ids: list[str]) -> dict:
        """Select candidates for build handoff."""
        candidates = self.candidates.get(session_id, [])
        selected_count = 0

        for candidate in candidates:
            if candidate["id"] in candidate_ids:
                candidate["selected_for_build"] = True
                selected_count += 1

        return {"selected_count": selected_count}


class MockChatService:
    """In-memory mock for ChatService."""

    def __init__(self):
        self.messages: dict[str, list] = {}

    async def send_message(self, session_id: str, message: str) -> dict:
        """Process a chat message and return response."""
        if session_id not in self.messages:
            self.messages[session_id] = []

        # Store user message
        self.messages[session_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Generate mock response based on keywords
        message_lower = message.lower()

        if any(term in message_lower for term in ["mapping", "confidence", "o*net"]):
            response = (
                "I can help with role mapping. Some of your roles have low confidence "
                "matches to O*NET occupations. You can manually review and confirm each "
                "mapping, or search for alternative O*NET codes that better fit your "
                "organization's role definitions."
            )
        elif "help" in message_lower:
            response = (
                "I'm here to help you through the discovery process. We're currently "
                "working on mapping your organizational roles to standard O*NET "
                "occupations. Would you like me to explain the mapping process?"
            )
        else:
            response = (
                "I understand. Let me know if you have any questions about the "
                "discovery workflow or need help with specific roles."
            )

        # Store assistant response
        self.messages[session_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {"response": response}


class MockOnetService:
    """In-memory mock for O*NET API service."""

    OCCUPATIONS = [
        {"code": "11-1021.00", "title": "General and Operations Managers"},
        {"code": "13-1071.00", "title": "Human Resources Specialists"},
        {"code": "13-1161.00", "title": "Market Research Analysts and Marketing Specialists"},
        {"code": "13-2011.00", "title": "Accountants and Auditors"},
        {"code": "15-1232.00", "title": "Computer User Support Specialists"},
        {"code": "15-1252.00", "title": "Software Developers"},
        {"code": "43-3031.00", "title": "Bookkeeping, Accounting, and Auditing Clerks"},
        {"code": "43-4051.00", "title": "Customer Service Representatives"},
        {"code": "43-9021.00", "title": "Data Entry Keyers"},
    ]

    async def search(self, query: str) -> dict:
        """Search O*NET occupations."""
        query_lower = query.lower()
        results = [
            occ for occ in self.OCCUPATIONS
            if query_lower in occ["title"].lower()
        ]
        return {"results": results}
