# Phase 0: Opportunity Discovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement O*NET-powered opportunity discovery with orchestrator + subagent architecture, enabling enterprises to identify automation candidates through a collaborative 5-step wizard workflow.

**Architecture:** Docker Compose orchestration with 4 services: discovery-api (FastAPI), postgres (with O*NET tables), redis (caching/sessions), localstack (S3-compatible storage for development). Production uses AWS S3 directly. Weekly O*NET API sync populates local database with occupations, work activities (GWA→IWA→DWA hierarchy), tasks, and skills. Discovery orchestrator manages single conversation thread, routing to 5 specialized subagents (Upload, Mapping, Activity, Analysis, Roadmap). Each subagent has per-agent memory for continuous learning.

**Tech Stack:** Docker, Docker Compose, PostgreSQL 16, Redis 7, LocalStack (S3), FastAPI with uvicorn, React 18+ frontend with shadcn/ui, httpx for O*NET API calls.

**Dependencies:** None (standalone container-based module)

**Design Document:** `docs/plans/2026-01-31-opportunity-discovery-design.md`

---

## Part 0: Container Infrastructure (Tasks 0.0-0.8)

### Task 0.0: Remove Legacy Opportunity Module

**Files:**
- Delete: `backend/app/modules/opportunity/` (entire directory)
- Delete: `backend/migrations/versions/002_opportunity_tables.py`
- Delete: `backend/tests/unit/modules/opportunity/` (entire directory)
- Delete: `backend/tests/integration/opportunity/` (entire directory)
- Delete: `backend/tests/unit/test_main_opportunity.py`
- Modify: `backend/app/main.py` (remove opportunity router)

**Step 1: Verify legacy code exists**

Run: `ls backend/app/modules/opportunity/`
Expected: Shows existing files (models.py, router.py, service.py, etc.)

**Step 2: Remove opportunity module from main.py**

Edit `backend/app/main.py`:
- Remove line: `from app.modules.opportunity.router import router as opportunity_router`
- Remove line: `app.include_router(opportunity_router, prefix="/api/v1/opportunity", tags=["opportunity"])`

**Step 3: Delete legacy directories and files**

```bash
rm -rf backend/app/modules/opportunity/
rm -rf backend/tests/unit/modules/opportunity/
rm -rf backend/tests/integration/opportunity/
rm -f backend/tests/unit/test_main_opportunity.py
rm -f backend/migrations/versions/002_opportunity_tables.py
```

**Step 4: Verify removal and tests still pass**

Run: `cd backend && python -m pytest tests/ -v --ignore=tests/unit/modules/opportunity --ignore=tests/integration/opportunity`
Expected: PASS (remaining tests unaffected)

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove legacy opportunity module (replaced by standalone discovery)"
```

---

### Task 0.1: Discovery Module Directory Structure

**Files:**
- Create: `discovery/README.md`
- Create: `discovery/.gitignore`
- Create: `discovery/.env.example`
- Test: (Manual verification)

**Step 1: Write the failing test**

```bash
# Verify directory structure exists
test -d discovery && test -f discovery/README.md && test -f discovery/.env.example
```

**Step 2: Run test to verify it fails**

Run: `test -d discovery && echo "EXISTS" || echo "MISSING"`
Expected: "MISSING"

**Step 3: Write minimal implementation**

(Implementer determines the code)

README.md should include:
- Module purpose
- Quick start with docker-compose
- Environment variable reference
- Development vs production setup

.env.example should include:
```
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=discovery
POSTGRES_PASSWORD=discovery_dev
POSTGRES_DB=discovery

# Redis
REDIS_URL=redis://redis:6379/0

# S3 Storage
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET=discovery-uploads
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1

# O*NET API
ONET_API_USERNAME=your_api_key_here
ONET_API_BASE_URL=https://services.onetcenter.org/ws/

# Application
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=true
LOG_LEVEL=INFO
```

.gitignore should include:
```
.env
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.venv/
*.egg-info/
dist/
build/
```

**Step 4: Verify structure exists**

Run: `ls -la discovery/`
Expected: README.md, .gitignore, .env.example visible

**Step 5: Commit**

```bash
git add discovery/
git commit -m "chore(discovery): initialize module directory structure"
```

---

### Task 0.2: Dockerfile for Discovery API

**Files:**
- Create: `discovery/Dockerfile`
- Create: `discovery/Dockerfile.dev`
- Test: `discovery/tests/test_docker_build.sh`

**Step 1: Write the failing test**

```bash
# discovery/tests/test_docker_build.sh
#!/bin/bash
set -e

echo "Testing Dockerfile builds..."

# Build should succeed
docker build -t discovery-api-test -f discovery/Dockerfile discovery/

# Image should exist
docker images discovery-api-test | grep -q discovery-api-test

# Cleanup
docker rmi discovery-api-test

echo "Dockerfile build test passed!"
```

**Step 2: Run test to verify it fails**

Run: `bash discovery/tests/test_docker_build.sh`
Expected: FAIL with "Dockerfile not found" or build error

**Step 3: Write minimal implementation**

(Implementer determines the code)

Dockerfile should include:
- Python 3.12-slim base image
- Non-root user for security
- Multi-stage build for smaller image
- Health check endpoint
- uvicorn as entrypoint

Dockerfile.dev should include:
- Volume mounts for hot reload
- Development dependencies
- Debug mode enabled

**Step 4: Run test to verify it passes**

Run: `bash discovery/tests/test_docker_build.sh`
Expected: "Dockerfile build test passed!"

**Step 5: Commit**

```bash
git add discovery/Dockerfile discovery/Dockerfile.dev discovery/tests/
git commit -m "feat(discovery): add Dockerfiles for API service"
```

---

### Task 0.3: Docker Compose Development Stack

**Files:**
- Create: `discovery/docker-compose.yml`
- Create: `discovery/docker-compose.dev.yml`
- Test: `discovery/tests/test_compose_config.sh`

**Step 1: Write the failing test**

```bash
# discovery/tests/test_compose_config.sh
#!/bin/bash
set -e

echo "Validating docker-compose configuration..."

# Validate compose file syntax
docker compose -f discovery/docker-compose.yml config > /dev/null
docker compose -f discovery/docker-compose.yml -f discovery/docker-compose.dev.yml config > /dev/null

# Check required services exist
docker compose -f discovery/docker-compose.yml config --services | grep -q "api"
docker compose -f discovery/docker-compose.yml config --services | grep -q "postgres"
docker compose -f discovery/docker-compose.yml config --services | grep -q "redis"
docker compose -f discovery/docker-compose.yml config --services | grep -q "localstack"

echo "Docker Compose config validation passed!"
```

**Step 2: Run test to verify it fails**

Run: `bash discovery/tests/test_compose_config.sh`
Expected: FAIL with "docker-compose.yml not found"

**Step 3: Write minimal implementation**

(Implementer determines the code)

docker-compose.yml should define 4 services:
- `api`: Discovery FastAPI service (port 8001)
- `postgres`: PostgreSQL 16 with discovery database
- `redis`: Redis 7 for caching
- `localstack`: S3-compatible storage (port 4566)

docker-compose.dev.yml overrides:
- Volume mounts for hot reload
- Debug environment variables
- Exposed ports for debugging

**Step 4: Run test to verify it passes**

Run: `bash discovery/tests/test_compose_config.sh`
Expected: "Docker Compose config validation passed!"

**Step 5: Commit**

```bash
git add discovery/docker-compose.yml discovery/docker-compose.dev.yml
git commit -m "feat(discovery): add Docker Compose stack with postgres, redis, localstack"
```

---

### Task 0.4: PostgreSQL Initialization Scripts

**Files:**
- Create: `discovery/docker/postgres/init.sql`
- Create: `discovery/docker/postgres/create-extensions.sql`
- Test: `discovery/tests/test_postgres_init.sh`

**Step 1: Write the failing test**

```bash
# discovery/tests/test_postgres_init.sh
#!/bin/bash
set -e

echo "Testing PostgreSQL initialization..."

# Start postgres only
docker compose -f discovery/docker-compose.yml up -d postgres
sleep 5

# Check database exists
docker compose -f discovery/docker-compose.yml exec -T postgres \
  psql -U discovery -d discovery -c "SELECT 1" > /dev/null

# Check uuid-ossp extension
docker compose -f discovery/docker-compose.yml exec -T postgres \
  psql -U discovery -d discovery -c "SELECT uuid_generate_v4();" > /dev/null

# Cleanup
docker compose -f discovery/docker-compose.yml down -v

echo "PostgreSQL initialization test passed!"
```

**Step 2: Run test to verify it fails**

Run: `bash discovery/tests/test_postgres_init.sh`
Expected: FAIL with extension or database errors

**Step 3: Write minimal implementation**

(Implementer determines the code)

init.sql should:
- Create discovery database if not exists
- Set up search paths

create-extensions.sql should:
- Enable uuid-ossp extension
- Enable pg_trgm for text search (used in occupation matching)

**Step 4: Run test to verify it passes**

Run: `bash discovery/tests/test_postgres_init.sh`
Expected: "PostgreSQL initialization test passed!"

**Step 5: Commit**

```bash
git add discovery/docker/postgres/
git commit -m "feat(discovery): add PostgreSQL initialization scripts with extensions"
```

---

### Task 0.5: LocalStack S3 Bucket Initialization

**Files:**
- Create: `discovery/docker/localstack/init-s3.sh`
- Test: `discovery/tests/test_localstack_s3.sh`

**Step 1: Write the failing test**

```bash
# discovery/tests/test_localstack_s3.sh
#!/bin/bash
set -e

echo "Testing LocalStack S3 initialization..."

# Start localstack only
docker compose -f discovery/docker-compose.yml up -d localstack
sleep 10

# Check bucket exists
docker compose -f discovery/docker-compose.yml exec -T localstack \
  awslocal s3 ls s3://discovery-uploads

# Test upload and download
echo "test content" | docker compose -f discovery/docker-compose.yml exec -T localstack \
  awslocal s3 cp - s3://discovery-uploads/test.txt

docker compose -f discovery/docker-compose.yml exec -T localstack \
  awslocal s3 cp s3://discovery-uploads/test.txt - | grep -q "test content"

# Cleanup
docker compose -f discovery/docker-compose.yml down -v

echo "LocalStack S3 initialization test passed!"
```

**Step 2: Run test to verify it fails**

Run: `bash discovery/tests/test_localstack_s3.sh`
Expected: FAIL with bucket not found

**Step 3: Write minimal implementation**

(Implementer determines the code)

init-s3.sh should:
- Wait for LocalStack to be ready
- Create discovery-uploads bucket
- Set bucket CORS policy for frontend uploads

**Step 4: Run test to verify it passes**

Run: `bash discovery/tests/test_localstack_s3.sh`
Expected: "LocalStack S3 initialization test passed!"

**Step 5: Commit**

```bash
git add discovery/docker/localstack/
git commit -m "feat(discovery): add LocalStack S3 bucket initialization"
```

---

### Task 0.6: Discovery API Python Project Structure

**Files:**
- Create: `discovery/api/pyproject.toml`
- Create: `discovery/api/requirements.txt`
- Create: `discovery/api/src/discovery/__init__.py`
- Create: `discovery/api/src/discovery/config.py`
- Test: `discovery/api/tests/test_project_structure.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/__init__.py
# empty file

# discovery/api/tests/test_project_structure.py
import pytest
from pathlib import Path


def test_pyproject_toml_exists():
    """pyproject.toml should exist with project metadata."""
    path = Path(__file__).parent.parent / "pyproject.toml"
    assert path.exists()

    content = path.read_text()
    assert "[project]" in content
    assert 'name = "discovery"' in content or "name = 'discovery'" in content
    assert "fastapi" in content.lower()


def test_requirements_txt_exists():
    """requirements.txt should exist with dependencies."""
    path = Path(__file__).parent.parent / "requirements.txt"
    assert path.exists()

    content = path.read_text()
    assert "fastapi" in content.lower()
    assert "sqlalchemy" in content.lower()
    assert "httpx" in content.lower()  # For O*NET API calls
    assert "boto3" in content.lower()  # For S3


def test_discovery_package_exists():
    """discovery package should be importable."""
    import discovery
    assert discovery is not None


def test_config_loads():
    """Config should load from environment."""
    from discovery.config import Settings

    # Should have discovery-specific settings
    fields = Settings.model_fields.keys()
    assert "postgres_host" in fields
    assert "redis_url" in fields
    assert "s3_bucket" in fields
    assert "onet_api_username" in fields
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/test_project_structure.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

(Implementer determines the code)

pyproject.toml should define:
- Project name: discovery
- Python 3.12 requirement
- FastAPI, SQLAlchemy, httpx, boto3 dependencies
- Pytest configuration

config.py should use Pydantic Settings with:
- Database connection settings
- Redis URL
- S3 configuration
- O*NET API credentials

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/test_project_structure.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/
git commit -m "feat(discovery): add Python project structure with config"
```

---

### Task 0.7: Discovery API Health Check Endpoint

**Files:**
- Create: `discovery/api/src/discovery/main.py`
- Create: `discovery/api/src/discovery/routes/__init__.py`
- Create: `discovery/api/src/discovery/routes/health.py`
- Test: `discovery/api/tests/test_health.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/test_health.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health check should return service status."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_checks_dependencies():
    """Health check should report dependency status."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health?detailed=true")

    assert response.status_code == 200
    data = response.json()
    assert "dependencies" in data
    assert "postgres" in data["dependencies"]
    assert "redis" in data["dependencies"]
    assert "s3" in data["dependencies"]


@pytest.mark.asyncio
async def test_readiness_endpoint():
    """Readiness probe should check if service can handle requests."""
    from discovery.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/ready")

    # May return 503 if dependencies down, but endpoint should exist
    assert response.status_code in [200, 503]
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/test_health.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'discovery.main'"

**Step 3: Write minimal implementation**

(Implementer determines the code)

main.py should:
- Create FastAPI app with title "Discovery API"
- Include health router
- Configure CORS for frontend

health.py should:
- Implement /health endpoint
- Implement /ready endpoint (Kubernetes readiness probe)
- Check postgres, redis, s3 connectivity when detailed=true

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/test_health.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/
git commit -m "feat(discovery): add FastAPI health check endpoints"
```

---

### Task 0.8: Full Stack Integration Test

**Files:**
- Create: `discovery/tests/test_full_stack.sh`
- Test: (Self-testing script)

**Step 1: Write the failing test**

```bash
# discovery/tests/test_full_stack.sh
#!/bin/bash
set -e

echo "=========================================="
echo "Discovery Module Full Stack Integration Test"
echo "=========================================="

# Start all services
echo "Starting services..."
docker compose -f discovery/docker-compose.yml -f discovery/docker-compose.dev.yml up -d --build

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 15

# Test API health endpoint
echo "Testing API health..."
curl -f http://localhost:8001/health || { echo "API health check failed"; exit 1; }

# Test detailed health (checks all dependencies)
echo "Testing dependency connectivity..."
HEALTH=$(curl -s http://localhost:8001/health?detailed=true)
echo "$HEALTH" | jq .

# Verify postgres is connected
echo "$HEALTH" | jq -e '.dependencies.postgres == "connected"' > /dev/null || { echo "Postgres not connected"; exit 1; }

# Verify redis is connected
echo "$HEALTH" | jq -e '.dependencies.redis == "connected"' > /dev/null || { echo "Redis not connected"; exit 1; }

# Verify S3 is connected
echo "$HEALTH" | jq -e '.dependencies.s3 == "connected"' > /dev/null || { echo "S3 not connected"; exit 1; }

# Test readiness endpoint
echo "Testing readiness probe..."
curl -f http://localhost:8001/ready || { echo "Readiness probe failed"; exit 1; }

# Cleanup
echo "Cleaning up..."
docker compose -f discovery/docker-compose.yml down -v

echo "=========================================="
echo "Full stack integration test PASSED!"
echo "=========================================="
```

**Step 2: Run test to verify it fails**

Run: `bash discovery/tests/test_full_stack.sh`
Expected: FAIL (services not configured correctly yet)

**Step 3: Fix any integration issues**

(Implementer fixes issues found during integration testing)

Common issues to address:
- Container networking between services
- Environment variable passing
- Volume mount permissions
- Service startup order and health checks

**Step 4: Run test to verify it passes**

Run: `bash discovery/tests/test_full_stack.sh`
Expected: "Full stack integration test PASSED!"

**Step 5: Commit**

```bash
git add discovery/
git commit -m "feat(discovery): complete container infrastructure with integration tests"
```

---

## Part 0 Complete

After completing all 8 infrastructure tasks:

1. Run full integration test: `bash discovery/tests/test_full_stack.sh`
2. Verify all services start correctly
3. Create summary commit: `git commit -m "feat(discovery): complete Phase 0 container infrastructure"`

**Infrastructure Ready:**
- Discovery API container (port 8001)
- PostgreSQL 16 with extensions
- Redis 7 for caching
- LocalStack S3 for file storage
- Health/readiness endpoints for Kubernetes

## Part 1: O*NET Data Layer (Tasks 1-8)

### Task 1: O*NET Enums

**Files:**
- Create: `backend/app/modules/discovery/__init__.py`
- Create: `backend/app/modules/discovery/enums.py`
- Create: `backend/tests/unit/modules/discovery/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_enums.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/__init__.py
# empty file

# backend/tests/unit/modules/discovery/test_enums.py
import pytest

from app.modules.discovery.enums import (
    SessionStatus,
    AnalysisDimension,
    PriorityTier,
)


def test_session_status_enum():
    """SessionStatus should track discovery session lifecycle."""
    assert SessionStatus.DRAFT.value == "draft"
    assert SessionStatus.IN_PROGRESS.value == "in_progress"
    assert SessionStatus.COMPLETED.value == "completed"
    assert SessionStatus.ARCHIVED.value == "archived"


def test_analysis_dimension_enum():
    """AnalysisDimension should define 5 view dimensions."""
    assert AnalysisDimension.ROLE.value == "role"
    assert AnalysisDimension.TASK.value == "task"
    assert AnalysisDimension.LOB.value == "lob"
    assert AnalysisDimension.GEOGRAPHY.value == "geography"
    assert AnalysisDimension.DEPARTMENT.value == "department"


def test_priority_tier_enum():
    """PriorityTier should define roadmap timeline buckets."""
    assert PriorityTier.NOW.value == "now"
    assert PriorityTier.NEXT_QUARTER.value == "next_quarter"
    assert PriorityTier.FUTURE.value == "future"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_enums.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.modules.discovery'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_enums.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/ backend/tests/unit/modules/discovery/
git commit -m "feat(discovery): add discovery session enums"
```

---

### Task 2: O*NET Occupation Model

**Files:**
- Create: `backend/app/modules/discovery/models/__init__.py`
- Create: `backend/app/modules/discovery/models/onet.py`
- Test: `backend/tests/unit/modules/discovery/test_onet_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_onet_models.py
import pytest

from app.modules.discovery.models.onet import (
    OnetOccupation,
    OnetGwa,
    OnetIwa,
    OnetDwa,
    OnetTask,
    OnetSkill,
    OnetTechnologySkill,
)


def test_onet_occupation_has_required_columns():
    """OnetOccupation model should have O*NET occupation columns."""
    columns = {c.name for c in OnetOccupation.__table__.columns}
    assert "code" in columns  # PK, e.g., "15-1252.00"
    assert "title" in columns
    assert "description" in columns
    assert "updated_at" in columns


def test_onet_gwa_has_required_columns():
    """OnetGwa model should have generalized work activity columns."""
    columns = {c.name for c in OnetGwa.__table__.columns}
    assert "id" in columns  # e.g., "4.A.1.a.1"
    assert "name" in columns
    assert "description" in columns
    assert "ai_exposure_score" in columns  # 0.0-1.0


def test_onet_iwa_has_required_columns():
    """OnetIwa model should have intermediate work activity columns."""
    columns = {c.name for c in OnetIwa.__table__.columns}
    assert "id" in columns
    assert "gwa_id" in columns  # FK to OnetGwa
    assert "name" in columns
    assert "description" in columns


def test_onet_dwa_has_required_columns():
    """OnetDwa model should have detailed work activity columns."""
    columns = {c.name for c in OnetDwa.__table__.columns}
    assert "id" in columns
    assert "iwa_id" in columns  # FK to OnetIwa
    assert "name" in columns
    assert "description" in columns
    assert "ai_exposure_override" in columns  # NULL = inherit from GWA


def test_onet_task_has_required_columns():
    """OnetTask model should have task columns."""
    columns = {c.name for c in OnetTask.__table__.columns}
    assert "id" in columns
    assert "occupation_code" in columns  # FK to OnetOccupation
    assert "description" in columns
    assert "importance" in columns


def test_onet_skill_has_required_columns():
    """OnetSkill model should have skill columns."""
    columns = {c.name for c in OnetSkill.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "description" in columns


def test_onet_technology_skill_has_required_columns():
    """OnetTechnologySkill model should have tech skill columns."""
    columns = {c.name for c in OnetTechnologySkill.__table__.columns}
    assert "id" in columns
    assert "occupation_code" in columns
    assert "technology_name" in columns
    assert "hot_technology" in columns
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.modules.discovery.models'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/models/
git commit -m "feat(discovery): add O*NET data models with GWA/IWA/DWA hierarchy"
```

---

### Task 3: Discovery Session Models

**Files:**
- Create: `backend/app/modules/discovery/models/session.py`
- Modify: `backend/app/modules/discovery/models/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_session_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_session_models.py
import pytest

from app.modules.discovery.models.session import (
    DiscoverySession,
    DiscoveryUpload,
    DiscoveryRoleMapping,
    DiscoveryActivitySelection,
    DiscoveryAnalysisResult,
    AgentificationCandidate,
)


def test_discovery_session_has_required_columns():
    """DiscoverySession should track wizard state."""
    columns = {c.name for c in DiscoverySession.__table__.columns}
    assert "id" in columns
    assert "user_id" in columns
    assert "organization_id" in columns
    assert "status" in columns
    assert "current_step" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_discovery_upload_has_required_columns():
    """DiscoveryUpload should store file metadata."""
    columns = {c.name for c in DiscoveryUpload.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "file_name" in columns
    assert "file_url" in columns
    assert "row_count" in columns
    assert "column_mappings" in columns
    assert "detected_schema" in columns


def test_discovery_role_mapping_has_required_columns():
    """DiscoveryRoleMapping should link roles to O*NET."""
    columns = {c.name for c in DiscoveryRoleMapping.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "source_role" in columns
    assert "onet_code" in columns
    assert "confidence_score" in columns
    assert "user_confirmed" in columns
    assert "row_count" in columns


def test_discovery_activity_selection_has_required_columns():
    """DiscoveryActivitySelection should track DWA selections."""
    columns = {c.name for c in DiscoveryActivitySelection.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dwa_id" in columns
    assert "selected" in columns
    assert "user_modified" in columns


def test_discovery_analysis_result_has_required_columns():
    """DiscoveryAnalysisResult should store scores."""
    columns = {c.name for c in DiscoveryAnalysisResult.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dimension" in columns
    assert "dimension_value" in columns
    assert "ai_exposure_score" in columns
    assert "impact_score" in columns
    assert "complexity_score" in columns
    assert "priority_score" in columns
    assert "breakdown" in columns


def test_agentification_candidate_has_required_columns():
    """AgentificationCandidate should track roadmap items."""
    columns = {c.name for c in AgentificationCandidate.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "name" in columns
    assert "description" in columns
    assert "priority_tier" in columns
    assert "estimated_impact" in columns
    assert "selected_for_build" in columns
    assert "intake_request_id" in columns
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_models.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoverySession'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/models/
git commit -m "feat(discovery): add discovery session and candidate models"
```

---

### Task 4: Agent Memory Models

**Files:**
- Create: `backend/app/modules/discovery/models/memory.py`
- Modify: `backend/app/modules/discovery/models/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_memory_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_memory_models.py
import pytest

from app.modules.discovery.models.memory import (
    AgentMemoryWorking,
    AgentMemoryEpisodic,
    AgentMemorySemantic,
)


def test_agent_memory_working_has_required_columns():
    """AgentMemoryWorking should store session-scoped context."""
    columns = {c.name for c in AgentMemoryWorking.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "session_id" in columns
    assert "context" in columns
    assert "expires_at" in columns


def test_agent_memory_episodic_has_required_columns():
    """AgentMemoryEpisodic should store specific interactions."""
    columns = {c.name for c in AgentMemoryEpisodic.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "organization_id" in columns
    assert "episode_type" in columns
    assert "content" in columns
    assert "created_at" in columns
    assert "relevance_score" in columns


def test_agent_memory_semantic_has_required_columns():
    """AgentMemorySemantic should store learned patterns."""
    columns = {c.name for c in AgentMemorySemantic.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "organization_id" in columns
    assert "fact_type" in columns
    assert "content" in columns
    assert "confidence" in columns
    assert "occurrence_count" in columns
    assert "last_updated" in columns
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_memory_models.py -v`
Expected: FAIL with "ImportError: cannot import name 'AgentMemoryWorking'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_memory_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/models/
git commit -m "feat(discovery): add per-agent memory models (working, episodic, semantic)"
```

---

### Task 5: O*NET Database Migrations

**Files:**
- Create: `backend/migrations/versions/070_discovery_onet_tables.py`
- Create: `backend/tests/integration/discovery/__init__.py`
- Test: `backend/tests/integration/discovery/test_onet_migration.py`

**Step 1: Write the failing test**

```python
# backend/tests/integration/discovery/__init__.py
# empty file

# backend/tests/integration/discovery/test_onet_migration.py
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
async def test_onet_gwa_table_exists(db_engine):
    """onet_gwa table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_gwa" in tables


@pytest.mark.asyncio
async def test_onet_iwa_table_exists(db_engine):
    """onet_iwa table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_iwa" in tables


@pytest.mark.asyncio
async def test_onet_dwa_table_exists(db_engine):
    """onet_dwa table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "onet_dwa" in tables


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
async def test_gwa_iwa_foreign_key(db_engine):
    """onet_iwa.gwa_id should reference onet_gwa."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("onet_iwa")

        fks = await conn.run_sync(get_fks)
        gwa_fk = next((fk for fk in fks if "gwa_id" in fk["constrained_columns"]), None)
        assert gwa_fk is not None
        assert gwa_fk["referred_table"] == "onet_gwa"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/integration/discovery/test_onet_migration.py -v`
Expected: FAIL with "onet_occupations table not found"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && alembic upgrade head && python -m pytest tests/integration/discovery/test_onet_migration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/migrations/versions/070_discovery_onet_tables.py backend/tests/integration/discovery/
git commit -m "feat(discovery): add O*NET tables migration"
```

---

### Task 6: Discovery Session Migrations

**Files:**
- Create: `backend/migrations/versions/071_discovery_session_tables.py`
- Test: `backend/tests/integration/discovery/test_session_migration.py`

**Step 1: Write the failing test**

```python
# backend/tests/integration/discovery/test_session_migration.py
import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_discovery_sessions_table_exists(db_engine):
    """discovery_sessions table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_sessions" in tables


@pytest.mark.asyncio
async def test_discovery_uploads_table_exists(db_engine):
    """discovery_uploads table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_uploads" in tables


@pytest.mark.asyncio
async def test_discovery_role_mappings_table_exists(db_engine):
    """discovery_role_mappings table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_role_mappings" in tables


@pytest.mark.asyncio
async def test_discovery_activity_selections_table_exists(db_engine):
    """discovery_activity_selections table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_activity_selections" in tables


@pytest.mark.asyncio
async def test_agentification_candidates_table_exists(db_engine):
    """agentification_candidates table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agentification_candidates" in tables
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/integration/discovery/test_session_migration.py -v`
Expected: FAIL with "discovery_sessions table not found"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && alembic upgrade head && python -m pytest tests/integration/discovery/test_session_migration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/migrations/versions/071_discovery_session_tables.py backend/tests/integration/discovery/
git commit -m "feat(discovery): add discovery session tables migration"
```

---

### Task 7: Agent Memory Migrations

**Files:**
- Create: `backend/migrations/versions/072_discovery_memory_tables.py`
- Test: `backend/tests/integration/discovery/test_memory_migration.py`

**Step 1: Write the failing test**

```python
# backend/tests/integration/discovery/test_memory_migration.py
import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_agent_memory_working_table_exists(db_engine):
    """agent_memory_working table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_working" in tables


@pytest.mark.asyncio
async def test_agent_memory_episodic_table_exists(db_engine):
    """agent_memory_episodic table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_episodic" in tables


@pytest.mark.asyncio
async def test_agent_memory_semantic_table_exists(db_engine):
    """agent_memory_semantic table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_semantic" in tables
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/integration/discovery/test_memory_migration.py -v`
Expected: FAIL with "agent_memory_working table not found"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && alembic upgrade head && python -m pytest tests/integration/discovery/test_memory_migration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/migrations/versions/072_discovery_memory_tables.py backend/tests/integration/discovery/
git commit -m "feat(discovery): add agent memory tables migration"
```

---

### Task 8: Pew Research GWA Seed Data

**Files:**
- Create: `backend/migrations/versions/073_discovery_gwa_seed.py`
- Test: `backend/tests/integration/discovery/test_gwa_seed.py`

**Step 1: Write the failing test**

```python
# backend/tests/integration/discovery/test_gwa_seed.py
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_gwa_seed_data_populated(db_engine):
    """GWA table should have 41 records with AI exposure scores."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM onet_gwa"))
        count = result.scalar()
        assert count == 41


@pytest.mark.asyncio
async def test_gwa_has_ai_exposure_scores(db_engine):
    """Each GWA should have an ai_exposure_score between 0 and 1."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT id, ai_exposure_score FROM onet_gwa WHERE ai_exposure_score IS NULL OR ai_exposure_score < 0 OR ai_exposure_score > 1"
        ))
        invalid_rows = result.fetchall()
        assert len(invalid_rows) == 0, f"Invalid GWA scores: {invalid_rows}"


@pytest.mark.asyncio
async def test_gwa_getting_information_high_score(db_engine):
    """'Getting Information' GWA should have high AI exposure."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT ai_exposure_score FROM onet_gwa WHERE id = '4.A.1.a.1'"
        ))
        score = result.scalar()
        assert score is not None
        assert score >= 0.8  # High exposure activity
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/integration/discovery/test_gwa_seed.py -v`
Expected: FAIL with count != 41

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

Reference: See Appendix in design document for full GWA list with Pew Research AI exposure scores.

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && alembic upgrade head && python -m pytest tests/integration/discovery/test_gwa_seed.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/migrations/versions/073_discovery_gwa_seed.py backend/tests/integration/discovery/
git commit -m "feat(discovery): seed GWA with Pew Research AI exposure scores"
```

---
## Part 2: O*NET API Integration (Tasks 9-14)

### Task 9: O*NET API Client

**Files:**
- Create: `backend/app/modules/discovery/services/__init__.py`
- Create: `backend/app/modules/discovery/services/onet_client.py`
- Test: `backend/tests/unit/modules/discovery/test_onet_client.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_onet_client.py
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.modules.discovery.services.onet_client import OnetApiClient


@pytest.fixture
def onet_client():
    return OnetApiClient(api_key="test_key")


def test_onet_client_init():
    """OnetApiClient should initialize with API key."""
    client = OnetApiClient(api_key="my_key")
    assert client.api_key == "my_key"
    assert client.base_url == "https://services.onetcenter.org/ws/"


def test_onet_client_auth_header(onet_client):
    """OnetApiClient should create basic auth header."""
    auth = onet_client._get_auth()
    assert auth is not None


@pytest.mark.asyncio
async def test_search_occupations(onet_client):
    """Should search O*NET occupations by keyword."""
    mock_response = {
        "occupation": [
            {"code": "15-1252.00", "title": "Software Developers"},
            {"code": "15-1251.00", "title": "Computer Programmers"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        results = await onet_client.search_occupations("software")

        assert len(results) == 2
        assert results[0]["code"] == "15-1252.00"


@pytest.mark.asyncio
async def test_get_occupation_tasks(onet_client):
    """Should fetch tasks for an occupation."""
    mock_response = {
        "task": [
            {"id": "1", "statement": "Analyze user needs"},
            {"id": "2", "statement": "Write code"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        tasks = await onet_client.get_occupation_tasks("15-1252.00")

        assert len(tasks) == 2


@pytest.mark.asyncio
async def test_get_work_activities(onet_client):
    """Should fetch work activities for an occupation."""
    mock_response = {
        "element": [
            {"id": "4.A.1.a.1", "name": "Getting Information"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        activities = await onet_client.get_work_activities("15-1252.00")

        assert len(activities) >= 1


def test_rate_limiting(onet_client):
    """Should respect rate limits (10 req/sec)."""
    assert onet_client.rate_limit == 10
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_client.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetApiClient'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/
git commit -m "feat(discovery): add O*NET API client with rate limiting"
```

---

### Task 10: O*NET Occupation Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/__init__.py`
- Create: `backend/app/modules/discovery/repositories/onet_repository.py`
- Test: `backend/tests/unit/modules/discovery/test_onet_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_onet_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.onet_repository import OnetOccupationRepository


@pytest.mark.asyncio
async def test_create_occupation(db_session):
    """Should create an O*NET occupation record."""
    repo = OnetOccupationRepository(db_session)

    occupation = await repo.create(
        code="15-1252.00",
        title="Software Developers",
        description="Develop applications"
    )

    assert occupation.code == "15-1252.00"
    assert occupation.title == "Software Developers"


@pytest.mark.asyncio
async def test_get_by_code(db_session):
    """Should retrieve occupation by code."""
    repo = OnetOccupationRepository(db_session)

    await repo.create(code="15-1252.00", title="Software Developers")

    result = await repo.get_by_code("15-1252.00")
    assert result is not None
    assert result.title == "Software Developers"


@pytest.mark.asyncio
async def test_search_by_title(db_session):
    """Should search occupations by title keyword."""
    repo = OnetOccupationRepository(db_session)

    await repo.create(code="15-1252.00", title="Software Developers")
    await repo.create(code="43-4051.00", title="Customer Service Representatives")

    results = await repo.search("software")
    assert len(results) == 1
    assert results[0].code == "15-1252.00"


@pytest.mark.asyncio
async def test_upsert_occupation(db_session):
    """Should upsert occupation (insert or update)."""
    repo = OnetOccupationRepository(db_session)

    await repo.upsert(code="15-1252.00", title="Software Developers")
    await repo.upsert(code="15-1252.00", title="Software Developers, Applications")

    result = await repo.get_by_code("15-1252.00")
    assert result.title == "Software Developers, Applications"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetOccupationRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/
git commit -m "feat(discovery): add O*NET occupation repository with upsert"
```

---

### Task 11: O*NET Work Activity Repository

**Files:**
- Modify: `backend/app/modules/discovery/repositories/onet_repository.py`
- Test: `backend/tests/unit/modules/discovery/test_activity_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_activity_repository.py
import pytest

from app.modules.discovery.repositories.onet_repository import (
    OnetGwaRepository,
    OnetIwaRepository,
    OnetDwaRepository,
)


@pytest.mark.asyncio
async def test_get_gwa_with_exposure_score(db_session):
    """Should retrieve GWA with AI exposure score."""
    repo = OnetGwaRepository(db_session)

    gwa = await repo.get_by_id("4.A.1.a.1")
    assert gwa is not None
    assert gwa.ai_exposure_score >= 0.0
    assert gwa.ai_exposure_score <= 1.0


@pytest.mark.asyncio
async def test_get_iwas_for_gwa(db_session):
    """Should retrieve IWAs for a given GWA."""
    iwa_repo = OnetIwaRepository(db_session)

    iwas = await iwa_repo.get_by_gwa_id("4.A.1.a.1")
    assert isinstance(iwas, list)


@pytest.mark.asyncio
async def test_get_dwas_for_iwa(db_session):
    """Should retrieve DWAs for a given IWA."""
    dwa_repo = OnetDwaRepository(db_session)

    dwas = await dwa_repo.get_by_iwa_id("some_iwa_id")
    assert isinstance(dwas, list)


@pytest.mark.asyncio
async def test_dwa_inherits_gwa_score(db_session):
    """DWA without override should inherit GWA exposure score."""
    dwa_repo = OnetDwaRepository(db_session)

    dwa = await dwa_repo.get_by_id("some_dwa_id")
    if dwa and dwa.ai_exposure_override is None:
        # Should be able to get inherited score
        effective_score = await dwa_repo.get_effective_exposure_score(dwa.id)
        assert effective_score is not None


@pytest.mark.asyncio
async def test_get_dwas_for_occupation(db_session):
    """Should retrieve all DWAs associated with an occupation."""
    dwa_repo = OnetDwaRepository(db_session)

    dwas = await dwa_repo.get_by_occupation_code("15-1252.00")
    assert isinstance(dwas, list)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetGwaRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/
git commit -m "feat(discovery): add GWA/IWA/DWA repositories with hierarchy queries"
```

---

### Task 12: O*NET Sync Job Service

**Files:**
- Create: `backend/app/modules/discovery/services/onet_sync.py`
- Test: `backend/tests/unit/modules/discovery/test_onet_sync.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_onet_sync.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.discovery.services.onet_sync import OnetSyncJob


@pytest.fixture
def mock_onet_client():
    return AsyncMock()


@pytest.fixture
def mock_occupation_repo():
    return AsyncMock()


@pytest.fixture
def sync_job(mock_onet_client, mock_occupation_repo):
    return OnetSyncJob(
        onet_client=mock_onet_client,
        occupation_repo=mock_occupation_repo
    )


@pytest.mark.asyncio
async def test_sync_fetches_all_occupations(sync_job, mock_onet_client):
    """Sync should fetch all O*NET occupations."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"}
    ]

    await sync_job.sync_occupations()

    mock_onet_client.search_occupations.assert_called()


@pytest.mark.asyncio
async def test_sync_upserts_occupations(sync_job, mock_onet_client, mock_occupation_repo):
    """Sync should upsert occupations to database."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"}
    ]

    await sync_job.sync_occupations()

    mock_occupation_repo.upsert.assert_called()


@pytest.mark.asyncio
async def test_sync_handles_api_errors(sync_job, mock_onet_client):
    """Sync should handle API errors gracefully."""
    mock_onet_client.search_occupations.side_effect = Exception("API Error")

    # Should not raise, should log error
    result = await sync_job.sync_occupations()
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_sync_tracks_progress(sync_job, mock_onet_client):
    """Sync should track and report progress."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Dev1"},
        {"code": "15-1251.00", "title": "Dev2"},
    ]

    result = await sync_job.sync_occupations()

    assert "processed_count" in result
    assert result["processed_count"] == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_sync.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetSyncJob'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_sync.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/
git commit -m "feat(discovery): add O*NET sync job service"
```

---

### Task 13: O*NET Sync Scheduler

**Files:**
- Create: `backend/app/modules/discovery/jobs/__init__.py`
- Create: `backend/app/modules/discovery/jobs/scheduler.py`
- Test: `backend/tests/unit/modules/discovery/test_scheduler.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_scheduler.py
import pytest
from unittest.mock import MagicMock, patch

from app.modules.discovery.jobs.scheduler import OnetSyncScheduler


def test_scheduler_initializes():
    """Scheduler should initialize with APScheduler."""
    scheduler = OnetSyncScheduler()
    assert scheduler is not None


def test_scheduler_weekly_job_configured():
    """Scheduler should have weekly job configured for Sunday 2am UTC."""
    scheduler = OnetSyncScheduler()

    job = scheduler.get_job("onet_weekly_sync")
    assert job is not None


def test_scheduler_can_trigger_manual_sync():
    """Scheduler should allow manual sync trigger."""
    scheduler = OnetSyncScheduler()

    with patch.object(scheduler, "_run_sync") as mock_run:
        scheduler.trigger_manual_sync()
        mock_run.assert_called_once()


def test_scheduler_start_and_shutdown():
    """Scheduler should start and shutdown cleanly."""
    scheduler = OnetSyncScheduler()

    scheduler.start()
    assert scheduler.is_running()

    scheduler.shutdown()
    assert not scheduler.is_running()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scheduler.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetSyncScheduler'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/jobs/
git commit -m "feat(discovery): add O*NET weekly sync scheduler"
```

---

### Task 14: O*NET API Error Handling

**Files:**
- Modify: `backend/app/modules/discovery/services/onet_client.py`
- Create: `backend/app/modules/discovery/exceptions.py`
- Test: `backend/tests/unit/modules/discovery/test_onet_errors.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_onet_errors.py
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.modules.discovery.services.onet_client import OnetApiClient
from app.modules.discovery.exceptions import (
    OnetApiError,
    OnetRateLimitError,
    OnetNotFoundError,
)


@pytest.fixture
def onet_client():
    return OnetApiClient(api_key="test_key")


@pytest.mark.asyncio
async def test_rate_limit_error_raises_specific_exception(onet_client):
    """Should raise OnetRateLimitError on 429 response."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(OnetRateLimitError):
            await onet_client.search_occupations("test")


@pytest.mark.asyncio
async def test_not_found_error_raises_specific_exception(onet_client):
    """Should raise OnetNotFoundError on 404 response."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(OnetNotFoundError):
            await onet_client.get_occupation("99-9999.99")


@pytest.mark.asyncio
async def test_generic_api_error(onet_client):
    """Should raise OnetApiError on other HTTP errors."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(OnetApiError):
            await onet_client.search_occupations("test")


@pytest.mark.asyncio
async def test_exponential_backoff_on_rate_limit(onet_client):
    """Should implement exponential backoff on rate limit."""
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise OnetRateLimitError("Rate limited")
        return {"occupation": []}

    with patch.object(onet_client, "_get", side_effect=mock_get):
        result = await onet_client.search_occupations_with_retry("test", max_retries=3)
        assert call_count == 3
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_errors.py -v`
Expected: FAIL with "ImportError: cannot import name 'OnetApiError'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_onet_errors.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/exceptions.py backend/app/modules/discovery/services/
git commit -m "feat(discovery): add O*NET API error handling with retries"
```

---
## Part 3: Discovery Session Layer (Tasks 15-22)

### Task 15: Discovery Session Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/session_repository.py`
- Test: `backend/tests/unit/modules/discovery/test_session_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_session_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.session_repository import DiscoverySessionRepository
from app.modules.discovery.enums import SessionStatus


@pytest.mark.asyncio
async def test_create_session(db_session):
    """Should create a discovery session."""
    repo = DiscoverySessionRepository(db_session)
    user_id = uuid4()
    org_id = uuid4()

    session = await repo.create(user_id=user_id, organization_id=org_id)

    assert session.id is not None
    assert session.user_id == user_id
    assert session.status == SessionStatus.DRAFT
    assert session.current_step == 1


@pytest.mark.asyncio
async def test_get_session_by_id(db_session):
    """Should retrieve session by ID."""
    repo = DiscoverySessionRepository(db_session)
    user_id = uuid4()
    org_id = uuid4()

    created = await repo.create(user_id=user_id, organization_id=org_id)
    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id


@pytest.mark.asyncio
async def test_update_session_step(db_session):
    """Should update current step."""
    repo = DiscoverySessionRepository(db_session)
    session = await repo.create(user_id=uuid4(), organization_id=uuid4())

    updated = await repo.update_step(session.id, step=2)

    assert updated.current_step == 2


@pytest.mark.asyncio
async def test_update_session_status(db_session):
    """Should update session status."""
    repo = DiscoverySessionRepository(db_session)
    session = await repo.create(user_id=uuid4(), organization_id=uuid4())

    updated = await repo.update_status(session.id, SessionStatus.IN_PROGRESS)

    assert updated.status == SessionStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_list_sessions_for_user(db_session):
    """Should list sessions for a user."""
    repo = DiscoverySessionRepository(db_session)
    user_id = uuid4()
    org_id = uuid4()

    await repo.create(user_id=user_id, organization_id=org_id)
    await repo.create(user_id=user_id, organization_id=org_id)

    sessions = await repo.list_for_user(user_id)

    assert len(sessions) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoverySessionRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/
git commit -m "feat(discovery): add discovery session repository"
```

---
## Task 16: Discovery Upload Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/upload_repository.py`
- Modify: `backend/app/modules/discovery/repositories/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_upload_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_upload_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.upload_repository import DiscoveryUploadRepository


@pytest.mark.asyncio
async def test_create_upload(db_session):
    """Should create a discovery upload record with file metadata."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    upload = await repo.create(
        session_id=session_id,
        file_name="hr_data.xlsx",
        file_url="s3://bucket/uploads/hr_data.xlsx",
        row_count=1500,
        column_mappings={"role": "Column B", "department": "Column C"},
        detected_schema={"columns": ["A", "B", "C"], "types": ["string", "string", "string"]}
    )

    assert upload.id is not None
    assert upload.session_id == session_id
    assert upload.file_name == "hr_data.xlsx"
    assert upload.file_url == "s3://bucket/uploads/hr_data.xlsx"
    assert upload.row_count == 1500
    assert upload.column_mappings["role"] == "Column B"
    assert upload.detected_schema["columns"] == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_get_upload_by_id(db_session):
    """Should retrieve upload by ID."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    created = await repo.create(
        session_id=session_id,
        file_name="data.csv",
        file_url="s3://bucket/data.csv",
        row_count=100
    )

    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.file_name == "data.csv"


@pytest.mark.asyncio
async def test_get_uploads_by_session_id(db_session):
    """Should retrieve all uploads for a session."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    await repo.create(session_id=session_id, file_name="file1.xlsx", file_url="s3://a", row_count=10)
    await repo.create(session_id=session_id, file_name="file2.xlsx", file_url="s3://b", row_count=20)

    uploads = await repo.get_by_session_id(session_id)

    assert len(uploads) == 2
    assert {u.file_name for u in uploads} == {"file1.xlsx", "file2.xlsx"}


@pytest.mark.asyncio
async def test_update_column_mappings(db_session):
    """Should update column mappings after user confirmation."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    upload = await repo.create(
        session_id=session_id,
        file_name="data.xlsx",
        file_url="s3://bucket/data.xlsx",
        row_count=500,
        column_mappings={"role": "Column A"}
    )

    updated = await repo.update_column_mappings(
        upload.id,
        column_mappings={"role": "Column B", "department": "Column C", "geography": "Column D"}
    )

    assert updated.column_mappings["role"] == "Column B"
    assert updated.column_mappings["department"] == "Column C"
    assert updated.column_mappings["geography"] == "Column D"


@pytest.mark.asyncio
async def test_update_detected_schema(db_session):
    """Should update detected schema after parsing."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    upload = await repo.create(
        session_id=session_id,
        file_name="data.xlsx",
        file_url="s3://bucket/data.xlsx",
        row_count=500
    )

    updated = await repo.update_detected_schema(
        upload.id,
        detected_schema={
            "columns": ["Name", "Role", "Department"],
            "types": ["string", "string", "string"],
            "sample_values": [["John", "Engineer", "IT"]]
        }
    )

    assert updated.detected_schema["columns"] == ["Name", "Role", "Department"]
    assert "sample_values" in updated.detected_schema


@pytest.mark.asyncio
async def test_delete_upload(db_session):
    """Should delete upload record."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    upload = await repo.create(
        session_id=session_id,
        file_name="delete_me.xlsx",
        file_url="s3://bucket/delete_me.xlsx",
        row_count=10
    )

    await repo.delete(upload.id)

    result = await repo.get_by_id(upload.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_upload_for_session(db_session):
    """Should retrieve the most recent upload for a session."""
    repo = DiscoveryUploadRepository(db_session)
    session_id = uuid4()

    await repo.create(session_id=session_id, file_name="first.xlsx", file_url="s3://a", row_count=10)
    await repo.create(session_id=session_id, file_name="second.xlsx", file_url="s3://b", row_count=20)
    await repo.create(session_id=session_id, file_name="latest.xlsx", file_url="s3://c", row_count=30)

    latest = await repo.get_latest_for_session(session_id)

    assert latest is not None
    assert latest.file_name == "latest.xlsx"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_upload_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoveryUploadRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_upload_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/upload_repository.py backend/app/modules/discovery/repositories/__init__.py backend/tests/unit/modules/discovery/test_upload_repository.py
git commit -m "feat(discovery): add discovery upload repository for file metadata CRUD"
```

---

## Task 17: Role Mapping Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/role_mapping_repository.py`
- Modify: `backend/app/modules/discovery/repositories/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_role_mapping_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_role_mapping_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.role_mapping_repository import DiscoveryRoleMappingRepository


@pytest.mark.asyncio
async def test_create_role_mapping(db_session):
    """Should create a role to O*NET mapping record."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    mapping = await repo.create(
        session_id=session_id,
        source_role="Software Engineer",
        onet_code="15-1252.00",
        confidence_score=0.92,
        user_confirmed=False,
        row_count=45
    )

    assert mapping.id is not None
    assert mapping.session_id == session_id
    assert mapping.source_role == "Software Engineer"
    assert mapping.onet_code == "15-1252.00"
    assert mapping.confidence_score == 0.92
    assert mapping.user_confirmed is False
    assert mapping.row_count == 45


@pytest.mark.asyncio
async def test_get_role_mapping_by_id(db_session):
    """Should retrieve role mapping by ID."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    created = await repo.create(
        session_id=session_id,
        source_role="Data Analyst",
        onet_code="15-2051.00",
        confidence_score=0.88
    )

    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.source_role == "Data Analyst"


@pytest.mark.asyncio
async def test_get_mappings_by_session_id(db_session):
    """Should retrieve all role mappings for a session."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    await repo.create(session_id=session_id, source_role="Engineer", onet_code="15-1252.00")
    await repo.create(session_id=session_id, source_role="Analyst", onet_code="15-2051.00")
    await repo.create(session_id=session_id, source_role="Manager", onet_code="11-1021.00")

    mappings = await repo.get_by_session_id(session_id)

    assert len(mappings) == 3


@pytest.mark.asyncio
async def test_update_onet_code(db_session):
    """Should update O*NET code when user corrects mapping."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    mapping = await repo.create(
        session_id=session_id,
        source_role="Software Developer",
        onet_code="15-1251.00",  # Initially matched to Computer Programmers
        confidence_score=0.75
    )

    updated = await repo.update_onet_code(
        mapping.id,
        onet_code="15-1252.00",  # Corrected to Software Developers
        user_confirmed=True
    )

    assert updated.onet_code == "15-1252.00"
    assert updated.user_confirmed is True


@pytest.mark.asyncio
async def test_update_confidence_score(db_session):
    """Should update confidence score."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    mapping = await repo.create(
        session_id=session_id,
        source_role="Tech Lead",
        onet_code="15-1252.00",
        confidence_score=0.70
    )

    updated = await repo.update_confidence_score(mapping.id, confidence_score=0.95)

    assert updated.confidence_score == 0.95


@pytest.mark.asyncio
async def test_confirm_mapping(db_session):
    """Should mark mapping as user confirmed."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    mapping = await repo.create(
        session_id=session_id,
        source_role="Product Manager",
        onet_code="11-2021.00",
        user_confirmed=False
    )

    updated = await repo.confirm_mapping(mapping.id)

    assert updated.user_confirmed is True


@pytest.mark.asyncio
async def test_bulk_confirm_mappings(db_session):
    """Should bulk confirm mappings above confidence threshold."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    m1 = await repo.create(session_id=session_id, source_role="Eng", onet_code="15-1252.00", confidence_score=0.90)
    m2 = await repo.create(session_id=session_id, source_role="PM", onet_code="11-2021.00", confidence_score=0.85)
    m3 = await repo.create(session_id=session_id, source_role="Sales", onet_code="41-3031.00", confidence_score=0.70)

    confirmed_count = await repo.bulk_confirm_above_threshold(session_id, threshold=0.80)

    assert confirmed_count == 2

    mappings = await repo.get_by_session_id(session_id)
    confirmed_mappings = [m for m in mappings if m.user_confirmed]
    assert len(confirmed_mappings) == 2


@pytest.mark.asyncio
async def test_get_unconfirmed_mappings(db_session):
    """Should retrieve only unconfirmed mappings for a session."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    await repo.create(session_id=session_id, source_role="Eng", onet_code="15-1252.00", user_confirmed=True)
    await repo.create(session_id=session_id, source_role="PM", onet_code="11-2021.00", user_confirmed=False)
    await repo.create(session_id=session_id, source_role="QA", onet_code="15-1253.00", user_confirmed=False)

    unconfirmed = await repo.get_unconfirmed(session_id)

    assert len(unconfirmed) == 2


@pytest.mark.asyncio
async def test_delete_role_mapping(db_session):
    """Should delete role mapping record."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    mapping = await repo.create(
        session_id=session_id,
        source_role="Delete Me",
        onet_code="99-9999.00"
    )

    await repo.delete(mapping.id)

    result = await repo.get_by_id(mapping.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_mapping_by_source_role(db_session):
    """Should retrieve mapping by source role name within a session."""
    repo = DiscoveryRoleMappingRepository(db_session)
    session_id = uuid4()

    await repo.create(session_id=session_id, source_role="Software Engineer", onet_code="15-1252.00")

    mapping = await repo.get_by_source_role(session_id, "Software Engineer")

    assert mapping is not None
    assert mapping.onet_code == "15-1252.00"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_role_mapping_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoveryRoleMappingRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_role_mapping_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/role_mapping_repository.py backend/app/modules/discovery/repositories/__init__.py backend/tests/unit/modules/discovery/test_role_mapping_repository.py
git commit -m "feat(discovery): add role mapping repository for O*NET mapping CRUD"
```

---

## Task 18: Activity Selection Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/activity_selection_repository.py`
- Modify: `backend/app/modules/discovery/repositories/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_activity_selection_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_activity_selection_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.activity_selection_repository import DiscoveryActivitySelectionRepository


@pytest.mark.asyncio
async def test_create_activity_selection(db_session):
    """Should create a DWA selection record."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1.I01",
        selected=True,
        user_modified=False
    )

    assert selection.id is not None
    assert selection.session_id == session_id
    assert selection.role_mapping_id == role_mapping_id
    assert selection.dwa_id == "4.A.1.a.1.I01"
    assert selection.selected is True
    assert selection.user_modified is False


@pytest.mark.asyncio
async def test_get_selection_by_id(db_session):
    """Should retrieve activity selection by ID."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    created = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.2.a.1.I01",
        selected=True
    )

    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.dwa_id == "4.A.2.a.1.I01"


@pytest.mark.asyncio
async def test_get_selections_by_session_id(db_session):
    """Should retrieve all activity selections for a session."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I01", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I02", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I03", selected=False)

    selections = await repo.get_by_session_id(session_id)

    assert len(selections) == 3


@pytest.mark.asyncio
async def test_get_selections_by_role_mapping(db_session):
    """Should retrieve activity selections for a specific role mapping."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_1 = uuid4()
    role_mapping_2 = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, dwa_id="4.A.1.a.1.I01", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, dwa_id="4.A.1.a.1.I02", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_2, dwa_id="4.A.2.a.1.I01", selected=True)

    selections = await repo.get_by_role_mapping_id(role_mapping_1)

    assert len(selections) == 2


@pytest.mark.asyncio
async def test_toggle_selection(db_session):
    """Should toggle the selected state of an activity."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1.I01",
        selected=True,
        user_modified=False
    )

    toggled = await repo.toggle_selection(selection.id)

    assert toggled.selected is False
    assert toggled.user_modified is True


@pytest.mark.asyncio
async def test_update_selection(db_session):
    """Should update selection state and mark as user modified."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1.I01",
        selected=True,
        user_modified=False
    )

    updated = await repo.update_selection(selection.id, selected=False)

    assert updated.selected is False
    assert updated.user_modified is True


@pytest.mark.asyncio
async def test_bulk_create_selections(db_session):
    """Should bulk create activity selections for a role mapping."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    dwa_ids = ["4.A.1.a.1.I01", "4.A.1.a.1.I02", "4.A.1.a.1.I03", "4.A.2.a.1.I01"]

    created = await repo.bulk_create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_ids=dwa_ids,
        selected=True
    )

    assert len(created) == 4


@pytest.mark.asyncio
async def test_get_selected_activities(db_session):
    """Should retrieve only selected activities for a role mapping."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I01", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I02", selected=False)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I03", selected=True)

    selected = await repo.get_selected_for_role_mapping(role_mapping_id)

    assert len(selected) == 2


@pytest.mark.asyncio
async def test_get_user_modified_selections(db_session):
    """Should retrieve activities that user has modified."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I01", selected=True, user_modified=False)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I02", selected=False, user_modified=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I03", selected=True, user_modified=True)

    modified = await repo.get_user_modified(session_id)

    assert len(modified) == 2


@pytest.mark.asyncio
async def test_delete_selection(db_session):
    """Should delete activity selection record."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1.I01",
        selected=True
    )

    await repo.delete(selection.id)

    result = await repo.get_by_id(selection.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_by_role_mapping(db_session):
    """Should delete all selections for a role mapping."""
    repo = DiscoveryActivitySelectionRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I01", selected=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dwa_id="4.A.1.a.1.I02", selected=True)

    deleted_count = await repo.delete_by_role_mapping_id(role_mapping_id)

    assert deleted_count == 2

    selections = await repo.get_by_role_mapping_id(role_mapping_id)
    assert len(selections) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_selection_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoveryActivitySelectionRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_selection_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/activity_selection_repository.py backend/app/modules/discovery/repositories/__init__.py backend/tests/unit/modules/discovery/test_activity_selection_repository.py
git commit -m "feat(discovery): add activity selection repository for DWA selection CRUD"
```

---

## Task 19: Analysis Result Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/analysis_result_repository.py`
- Modify: `backend/app/modules/discovery/repositories/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_analysis_result_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_analysis_result_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.analysis_result_repository import DiscoveryAnalysisResultRepository
from app.modules.discovery.enums import AnalysisDimension


@pytest.mark.asyncio
async def test_create_analysis_result(db_session):
    """Should create an analysis result record with scores."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Software Engineer",
        ai_exposure_score=0.78,
        impact_score=0.85,
        complexity_score=0.45,
        priority_score=0.72,
        breakdown={
            "dwa_scores": [
                {"dwa_id": "4.A.1.a.1.I01", "score": 0.85},
                {"dwa_id": "4.A.2.a.1.I01", "score": 0.70}
            ],
            "contributing_factors": ["high_data_analysis", "moderate_automation_potential"]
        }
    )

    assert result.id is not None
    assert result.session_id == session_id
    assert result.role_mapping_id == role_mapping_id
    assert result.dimension == AnalysisDimension.ROLE
    assert result.dimension_value == "Software Engineer"
    assert result.ai_exposure_score == 0.78
    assert result.impact_score == 0.85
    assert result.complexity_score == 0.45
    assert result.priority_score == 0.72
    assert "dwa_scores" in result.breakdown


@pytest.mark.asyncio
async def test_get_analysis_result_by_id(db_session):
    """Should retrieve analysis result by ID."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    created = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.TASK,
        dimension_value="Data Analysis",
        ai_exposure_score=0.90
    )

    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.dimension_value == "Data Analysis"


@pytest.mark.asyncio
async def test_get_results_by_session_id(db_session):
    """Should retrieve all analysis results for a session."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng", ai_exposure_score=0.8)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.DEPARTMENT, dimension_value="IT", ai_exposure_score=0.7)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.GEOGRAPHY, dimension_value="US", ai_exposure_score=0.75)

    results = await repo.get_by_session_id(session_id)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_get_results_by_dimension(db_session):
    """Should retrieve analysis results filtered by dimension."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng", ai_exposure_score=0.8)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="PM", ai_exposure_score=0.6)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.DEPARTMENT, dimension_value="IT", ai_exposure_score=0.7)

    role_results = await repo.get_by_dimension(session_id, AnalysisDimension.ROLE)

    assert len(role_results) == 2


@pytest.mark.asyncio
async def test_get_results_by_role_mapping(db_session):
    """Should retrieve analysis results for a specific role mapping."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_1 = uuid4()
    role_mapping_2 = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, dimension=AnalysisDimension.ROLE, dimension_value="Eng", ai_exposure_score=0.8)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, dimension=AnalysisDimension.TASK, dimension_value="Code", ai_exposure_score=0.85)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_2, dimension=AnalysisDimension.ROLE, dimension_value="PM", ai_exposure_score=0.6)

    results = await repo.get_by_role_mapping_id(role_mapping_1)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_update_scores(db_session):
    """Should update all scores for an analysis result."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Engineer",
        ai_exposure_score=0.70,
        impact_score=0.60,
        complexity_score=0.50,
        priority_score=0.55
    )

    updated = await repo.update_scores(
        result.id,
        ai_exposure_score=0.85,
        impact_score=0.80,
        complexity_score=0.40,
        priority_score=0.75
    )

    assert updated.ai_exposure_score == 0.85
    assert updated.impact_score == 0.80
    assert updated.complexity_score == 0.40
    assert updated.priority_score == 0.75


@pytest.mark.asyncio
async def test_update_breakdown(db_session):
    """Should update breakdown JSONB for an analysis result."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Engineer",
        ai_exposure_score=0.70,
        breakdown={"initial": True}
    )

    updated = await repo.update_breakdown(
        result.id,
        breakdown={
            "dwa_scores": [{"dwa_id": "4.A.1.a.1.I01", "score": 0.90}],
            "recalculated": True
        }
    )

    assert updated.breakdown["recalculated"] is True
    assert "dwa_scores" in updated.breakdown


@pytest.mark.asyncio
async def test_get_top_by_priority_score(db_session):
    """Should retrieve top N results by priority score."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng1", ai_exposure_score=0.8, priority_score=0.90)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng2", ai_exposure_score=0.7, priority_score=0.50)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng3", ai_exposure_score=0.9, priority_score=0.85)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng4", ai_exposure_score=0.6, priority_score=0.75)

    top_results = await repo.get_top_by_priority(session_id, limit=3)

    assert len(top_results) == 3
    assert top_results[0].priority_score == 0.90
    assert top_results[1].priority_score == 0.85
    assert top_results[2].priority_score == 0.75


@pytest.mark.asyncio
async def test_delete_analysis_result(db_session):
    """Should delete analysis result record."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    result = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dimension=AnalysisDimension.ROLE,
        dimension_value="Delete Me",
        ai_exposure_score=0.5
    )

    await repo.delete(result.id)

    retrieved = await repo.get_by_id(result.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_by_session(db_session):
    """Should delete all analysis results for a session."""
    repo = DiscoveryAnalysisResultRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.ROLE, dimension_value="Eng", ai_exposure_score=0.8)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, dimension=AnalysisDimension.TASK, dimension_value="Code", ai_exposure_score=0.9)

    deleted_count = await repo.delete_by_session_id(session_id)

    assert deleted_count == 2

    results = await repo.get_by_session_id(session_id)
    assert len(results) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_analysis_result_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoveryAnalysisResultRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_analysis_result_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/analysis_result_repository.py backend/app/modules/discovery/repositories/__init__.py backend/tests/unit/modules/discovery/test_analysis_result_repository.py
git commit -m "feat(discovery): add analysis result repository for scores CRUD"
```

---

## Task 20: Agentification Candidate Repository

**Files:**
- Create: `backend/app/modules/discovery/repositories/candidate_repository.py`
- Modify: `backend/app/modules/discovery/repositories/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_candidate_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_candidate_repository.py
import pytest
from uuid import uuid4

from app.modules.discovery.repositories.candidate_repository import AgentificationCandidateRepository
from app.modules.discovery.enums import PriorityTier


@pytest.mark.asyncio
async def test_create_candidate(db_session):
    """Should create an agentification candidate record."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Data Entry Automation Agent",
        description="Automates routine data entry tasks for customer service representatives",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.85,
        selected_for_build=False
    )

    assert candidate.id is not None
    assert candidate.session_id == session_id
    assert candidate.role_mapping_id == role_mapping_id
    assert candidate.name == "Data Entry Automation Agent"
    assert candidate.description == "Automates routine data entry tasks for customer service representatives"
    assert candidate.priority_tier == PriorityTier.NOW
    assert candidate.estimated_impact == 0.85
    assert candidate.selected_for_build is False
    assert candidate.intake_request_id is None


@pytest.mark.asyncio
async def test_get_candidate_by_id(db_session):
    """Should retrieve candidate by ID."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    created = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Report Generator",
        priority_tier=PriorityTier.NEXT_QUARTER,
        estimated_impact=0.70
    )

    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.name == "Report Generator"


@pytest.mark.asyncio
async def test_get_candidates_by_session_id(db_session):
    """Should retrieve all candidates for a session."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Agent1", priority_tier=PriorityTier.NOW, estimated_impact=0.9)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Agent2", priority_tier=PriorityTier.NEXT_QUARTER, estimated_impact=0.7)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Agent3", priority_tier=PriorityTier.FUTURE, estimated_impact=0.5)

    candidates = await repo.get_by_session_id(session_id)

    assert len(candidates) == 3


@pytest.mark.asyncio
async def test_get_candidates_by_priority_tier(db_session):
    """Should retrieve candidates filtered by priority tier."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Now1", priority_tier=PriorityTier.NOW, estimated_impact=0.9)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Now2", priority_tier=PriorityTier.NOW, estimated_impact=0.85)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Later", priority_tier=PriorityTier.FUTURE, estimated_impact=0.5)

    now_candidates = await repo.get_by_priority_tier(session_id, PriorityTier.NOW)

    assert len(now_candidates) == 2


@pytest.mark.asyncio
async def test_update_priority_tier(db_session):
    """Should update priority tier when user moves candidate in roadmap."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Movable Agent",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.6
    )

    updated = await repo.update_priority_tier(candidate.id, PriorityTier.NOW)

    assert updated.priority_tier == PriorityTier.NOW


@pytest.mark.asyncio
async def test_update_details(db_session):
    """Should update candidate name and description."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Original Name",
        description="Original description",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8
    )

    updated = await repo.update_details(
        candidate.id,
        name="Updated Agent Name",
        description="Updated description with more detail"
    )

    assert updated.name == "Updated Agent Name"
    assert updated.description == "Updated description with more detail"


@pytest.mark.asyncio
async def test_select_for_build(db_session):
    """Should mark candidate as selected for build."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Build Me",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.95,
        selected_for_build=False
    )

    updated = await repo.select_for_build(candidate.id)

    assert updated.selected_for_build is True


@pytest.mark.asyncio
async def test_deselect_for_build(db_session):
    """Should deselect candidate from build."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Changed My Mind",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.80,
        selected_for_build=True
    )

    updated = await repo.deselect_for_build(candidate.id)

    assert updated.selected_for_build is False


@pytest.mark.asyncio
async def test_link_intake_request(db_session):
    """Should link candidate to an intake request after handoff."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    intake_request_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Handed Off",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.90,
        selected_for_build=True
    )

    updated = await repo.link_intake_request(candidate.id, intake_request_id)

    assert updated.intake_request_id == intake_request_id


@pytest.mark.asyncio
async def test_get_selected_for_build(db_session):
    """Should retrieve only candidates selected for build."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Build1", priority_tier=PriorityTier.NOW, estimated_impact=0.9, selected_for_build=True)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Skip", priority_tier=PriorityTier.NOW, estimated_impact=0.7, selected_for_build=False)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="Build2", priority_tier=PriorityTier.NEXT_QUARTER, estimated_impact=0.8, selected_for_build=True)

    selected = await repo.get_selected_for_build(session_id)

    assert len(selected) == 2


@pytest.mark.asyncio
async def test_get_candidates_by_role_mapping(db_session):
    """Should retrieve candidates for a specific role mapping."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_1 = uuid4()
    role_mapping_2 = uuid4()

    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, name="Agent1", priority_tier=PriorityTier.NOW, estimated_impact=0.9)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_1, name="Agent2", priority_tier=PriorityTier.NOW, estimated_impact=0.8)
    await repo.create(session_id=session_id, role_mapping_id=role_mapping_2, name="Agent3", priority_tier=PriorityTier.NOW, estimated_impact=0.7)

    candidates = await repo.get_by_role_mapping_id(role_mapping_1)

    assert len(candidates) == 2


@pytest.mark.asyncio
async def test_delete_candidate(db_session):
    """Should delete candidate record."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Delete Me",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.3
    )

    await repo.delete(candidate.id)

    result = await repo.get_by_id(candidate.id)
    assert result is None


@pytest.mark.asyncio
async def test_bulk_update_priority_tier(db_session):
    """Should bulk update priority tier for multiple candidates."""
    repo = AgentificationCandidateRepository(db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    c1 = await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="A1", priority_tier=PriorityTier.FUTURE, estimated_impact=0.7)
    c2 = await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="A2", priority_tier=PriorityTier.FUTURE, estimated_impact=0.8)
    c3 = await repo.create(session_id=session_id, role_mapping_id=role_mapping_id, name="A3", priority_tier=PriorityTier.NOW, estimated_impact=0.9)

    updated_count = await repo.bulk_update_priority_tier([c1.id, c2.id], PriorityTier.NEXT_QUARTER)

    assert updated_count == 2

    c1_updated = await repo.get_by_id(c1.id)
    c2_updated = await repo.get_by_id(c2.id)
    c3_unchanged = await repo.get_by_id(c3.id)

    assert c1_updated.priority_tier == PriorityTier.NEXT_QUARTER
    assert c2_updated.priority_tier == PriorityTier.NEXT_QUARTER
    assert c3_unchanged.priority_tier == PriorityTier.NOW
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_candidate_repository.py -v`
Expected: FAIL with "ImportError: cannot import name 'AgentificationCandidateRepository'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_candidate_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/repositories/candidate_repository.py backend/app/modules/discovery/repositories/__init__.py backend/tests/unit/modules/discovery/test_candidate_repository.py
git commit -m "feat(discovery): add agentification candidate repository for roadmap items CRUD"
```

---

## Task 21: Discovery Session Service

**Files:**
- Create: `backend/app/modules/discovery/services/session_service.py`
- Modify: `backend/app/modules/discovery/services/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_session_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_session_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.discovery.services.session_service import DiscoverySessionService
from app.modules.discovery.enums import SessionStatus, AnalysisDimension, PriorityTier


@pytest.fixture
def mock_session_repo():
    return AsyncMock()


@pytest.fixture
def mock_upload_repo():
    return AsyncMock()


@pytest.fixture
def mock_role_mapping_repo():
    return AsyncMock()


@pytest.fixture
def mock_activity_selection_repo():
    return AsyncMock()


@pytest.fixture
def mock_analysis_result_repo():
    return AsyncMock()


@pytest.fixture
def mock_candidate_repo():
    return AsyncMock()


@pytest.fixture
def session_service(
    mock_session_repo,
    mock_upload_repo,
    mock_role_mapping_repo,
    mock_activity_selection_repo,
    mock_analysis_result_repo,
    mock_candidate_repo
):
    return DiscoverySessionService(
        session_repo=mock_session_repo,
        upload_repo=mock_upload_repo,
        role_mapping_repo=mock_role_mapping_repo,
        activity_selection_repo=mock_activity_selection_repo,
        analysis_result_repo=mock_analysis_result_repo,
        candidate_repo=mock_candidate_repo
    )


@pytest.mark.asyncio
async def test_create_session(session_service, mock_session_repo):
    """Should create a new discovery session."""
    user_id = uuid4()
    org_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.user_id = user_id
    mock_session.organization_id = org_id
    mock_session.status = SessionStatus.DRAFT
    mock_session.current_step = 1
    mock_session_repo.create.return_value = mock_session

    result = await session_service.create_session(user_id=user_id, organization_id=org_id)

    mock_session_repo.create.assert_called_once_with(user_id=user_id, organization_id=org_id)
    assert result.status == SessionStatus.DRAFT
    assert result.current_step == 1


@pytest.mark.asyncio
async def test_get_session(session_service, mock_session_repo):
    """Should retrieve a session by ID."""
    session_id = uuid4()
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session_repo.get_by_id.return_value = mock_session

    result = await session_service.get_session(session_id)

    mock_session_repo.get_by_id.assert_called_once_with(session_id)
    assert result.id == session_id


@pytest.mark.asyncio
async def test_advance_step(session_service, mock_session_repo):
    """Should advance session to next step."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 1
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.current_step = 2
    mock_session_repo.update_step.return_value = updated_session

    result = await session_service.advance_step(session_id)

    mock_session_repo.update_step.assert_called_once_with(session_id, step=2)
    assert result.current_step == 2


@pytest.mark.asyncio
async def test_advance_step_updates_status_to_in_progress(session_service, mock_session_repo):
    """Should update status to IN_PROGRESS when advancing from step 1."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 1
    mock_session.status = SessionStatus.DRAFT
    mock_session_repo.get_by_id.return_value = mock_session

    await session_service.advance_step(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.IN_PROGRESS)


@pytest.mark.asyncio
async def test_go_to_step(session_service, mock_session_repo):
    """Should allow going back to a previous step."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 4
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.current_step = 2
    mock_session_repo.update_step.return_value = updated_session

    result = await session_service.go_to_step(session_id, step=2)

    mock_session_repo.update_step.assert_called_once_with(session_id, step=2)
    assert result.current_step == 2


@pytest.mark.asyncio
async def test_go_to_step_rejects_invalid_step(session_service, mock_session_repo):
    """Should reject invalid step numbers."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 2
    mock_session_repo.get_by_id.return_value = mock_session

    with pytest.raises(ValueError, match="Step must be between 1 and 5"):
        await session_service.go_to_step(session_id, step=6)


@pytest.mark.asyncio
async def test_complete_session(session_service, mock_session_repo):
    """Should mark session as completed."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 5
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.status = SessionStatus.COMPLETED
    mock_session_repo.update_status.return_value = updated_session

    result = await session_service.complete_session(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.COMPLETED)
    assert result.status == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_archive_session(session_service, mock_session_repo):
    """Should archive a session."""
    session_id = uuid4()

    updated_session = MagicMock()
    updated_session.status = SessionStatus.ARCHIVED
    mock_session_repo.update_status.return_value = updated_session

    result = await session_service.archive_session(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.ARCHIVED)
    assert result.status == SessionStatus.ARCHIVED


@pytest.mark.asyncio
async def test_get_session_summary(session_service, mock_session_repo, mock_upload_repo, mock_role_mapping_repo, mock_candidate_repo):
    """Should return a summary of the session state."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.current_step = 3
    mock_session.status = SessionStatus.IN_PROGRESS
    mock_session_repo.get_by_id.return_value = mock_session

    mock_upload = MagicMock()
    mock_upload.row_count = 1500
    mock_upload_repo.get_latest_for_session.return_value = mock_upload

    mock_role_mapping_repo.get_by_session_id.return_value = [MagicMock(), MagicMock(), MagicMock()]

    mock_candidate_repo.get_by_session_id.return_value = [MagicMock(), MagicMock()]

    summary = await session_service.get_session_summary(session_id)

    assert summary["session_id"] == session_id
    assert summary["current_step"] == 3
    assert summary["status"] == SessionStatus.IN_PROGRESS
    assert summary["row_count"] == 1500
    assert summary["role_mapping_count"] == 3
    assert summary["candidate_count"] == 2


@pytest.mark.asyncio
async def test_register_upload(session_service, mock_upload_repo, mock_session_repo):
    """Should register an upload and update session status."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.status = SessionStatus.DRAFT
    mock_session_repo.get_by_id.return_value = mock_session

    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload_repo.create.return_value = mock_upload

    result = await session_service.register_upload(
        session_id=session_id,
        file_name="hr_data.xlsx",
        file_url="s3://bucket/hr_data.xlsx",
        row_count=1500,
        detected_schema={"columns": ["A", "B"]}
    )

    mock_upload_repo.create.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_create_role_mapping(session_service, mock_role_mapping_repo):
    """Should create a role mapping via the service."""
    session_id = uuid4()

    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Software Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_role_mapping_repo.create.return_value = mock_mapping

    result = await session_service.create_role_mapping(
        session_id=session_id,
        source_role="Software Engineer",
        onet_code="15-1252.00",
        confidence_score=0.92,
        row_count=45
    )

    mock_role_mapping_repo.create.assert_called_once()
    assert result.source_role == "Software Engineer"


@pytest.mark.asyncio
async def test_bulk_create_activity_selections(session_service, mock_activity_selection_repo):
    """Should bulk create activity selections for a role mapping."""
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_ids = ["4.A.1.a.1.I01", "4.A.1.a.1.I02", "4.A.2.a.1.I01"]

    mock_selections = [MagicMock() for _ in dwa_ids]
    mock_activity_selection_repo.bulk_create.return_value = mock_selections

    result = await session_service.bulk_create_activity_selections(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_ids=dwa_ids
    )

    mock_activity_selection_repo.bulk_create.assert_called_once()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_store_analysis_results(session_service, mock_analysis_result_repo):
    """Should store analysis results for multiple dimensions."""
    session_id = uuid4()
    role_mapping_id = uuid4()

    results_data = [
        {"dimension": AnalysisDimension.ROLE, "dimension_value": "Engineer", "ai_exposure_score": 0.85, "priority_score": 0.80},
        {"dimension": AnalysisDimension.DEPARTMENT, "dimension_value": "IT", "ai_exposure_score": 0.78, "priority_score": 0.75},
    ]

    mock_results = [MagicMock() for _ in results_data]
    mock_analysis_result_repo.create.side_effect = mock_results

    result = await session_service.store_analysis_results(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        results=results_data
    )

    assert mock_analysis_result_repo.create.call_count == 2
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_candidate(session_service, mock_candidate_repo):
    """Should create an agentification candidate."""
    session_id = uuid4()
    role_mapping_id = uuid4()

    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Data Entry Agent"
    mock_candidate.priority_tier = PriorityTier.NOW
    mock_candidate_repo.create.return_value = mock_candidate

    result = await session_service.create_candidate(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Data Entry Agent",
        description="Automates data entry tasks",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.85
    )

    mock_candidate_repo.create.assert_called_once()
    assert result.name == "Data Entry Agent"


@pytest.mark.asyncio
async def test_select_candidates_for_build(session_service, mock_candidate_repo):
    """Should select multiple candidates for build."""
    candidate_ids = [uuid4(), uuid4(), uuid4()]

    mock_candidates = [MagicMock(selected_for_build=True) for _ in candidate_ids]
    mock_candidate_repo.select_for_build.side_effect = mock_candidates

    result = await session_service.select_candidates_for_build(candidate_ids)

    assert mock_candidate_repo.select_for_build.call_count == 3
    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_handoff_bundle(session_service, mock_session_repo, mock_candidate_repo, mock_role_mapping_repo, mock_analysis_result_repo):
    """Should prepare a handoff bundle for intake."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session_repo.get_by_id.return_value = mock_session

    mock_candidates = [
        MagicMock(id=uuid4(), name="Agent1", selected_for_build=True, role_mapping_id=uuid4()),
        MagicMock(id=uuid4(), name="Agent2", selected_for_build=True, role_mapping_id=uuid4()),
    ]
    mock_candidate_repo.get_selected_for_build.return_value = mock_candidates

    mock_role_mapping_repo.get_by_id.return_value = MagicMock(source_role="Engineer", onet_code="15-1252.00")
    mock_analysis_result_repo.get_by_role_mapping_id.return_value = [MagicMock(ai_exposure_score=0.85)]

    bundle = await session_service.get_handoff_bundle(session_id)

    assert "session_id" in bundle
    assert "candidates" in bundle
    assert len(bundle["candidates"]) == 2


@pytest.mark.asyncio
async def test_list_user_sessions(session_service, mock_session_repo):
    """Should list all sessions for a user."""
    user_id = uuid4()

    mock_sessions = [MagicMock(), MagicMock()]
    mock_session_repo.list_for_user.return_value = mock_sessions

    result = await session_service.list_user_sessions(user_id)

    mock_session_repo.list_for_user.assert_called_once_with(user_id)
    assert len(result) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_service.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoverySessionService'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_session_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/session_service.py backend/app/modules/discovery/services/__init__.py backend/tests/unit/modules/discovery/test_session_service.py
git commit -m "feat(discovery): add discovery session service to orchestrate repositories"
```

---

## Task 22: File Upload Service

**Files:**
- Create: `backend/app/modules/discovery/services/file_upload_service.py`
- Modify: `backend/app/modules/discovery/services/__init__.py`
- Test: `backend/tests/unit/modules/discovery/test_file_upload_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_file_upload_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import io

from app.modules.discovery.services.file_upload_service import FileUploadService


@pytest.fixture
def mock_s3_client():
    return AsyncMock()


@pytest.fixture
def mock_upload_repo():
    return AsyncMock()


@pytest.fixture
def file_upload_service(mock_s3_client, mock_upload_repo):
    return FileUploadService(
        s3_client=mock_s3_client,
        upload_repo=mock_upload_repo,
        bucket_name="discovery-uploads"
    )


@pytest.mark.asyncio
async def test_upload_file_to_s3(file_upload_service, mock_s3_client):
    """Should upload file to S3 and return URL."""
    session_id = uuid4()
    file_content = b"col1,col2,col3\nval1,val2,val3"
    file_name = "test_data.csv"

    mock_s3_client.upload_fileobj.return_value = None

    result = await file_upload_service.upload_file(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    mock_s3_client.upload_fileobj.assert_called_once()
    assert "s3://" in result["file_url"] or "test_data.csv" in result["file_url"]


@pytest.mark.asyncio
async def test_upload_generates_unique_key(file_upload_service, mock_s3_client):
    """Should generate unique S3 key with session ID prefix."""
    session_id = uuid4()
    file_content = b"data"
    file_name = "hr_data.xlsx"

    await file_upload_service.upload_file(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    call_args = mock_s3_client.upload_fileobj.call_args
    s3_key = call_args[1].get("Key") or call_args[0][1] if len(call_args[0]) > 1 else None

    # The S3 key should contain the session ID for organization
    assert str(session_id) in str(call_args) or "hr_data" in str(call_args)


@pytest.mark.asyncio
async def test_parse_csv_file(file_upload_service):
    """Should parse CSV file and detect schema."""
    file_content = b"Name,Role,Department,Location\nJohn,Engineer,IT,NYC\nJane,Manager,HR,LA\nBob,Analyst,Finance,CHI"

    result = await file_upload_service.parse_file(
        file_name="test.csv",
        file_content=file_content
    )

    assert result["row_count"] == 3
    assert "Name" in result["detected_schema"]["columns"]
    assert "Role" in result["detected_schema"]["columns"]
    assert "Department" in result["detected_schema"]["columns"]
    assert len(result["detected_schema"]["columns"]) == 4


@pytest.mark.asyncio
async def test_parse_xlsx_file(file_upload_service):
    """Should parse XLSX file and detect schema."""
    # Create a minimal XLSX-like structure for testing
    # In real implementation, use openpyxl to create actual XLSX
    with patch.object(file_upload_service, "_parse_xlsx") as mock_parse:
        mock_parse.return_value = {
            "row_count": 100,
            "detected_schema": {
                "columns": ["Employee ID", "Job Title", "Department"],
                "types": ["integer", "string", "string"],
                "sample_values": [["1001", "Software Engineer", "Engineering"]]
            }
        }

        result = await file_upload_service.parse_file(
            file_name="employees.xlsx",
            file_content=b"fake xlsx content"
        )

        assert result["row_count"] == 100
        assert "Job Title" in result["detected_schema"]["columns"]


@pytest.mark.asyncio
async def test_detect_column_types(file_upload_service):
    """Should detect column data types from content."""
    file_content = b"ID,Name,Salary,Active\n1,John,50000,true\n2,Jane,60000,false"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    # Should detect types based on content
    assert "types" in result["detected_schema"]


@pytest.mark.asyncio
async def test_extract_sample_values(file_upload_service):
    """Should extract sample values for preview."""
    file_content = b"Name,Role\nAlice,Engineer\nBob,Manager\nCarol,Analyst\nDave,Designer\nEve,Director"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    # Should include sample values for preview (first 5 rows)
    assert "sample_values" in result["detected_schema"]
    assert len(result["detected_schema"]["sample_values"]) <= 5


@pytest.mark.asyncio
async def test_suggest_column_mappings(file_upload_service):
    """Should suggest column mappings based on column names."""
    file_content = b"Employee Name,Job Title,Dept,Office Location\nJohn,Engineer,IT,NYC"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    suggestions = await file_upload_service.suggest_column_mappings(result["detected_schema"])

    # Should suggest role column based on "Job Title"
    assert "role" in suggestions
    assert suggestions["role"] == "Job Title"

    # Should suggest department column based on "Dept"
    assert "department" in suggestions
    assert suggestions["department"] == "Dept"


@pytest.mark.asyncio
async def test_suggest_mappings_handles_variations(file_upload_service):
    """Should handle common column name variations."""
    # Test various common names for role column
    test_cases = [
        (b"Position,Name\nEng,John", "Position"),
        (b"Title,Name\nEng,John", "Title"),
        (b"Job,Name\nEng,John", "Job"),
        (b"Occupation,Name\nEng,John", "Occupation"),
    ]

    for file_content, expected_role_col in test_cases:
        result = await file_upload_service.parse_file(
            file_name="data.csv",
            file_content=file_content
        )
        suggestions = await file_upload_service.suggest_column_mappings(result["detected_schema"])

        assert suggestions.get("role") == expected_role_col, f"Expected {expected_role_col} for role"


@pytest.mark.asyncio
async def test_register_upload_with_parsed_data(file_upload_service, mock_upload_repo, mock_s3_client):
    """Should upload, parse, and register in one operation."""
    session_id = uuid4()
    file_content = b"Name,Role,Dept\nJohn,Engineer,IT\nJane,Manager,HR"
    file_name = "employees.csv"

    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload_repo.create.return_value = mock_upload

    result = await file_upload_service.upload_and_register(
        session_id=session_id,
        file_name=file_name,
        file_content=file_content
    )

    mock_s3_client.upload_fileobj.assert_called_once()
    mock_upload_repo.create.assert_called_once()
    assert "upload_id" in result
    assert "parsed_data" in result


@pytest.mark.asyncio
async def test_reject_unsupported_file_type(file_upload_service):
    """Should reject unsupported file types."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        await file_upload_service.parse_file(
            file_name="data.pdf",
            file_content=b"pdf content"
        )


@pytest.mark.asyncio
async def test_handle_empty_file(file_upload_service):
    """Should handle empty files gracefully."""
    with pytest.raises(ValueError, match="File is empty"):
        await file_upload_service.parse_file(
            file_name="empty.csv",
            file_content=b""
        )


@pytest.mark.asyncio
async def test_handle_malformed_csv(file_upload_service):
    """Should handle malformed CSV with appropriate error."""
    # CSV with inconsistent column counts
    file_content = b"A,B,C\n1,2\n3,4,5,6"

    # Should still parse but may have warnings
    result = await file_upload_service.parse_file(
        file_name="malformed.csv",
        file_content=file_content
    )

    # Should return what it can parse
    assert "detected_schema" in result


@pytest.mark.asyncio
async def test_delete_file_from_s3(file_upload_service, mock_s3_client, mock_upload_repo):
    """Should delete file from S3 and remove upload record."""
    upload_id = uuid4()
    file_url = "s3://discovery-uploads/sessions/abc/file.csv"

    mock_upload = MagicMock()
    mock_upload.id = upload_id
    mock_upload.file_url = file_url
    mock_upload_repo.get_by_id.return_value = mock_upload

    await file_upload_service.delete_upload(upload_id)

    mock_s3_client.delete_object.assert_called_once()
    mock_upload_repo.delete.assert_called_once_with(upload_id)


@pytest.mark.asyncio
async def test_get_download_url(file_upload_service, mock_s3_client):
    """Should generate presigned download URL."""
    file_url = "s3://discovery-uploads/sessions/abc/file.csv"

    mock_s3_client.generate_presigned_url.return_value = "https://signed-url.example.com/file.csv"

    result = await file_upload_service.get_download_url(file_url, expires_in=3600)

    mock_s3_client.generate_presigned_url.assert_called_once()
    assert "https://" in result


@pytest.mark.asyncio
async def test_extract_unique_roles(file_upload_service):
    """Should extract unique roles from parsed file data."""
    file_content = b"Name,Role\nJohn,Engineer\nJane,Manager\nBob,Engineer\nAlice,Analyst\nCarol,Manager"

    result = await file_upload_service.parse_file(
        file_name="data.csv",
        file_content=file_content
    )

    column_mappings = {"role": "Role"}
    unique_roles = await file_upload_service.extract_unique_values(
        file_content=file_content,
        file_name="data.csv",
        column_name=column_mappings["role"]
    )

    assert len(unique_roles) == 3
    assert set(unique_roles.keys()) == {"Engineer", "Manager", "Analyst"}
    assert unique_roles["Engineer"] == 2  # count
    assert unique_roles["Manager"] == 2


@pytest.mark.asyncio
async def test_validate_file_size(file_upload_service):
    """Should reject files exceeding size limit."""
    # 100MB limit
    large_content = b"x" * (101 * 1024 * 1024)

    with pytest.raises(ValueError, match="File size exceeds"):
        await file_upload_service.validate_file(
            file_name="large.csv",
            file_content=large_content
        )


@pytest.mark.asyncio
async def test_validate_row_count(file_upload_service):
    """Should warn when row count exceeds threshold."""
    # Create content with many rows
    header = b"Col1,Col2\n"
    rows = b"\n".join([f"val{i},val{i}".encode() for i in range(100001)])
    file_content = header + rows

    result = await file_upload_service.parse_file(
        file_name="large.csv",
        file_content=file_content
    )

    # Should include a warning for large files
    assert result["row_count"] > 100000
    # Implementation may include warnings field
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_file_upload_service.py -v`
Expected: FAIL with "ImportError: cannot import name 'FileUploadService'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_file_upload_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/file_upload_service.py backend/app/modules/discovery/services/__init__.py backend/tests/unit/modules/discovery/test_file_upload_service.py
git commit -m "feat(discovery): add file upload service with S3 integration and CSV/XLSX parsing"
```

---

## Summary

Tasks 16-22 implement the Discovery Session Layer with the following components:

| Task | Component | Description |
|------|-----------|-------------|
| 16 | DiscoveryUploadRepository | File metadata CRUD for uploaded HR data files |
| 17 | DiscoveryRoleMappingRepository | Role to O*NET occupation mapping CRUD |
| 18 | DiscoveryActivitySelectionRepository | DWA selection tracking CRUD |
| 19 | DiscoveryAnalysisResultRepository | Scores and breakdown storage CRUD |
| 20 | AgentificationCandidateRepository | Roadmap items and priority tier CRUD |
| 21 | DiscoverySessionService | Orchestration layer coordinating all repositories |
| 22 | FileUploadService | S3 integration, file parsing, schema detection |

Each repository follows the standard pattern:
- Create, Get by ID, Get by session/parent ID
- Update specific fields
- Delete
- Specialized queries for business logic

The service layer (Tasks 21-22) provides:
- Higher-level business operations
- Transaction coordination
- Cross-repository workflows
- External service integration (S3)

**Next:** Continue with Part 4: Scoring Engine (Tasks 23-27)
## Part 4: Scoring Engine (Tasks 23-27)

### Task 23: AI Exposure Score Calculator

**Files:**
- Create: `backend/app/modules/discovery/services/scoring.py`
- Test: `backend/tests/unit/modules/discovery/test_scoring.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_scoring.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


def test_calculate_exposure_from_dwas(scoring_service):
    """Should calculate exposure score from selected DWAs."""
    dwas = [
        MagicMock(ai_exposure_override=0.9),
        MagicMock(ai_exposure_override=0.7),
        MagicMock(ai_exposure_override=None, iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.5))),
    ]

    score = scoring_service.calculate_exposure_score(dwas)

    # (0.9 + 0.7 + 0.5) / 3 = 0.7
    assert score == pytest.approx(0.7, rel=0.01)


def test_dwa_inherits_gwa_score_when_no_override(scoring_service):
    """DWA without override should use GWA score."""
    dwa = MagicMock(
        ai_exposure_override=None,
        iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.85))
    )

    score = scoring_service.get_effective_dwa_score(dwa)

    assert score == 0.85


def test_dwa_uses_override_when_present(scoring_service):
    """DWA with override should use override score."""
    dwa = MagicMock(
        ai_exposure_override=0.95,
        iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.50))
    )

    score = scoring_service.get_effective_dwa_score(dwa)

    assert score == 0.95


def test_empty_dwas_returns_zero(scoring_service):
    """Empty DWA list should return 0."""
    score = scoring_service.calculate_exposure_score([])
    assert score == 0.0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scoring.py -v`
Expected: FAIL with "ImportError: cannot import name 'ScoringService'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scoring.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/scoring.py
git commit -m "feat(discovery): add AI exposure scoring with GWA inheritance"
```

---
## Task 24: Impact Score Calculator

**Files:**
- Modify: `backend/app/modules/discovery/services/scoring.py`
- Test: `backend/tests/unit/modules/discovery/test_impact_scoring.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_impact_scoring.py
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


class TestImpactScoreCalculator:
    """Tests for impact score calculation: impact = role_count * exposure."""

    def test_impact_score_basic_calculation(self, scoring_service):
        """Impact should be role_count * exposure_score."""
        role_mapping = MagicMock(
            row_count=100,  # 100 employees in this role
        )
        exposure_score = 0.8

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=exposure_score
        )

        # 100 * 0.8 = 80, normalized to 0-1 scale
        # Assuming max role count of 1000 for normalization
        assert impact == pytest.approx(0.08, rel=0.01)

    def test_impact_score_high_headcount(self, scoring_service):
        """High headcount should produce higher impact."""
        role_mapping_low = MagicMock(row_count=10)
        role_mapping_high = MagicMock(row_count=500)
        exposure = 0.7

        impact_low = scoring_service.calculate_impact_score(
            role_mapping=role_mapping_low,
            exposure_score=exposure
        )
        impact_high = scoring_service.calculate_impact_score(
            role_mapping=role_mapping_high,
            exposure_score=exposure
        )

        assert impact_high > impact_low

    def test_impact_score_high_exposure(self, scoring_service):
        """High exposure should produce higher impact."""
        role_mapping = MagicMock(row_count=100)

        impact_low = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.2
        )
        impact_high = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.9
        )

        assert impact_high > impact_low

    def test_impact_score_zero_headcount(self, scoring_service):
        """Zero headcount should return zero impact."""
        role_mapping = MagicMock(row_count=0)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.9
        )

        assert impact == 0.0

    def test_impact_score_zero_exposure(self, scoring_service):
        """Zero exposure should return zero impact."""
        role_mapping = MagicMock(row_count=100)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.0
        )

        assert impact == 0.0

    def test_impact_score_normalized_to_unit_interval(self, scoring_service):
        """Impact score should always be between 0 and 1."""
        role_mapping = MagicMock(row_count=5000)  # Very high headcount

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=1.0
        )

        assert 0.0 <= impact <= 1.0

    def test_impact_score_with_custom_max_headcount(self, scoring_service):
        """Should allow custom max headcount for normalization."""
        role_mapping = MagicMock(row_count=500)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=1.0,
            max_headcount=500  # Custom max
        )

        assert impact == pytest.approx(1.0, rel=0.01)

    def test_calculate_impact_for_session(self, scoring_service):
        """Should calculate impact scores for all role mappings in a session."""
        role_mappings = [
            MagicMock(id="role-1", row_count=100),
            MagicMock(id="role-2", row_count=200),
            MagicMock(id="role-3", row_count=50),
        ]
        exposure_scores = {
            "role-1": 0.8,
            "role-2": 0.6,
            "role-3": 0.9,
        }

        impacts = scoring_service.calculate_impact_scores_for_session(
            role_mappings=role_mappings,
            exposure_scores=exposure_scores
        )

        assert len(impacts) == 3
        assert "role-1" in impacts
        assert "role-2" in impacts
        assert "role-3" in impacts
        # role-2 has highest raw impact (200 * 0.6 = 120)
        # role-1 has second (100 * 0.8 = 80)
        # role-3 has lowest (50 * 0.9 = 45)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_impact_scoring.py -v`
Expected: FAIL with "AttributeError: 'ScoringService' object has no attribute 'calculate_impact_score'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_impact_scoring.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/scoring.py backend/tests/unit/modules/discovery/test_impact_scoring.py
git commit -m "feat(discovery): add impact score calculator (role_count * exposure)"
```

---

## Task 25: Priority Score Calculator

**Files:**
- Modify: `backend/app/modules/discovery/services/scoring.py`
- Test: `backend/tests/unit/modules/discovery/test_priority_scoring.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_priority_scoring.py
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


class TestPriorityScoreCalculator:
    """Tests for priority score: priority = (exposure * 0.4) + (impact * 0.4) + ((1 - complexity) * 0.2)."""

    def test_priority_score_formula(self, scoring_service):
        """Priority should follow weighted formula."""
        exposure = 0.8
        impact = 0.6
        complexity = 0.3

        priority = scoring_service.calculate_priority_score(
            exposure=exposure,
            impact=impact,
            complexity=complexity
        )

        # (0.8 * 0.4) + (0.6 * 0.4) + ((1 - 0.3) * 0.2)
        # = 0.32 + 0.24 + 0.14
        # = 0.70
        assert priority == pytest.approx(0.70, rel=0.01)

    def test_priority_high_exposure_high_impact_low_complexity(self, scoring_service):
        """Best case: high exposure, high impact, low complexity should give max priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=1.0,
            complexity=0.0
        )

        # (1.0 * 0.4) + (1.0 * 0.4) + ((1 - 0.0) * 0.2) = 0.4 + 0.4 + 0.2 = 1.0
        assert priority == pytest.approx(1.0, rel=0.01)

    def test_priority_low_exposure_low_impact_high_complexity(self, scoring_service):
        """Worst case: low exposure, low impact, high complexity should give min priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=0.0,
            complexity=1.0
        )

        # (0.0 * 0.4) + (0.0 * 0.4) + ((1 - 1.0) * 0.2) = 0 + 0 + 0 = 0.0
        assert priority == pytest.approx(0.0, rel=0.01)

    def test_priority_exposure_weight_is_40_percent(self, scoring_service):
        """Exposure should contribute 40% to priority."""
        # Only exposure contributes
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=0.0,
            complexity=1.0  # complexity=1 means (1-1)*0.2 = 0
        )

        assert priority == pytest.approx(0.4, rel=0.01)

    def test_priority_impact_weight_is_40_percent(self, scoring_service):
        """Impact should contribute 40% to priority."""
        # Only impact contributes
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=1.0,
            complexity=1.0
        )

        assert priority == pytest.approx(0.4, rel=0.01)

    def test_priority_inverse_complexity_weight_is_20_percent(self, scoring_service):
        """Inverse complexity should contribute 20% to priority."""
        # Only (1 - complexity) contributes
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=0.0,
            complexity=0.0  # (1 - 0) * 0.2 = 0.2
        )

        assert priority == pytest.approx(0.2, rel=0.01)

    def test_priority_bounded_zero_to_one(self, scoring_service):
        """Priority score should always be between 0 and 1."""
        test_cases = [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
            (0.5, 0.5, 0.5),
            (0.9, 0.1, 0.3),
            (0.2, 0.8, 0.7),
        ]

        for exposure, impact, complexity in test_cases:
            priority = scoring_service.calculate_priority_score(
                exposure=exposure,
                impact=impact,
                complexity=complexity
            )
            assert 0.0 <= priority <= 1.0, f"Failed for ({exposure}, {impact}, {complexity})"

    def test_priority_with_custom_weights(self, scoring_service):
        """Should allow custom weights for different prioritization strategies."""
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=0.0,
            complexity=1.0,
            weights={"exposure": 0.6, "impact": 0.3, "complexity": 0.1}
        )

        # 1.0 * 0.6 + 0.0 * 0.3 + (1 - 1.0) * 0.1 = 0.6
        assert priority == pytest.approx(0.6, rel=0.01)

    def test_calculate_complexity_from_exposure(self, scoring_service):
        """Complexity should be inverse of exposure (1 - exposure)."""
        exposure = 0.75

        complexity = scoring_service.calculate_complexity_score(exposure)

        assert complexity == pytest.approx(0.25, rel=0.01)

    def test_calculate_all_scores_for_role(self, scoring_service):
        """Should calculate all scores (exposure, impact, complexity, priority) for a role."""
        role_mapping = MagicMock(id="role-1", row_count=200)
        dwas = [
            MagicMock(ai_exposure_override=0.8),
            MagicMock(ai_exposure_override=0.6),
        ]

        scores = scoring_service.calculate_all_scores_for_role(
            role_mapping=role_mapping,
            selected_dwas=dwas,
            max_headcount=1000
        )

        assert "exposure" in scores
        assert "impact" in scores
        assert "complexity" in scores
        assert "priority" in scores

        # Verify exposure = (0.8 + 0.6) / 2 = 0.7
        assert scores["exposure"] == pytest.approx(0.7, rel=0.01)

        # Verify complexity = 1 - 0.7 = 0.3
        assert scores["complexity"] == pytest.approx(0.3, rel=0.01)

        # Verify impact = (200 * 0.7) / 1000 = 0.14
        assert scores["impact"] == pytest.approx(0.14, rel=0.01)

        # Verify priority = (0.7 * 0.4) + (0.14 * 0.4) + ((1 - 0.3) * 0.2)
        # = 0.28 + 0.056 + 0.14 = 0.476
        assert scores["priority"] == pytest.approx(0.476, rel=0.01)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_priority_scoring.py -v`
Expected: FAIL with "AttributeError: 'ScoringService' object has no attribute 'calculate_priority_score'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_priority_scoring.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/scoring.py backend/tests/unit/modules/discovery/test_priority_scoring.py
git commit -m "feat(discovery): add priority score calculator with weighted formula"
```

---

## Task 26: Multi-Dimension Aggregator

**Files:**
- Modify: `backend/app/modules/discovery/services/scoring.py`
- Test: `backend/tests/unit/modules/discovery/test_dimension_aggregator.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_dimension_aggregator.py
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.modules.discovery.services.scoring import ScoringService
from app.modules.discovery.enums import AnalysisDimension


@pytest.fixture
def scoring_service():
    return ScoringService()


@pytest.fixture
def sample_role_mappings():
    """Create sample role mappings with dimension data."""
    return [
        MagicMock(
            id=str(uuid4()),
            source_role="Software Engineer",
            row_count=100,
            # Dimension data from upload file
            metadata={
                "department": "Engineering",
                "lob": "Technology",
                "geography": "US-West",
            }
        ),
        MagicMock(
            id=str(uuid4()),
            source_role="Data Analyst",
            row_count=50,
            metadata={
                "department": "Analytics",
                "lob": "Technology",
                "geography": "US-East",
            }
        ),
        MagicMock(
            id=str(uuid4()),
            source_role="Customer Service Rep",
            row_count=200,
            metadata={
                "department": "Support",
                "lob": "Operations",
                "geography": "US-West",
            }
        ),
        MagicMock(
            id=str(uuid4()),
            source_role="Sales Associate",
            row_count=150,
            metadata={
                "department": "Sales",
                "lob": "Revenue",
                "geography": "US-East",
            }
        ),
    ]


@pytest.fixture
def sample_scores(sample_role_mappings):
    """Create sample scores for each role mapping."""
    return {
        sample_role_mappings[0].id: {"exposure": 0.85, "impact": 0.17, "complexity": 0.15, "priority": 0.75},
        sample_role_mappings[1].id: {"exposure": 0.90, "impact": 0.09, "complexity": 0.10, "priority": 0.70},
        sample_role_mappings[2].id: {"exposure": 0.60, "impact": 0.24, "complexity": 0.40, "priority": 0.55},
        sample_role_mappings[3].id: {"exposure": 0.45, "impact": 0.135, "complexity": 0.55, "priority": 0.40},
    }


class TestMultiDimensionAggregator:
    """Tests for aggregating scores by role, task, lob, geography, department."""

    def test_aggregate_by_role_dimension(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate scores grouped by role."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.ROLE
        )

        assert len(results) == 4  # One per role
        assert any(r["dimension_value"] == "Software Engineer" for r in results)
        assert any(r["dimension_value"] == "Data Analyst" for r in results)

    def test_aggregate_by_department_dimension(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate scores grouped by department."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT
        )

        # 4 unique departments: Engineering, Analytics, Support, Sales
        assert len(results) == 4

        engineering = next(r for r in results if r["dimension_value"] == "Engineering")
        assert engineering["ai_exposure_score"] == pytest.approx(0.85, rel=0.01)

    def test_aggregate_by_lob_dimension(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate scores grouped by line of business."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.LOB
        )

        # 3 unique LoB: Technology, Operations, Revenue
        assert len(results) == 3

        # Technology has 2 roles (Software Engineer + Data Analyst)
        technology = next(r for r in results if r["dimension_value"] == "Technology")
        assert "role_count" in technology
        assert technology["role_count"] == 2

    def test_aggregate_by_geography_dimension(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate scores grouped by geography."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.GEOGRAPHY
        )

        # 2 unique geographies: US-West, US-East
        assert len(results) == 2

        us_west = next(r for r in results if r["dimension_value"] == "US-West")
        us_east = next(r for r in results if r["dimension_value"] == "US-East")

        # US-West has Software Engineer (100) + Customer Service Rep (200) = 300 headcount
        assert us_west["total_headcount"] == 300
        # US-East has Data Analyst (50) + Sales Associate (150) = 200 headcount
        assert us_east["total_headcount"] == 200

    def test_aggregate_by_task_dimension(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate scores grouped by task (DWA)."""
        # Mock DWA selections for roles
        dwa_selections = {
            sample_role_mappings[0].id: [
                MagicMock(dwa_id="4.A.1.a.1", dwa_name="Getting Information"),
                MagicMock(dwa_id="4.A.2.a.1", dwa_name="Analyzing Data"),
            ],
            sample_role_mappings[1].id: [
                MagicMock(dwa_id="4.A.2.a.1", dwa_name="Analyzing Data"),
                MagicMock(dwa_id="4.A.3.b.6", dwa_name="Documenting Information"),
            ],
        }

        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings[:2],
            scores=sample_scores,
            dimension=AnalysisDimension.TASK,
            dwa_selections=dwa_selections
        )

        # 3 unique tasks
        assert len(results) == 3

        # "Analyzing Data" appears in both roles
        analyzing = next(r for r in results if r["dimension_value"] == "Analyzing Data")
        assert analyzing["role_count"] == 2

    def test_aggregation_includes_weighted_average_scores(self, scoring_service, sample_role_mappings, sample_scores):
        """Aggregated scores should be weighted by headcount."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.LOB
        )

        technology = next(r for r in results if r["dimension_value"] == "Technology")

        # Technology: Software Engineer (100, 0.85) + Data Analyst (50, 0.90)
        # Weighted exposure = (100 * 0.85 + 50 * 0.90) / (100 + 50) = 130 / 150 = 0.867
        assert technology["ai_exposure_score"] == pytest.approx(0.867, rel=0.02)

    def test_aggregation_result_structure(self, scoring_service, sample_role_mappings, sample_scores):
        """Aggregation result should include all required fields."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT
        )

        for result in results:
            assert "dimension" in result
            assert "dimension_value" in result
            assert "ai_exposure_score" in result
            assert "impact_score" in result
            assert "complexity_score" in result
            assert "priority_score" in result
            assert "total_headcount" in result
            assert "role_count" in result
            assert "breakdown" in result

    def test_breakdown_includes_contributing_roles(self, scoring_service, sample_role_mappings, sample_scores):
        """Breakdown should list all roles contributing to aggregation."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=sample_role_mappings,
            scores=sample_scores,
            dimension=AnalysisDimension.LOB
        )

        technology = next(r for r in results if r["dimension_value"] == "Technology")

        assert "roles" in technology["breakdown"]
        assert len(technology["breakdown"]["roles"]) == 2
        role_names = [r["role_name"] for r in technology["breakdown"]["roles"]]
        assert "Software Engineer" in role_names
        assert "Data Analyst" in role_names

    def test_aggregate_all_dimensions(self, scoring_service, sample_role_mappings, sample_scores):
        """Should aggregate across all dimensions in one call."""
        all_results = scoring_service.aggregate_all_dimensions(
            role_mappings=sample_role_mappings,
            scores=sample_scores
        )

        assert AnalysisDimension.ROLE in all_results
        assert AnalysisDimension.DEPARTMENT in all_results
        assert AnalysisDimension.LOB in all_results
        assert AnalysisDimension.GEOGRAPHY in all_results
        # TASK requires dwa_selections, so may be empty
        assert AnalysisDimension.TASK in all_results

    def test_empty_role_mappings_returns_empty_results(self, scoring_service):
        """Empty input should return empty results."""
        results = scoring_service.aggregate_by_dimension(
            role_mappings=[],
            scores={},
            dimension=AnalysisDimension.ROLE
        )

        assert results == []

    def test_missing_dimension_metadata_handled_gracefully(self, scoring_service, sample_scores):
        """Roles without dimension metadata should be grouped as 'Unknown'."""
        role_without_dept = MagicMock(
            id=str(uuid4()),
            source_role="Intern",
            row_count=10,
            metadata={}  # No department
        )
        sample_scores[role_without_dept.id] = {"exposure": 0.5, "impact": 0.01, "complexity": 0.5, "priority": 0.3}

        results = scoring_service.aggregate_by_dimension(
            role_mappings=[role_without_dept],
            scores=sample_scores,
            dimension=AnalysisDimension.DEPARTMENT
        )

        assert len(results) == 1
        assert results[0]["dimension_value"] == "Unknown"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_dimension_aggregator.py -v`
Expected: FAIL with "AttributeError: 'ScoringService' object has no attribute 'aggregate_by_dimension'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_dimension_aggregator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/scoring.py backend/tests/unit/modules/discovery/test_dimension_aggregator.py
git commit -m "feat(discovery): add multi-dimension score aggregator"
```

---

## Task 27: Scoring Service Integration

**Files:**
- Modify: `backend/app/modules/discovery/services/scoring.py`
- Modify: `backend/app/modules/discovery/services/__init__.py`
- Create: `backend/app/modules/discovery/schemas/scoring.py`
- Test: `backend/tests/unit/modules/discovery/test_scoring_integration.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_scoring_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.discovery.services.scoring import ScoringService
from app.modules.discovery.schemas.scoring import (
    AnalysisScores,
    DimensionAggregation,
    SessionScoringResult,
)
from app.modules.discovery.enums import AnalysisDimension


@pytest.fixture
def scoring_service():
    return ScoringService()


@pytest.fixture
def mock_repositories():
    """Mock all repositories needed for scoring."""
    return {
        "role_mapping_repo": AsyncMock(),
        "activity_selection_repo": AsyncMock(),
        "dwa_repo": AsyncMock(),
        "analysis_result_repo": AsyncMock(),
    }


@pytest.fixture
def sample_session():
    return MagicMock(id=uuid4(), organization_id=uuid4())


class TestScoringServiceIntegration:
    """Tests for complete scoring service integration."""

    @pytest.mark.asyncio
    async def test_score_session_returns_complete_result(
        self, scoring_service, mock_repositories, sample_session
    ):
        """score_session should return complete SessionScoringResult."""
        # Setup mocks
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(id="rm-1", source_role="Engineer", row_count=100, metadata={"department": "Eng"}),
            MagicMock(id="rm-2", source_role="Analyst", row_count=50, metadata={"department": "Analytics"}),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = [
            MagicMock(dwa_id="dwa-1"),
            MagicMock(dwa_id="dwa-2"),
        ]
        mock_repositories["dwa_repo"].get_by_ids.return_value = [
            MagicMock(id="dwa-1", ai_exposure_override=0.8, iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.7))),
            MagicMock(id="dwa-2", ai_exposure_override=None, iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.6))),
        ]

        result = await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
        )

        assert isinstance(result, SessionScoringResult)
        assert result.session_id == sample_session.id
        assert len(result.role_scores) == 2
        assert len(result.dimension_aggregations) > 0

    @pytest.mark.asyncio
    async def test_score_session_calculates_all_role_scores(
        self, scoring_service, mock_repositories, sample_session
    ):
        """Should calculate exposure, impact, complexity, priority for each role."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(id="rm-1", source_role="Engineer", row_count=100, metadata={}),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = [
            MagicMock(dwa_id="dwa-1"),
        ]
        mock_repositories["dwa_repo"].get_by_ids.return_value = [
            MagicMock(id="dwa-1", ai_exposure_override=0.8, iwa=MagicMock(gwa=MagicMock(ai_exposure_score=0.7))),
        ]

        result = await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
        )

        role_score = result.role_scores["rm-1"]
        assert isinstance(role_score, AnalysisScores)
        assert hasattr(role_score, "exposure")
        assert hasattr(role_score, "impact")
        assert hasattr(role_score, "complexity")
        assert hasattr(role_score, "priority")

    @pytest.mark.asyncio
    async def test_score_session_aggregates_all_dimensions(
        self, scoring_service, mock_repositories, sample_session
    ):
        """Should aggregate scores by all 5 dimensions."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(
                id="rm-1", source_role="Engineer", row_count=100,
                metadata={"department": "Eng", "lob": "Tech", "geography": "US"}
            ),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = []
        mock_repositories["dwa_repo"].get_by_ids.return_value = []

        result = await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
        )

        dimensions_covered = {agg.dimension for agg in result.dimension_aggregations}
        assert AnalysisDimension.ROLE in dimensions_covered
        assert AnalysisDimension.DEPARTMENT in dimensions_covered
        assert AnalysisDimension.LOB in dimensions_covered
        assert AnalysisDimension.GEOGRAPHY in dimensions_covered

    @pytest.mark.asyncio
    async def test_score_session_persists_results(
        self, scoring_service, mock_repositories, sample_session
    ):
        """Should persist analysis results to database."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(id="rm-1", source_role="Engineer", row_count=100, metadata={}),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = []
        mock_repositories["dwa_repo"].get_by_ids.return_value = []

        await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
            analysis_result_repo=mock_repositories["analysis_result_repo"],
            persist=True,
        )

        mock_repositories["analysis_result_repo"].bulk_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_score_session_handles_empty_dwas(
        self, scoring_service, mock_repositories, sample_session
    ):
        """Should handle roles with no selected DWAs gracefully."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(id="rm-1", source_role="New Role", row_count=10, metadata={}),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = []
        mock_repositories["dwa_repo"].get_by_ids.return_value = []

        result = await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
        )

        role_score = result.role_scores["rm-1"]
        assert role_score.exposure == 0.0
        assert role_score.impact == 0.0
        assert role_score.priority == pytest.approx(0.2, rel=0.01)  # Only (1-0)*0.2

    def test_analysis_scores_dataclass(self, scoring_service):
        """AnalysisScores should be a proper dataclass."""
        scores = AnalysisScores(
            exposure=0.8,
            impact=0.5,
            complexity=0.2,
            priority=0.7
        )

        assert scores.exposure == 0.8
        assert scores.impact == 0.5
        assert scores.complexity == 0.2
        assert scores.priority == 0.7

    def test_dimension_aggregation_dataclass(self, scoring_service):
        """DimensionAggregation should contain aggregated scores."""
        agg = DimensionAggregation(
            dimension=AnalysisDimension.DEPARTMENT,
            dimension_value="Engineering",
            ai_exposure_score=0.85,
            impact_score=0.6,
            complexity_score=0.15,
            priority_score=0.75,
            total_headcount=500,
            role_count=5,
            breakdown={"roles": []}
        )

        assert agg.dimension == AnalysisDimension.DEPARTMENT
        assert agg.dimension_value == "Engineering"

    def test_session_scoring_result_dataclass(self, scoring_service):
        """SessionScoringResult should contain all session scores."""
        session_id = uuid4()
        result = SessionScoringResult(
            session_id=session_id,
            role_scores={
                "rm-1": AnalysisScores(exposure=0.8, impact=0.5, complexity=0.2, priority=0.7)
            },
            dimension_aggregations=[
                DimensionAggregation(
                    dimension=AnalysisDimension.ROLE,
                    dimension_value="Engineer",
                    ai_exposure_score=0.8,
                    impact_score=0.5,
                    complexity_score=0.2,
                    priority_score=0.7,
                    total_headcount=100,
                    role_count=1,
                    breakdown={}
                )
            ],
            max_headcount=1000,
            total_headcount=100,
            total_roles=1
        )

        assert result.session_id == session_id
        assert len(result.role_scores) == 1
        assert len(result.dimension_aggregations) == 1

    @pytest.mark.asyncio
    async def test_get_session_max_headcount(self, scoring_service, mock_repositories, sample_session):
        """Should calculate max headcount from session for normalization."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = [
            MagicMock(id="rm-1", row_count=100, source_role="A", metadata={}),
            MagicMock(id="rm-2", row_count=500, source_role="B", metadata={}),  # Max
            MagicMock(id="rm-3", row_count=200, source_role="C", metadata={}),
        ]
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = []
        mock_repositories["dwa_repo"].get_by_ids.return_value = []

        result = await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
        )

        assert result.max_headcount == 500
        assert result.total_headcount == 800
        assert result.total_roles == 3

    @pytest.mark.asyncio
    async def test_rescore_session_clears_old_results(
        self, scoring_service, mock_repositories, sample_session
    ):
        """Re-scoring should clear previous results before saving new ones."""
        mock_repositories["role_mapping_repo"].get_by_session_id.return_value = []
        mock_repositories["activity_selection_repo"].get_selected_by_role_mapping.return_value = []
        mock_repositories["dwa_repo"].get_by_ids.return_value = []

        await scoring_service.score_session(
            session=sample_session,
            role_mapping_repo=mock_repositories["role_mapping_repo"],
            activity_selection_repo=mock_repositories["activity_selection_repo"],
            dwa_repo=mock_repositories["dwa_repo"],
            analysis_result_repo=mock_repositories["analysis_result_repo"],
            persist=True,
        )

        mock_repositories["analysis_result_repo"].delete_by_session_id.assert_called_once_with(
            sample_session.id
        )


class TestScoringServiceExports:
    """Tests for scoring service module exports."""

    def test_scoring_service_exported_from_services_init(self):
        """ScoringService should be importable from services package."""
        from app.modules.discovery.services import ScoringService

        assert ScoringService is not None

    def test_scoring_schemas_exported(self):
        """Scoring schemas should be importable."""
        from app.modules.discovery.schemas.scoring import (
            AnalysisScores,
            DimensionAggregation,
            SessionScoringResult,
        )

        assert AnalysisScores is not None
        assert DimensionAggregation is not None
        assert SessionScoringResult is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scoring_integration.py -v`
Expected: FAIL with "ImportError: cannot import name 'AnalysisScores' from 'app.modules.discovery.schemas.scoring'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

Create the scoring schemas:

```python
# backend/app/modules/discovery/schemas/scoring.py
from dataclasses import dataclass
from typing import Dict, List, Any
from uuid import UUID

from app.modules.discovery.enums import AnalysisDimension


@dataclass
class AnalysisScores:
    """Scores for a single role mapping."""
    exposure: float      # 0-1, AI exposure score
    impact: float        # 0-1, role_count * exposure (normalized)
    complexity: float    # 0-1, inverse of exposure
    priority: float      # 0-1, weighted combination


@dataclass
class DimensionAggregation:
    """Aggregated scores for a dimension value."""
    dimension: AnalysisDimension
    dimension_value: str
    ai_exposure_score: float
    impact_score: float
    complexity_score: float
    priority_score: float
    total_headcount: int
    role_count: int
    breakdown: Dict[str, Any]


@dataclass
class SessionScoringResult:
    """Complete scoring result for a discovery session."""
    session_id: UUID
    role_scores: Dict[str, AnalysisScores]
    dimension_aggregations: List[DimensionAggregation]
    max_headcount: int
    total_headcount: int
    total_roles: int
```

Update the services `__init__.py`:

```python
# backend/app/modules/discovery/services/__init__.py
from .scoring import ScoringService
from .onet_client import OnetApiClient
from .onet_sync import OnetSyncJob

__all__ = ["ScoringService", "OnetApiClient", "OnetSyncJob"]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scoring_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/ backend/app/modules/discovery/schemas/scoring.py backend/tests/unit/modules/discovery/test_scoring_integration.py
git commit -m "feat(discovery): integrate scoring service with schemas and session scoring"
```

---

## Summary

After completing Tasks 24-27, the Scoring Engine will have:

1. **Impact Score Calculator (Task 24):** Calculates `impact = role_count * exposure`, normalized to 0-1 scale
2. **Priority Score Calculator (Task 25):** Calculates `priority = (exposure * 0.4) + (impact * 0.4) + ((1 - complexity) * 0.2)`
3. **Multi-Dimension Aggregator (Task 26):** Aggregates scores by role, task, LoB, geography, and department
4. **Scoring Service Integration (Task 27):** Wires up all calculators with proper schemas and persistence

**Run all scoring tests:**

```bash
cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_scoring.py tests/unit/modules/discovery/test_impact_scoring.py tests/unit/modules/discovery/test_priority_scoring.py tests/unit/modules/discovery/test_dimension_aggregator.py tests/unit/modules/discovery/test_scoring_integration.py -v
```

**Next:** Continue to Part 5: Agent Architecture (Tasks 28-38)
## Part 5: Agent Architecture (Tasks 28-38)

### Task 28: Base Subagent Class

**Files:**
- Create: `backend/app/modules/discovery/agents/__init__.py`
- Create: `backend/app/modules/discovery/agents/base.py`
- Test: `backend/tests/unit/modules/discovery/test_base_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_base_agent.py
import pytest
from unittest.mock import AsyncMock

from app.modules.discovery.agents.base import BaseSubagent


def test_base_subagent_has_agent_type():
    """BaseSubagent should define agent_type."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

    agent = TestAgent(session=None, memory_service=None)
    assert agent.agent_type == "test_agent"


def test_base_subagent_protocol_flags_default_false():
    """Protocol flags should default to False."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

    agent = TestAgent(session=None, memory_service=None)
    assert agent.mcp_enabled is False
    assert agent.a2a_enabled is False
    assert agent.a2ui_enabled is False


@pytest.mark.asyncio
async def test_base_subagent_process_abstract():
    """Subagents must implement process method."""
    with pytest.raises(TypeError):
        BaseSubagent(session=None, memory_service=None)


def test_base_subagent_uses_brainstorming_style():
    """Subagent should format responses with brainstorming style."""
    class TestAgent(BaseSubagent):
        agent_type = "test_agent"

        async def process(self, message: str):
            return self.format_response("What column?", choices=["A", "B"])

    agent = TestAgent(session=None, memory_service=None)
    # Verify format_response exists and returns structured response
    assert hasattr(agent, "format_response")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_base_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'BaseSubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_base_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/
git commit -m "feat(discovery): add BaseSubagent with protocol flags"
```

---

### Task 29: Agent Memory Service

**Files:**
- Create: `backend/app/modules/discovery/services/memory_service.py`
- Test: `backend/tests/unit/modules/discovery/test_memory_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_memory_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.services.memory_service import AgentMemoryService


@pytest.fixture
def memory_service():
    return AgentMemoryService()


@pytest.fixture
def mock_repos():
    return {
        "working_memory_repo": AsyncMock(),
        "episodic_memory_repo": AsyncMock(),
        "semantic_memory_repo": AsyncMock(),
    }


class TestWorkingMemory:
    """Tests for working memory operations."""

    @pytest.mark.asyncio
    async def test_get_working_memory_returns_session_context(
        self, memory_service, mock_repos
    ):
        """Should retrieve current session context from working memory."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = MagicMock(
            context={"current_step": "upload", "last_action": "file_selected"}
        )

        result = await memory_service.get_working_memory(
            session_id=session_id,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        assert result["current_step"] == "upload"
        mock_repos["working_memory_repo"].get_by_session_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_update_working_memory_merges_context(
        self, memory_service, mock_repos
    ):
        """Should merge new context into existing working memory."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = MagicMock(
            context={"current_step": "upload"}
        )

        await memory_service.update_working_memory(
            session_id=session_id,
            updates={"last_action": "column_mapped"},
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        mock_repos["working_memory_repo"].update.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_working_memory_on_session_complete(
        self, memory_service, mock_repos
    ):
        """Should clear working memory when session completes."""
        session_id = uuid4()

        await memory_service.clear_working_memory(
            session_id=session_id,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        mock_repos["working_memory_repo"].delete_by_session_id.assert_called_once_with(session_id)


class TestEpisodicMemory:
    """Tests for episodic memory operations."""

    @pytest.mark.asyncio
    async def test_store_episode_saves_interaction(
        self, memory_service, mock_repos
    ):
        """Should store an interaction episode for learning."""
        agent_id = uuid4()
        episode = {
            "action": "suggested_mapping",
            "input": "Software Engineer",
            "output": "15-1252.00",
            "feedback": "accepted",
        }

        await memory_service.store_episode(
            agent_id=agent_id,
            episode=episode,
            episodic_memory_repo=mock_repos["episodic_memory_repo"],
        )

        mock_repos["episodic_memory_repo"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_similar_episodes(
        self, memory_service, mock_repos
    ):
        """Should retrieve similar past episodes for context."""
        agent_id = uuid4()
        mock_repos["episodic_memory_repo"].find_similar.return_value = [
            MagicMock(action="suggested_mapping", feedback="accepted"),
            MagicMock(action="suggested_mapping", feedback="rejected"),
        ]

        result = await memory_service.retrieve_similar_episodes(
            agent_id=agent_id,
            query="Software Engineer mapping",
            limit=5,
            episodic_memory_repo=mock_repos["episodic_memory_repo"],
        )

        assert len(result) == 2


class TestSemanticMemory:
    """Tests for semantic memory operations."""

    @pytest.mark.asyncio
    async def test_store_learned_pattern(
        self, memory_service, mock_repos
    ):
        """Should store a learned pattern in semantic memory."""
        agent_id = uuid4()
        pattern = {
            "pattern_type": "role_mapping_preference",
            "description": "User prefers exact title matches",
            "confidence": 0.85,
        }

        await memory_service.store_pattern(
            agent_id=agent_id,
            pattern=pattern,
            semantic_memory_repo=mock_repos["semantic_memory_repo"],
        )

        mock_repos["semantic_memory_repo"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_patterns_for_context(
        self, memory_service, mock_repos
    ):
        """Should retrieve relevant patterns for current context."""
        agent_id = uuid4()
        mock_repos["semantic_memory_repo"].get_by_agent_and_type.return_value = [
            MagicMock(pattern_type="role_mapping_preference", confidence=0.85),
        ]

        result = await memory_service.get_patterns(
            agent_id=agent_id,
            pattern_type="role_mapping_preference",
            semantic_memory_repo=mock_repos["semantic_memory_repo"],
        )

        assert len(result) == 1
        assert result[0].confidence == 0.85
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_memory_service.py -v`
Expected: FAIL with "ImportError: cannot import name 'AgentMemoryService'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_memory_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/services/memory_service.py backend/tests/unit/modules/discovery/test_memory_service.py
git commit -m "feat(discovery): add AgentMemoryService for working/episodic/semantic memory"
```

---

### Task 30: Upload Subagent

**Files:**
- Create: `backend/app/modules/discovery/agents/upload_agent.py`
- Test: `backend/tests/unit/modules/discovery/test_upload_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_upload_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.agents.upload_agent import UploadSubagent
from app.modules.discovery.agents.base import BaseSubagent


@pytest.fixture
def upload_agent():
    return UploadSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


class TestUploadSubagentSetup:
    """Tests for upload agent configuration."""

    def test_upload_agent_extends_base_subagent(self, upload_agent):
        """UploadSubagent should extend BaseSubagent."""
        assert isinstance(upload_agent, BaseSubagent)

    def test_upload_agent_type_is_upload(self, upload_agent):
        """Agent type should be 'upload'."""
        assert upload_agent.agent_type == "upload"


class TestColumnDetection:
    """Tests for file column detection."""

    @pytest.mark.asyncio
    async def test_detect_columns_from_csv(self, upload_agent):
        """Should detect column names from uploaded CSV."""
        file_content = "Name,Department,Role\nJohn,Engineering,Developer"

        result = await upload_agent.detect_columns(file_content, file_type="csv")

        assert "Name" in result
        assert "Department" in result
        assert "Role" in result

    @pytest.mark.asyncio
    async def test_suggest_column_mappings(self, upload_agent):
        """Should suggest which columns map to required fields."""
        columns = ["Employee Name", "Dept", "Job Title", "Location", "Headcount"]

        result = await upload_agent.suggest_column_mappings(columns)

        assert "role_column" in result
        assert "department_column" in result
        assert "headcount_column" in result


class TestBrainstormingInteraction:
    """Tests for brainstorming-style interactions."""

    @pytest.mark.asyncio
    async def test_process_asks_one_question_at_time(self, upload_agent):
        """Should ask one clarifying question at a time."""
        upload_agent._file_uploaded = True
        upload_agent._columns = ["Name", "Title", "Dept"]

        response = await upload_agent.process("I uploaded the file")

        assert response.question is not None
        assert response.choices is not None
        assert len(response.choices) <= 5  # Max 5 choices

    @pytest.mark.asyncio
    async def test_process_confirms_column_selection(self, upload_agent):
        """Should confirm user's column selection."""
        upload_agent._file_uploaded = True
        upload_agent._pending_question = "role_column"

        response = await upload_agent.process("Job Title")

        assert "Job Title" in str(response) or response.confirmed_value == "Job Title"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_upload_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'UploadSubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_upload_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/upload_agent.py backend/tests/unit/modules/discovery/test_upload_agent.py
git commit -m "feat(discovery): add UploadSubagent for file parsing and column detection"
```

---

### Task 31: Mapping Subagent

**Files:**
- Create: `backend/app/modules/discovery/agents/mapping_agent.py`
- Test: `backend/tests/unit/modules/discovery/test_mapping_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_mapping_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.agents.mapping_agent import MappingSubagent
from app.modules.discovery.agents.base import BaseSubagent


@pytest.fixture
def mapping_agent():
    return MappingSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_onet_repo():
    repo = AsyncMock()
    repo.search_occupations.return_value = [
        MagicMock(code="15-1252.00", title="Software Developers", score=0.95),
        MagicMock(code="15-1254.00", title="Web Developers", score=0.85),
    ]
    return repo


class TestMappingSubagentSetup:
    """Tests for mapping agent configuration."""

    def test_mapping_agent_extends_base_subagent(self, mapping_agent):
        """MappingSubagent should extend BaseSubagent."""
        assert isinstance(mapping_agent, BaseSubagent)

    def test_mapping_agent_type_is_mapping(self, mapping_agent):
        """Agent type should be 'mapping'."""
        assert mapping_agent.agent_type == "mapping"


class TestOnetMatching:
    """Tests for O*NET occupation matching."""

    @pytest.mark.asyncio
    async def test_suggest_onet_matches_for_role(
        self, mapping_agent, mock_onet_repo
    ):
        """Should suggest O*NET occupations for a source role."""
        result = await mapping_agent.suggest_matches(
            source_role="Software Engineer",
            onet_repo=mock_onet_repo,
            limit=5,
        )

        assert len(result) == 2
        assert result[0].code == "15-1252.00"
        mock_onet_repo.search_occupations.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_mapping_stores_selection(
        self, mapping_agent, mock_onet_repo
    ):
        """Should store confirmed mapping."""
        role_mapping_id = uuid4()

        await mapping_agent.confirm_mapping(
            role_mapping_id=role_mapping_id,
            onet_code="15-1252.00",
            confidence=0.95,
        )

        assert mapping_agent._confirmed_mappings[str(role_mapping_id)] == "15-1252.00"


class TestBrainstormingFlow:
    """Tests for brainstorming-style role mapping."""

    @pytest.mark.asyncio
    async def test_process_presents_mapping_choices(self, mapping_agent, mock_onet_repo):
        """Should present O*NET choices for unmapped role."""
        mapping_agent._onet_repo = mock_onet_repo
        mapping_agent._current_role = MagicMock(source_role="Data Analyst")

        response = await mapping_agent.process("Map this role")

        assert response.question is not None
        assert len(response.choices) >= 1

    @pytest.mark.asyncio
    async def test_process_handles_none_of_these(self, mapping_agent):
        """Should handle 'none of these' selection."""
        mapping_agent._pending_role_id = uuid4()

        response = await mapping_agent.process("None of these match")

        assert "search" in response.question.lower() or "specify" in response.question.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_mapping_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'MappingSubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_mapping_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/mapping_agent.py backend/tests/unit/modules/discovery/test_mapping_agent.py
git commit -m "feat(discovery): add MappingSubagent for O*NET role matching"
```

---

### Task 32: Activity Subagent

**Files:**
- Create: `backend/app/modules/discovery/agents/activity_agent.py`
- Test: `backend/tests/unit/modules/discovery/test_activity_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_activity_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.agents.activity_agent import ActivitySubagent
from app.modules.discovery.agents.base import BaseSubagent


@pytest.fixture
def activity_agent():
    return ActivitySubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_dwa_list():
    return [
        MagicMock(id="4.A.1.a.1", name="Analyzing data", gwa_exposure=0.85),
        MagicMock(id="4.A.2.b.2", name="Writing reports", gwa_exposure=0.70),
        MagicMock(id="4.A.3.c.3", name="Coordinating meetings", gwa_exposure=0.45),
    ]


class TestActivitySubagentSetup:
    """Tests for activity agent configuration."""

    def test_activity_agent_extends_base_subagent(self, activity_agent):
        """ActivitySubagent should extend BaseSubagent."""
        assert isinstance(activity_agent, BaseSubagent)

    def test_activity_agent_type_is_activity(self, activity_agent):
        """Agent type should be 'activity'."""
        assert activity_agent.agent_type == "activity"


class TestDwaSelection:
    """Tests for DWA selection management."""

    @pytest.mark.asyncio
    async def test_get_dwas_for_role_mapping(self, activity_agent, mock_dwa_list):
        """Should retrieve DWAs for a mapped O*NET occupation."""
        activity_agent._dwa_repo = AsyncMock()
        activity_agent._dwa_repo.get_by_occupation.return_value = mock_dwa_list

        result = await activity_agent.get_dwas_for_role(
            onet_code="15-1252.00",
        )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_toggle_dwa_selection(self, activity_agent):
        """Should toggle DWA selection state."""
        role_mapping_id = uuid4()
        dwa_id = "4.A.1.a.1"

        await activity_agent.toggle_dwa(
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=True,
        )

        assert activity_agent._selections[(str(role_mapping_id), dwa_id)] is True

        await activity_agent.toggle_dwa(
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=False,
        )

        assert activity_agent._selections[(str(role_mapping_id), dwa_id)] is False

    @pytest.mark.asyncio
    async def test_bulk_select_by_exposure_threshold(self, activity_agent, mock_dwa_list):
        """Should bulk select DWAs above exposure threshold."""
        role_mapping_id = uuid4()
        activity_agent._current_dwas = mock_dwa_list

        await activity_agent.select_above_threshold(
            role_mapping_id=role_mapping_id,
            threshold=0.6,
        )

        # Should select 2 DWAs (0.85 and 0.70, not 0.45)
        selected = [k for k, v in activity_agent._selections.items() if v]
        assert len(selected) == 2


class TestBrainstormingFlow:
    """Tests for brainstorming-style activity selection."""

    @pytest.mark.asyncio
    async def test_process_asks_about_activity_relevance(self, activity_agent, mock_dwa_list):
        """Should ask if activity is relevant to role."""
        activity_agent._current_dwas = mock_dwa_list
        activity_agent._current_dwa_index = 0

        response = await activity_agent.process("Start activity selection")

        assert response.question is not None
        assert "Analyzing data" in response.question or mock_dwa_list[0].name in str(response)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'ActivitySubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_activity_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/activity_agent.py backend/tests/unit/modules/discovery/test_activity_agent.py
git commit -m "feat(discovery): add ActivitySubagent for DWA selection management"
```

---

### Task 33: Analysis Subagent

**Files:**
- Create: `backend/app/modules/discovery/agents/analysis_agent.py`
- Test: `backend/tests/unit/modules/discovery/test_analysis_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_analysis_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.agents.analysis_agent import AnalysisSubagent
from app.modules.discovery.agents.base import BaseSubagent


@pytest.fixture
def analysis_agent():
    return AnalysisSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_scoring_service():
    service = MagicMock()
    service.score_session = AsyncMock(return_value=MagicMock(
        role_scores={"role-1": MagicMock(exposure=0.8, impact=0.6, priority=0.75)},
        dimension_aggregations=[],
    ))
    return service


class TestAnalysisSubagentSetup:
    """Tests for analysis agent configuration."""

    def test_analysis_agent_extends_base_subagent(self, analysis_agent):
        """AnalysisSubagent should extend BaseSubagent."""
        assert isinstance(analysis_agent, BaseSubagent)

    def test_analysis_agent_type_is_analysis(self, analysis_agent):
        """Agent type should be 'analysis'."""
        assert analysis_agent.agent_type == "analysis"


class TestScoreCalculation:
    """Tests for score calculation orchestration."""

    @pytest.mark.asyncio
    async def test_trigger_scoring_uses_scoring_service(
        self, analysis_agent, mock_scoring_service
    ):
        """Should delegate to ScoringService for calculations."""
        analysis_agent._scoring_service = mock_scoring_service

        result = await analysis_agent.calculate_scores()

        mock_scoring_service.score_session.assert_called_once()
        assert result.role_scores["role-1"].exposure == 0.8


class TestInsightGeneration:
    """Tests for insight generation."""

    @pytest.mark.asyncio
    async def test_generate_top_opportunities_insight(self, analysis_agent):
        """Should generate insight about top automation opportunities."""
        analysis_agent._scoring_result = MagicMock(
            role_scores={
                "role-1": MagicMock(priority=0.9, exposure=0.85),
                "role-2": MagicMock(priority=0.6, exposure=0.5),
            }
        )

        insights = await analysis_agent.generate_insights()

        assert any("opportunity" in i.lower() or "priority" in i.lower() for i in insights)

    @pytest.mark.asyncio
    async def test_generate_department_summary_insight(self, analysis_agent):
        """Should summarize scores by department."""
        analysis_agent._scoring_result = MagicMock(
            dimension_aggregations=[
                MagicMock(dimension="DEPARTMENT", dimension_value="Engineering", ai_exposure_score=0.8),
                MagicMock(dimension="DEPARTMENT", dimension_value="HR", ai_exposure_score=0.4),
            ]
        )

        summary = await analysis_agent.get_dimension_summary("DEPARTMENT")

        assert len(summary) == 2


class TestBrainstormingFlow:
    """Tests for brainstorming-style analysis presentation."""

    @pytest.mark.asyncio
    async def test_process_presents_analysis_dimensions(self, analysis_agent):
        """Should ask which dimension to explore."""
        analysis_agent._scores_calculated = True

        response = await analysis_agent.process("Show me the analysis")

        assert response.question is not None
        assert response.choices is not None
        # Should offer dimension choices
        dimension_names = ["role", "department", "geography", "task"]
        assert any(d in str(response.choices).lower() for d in dimension_names)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_analysis_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'AnalysisSubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_analysis_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/analysis_agent.py backend/tests/unit/modules/discovery/test_analysis_agent.py
git commit -m "feat(discovery): add AnalysisSubagent for scoring and insights"
```

---

### Task 34: Roadmap Subagent

**Files:**
- Create: `backend/app/modules/discovery/agents/roadmap_agent.py`
- Test: `backend/tests/unit/modules/discovery/test_roadmap_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_roadmap_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.discovery.agents.roadmap_agent import RoadmapSubagent
from app.modules.discovery.agents.base import BaseSubagent


@pytest.fixture
def roadmap_agent():
    return RoadmapSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


class TestRoadmapSubagentSetup:
    """Tests for roadmap agent configuration."""

    def test_roadmap_agent_extends_base_subagent(self, roadmap_agent):
        """RoadmapSubagent should extend BaseSubagent."""
        assert isinstance(roadmap_agent, BaseSubagent)

    def test_roadmap_agent_type_is_roadmap(self, roadmap_agent):
        """Agent type should be 'roadmap'."""
        assert roadmap_agent.agent_type == "roadmap"


class TestPrioritization:
    """Tests for candidate prioritization."""

    @pytest.mark.asyncio
    async def test_prioritize_candidates_by_score(self, roadmap_agent):
        """Should prioritize candidates by priority score."""
        candidates = [
            MagicMock(id="c1", role_name="Engineer", priority_score=0.6),
            MagicMock(id="c2", role_name="Analyst", priority_score=0.9),
            MagicMock(id="c3", role_name="Manager", priority_score=0.7),
        ]

        result = await roadmap_agent.prioritize(candidates)

        assert result[0].id == "c2"  # Highest priority first
        assert result[1].id == "c3"
        assert result[2].id == "c1"

    @pytest.mark.asyncio
    async def test_assign_priority_tiers(self, roadmap_agent):
        """Should assign high/medium/low tiers based on scores."""
        candidates = [
            MagicMock(id="c1", priority_score=0.85),  # High
            MagicMock(id="c2", priority_score=0.55),  # Medium
            MagicMock(id="c3", priority_score=0.25),  # Low
        ]

        result = await roadmap_agent.assign_tiers(candidates)

        assert result["c1"] == "high"
        assert result["c2"] == "medium"
        assert result["c3"] == "low"


class TestTimelineGeneration:
    """Tests for implementation timeline."""

    @pytest.mark.asyncio
    async def test_generate_quarterly_timeline(self, roadmap_agent):
        """Should organize candidates into quarterly timeline."""
        candidates = [
            MagicMock(id="c1", priority_score=0.9, complexity_score=0.2),
            MagicMock(id="c2", priority_score=0.7, complexity_score=0.5),
            MagicMock(id="c3", priority_score=0.5, complexity_score=0.8),
        ]

        timeline = await roadmap_agent.generate_timeline(candidates, quarters=4)

        assert "Q1" in timeline
        assert "Q2" in timeline
        assert len(timeline["Q1"]) >= 1  # High priority, low complexity first


class TestBrainstormingFlow:
    """Tests for brainstorming-style roadmap planning."""

    @pytest.mark.asyncio
    async def test_process_asks_about_priorities(self, roadmap_agent):
        """Should ask about prioritization preferences."""
        roadmap_agent._candidates = [MagicMock(), MagicMock()]

        response = await roadmap_agent.process("Create a roadmap")

        assert response.question is not None

    @pytest.mark.asyncio
    async def test_process_offers_timeline_options(self, roadmap_agent):
        """Should offer timeline duration options."""
        roadmap_agent._prioritized = True

        response = await roadmap_agent.process("Generate timeline")

        assert response.choices is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_roadmap_agent.py -v`
Expected: FAIL with "ImportError: cannot import name 'RoadmapSubagent'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_roadmap_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/roadmap_agent.py backend/tests/unit/modules/discovery/test_roadmap_agent.py
git commit -m "feat(discovery): add RoadmapSubagent for prioritization and timeline"
```

---

### Task 35: Discovery Orchestrator

**Files:**
- Create: `backend/app/modules/discovery/agents/orchestrator.py`
- Test: `backend/tests/unit/modules/discovery/test_orchestrator.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.discovery.agents.orchestrator import DiscoveryOrchestrator
from app.modules.discovery.enums import DiscoveryStep


@pytest.fixture
def orchestrator():
    return DiscoveryOrchestrator(
        session=MagicMock(id=uuid4(), current_step=DiscoveryStep.UPLOAD),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_subagents():
    return {
        "upload": AsyncMock(),
        "mapping": AsyncMock(),
        "activity": AsyncMock(),
        "analysis": AsyncMock(),
        "roadmap": AsyncMock(),
    }


class TestOrchestratorRouting:
    """Tests for message routing to subagents."""

    @pytest.mark.asyncio
    async def test_routes_to_upload_agent_on_upload_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to UploadSubagent during upload step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.UPLOAD

        await orchestrator.process("I have a file")

        mock_subagents["upload"].process.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_mapping_agent_on_mapping_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to MappingSubagent during mapping step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.MAP_ROLES

        await orchestrator.process("Map this role")

        mock_subagents["mapping"].process.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_activity_agent_on_activity_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to ActivitySubagent during activity step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.SELECT_ACTIVITIES

        await orchestrator.process("Select activities")

        mock_subagents["activity"].process.assert_called_once()


class TestStepTransitions:
    """Tests for wizard step transitions."""

    @pytest.mark.asyncio
    async def test_advance_step_on_completion(self, orchestrator, mock_subagents):
        """Should advance to next step when current completes."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.UPLOAD
        mock_subagents["upload"].process.return_value = MagicMock(step_complete=True)

        await orchestrator.process("Done uploading")

        assert orchestrator._session.current_step == DiscoveryStep.MAP_ROLES

    @pytest.mark.asyncio
    async def test_stay_on_step_if_not_complete(self, orchestrator, mock_subagents):
        """Should stay on current step if not complete."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.MAP_ROLES
        mock_subagents["mapping"].process.return_value = MagicMock(step_complete=False)

        await orchestrator.process("Still mapping")

        assert orchestrator._session.current_step == DiscoveryStep.MAP_ROLES


class TestConversationManagement:
    """Tests for conversation thread management."""

    @pytest.mark.asyncio
    async def test_maintains_single_conversation_thread(self, orchestrator):
        """Should maintain one conversation thread per session."""
        assert orchestrator._conversation_id is not None

        conversation_id = orchestrator._conversation_id
        await orchestrator.process("Message 1")
        await orchestrator.process("Message 2")

        assert orchestrator._conversation_id == conversation_id

    @pytest.mark.asyncio
    async def test_stores_messages_in_history(self, orchestrator, mock_subagents):
        """Should store user and agent messages."""
        orchestrator._subagents = mock_subagents
        mock_subagents["upload"].process.return_value = MagicMock(
            message="What file?", step_complete=False
        )

        await orchestrator.process("Hello")

        assert len(orchestrator._message_history) >= 2  # User + Agent
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_orchestrator.py -v`
Expected: FAIL with "ImportError: cannot import name 'DiscoveryOrchestrator'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_orchestrator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/orchestrator.py backend/tests/unit/modules/discovery/test_orchestrator.py
git commit -m "feat(discovery): add DiscoveryOrchestrator for subagent routing"
```

---

### Task 36: Brainstorming Interaction Handler

**Files:**
- Create: `backend/app/modules/discovery/agents/interaction_handler.py`
- Test: `backend/tests/unit/modules/discovery/test_interaction_handler.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_interaction_handler.py
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.agents.interaction_handler import BrainstormingHandler


@pytest.fixture
def handler():
    return BrainstormingHandler()


class TestQuestionFormatting:
    """Tests for question formatting."""

    def test_format_single_question(self, handler):
        """Should format a single question with choices."""
        result = handler.format_question(
            question="Which column contains the role?",
            choices=["Column A", "Column B", "Column C"],
        )

        assert result.question == "Which column contains the role?"
        assert len(result.choices) == 3
        assert result.allow_freeform is False

    def test_format_question_with_freeform_option(self, handler):
        """Should allow freeform input when specified."""
        result = handler.format_question(
            question="What is the role name?",
            choices=["Engineer", "Analyst"],
            allow_freeform=True,
        )

        assert result.allow_freeform is True

    def test_limit_choices_to_five(self, handler):
        """Should limit choices to max 5 options."""
        result = handler.format_question(
            question="Pick one",
            choices=["A", "B", "C", "D", "E", "F", "G"],
        )

        assert len(result.choices) <= 5


class TestOneQuestionAtATime:
    """Tests for one-question-at-a-time pattern."""

    def test_queue_multiple_questions(self, handler):
        """Should queue multiple questions."""
        handler.queue_question("Question 1?", ["A", "B"])
        handler.queue_question("Question 2?", ["C", "D"])

        assert handler.pending_count == 2

    def test_get_next_returns_first_queued(self, handler):
        """Should return questions in FIFO order."""
        handler.queue_question("First?", ["A"])
        handler.queue_question("Second?", ["B"])

        result = handler.get_next_question()

        assert result.question == "First?"

    def test_mark_answered_removes_from_queue(self, handler):
        """Should remove answered question from queue."""
        handler.queue_question("Question?", ["A", "B"])

        handler.get_next_question()
        handler.mark_answered("A")

        assert handler.pending_count == 0


class TestResponseParsing:
    """Tests for parsing user responses."""

    def test_match_choice_by_text(self, handler):
        """Should match user response to choice."""
        handler._current_choices = ["Column A", "Column B"]

        result = handler.parse_response("Column A")

        assert result.matched_choice == "Column A"
        assert result.is_freeform is False

    def test_detect_freeform_response(self, handler):
        """Should detect freeform response when no match."""
        handler._current_choices = ["Option 1", "Option 2"]
        handler._allow_freeform = True

        result = handler.parse_response("Something else entirely")

        assert result.is_freeform is True
        assert result.freeform_value == "Something else entirely"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_interaction_handler.py -v`
Expected: FAIL with "ImportError: cannot import name 'BrainstormingHandler'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_interaction_handler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/interaction_handler.py backend/tests/unit/modules/discovery/test_interaction_handler.py
git commit -m "feat(discovery): add BrainstormingHandler for one-question-at-a-time"
```

---

### Task 37: Chat Message Formatter

**Files:**
- Create: `backend/app/modules/discovery/agents/message_formatter.py`
- Test: `backend/tests/unit/modules/discovery/test_message_formatter.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_message_formatter.py
import pytest
from uuid import uuid4

from app.modules.discovery.agents.message_formatter import ChatMessageFormatter


@pytest.fixture
def formatter():
    return ChatMessageFormatter()


class TestMessageFormatting:
    """Tests for chat message formatting."""

    def test_format_agent_message(self, formatter):
        """Should format agent message with metadata."""
        result = formatter.format_agent_message(
            content="Which column contains roles?",
            agent_type="upload",
        )

        assert result.role == "assistant"
        assert result.content == "Which column contains roles?"
        assert result.agent_type == "upload"

    def test_format_user_message(self, formatter):
        """Should format user message."""
        result = formatter.format_user_message(
            content="Column B",
        )

        assert result.role == "user"
        assert result.content == "Column B"

    def test_include_timestamp(self, formatter):
        """Should include timestamp in messages."""
        result = formatter.format_agent_message(
            content="Hello",
            agent_type="orchestrator",
        )

        assert result.timestamp is not None


class TestQuickActionFormatting:
    """Tests for quick action chip formatting."""

    def test_format_choices_as_quick_actions(self, formatter):
        """Should format choices as quick action chips."""
        result = formatter.format_with_quick_actions(
            content="Select a column:",
            choices=["Column A", "Column B"],
        )

        assert len(result.quick_actions) == 2
        assert result.quick_actions[0].label == "Column A"

    def test_quick_action_includes_value(self, formatter):
        """Quick actions should include value for API."""
        result = formatter.format_with_quick_actions(
            content="Choose:",
            choices=[("Display Text", "api_value")],
        )

        assert result.quick_actions[0].label == "Display Text"
        assert result.quick_actions[0].value == "api_value"


class TestConversationHistory:
    """Tests for conversation history formatting."""

    def test_format_history_for_display(self, formatter):
        """Should format message history for UI display."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!", "agent_type": "orchestrator"},
        ]

        result = formatter.format_history(messages)

        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"

    def test_group_by_conversation_turn(self, formatter):
        """Should group messages by conversation turn."""
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]

        result = formatter.group_by_turn(messages)

        assert len(result) == 2  # Two turns
        assert result[0].user_message.content == "Q1"
        assert result[0].agent_message.content == "A1"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_message_formatter.py -v`
Expected: FAIL with "ImportError: cannot import name 'ChatMessageFormatter'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_message_formatter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/message_formatter.py backend/tests/unit/modules/discovery/test_message_formatter.py
git commit -m "feat(discovery): add ChatMessageFormatter for agent responses"
```

---

### Task 38: Quick Action Chip Generator

**Files:**
- Create: `backend/app/modules/discovery/agents/chip_generator.py`
- Test: `backend/tests/unit/modules/discovery/test_chip_generator.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/modules/discovery/test_chip_generator.py
import pytest

from app.modules.discovery.agents.chip_generator import QuickActionChipGenerator


@pytest.fixture
def generator():
    return QuickActionChipGenerator()


class TestChipGeneration:
    """Tests for quick action chip generation."""

    def test_generate_choice_chips(self, generator):
        """Should generate chips from choices."""
        result = generator.generate(
            choices=["Option A", "Option B", "Option C"],
        )

        assert len(result) == 3
        assert all(chip.type == "choice" for chip in result)

    def test_generate_with_icons(self, generator):
        """Should include icons when specified."""
        result = generator.generate(
            choices=[
                {"label": "Yes", "icon": "check"},
                {"label": "No", "icon": "x"},
            ],
        )

        assert result[0].icon == "check"
        assert result[1].icon == "x"

    def test_limit_to_max_chips(self, generator):
        """Should limit to maximum number of chips."""
        result = generator.generate(
            choices=["A", "B", "C", "D", "E", "F", "G", "H"],
            max_chips=5,
        )

        assert len(result) == 5


class TestContextualChips:
    """Tests for context-aware chip generation."""

    def test_generate_column_selection_chips(self, generator):
        """Should generate chips for column selection."""
        result = generator.generate_column_chips(
            columns=["Name", "Department", "Title"],
            context="role_column",
        )

        assert len(result) == 3
        assert any("Title" in chip.label for chip in result)

    def test_generate_confirmation_chips(self, generator):
        """Should generate yes/no confirmation chips."""
        result = generator.generate_confirmation_chips()

        assert len(result) == 2
        assert any(chip.label == "Yes" for chip in result)
        assert any(chip.label == "No" for chip in result)

    def test_generate_onet_suggestion_chips(self, generator):
        """Should generate chips for O*NET suggestions."""
        suggestions = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.95},
            {"code": "15-1254.00", "title": "Web Developers", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 2
        assert "Software Developers" in result[0].label


class TestChipStyling:
    """Tests for chip styling."""

    def test_primary_chip_style(self, generator):
        """Should apply primary style to recommended option."""
        result = generator.generate(
            choices=["Recommended", "Alternative"],
            primary_index=0,
        )

        assert result[0].style == "primary"
        assert result[1].style == "secondary"

    def test_disabled_chip_state(self, generator):
        """Should support disabled chips."""
        result = generator.generate(
            choices=[
                {"label": "Available", "disabled": False},
                {"label": "Unavailable", "disabled": True},
            ],
        )

        assert result[0].disabled is False
        assert result[1].disabled is True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_chip_generator.py -v`
Expected: FAIL with "ImportError: cannot import name 'QuickActionChipGenerator'"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/test_chip_generator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/modules/discovery/agents/chip_generator.py backend/tests/unit/modules/discovery/test_chip_generator.py
git commit -m "feat(discovery): add QuickActionChipGenerator for choice chips"
```

---

## Part 6: API Endpoints (Tasks 39-48)

### Task 39: Discovery Session Router - CRUD Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/__init__.py`
- Create: `discovery/api/src/discovery/routers/sessions.py`
- Create: `discovery/api/src/discovery/schemas/session.py`
- Test: `discovery/api/tests/unit/routers/test_sessions.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/__init__.py
# empty file

# discovery/api/tests/unit/routers/test_sessions.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_create_session(client, mock_session_service):
    """POST /discovery/sessions should create a new session."""
    response = await client.post(
        "/discovery/sessions",
        json={"organization_id": str(uuid4())}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "draft"
    assert data["current_step"] == 1


@pytest.mark.asyncio
async def test_get_session(client, mock_session_service):
    """GET /discovery/sessions/{id} should return session details."""
    session_id = str(uuid4())
    mock_session_service.get_by_id.return_value = {
        "id": session_id,
        "status": "in_progress",
        "current_step": 2
    }

    response = await client.get(f"/discovery/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client, mock_session_service):
    """GET /discovery/sessions/{id} should return 404 if not found."""
    mock_session_service.get_by_id.return_value = None

    response = await client.get(f"/discovery/sessions/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions(client, mock_session_service):
    """GET /discovery/sessions should return paginated list."""
    mock_session_service.list_for_user.return_value = {
        "items": [{"id": str(uuid4()), "status": "draft"}],
        "total": 1,
        "page": 1,
        "per_page": 20
    }

    response = await client.get("/discovery/sessions")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_update_session_step(client, mock_session_service):
    """PATCH /discovery/sessions/{id}/step should update step."""
    session_id = str(uuid4())

    response = await client.patch(
        f"/discovery/sessions/{session_id}/step",
        json={"step": 3}
    )

    assert response.status_code == 200
    mock_session_service.update_step.assert_called_once()


@pytest.mark.asyncio
async def test_delete_session(client, mock_session_service):
    """DELETE /discovery/sessions/{id} should delete session."""
    session_id = str(uuid4())

    response = await client.delete(f"/discovery/sessions/{session_id}")

    assert response.status_code == 204
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_sessions.py -v`
Expected: FAIL with "ImportError" or "AttributeError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_sessions.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/ discovery/api/src/discovery/schemas/
git commit -m "feat(discovery): add discovery session router with CRUD endpoints"
```

---

### Task 40: Upload Endpoint

**Files:**
- Create: `discovery/api/src/discovery/routers/uploads.py`
- Create: `discovery/api/src/discovery/schemas/upload.py`
- Test: `discovery/api/tests/unit/routers/test_uploads.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_uploads.py
import pytest
from httpx import AsyncClient
from uuid import uuid4
from io import BytesIO

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def sample_csv():
    content = b"Name,Role,Department\nJohn,Engineer,IT\nJane,Analyst,Finance"
    return BytesIO(content)


@pytest.mark.asyncio
async def test_upload_file(client, mock_upload_service, sample_csv):
    """POST /discovery/sessions/{id}/upload should upload and parse file."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("hr_data.csv", sample_csv, "text/csv")}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["file_name"] == "hr_data.csv"
    assert "row_count" in data
    assert "detected_schema" in data


@pytest.mark.asyncio
async def test_upload_xlsx(client, mock_upload_service):
    """POST should accept XLSX files."""
    session_id = str(uuid4())
    # Minimal xlsx bytes (would normally be a real file)
    xlsx_content = BytesIO(b"fake xlsx content for test")

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("data.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )

    # Mock service handles the parsing
    assert response.status_code in (201, 400)  # 400 if real parsing fails


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client, mock_upload_service):
    """POST should reject unsupported file types."""
    session_id = str(uuid4())
    pdf_content = BytesIO(b"%PDF-1.4 fake pdf content")

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("report.pdf", pdf_content, "application/pdf")}
    )

    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_too_large(client, mock_upload_service):
    """POST should reject files exceeding size limit."""
    session_id = str(uuid4())
    # Simulate large file (10MB+)
    large_content = BytesIO(b"x" * (11 * 1024 * 1024))

    response = await client.post(
        f"/discovery/sessions/{session_id}/upload",
        files={"file": ("huge.csv", large_content, "text/csv")}
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_get_uploads_for_session(client, mock_upload_service):
    """GET /discovery/sessions/{id}/uploads should list uploads."""
    session_id = str(uuid4())
    mock_upload_service.get_by_session_id.return_value = [
        {"id": str(uuid4()), "file_name": "data.csv", "row_count": 100}
    ]

    response = await client.get(f"/discovery/sessions/{session_id}/uploads")

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_update_column_mappings(client, mock_upload_service):
    """PUT /discovery/uploads/{id}/mappings should update column mappings."""
    upload_id = str(uuid4())

    response = await client.put(
        f"/discovery/uploads/{upload_id}/mappings",
        json={
            "role": "Column B",
            "department": "Column C",
            "geography": "Column D"
        }
    )

    assert response.status_code == 200
    mock_upload_service.update_column_mappings.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_uploads.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_uploads.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/uploads.py discovery/api/src/discovery/schemas/upload.py
git commit -m "feat(discovery): add file upload endpoint with validation"
```

---

### Task 41: Role Mapping Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/role_mappings.py`
- Create: `discovery/api/src/discovery/schemas/role_mapping.py`
- Test: `discovery/api/tests/unit/routers/test_role_mappings.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_role_mappings.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_get_role_mappings(client, mock_role_mapping_service):
    """GET /discovery/sessions/{id}/role-mappings should return mappings."""
    session_id = str(uuid4())
    mock_role_mapping_service.get_by_session_id.return_value = [
        {
            "id": str(uuid4()),
            "source_role": "Software Engineer",
            "onet_code": "15-1252.00",
            "onet_title": "Software Developers",
            "confidence_score": 0.95,
            "is_confirmed": False
        }
    ]

    response = await client.get(f"/discovery/sessions/{session_id}/role-mappings")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_role"] == "Software Engineer"


@pytest.mark.asyncio
async def test_update_role_mapping(client, mock_role_mapping_service):
    """PUT /discovery/role-mappings/{id} should update mapping."""
    mapping_id = str(uuid4())

    response = await client.put(
        f"/discovery/role-mappings/{mapping_id}",
        json={
            "onet_code": "15-1251.00",
            "onet_title": "Computer Programmers",
            "is_confirmed": True
        }
    )

    assert response.status_code == 200
    mock_role_mapping_service.update.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_confirm_mappings(client, mock_role_mapping_service):
    """POST /discovery/sessions/{id}/role-mappings/confirm should bulk confirm."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/role-mappings/confirm",
        json={"threshold": 0.8}
    )

    assert response.status_code == 200
    data = response.json()
    assert "confirmed_count" in data


@pytest.mark.asyncio
async def test_search_onet_occupations(client, mock_onet_service):
    """GET /discovery/onet/search should search O*NET occupations."""
    mock_onet_service.search.return_value = [
        {"code": "15-1252.00", "title": "Software Developers", "score": 0.95}
    ]

    response = await client.get(
        "/discovery/onet/search",
        params={"q": "software engineer"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "code" in data[0]
    assert "title" in data[0]


@pytest.mark.asyncio
async def test_get_onet_occupation_details(client, mock_onet_service):
    """GET /discovery/onet/{code} should return occupation details."""
    mock_onet_service.get_occupation.return_value = {
        "code": "15-1252.00",
        "title": "Software Developers",
        "description": "Develop software...",
        "gwas": [{"id": "4.A.2.a.4", "title": "Analyzing Data"}]
    }

    response = await client.get("/discovery/onet/15-1252.00")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "15-1252.00"
    assert "gwas" in data
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_role_mappings.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_role_mappings.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/role_mappings.py discovery/api/src/discovery/schemas/role_mapping.py
git commit -m "feat(discovery): add role mapping endpoints with O*NET search"
```

---

### Task 42: Activity Selection Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/activities.py`
- Create: `discovery/api/src/discovery/schemas/activity.py`
- Test: `discovery/api/tests/unit/routers/test_activities.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_activities.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_get_activities_for_session(client, mock_activity_service):
    """GET /discovery/sessions/{id}/activities should return activities grouped by GWA."""
    session_id = str(uuid4())
    mock_activity_service.get_grouped_by_gwa.return_value = {
        "4.A.2.a.4": {
            "gwa_id": "4.A.2.a.4",
            "gwa_title": "Analyzing Data or Information",
            "ai_exposure_score": 0.72,
            "dwas": [
                {
                    "id": str(uuid4()),
                    "dwa_id": "4.A.2.a.4.1",
                    "dwa_title": "Analyze business data",
                    "is_selected": False
                }
            ]
        }
    }

    response = await client.get(f"/discovery/sessions/{session_id}/activities")

    assert response.status_code == 200
    data = response.json()
    assert "4.A.2.a.4" in data
    assert "dwas" in data["4.A.2.a.4"]


@pytest.mark.asyncio
async def test_update_dwa_selection(client, mock_activity_service):
    """PUT /discovery/activities/{id} should update DWA selection."""
    activity_id = str(uuid4())

    response = await client.put(
        f"/discovery/activities/{activity_id}",
        json={"is_selected": True}
    )

    assert response.status_code == 200
    mock_activity_service.update_selection.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_select_dwas(client, mock_activity_service):
    """POST /discovery/sessions/{id}/activities/select should bulk select."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/activities/select",
        json={
            "dwa_ids": [str(uuid4()), str(uuid4())],
            "is_selected": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data


@pytest.mark.asyncio
async def test_bulk_deselect_dwas(client, mock_activity_service):
    """POST /discovery/sessions/{id}/activities/select can deselect."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/activities/select",
        json={
            "dwa_ids": [str(uuid4())],
            "is_selected": False
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_selected_count(client, mock_activity_service):
    """GET /discovery/sessions/{id}/activities/count should return selection stats."""
    session_id = str(uuid4())
    mock_activity_service.get_selection_stats.return_value = {
        "total_dwas": 150,
        "selected_dwas": 42,
        "gwas_with_selections": 8
    }

    response = await client.get(f"/discovery/sessions/{session_id}/activities/count")

    assert response.status_code == 200
    data = response.json()
    assert data["selected_dwas"] == 42
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_activities.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_activities.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/activities.py discovery/api/src/discovery/schemas/activity.py
git commit -m "feat(discovery): add activity selection endpoints with bulk operations"
```

---

### Task 43: Analysis Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/analysis.py`
- Create: `discovery/api/src/discovery/schemas/analysis.py`
- Test: `discovery/api/tests/unit/routers/test_analysis.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_analysis.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_trigger_analysis(client, mock_scoring_service):
    """POST /discovery/sessions/{id}/analyze should trigger scoring."""
    session_id = str(uuid4())

    response = await client.post(f"/discovery/sessions/{session_id}/analyze")

    assert response.status_code == 202
    data = response.json()
    assert "status" in data
    mock_scoring_service.score_session.assert_called_once()


@pytest.mark.asyncio
async def test_get_analysis_by_dimension(client, mock_analysis_service):
    """GET /discovery/sessions/{id}/analysis/{dimension} should return scores."""
    session_id = str(uuid4())
    mock_analysis_service.get_by_dimension.return_value = {
        "dimension": "ROLE",
        "results": [
            {
                "id": str(uuid4()),
                "name": "Software Engineer",
                "ai_exposure_score": 0.72,
                "impact_score": 0.85,
                "complexity_score": 0.65,
                "priority_score": 0.78,
                "priority_tier": "HIGH"
            }
        ]
    }

    response = await client.get(f"/discovery/sessions/{session_id}/analysis/ROLE")

    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "ROLE"
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_get_analysis_all_dimensions(client, mock_analysis_service):
    """GET /discovery/sessions/{id}/analysis should return all dimensions."""
    session_id = str(uuid4())
    mock_analysis_service.get_all_dimensions.return_value = {
        "ROLE": {"count": 15, "avg_exposure": 0.68},
        "DEPARTMENT": {"count": 5, "avg_exposure": 0.71},
        "LOB": {"count": 3, "avg_exposure": 0.65}
    }

    response = await client.get(f"/discovery/sessions/{session_id}/analysis")

    assert response.status_code == 200
    data = response.json()
    assert "ROLE" in data
    assert "DEPARTMENT" in data


@pytest.mark.asyncio
async def test_get_analysis_not_ready(client, mock_analysis_service):
    """GET should return 404 if analysis not yet run."""
    session_id = str(uuid4())
    mock_analysis_service.get_by_dimension.return_value = None

    response = await client.get(f"/discovery/sessions/{session_id}/analysis/ROLE")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_priority_tier_filter(client, mock_analysis_service):
    """GET should support filtering by priority tier."""
    session_id = str(uuid4())
    mock_analysis_service.get_by_dimension.return_value = {
        "dimension": "ROLE",
        "results": [
            {"name": "High Priority Role", "priority_tier": "HIGH"}
        ]
    }

    response = await client.get(
        f"/discovery/sessions/{session_id}/analysis/ROLE",
        params={"priority_tier": "HIGH"}
    )

    assert response.status_code == 200
    data = response.json()
    assert all(r["priority_tier"] == "HIGH" for r in data["results"])
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_analysis.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_analysis.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/analysis.py discovery/api/src/discovery/schemas/analysis.py
git commit -m "feat(discovery): add analysis endpoints with dimension filtering"
```

---

### Task 44: Roadmap Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/roadmap.py`
- Create: `discovery/api/src/discovery/schemas/roadmap.py`
- Test: `discovery/api/tests/unit/routers/test_roadmap.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_roadmap.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_get_roadmap_items(client, mock_roadmap_service):
    """GET /discovery/sessions/{id}/roadmap should return prioritized candidates."""
    session_id = str(uuid4())
    mock_roadmap_service.get_roadmap.return_value = [
        {
            "id": str(uuid4()),
            "role_name": "Data Analyst",
            "priority_score": 0.92,
            "priority_tier": "HIGH",
            "phase": "NOW",
            "estimated_effort": "medium"
        }
    ]

    response = await client.get(f"/discovery/sessions/{session_id}/roadmap")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phase"] == "NOW"


@pytest.mark.asyncio
async def test_update_roadmap_item_phase(client, mock_roadmap_service):
    """PUT /discovery/roadmap/{id} should update phase."""
    item_id = str(uuid4())

    response = await client.put(
        f"/discovery/roadmap/{item_id}",
        json={"phase": "NEXT"}
    )

    assert response.status_code == 200
    mock_roadmap_service.update_phase.assert_called_once()


@pytest.mark.asyncio
async def test_reorder_roadmap_items(client, mock_roadmap_service):
    """POST /discovery/sessions/{id}/roadmap/reorder should reorder items."""
    session_id = str(uuid4())
    item_ids = [str(uuid4()), str(uuid4()), str(uuid4())]

    response = await client.post(
        f"/discovery/sessions/{session_id}/roadmap/reorder",
        json={"item_ids": item_ids}
    )

    assert response.status_code == 200
    mock_roadmap_service.reorder.assert_called_once()


@pytest.mark.asyncio
async def test_get_roadmap_by_phase(client, mock_roadmap_service):
    """GET should support filtering by phase."""
    session_id = str(uuid4())
    mock_roadmap_service.get_roadmap.return_value = [
        {"id": str(uuid4()), "phase": "NOW"}
    ]

    response = await client.get(
        f"/discovery/sessions/{session_id}/roadmap",
        params={"phase": "NOW"}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bulk_update_phases(client, mock_roadmap_service):
    """POST /discovery/sessions/{id}/roadmap/bulk-update should bulk update."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/roadmap/bulk-update",
        json={
            "updates": [
                {"id": str(uuid4()), "phase": "NOW"},
                {"id": str(uuid4()), "phase": "NEXT"}
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_roadmap.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_roadmap.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/roadmap.py discovery/api/src/discovery/schemas/roadmap.py
git commit -m "feat(discovery): add roadmap endpoints with phase management"
```

---

### Task 45: Chat/Message Endpoint

**Files:**
- Create: `discovery/api/src/discovery/routers/chat.py`
- Create: `discovery/api/src/discovery/schemas/chat.py`
- Test: `discovery/api/tests/unit/routers/test_chat.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_chat.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_send_message(client, mock_orchestrator):
    """POST /discovery/sessions/{id}/chat should send message to orchestrator."""
    session_id = str(uuid4())
    mock_orchestrator.process_message.return_value = {
        "response": "I've analyzed your data. Here are the top 5 roles...",
        "quick_actions": [
            {"label": "Show details", "action": "show_details"},
            {"label": "Export results", "action": "export"}
        ]
    }

    response = await client.post(
        f"/discovery/sessions/{session_id}/chat",
        json={"message": "What are the highest priority roles?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "quick_actions" in data


@pytest.mark.asyncio
async def test_get_chat_history(client, mock_chat_service):
    """GET /discovery/sessions/{id}/chat should return message history."""
    session_id = str(uuid4())
    mock_chat_service.get_history.return_value = [
        {"role": "user", "content": "Hello", "timestamp": "2026-01-31T10:00:00Z"},
        {"role": "assistant", "content": "Hi! Let's start...", "timestamp": "2026-01-31T10:00:01Z"}
    ]

    response = await client.get(f"/discovery/sessions/{session_id}/chat")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_stream_response(client, mock_orchestrator):
    """GET /discovery/sessions/{id}/chat/stream should stream response."""
    session_id = str(uuid4())

    async with client.stream(
        "GET",
        f"/discovery/sessions/{session_id}/chat/stream"
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


@pytest.mark.asyncio
async def test_execute_quick_action(client, mock_orchestrator):
    """POST /discovery/sessions/{id}/chat/action should execute action."""
    session_id = str(uuid4())
    mock_orchestrator.execute_action.return_value = {
        "response": "Here are the details...",
        "data": {"roles": []}
    }

    response = await client.post(
        f"/discovery/sessions/{session_id}/chat/action",
        json={"action": "show_details", "params": {"role_id": str(uuid4())}}
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data


@pytest.mark.asyncio
async def test_chat_with_context(client, mock_orchestrator):
    """POST should include session context in orchestrator call."""
    session_id = str(uuid4())

    response = await client.post(
        f"/discovery/sessions/{session_id}/chat",
        json={"message": "Continue where we left off"}
    )

    assert response.status_code == 200
    # Verify orchestrator received session context
    call_args = mock_orchestrator.process_message.call_args
    assert "session_id" in call_args.kwargs or session_id in str(call_args)
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_chat.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_chat.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/chat.py discovery/api/src/discovery/schemas/chat.py
git commit -m "feat(discovery): add chat endpoints with SSE streaming"
```

---

### Task 46: Export Endpoints

**Files:**
- Create: `discovery/api/src/discovery/routers/exports.py`
- Create: `discovery/api/src/discovery/services/export_service.py`
- Test: `discovery/api/tests/unit/routers/test_exports.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_exports.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_export_csv(client, mock_export_service):
    """GET /discovery/sessions/{id}/export/csv should return CSV."""
    session_id = str(uuid4())
    mock_export_service.generate_csv.return_value = b"Role,Score\nEngineer,0.85"

    response = await client.get(f"/discovery/sessions/{session_id}/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert response.headers["content-disposition"].startswith("attachment")
    assert b"Role,Score" in response.content


@pytest.mark.asyncio
async def test_export_excel(client, mock_export_service):
    """GET /discovery/sessions/{id}/export/xlsx should return Excel file."""
    session_id = str(uuid4())
    mock_export_service.generate_xlsx.return_value = b"fake xlsx bytes"

    response = await client.get(f"/discovery/sessions/{session_id}/export/xlsx")

    assert response.status_code == 200
    assert "spreadsheet" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_export_pdf(client, mock_export_service):
    """GET /discovery/sessions/{id}/export/pdf should return PDF report."""
    session_id = str(uuid4())
    mock_export_service.generate_pdf.return_value = b"%PDF-1.4 fake pdf"

    response = await client.get(f"/discovery/sessions/{session_id}/export/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_export_with_dimension_filter(client, mock_export_service):
    """GET export should support dimension filtering."""
    session_id = str(uuid4())

    response = await client.get(
        f"/discovery/sessions/{session_id}/export/csv",
        params={"dimension": "ROLE"}
    )

    assert response.status_code == 200
    mock_export_service.generate_csv.assert_called_with(
        session_id=session_id,
        dimension="ROLE"
    )


@pytest.mark.asyncio
async def test_export_handoff_bundle(client, mock_export_service):
    """GET /discovery/sessions/{id}/export/handoff should return full bundle."""
    session_id = str(uuid4())
    mock_export_service.generate_handoff_bundle.return_value = {
        "session_summary": {},
        "role_mappings": [],
        "analysis_results": [],
        "roadmap": []
    }

    response = await client.get(f"/discovery/sessions/{session_id}/export/handoff")

    assert response.status_code == 200
    data = response.json()
    assert "session_summary" in data
    assert "roadmap" in data
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_exports.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_exports.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/exports.py discovery/api/src/discovery/services/export_service.py
git commit -m "feat(discovery): add export endpoints for CSV/Excel/PDF"
```

---

### Task 47: Handoff to Build Endpoint

**Files:**
- Create: `discovery/api/src/discovery/routers/handoff.py`
- Create: `discovery/api/src/discovery/services/handoff_service.py`
- Test: `discovery/api/tests/unit/routers/test_handoff.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/routers/test_handoff.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_submit_to_intake(client, mock_handoff_service):
    """POST /discovery/sessions/{id}/handoff should submit to intake."""
    session_id = str(uuid4())
    mock_handoff_service.submit_to_intake.return_value = {
        "intake_request_id": str(uuid4()),
        "status": "submitted",
        "candidates_count": 5
    }

    response = await client.post(
        f"/discovery/sessions/{session_id}/handoff",
        json={
            "candidate_ids": [str(uuid4()), str(uuid4())],
            "notes": "Prioritize these for Q1"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "intake_request_id" in data
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_submit_all_high_priority(client, mock_handoff_service):
    """POST should support submitting all high priority candidates."""
    session_id = str(uuid4())
    mock_handoff_service.submit_to_intake.return_value = {
        "intake_request_id": str(uuid4()),
        "candidates_count": 10
    }

    response = await client.post(
        f"/discovery/sessions/{session_id}/handoff",
        json={"priority_tier": "HIGH"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["candidates_count"] == 10


@pytest.mark.asyncio
async def test_validate_before_handoff(client, mock_handoff_service):
    """POST /discovery/sessions/{id}/handoff/validate should check readiness."""
    session_id = str(uuid4())
    mock_handoff_service.validate_readiness.return_value = {
        "is_ready": True,
        "warnings": [],
        "errors": []
    }

    response = await client.post(f"/discovery/sessions/{session_id}/handoff/validate")

    assert response.status_code == 200
    data = response.json()
    assert data["is_ready"] is True


@pytest.mark.asyncio
async def test_handoff_not_ready(client, mock_handoff_service):
    """POST handoff should fail if validation fails."""
    session_id = str(uuid4())
    mock_handoff_service.validate_readiness.return_value = {
        "is_ready": False,
        "errors": ["No candidates selected"]
    }

    response = await client.post(
        f"/discovery/sessions/{session_id}/handoff",
        json={}
    )

    assert response.status_code == 400
    assert "errors" in response.json()


@pytest.mark.asyncio
async def test_get_handoff_status(client, mock_handoff_service):
    """GET /discovery/sessions/{id}/handoff should return handoff status."""
    session_id = str(uuid4())
    mock_handoff_service.get_status.return_value = {
        "session_id": session_id,
        "handed_off": True,
        "intake_request_id": str(uuid4()),
        "handed_off_at": "2026-01-31T12:00:00Z"
    }

    response = await client.get(f"/discovery/sessions/{session_id}/handoff")

    assert response.status_code == 200
    data = response.json()
    assert data["handed_off"] is True
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_handoff.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/routers/test_handoff.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/routers/handoff.py discovery/api/src/discovery/services/handoff_service.py
git commit -m "feat(discovery): add handoff endpoint for intake submission"
```

---

### Task 48: Wire Up to Main App

**Files:**
- Modify: `discovery/api/src/discovery/main.py`
- Modify: `discovery/api/src/discovery/routers/__init__.py`
- Test: `discovery/api/tests/unit/test_main_routes.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/test_main_routes.py
import pytest
from httpx import AsyncClient

from discovery.main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_all_routers_registered(client):
    """All discovery routers should be registered."""
    # Get OpenAPI schema
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    # Session routes
    assert "/discovery/sessions" in paths
    assert "/discovery/sessions/{session_id}" in paths

    # Upload routes
    assert "/discovery/sessions/{session_id}/upload" in paths

    # Role mapping routes
    assert "/discovery/sessions/{session_id}/role-mappings" in paths
    assert "/discovery/onet/search" in paths

    # Activity routes
    assert "/discovery/sessions/{session_id}/activities" in paths

    # Analysis routes
    assert "/discovery/sessions/{session_id}/analysis" in paths

    # Roadmap routes
    assert "/discovery/sessions/{session_id}/roadmap" in paths

    # Chat routes
    assert "/discovery/sessions/{session_id}/chat" in paths

    # Export routes
    assert "/discovery/sessions/{session_id}/export/csv" in paths

    # Handoff routes
    assert "/discovery/sessions/{session_id}/handoff" in paths


@pytest.mark.asyncio
async def test_health_check_still_works(client):
    """Health check should still be accessible."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cors_headers(client):
    """CORS should be configured for frontend."""
    response = await client.options(
        "/discovery/sessions",
        headers={"Origin": "http://localhost:3000"}
    )
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_api_prefix(client):
    """All discovery routes should have /discovery prefix."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]

    discovery_paths = [p for p in paths if p.startswith("/discovery")]
    non_discovery_paths = [p for p in paths if not p.startswith("/discovery") and not p.startswith("/health") and not p.startswith("/openapi")]

    assert len(discovery_paths) > 0
    # Only health and openapi should be outside /discovery
    assert len(non_discovery_paths) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/test_main_routes.py -v`
Expected: FAIL with missing routes

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/test_main_routes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/main.py discovery/api/src/discovery/routers/__init__.py
git commit -m "feat(discovery): wire up all routers to main app"
```

---

## Part 7: Frontend Components (Tasks 49-65)

### Task 49: Discovery Layout Component

**Files:**
- Create: `frontend/src/components/features/discovery/DiscoveryLayout.tsx`
- Create: `frontend/src/components/features/discovery/index.ts`
- Test: `frontend/tests/unit/discovery/DiscoveryLayout.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/DiscoveryLayout.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { DiscoveryLayout } from '@/components/features/discovery/DiscoveryLayout'

describe('DiscoveryLayout', () => {
  it('renders the layout with header and main content area', () => {
    render(
      <DiscoveryLayout>
        <div data-testid="child-content">Content</div>
      </DiscoveryLayout>
    )

    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('renders the step indicator in sidebar', () => {
    render(<DiscoveryLayout currentStep={2} totalSteps={5}><div /></DiscoveryLayout>)

    expect(screen.getByRole('navigation', { name: /steps/i })).toBeInTheDocument()
  })

  it('renders the chat panel in sidebar', () => {
    render(<DiscoveryLayout><div /></DiscoveryLayout>)

    expect(screen.getByRole('complementary', { name: /chat/i })).toBeInTheDocument()
  })

  it('applies correct grid layout classes', () => {
    const { container } = render(<DiscoveryLayout><div /></DiscoveryLayout>)

    const layout = container.firstChild
    expect(layout).toHaveClass('grid')
  })

  it('shows session title when provided', () => {
    render(<DiscoveryLayout sessionTitle="Q1 Discovery"><div /></DiscoveryLayout>)

    expect(screen.getByText('Q1 Discovery')).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoveryLayout.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoveryLayout.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/
git commit -m "feat(discovery): add DiscoveryLayout component with sidebar"
```

---

### Task 50: Step Indicator Component

**Files:**
- Create: `frontend/src/components/features/discovery/StepIndicator.tsx`
- Test: `frontend/tests/unit/discovery/StepIndicator.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/StepIndicator.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StepIndicator } from '@/components/features/discovery/StepIndicator'

const steps = [
  { id: 1, title: 'Upload', status: 'completed' },
  { id: 2, title: 'Map Roles', status: 'current' },
  { id: 3, title: 'Activities', status: 'upcoming' },
  { id: 4, title: 'Analysis', status: 'upcoming' },
  { id: 5, title: 'Roadmap', status: 'upcoming' },
]

describe('StepIndicator', () => {
  it('renders all steps', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    expect(screen.getByText('Upload')).toBeInTheDocument()
    expect(screen.getByText('Map Roles')).toBeInTheDocument()
    expect(screen.getByText('Roadmap')).toBeInTheDocument()
  })

  it('marks completed steps with checkmark', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const uploadStep = screen.getByText('Upload').closest('li')
    expect(uploadStep).toHaveAttribute('data-status', 'completed')
  })

  it('highlights current step', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const currentStep = screen.getByText('Map Roles').closest('li')
    expect(currentStep).toHaveAttribute('data-status', 'current')
  })

  it('dims upcoming steps', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const upcomingStep = screen.getByText('Activities').closest('li')
    expect(upcomingStep).toHaveAttribute('data-status', 'upcoming')
  })

  it('supports vertical orientation', () => {
    const { container } = render(
      <StepIndicator steps={steps} currentStep={2} orientation="vertical" />
    )

    expect(container.firstChild).toHaveClass('flex-col')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/StepIndicator.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/StepIndicator.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/StepIndicator.tsx
git commit -m "feat(discovery): add StepIndicator component with 5-step workflow"
```

---

### Task 51: Chat Panel Component

**Files:**
- Create: `frontend/src/components/features/discovery/ChatPanel.tsx`
- Create: `frontend/src/hooks/useDiscoveryChat.ts`
- Test: `frontend/tests/unit/discovery/ChatPanel.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/ChatPanel.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatPanel } from '@/components/features/discovery/ChatPanel'

describe('ChatPanel', () => {
  it('renders message input', () => {
    render(<ChatPanel sessionId="test-session" />)

    expect(screen.getByRole('textbox', { name: /message/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('displays message history', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hello' },
      { id: '2', role: 'assistant', content: 'Hi! How can I help?' },
    ]

    render(<ChatPanel sessionId="test-session" initialMessages={messages} />)

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi! How can I help?')).toBeInTheDocument()
  })

  it('sends message on submit', async () => {
    const onSend = vi.fn()
    render(<ChatPanel sessionId="test-session" onSendMessage={onSend} />)

    const input = screen.getByRole('textbox', { name: /message/i })
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith('Test message')
    })
  })

  it('shows loading indicator while waiting for response', () => {
    render(<ChatPanel sessionId="test-session" isLoading={true} />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders quick action chips when provided', () => {
    const quickActions = [
      { label: 'Show details', action: 'show_details' },
      { label: 'Export', action: 'export' },
    ]

    render(<ChatPanel sessionId="test-session" quickActions={quickActions} />)

    expect(screen.getByText('Show details')).toBeInTheDocument()
    expect(screen.getByText('Export')).toBeInTheDocument()
  })

  it('auto-scrolls to latest message', async () => {
    const { rerender } = render(<ChatPanel sessionId="test-session" initialMessages={[]} />)

    const messages = [
      { id: '1', role: 'assistant', content: 'New message!' },
    ]
    rerender(<ChatPanel sessionId="test-session" initialMessages={messages} />)

    // Verify scroll container exists
    expect(screen.getByRole('log')).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/ChatPanel.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/ChatPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/ChatPanel.tsx frontend/src/hooks/useDiscoveryChat.ts
git commit -m "feat(discovery): add ChatPanel with message history and quick actions"
```

---

### Task 52: Quick Action Chips Component

**Files:**
- Create: `frontend/src/components/features/discovery/QuickActionChips.tsx`
- Test: `frontend/tests/unit/discovery/QuickActionChips.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/QuickActionChips.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QuickActionChips } from '@/components/features/discovery/QuickActionChips'

const chips = [
  { label: 'Confirm all', action: 'confirm_all', variant: 'primary' },
  { label: 'Skip step', action: 'skip', variant: 'secondary' },
  { label: 'Show help', action: 'help', variant: 'ghost' },
]

describe('QuickActionChips', () => {
  it('renders all chips', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    expect(screen.getByText('Confirm all')).toBeInTheDocument()
    expect(screen.getByText('Skip step')).toBeInTheDocument()
    expect(screen.getByText('Show help')).toBeInTheDocument()
  })

  it('calls onAction with correct action when clicked', () => {
    const onAction = vi.fn()
    render(<QuickActionChips chips={chips} onAction={onAction} />)

    fireEvent.click(screen.getByText('Confirm all'))

    expect(onAction).toHaveBeenCalledWith('confirm_all')
  })

  it('applies variant styling', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    const primaryChip = screen.getByText('Confirm all')
    expect(primaryChip).toHaveClass('bg-primary')
  })

  it('disables chips when loading', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} isLoading={true} />)

    const chip = screen.getByText('Confirm all')
    expect(chip).toBeDisabled()
  })

  it('handles empty chips array', () => {
    const { container } = render(<QuickActionChips chips={[]} onAction={vi.fn()} />)

    expect(container.firstChild).toBeEmptyDOMElement()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/QuickActionChips.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/QuickActionChips.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/QuickActionChips.tsx
git commit -m "feat(discovery): add QuickActionChips for contextual actions"
```

---

### Task 53: Upload Step Page

**Files:**
- Create: `frontend/src/pages/discovery/UploadStep.tsx`
- Create: `frontend/src/hooks/useFileUpload.ts`
- Test: `frontend/tests/unit/discovery/UploadStep.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/UploadStep.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { UploadStep } from '@/pages/discovery/UploadStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/upload']}>
      <Routes>
        <Route path="/discovery/:sessionId/upload" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('UploadStep', () => {
  it('renders upload instructions', () => {
    renderWithRouter(<UploadStep />)

    expect(screen.getByText(/upload your organization data/i)).toBeInTheDocument()
    expect(screen.getByText(/csv or xlsx/i)).toBeInTheDocument()
  })

  it('shows file drop zone', () => {
    renderWithRouter(<UploadStep />)

    expect(screen.getByRole('button', { name: /browse files/i })).toBeInTheDocument()
  })

  it('displays uploaded file info after upload', async () => {
    renderWithRouter(<UploadStep />)

    const file = new File(['name,role\nJohn,Engineer'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')

    // Simulate file drop
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    })

    await waitFor(() => {
      expect(screen.getByText('data.csv')).toBeInTheDocument()
    })
  })

  it('shows column mapping preview after upload', async () => {
    renderWithRouter(<UploadStep />)

    // After file is uploaded, should show mapping preview
    expect(screen.queryByText(/detected columns/i)).toBeInTheDocument()
  })

  it('enables next step button when upload complete', async () => {
    renderWithRouter(<UploadStep />)

    // Initially disabled
    expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/UploadStep.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/UploadStep.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/UploadStep.tsx frontend/src/hooks/useFileUpload.ts
git commit -m "feat(discovery): add UploadStep page with file handling"
```

---

### Task 54: File Drop Zone Component

**Files:**
- Create: `frontend/src/components/features/discovery/FileDropZone.tsx`
- Test: `frontend/tests/unit/discovery/FileDropZone.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/FileDropZone.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { FileDropZone } from '@/components/features/discovery/FileDropZone'

describe('FileDropZone', () => {
  it('renders drop zone with instructions', () => {
    render(<FileDropZone onFileDrop={vi.fn()} />)

    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /browse/i })).toBeInTheDocument()
  })

  it('accepts CSV files', async () => {
    const onFileDrop = vi.fn()
    render(<FileDropZone onFileDrop={onFileDrop} accept={['.csv', '.xlsx']} />)

    const file = new File(['content'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    await waitFor(() => {
      expect(onFileDrop).toHaveBeenCalledWith(file)
    })
  })

  it('rejects unsupported file types', async () => {
    const onFileDrop = vi.fn()
    const onError = vi.fn()
    render(<FileDropZone onFileDrop={onFileDrop} onError={onError} accept={['.csv']} />)

    const file = new File(['content'], 'report.pdf', { type: 'application/pdf' })
    const dropzone = screen.getByTestId('file-dropzone')

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    await waitFor(() => {
      expect(onFileDrop).not.toHaveBeenCalled()
      expect(onError).toHaveBeenCalled()
    })
  })

  it('shows drag over state', () => {
    render(<FileDropZone onFileDrop={vi.fn()} />)

    const dropzone = screen.getByTestId('file-dropzone')
    fireEvent.dragEnter(dropzone)

    expect(dropzone).toHaveClass('border-primary')
  })

  it('shows file size limit', () => {
    render(<FileDropZone onFileDrop={vi.fn()} maxSizeMB={10} />)

    expect(screen.getByText(/10 MB/i)).toBeInTheDocument()
  })

  it('shows uploading state', () => {
    render(<FileDropZone onFileDrop={vi.fn()} isUploading={true} progress={50} />)

    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/FileDropZone.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/FileDropZone.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/FileDropZone.tsx
git commit -m "feat(discovery): add FileDropZone with drag-and-drop support"
```

---

### Task 55: Column Mapping Preview

**Files:**
- Create: `frontend/src/components/features/discovery/ColumnMappingPreview.tsx`
- Test: `frontend/tests/unit/discovery/ColumnMappingPreview.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/ColumnMappingPreview.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ColumnMappingPreview } from '@/components/features/discovery/ColumnMappingPreview'

const schema = {
  columns: ['Name', 'Job Title', 'Department', 'Location'],
  sampleRows: [
    ['John Smith', 'Software Engineer', 'Engineering', 'NYC'],
    ['Jane Doe', 'Data Analyst', 'Analytics', 'SF'],
  ],
}

const mappings = {
  role: 'Job Title',
  department: 'Department',
  geography: 'Location',
}

describe('ColumnMappingPreview', () => {
  it('renders detected columns', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Job Title')).toBeInTheDocument()
    expect(screen.getByText('Department')).toBeInTheDocument()
  })

  it('shows sample data rows', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Software Engineer')).toBeInTheDocument()
  })

  it('highlights mapped columns', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    const roleColumn = screen.getByText('Job Title').closest('th')
    expect(roleColumn).toHaveClass('bg-primary-50')
  })

  it('allows changing column mapping', () => {
    const onMappingChange = vi.fn()
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={onMappingChange} />)

    const select = screen.getByLabelText(/role column/i)
    fireEvent.change(select, { target: { value: 'Name' } })

    expect(onMappingChange).toHaveBeenCalledWith({ ...mappings, role: 'Name' })
  })

  it('shows required column indicators', () => {
    render(<ColumnMappingPreview schema={schema} mappings={{}} onMappingChange={vi.fn()} />)

    expect(screen.getByText(/role.*required/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/ColumnMappingPreview.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/ColumnMappingPreview.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/ColumnMappingPreview.tsx
git commit -m "feat(discovery): add ColumnMappingPreview with sample data"
```

---

### Task 56: Map Roles Step Page

**Files:**
- Create: `frontend/src/pages/discovery/MapRolesStep.tsx`
- Create: `frontend/src/hooks/useRoleMappings.ts`
- Test: `frontend/tests/unit/discovery/MapRolesStep.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/MapRolesStep.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MapRolesStep } from '@/pages/discovery/MapRolesStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/map-roles']}>
      <Routes>
        <Route path="/discovery/:sessionId/map-roles" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('MapRolesStep', () => {
  it('renders role mapping list', () => {
    renderWithRouter(<MapRolesStep />)

    expect(screen.getByText(/map your roles/i)).toBeInTheDocument()
  })

  it('shows auto-detected mappings', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('allows confirming a mapping', async () => {
    renderWithRouter(<MapRolesStep />)

    const confirmButton = await screen.findByRole('button', { name: /confirm/i })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(screen.getByTestId('confirmed-badge')).toBeInTheDocument()
    })
  })

  it('allows bulk confirm above threshold', async () => {
    renderWithRouter(<MapRolesStep />)

    const bulkConfirmButton = screen.getByRole('button', { name: /confirm all above/i })
    expect(bulkConfirmButton).toBeInTheDocument()
  })

  it('shows confidence score for each mapping', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByText(/95%/)).toBeInTheDocument()
    })
  })

  it('enables search to remap roles', async () => {
    renderWithRouter(<MapRolesStep />)

    const searchInput = screen.getByRole('combobox', { name: /search o\*net/i })
    expect(searchInput).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/MapRolesStep.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/MapRolesStep.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/MapRolesStep.tsx frontend/src/hooks/useRoleMappings.ts
git commit -m "feat(discovery): add MapRolesStep page with role confirmation"
```

---

### Task 57: Role Mapping Card Component

**Files:**
- Create: `frontend/src/components/features/discovery/RoleMappingCard.tsx`
- Test: `frontend/tests/unit/discovery/RoleMappingCard.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/RoleMappingCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RoleMappingCard } from '@/components/features/discovery/RoleMappingCard'

const mapping = {
  id: '1',
  sourceRole: 'Software Engineer',
  onetCode: '15-1252.00',
  onetTitle: 'Software Developers',
  confidenceScore: 0.95,
  isConfirmed: false,
  headcount: 45,
}

describe('RoleMappingCard', () => {
  it('renders source role and O*NET mapping', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('Software Engineer')).toBeInTheDocument()
    expect(screen.getByText('Software Developers')).toBeInTheDocument()
    expect(screen.getByText('15-1252.00')).toBeInTheDocument()
  })

  it('shows confidence score as percentage', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  it('shows headcount', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('45 employees')).toBeInTheDocument()
  })

  it('calls onConfirm when confirm clicked', () => {
    const onConfirm = vi.fn()
    render(<RoleMappingCard mapping={mapping} onConfirm={onConfirm} onRemap={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))

    expect(onConfirm).toHaveBeenCalledWith(mapping.id)
  })

  it('calls onRemap when remap clicked', () => {
    const onRemap = vi.fn()
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={onRemap} />)

    fireEvent.click(screen.getByRole('button', { name: /remap/i }))

    expect(onRemap).toHaveBeenCalledWith(mapping.id)
  })

  it('shows confirmed state', () => {
    const confirmedMapping = { ...mapping, isConfirmed: true }
    render(<RoleMappingCard mapping={confirmedMapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByTestId('confirmed-badge')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /confirm/i })).not.toBeInTheDocument()
  })

  it('shows low confidence warning', () => {
    const lowConfidenceMapping = { ...mapping, confidenceScore: 0.45 }
    render(<RoleMappingCard mapping={lowConfidenceMapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText(/low confidence/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/RoleMappingCard.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/RoleMappingCard.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/RoleMappingCard.tsx
git commit -m "feat(discovery): add RoleMappingCard with confirm/remap actions"
```

---

### Task 58: O*NET Search Autocomplete

**Files:**
- Create: `frontend/src/components/features/discovery/OnetSearchAutocomplete.tsx`
- Create: `frontend/src/hooks/useOnetSearch.ts`
- Test: `frontend/tests/unit/discovery/OnetSearchAutocomplete.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/OnetSearchAutocomplete.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { OnetSearchAutocomplete } from '@/components/features/discovery/OnetSearchAutocomplete'

describe('OnetSearchAutocomplete', () => {
  it('renders search input', () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('shows loading state while searching', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('displays search results', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByText('Software Developers')).toBeInTheDocument()
      expect(screen.getByText('15-1252.00')).toBeInTheDocument()
    })
  })

  it('calls onSelect when result clicked', async () => {
    const onSelect = vi.fn()
    render(<OnetSearchAutocomplete onSelect={onSelect} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      fireEvent.click(screen.getByText('Software Developers'))
    })

    expect(onSelect).toHaveBeenCalledWith({
      code: '15-1252.00',
      title: 'Software Developers',
    })
  })

  it('debounces search requests', async () => {
    const { rerender } = render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 's' } })
    fireEvent.change(input, { target: { value: 'so' } })
    fireEvent.change(input, { target: { value: 'sof' } })

    // Should debounce to single request
    await waitFor(() => {
      expect(screen.queryByRole('listbox')).toBeInTheDocument()
    }, { timeout: 500 })
  })

  it('shows no results message', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'xyznotfound123' } })

    await waitFor(() => {
      expect(screen.getByText(/no results/i)).toBeInTheDocument()
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/OnetSearchAutocomplete.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/OnetSearchAutocomplete.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/OnetSearchAutocomplete.tsx frontend/src/hooks/useOnetSearch.ts
git commit -m "feat(discovery): add OnetSearchAutocomplete with debounced search"
```

---

### Task 59: Activities Step Page

**Files:**
- Create: `frontend/src/pages/discovery/ActivitiesStep.tsx`
- Create: `frontend/src/hooks/useActivitySelections.ts`
- Test: `frontend/tests/unit/discovery/ActivitiesStep.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/ActivitiesStep.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ActivitiesStep } from '@/pages/discovery/ActivitiesStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/activities']}>
      <Routes>
        <Route path="/discovery/:sessionId/activities" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ActivitiesStep', () => {
  it('renders GWA groups', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/analyzing data/i)).toBeInTheDocument()
    })
  })

  it('shows AI exposure score for each GWA', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/72%/)).toBeInTheDocument()
    })
  })

  it('expands GWA to show DWAs', async () => {
    renderWithRouter(<ActivitiesStep />)

    const accordion = await screen.findByRole('button', { name: /analyzing data/i })
    fireEvent.click(accordion)

    await waitFor(() => {
      expect(screen.getByText(/analyze business data/i)).toBeInTheDocument()
    })
  })

  it('allows selecting individual DWAs', async () => {
    renderWithRouter(<ActivitiesStep />)

    const accordion = await screen.findByRole('button', { name: /analyzing data/i })
    fireEvent.click(accordion)

    const checkbox = await screen.findByRole('checkbox', { name: /analyze business data/i })
    fireEvent.click(checkbox)

    expect(checkbox).toBeChecked()
  })

  it('shows selection count', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/0 activities selected/i)).toBeInTheDocument()
    })
  })

  it('enables bulk select for high exposure activities', () => {
    renderWithRouter(<ActivitiesStep />)

    expect(screen.getByRole('button', { name: /select high exposure/i })).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/ActivitiesStep.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/ActivitiesStep.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/ActivitiesStep.tsx frontend/src/hooks/useActivitySelections.ts
git commit -m "feat(discovery): add ActivitiesStep page with GWA/DWA selection"
```

---

### Task 60: DWA Accordion Component

**Files:**
- Create: `frontend/src/components/features/discovery/DwaAccordion.tsx`
- Test: `frontend/tests/unit/discovery/DwaAccordion.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/DwaAccordion.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DwaAccordion } from '@/components/features/discovery/DwaAccordion'

const gwaGroup = {
  gwaId: '4.A.2.a.4',
  gwaTitle: 'Analyzing Data or Information',
  aiExposureScore: 0.72,
  dwas: [
    { id: '1', dwaId: '4.A.2.a.4.01', title: 'Analyze business data', isSelected: false },
    { id: '2', dwaId: '4.A.2.a.4.02', title: 'Interpret statistical results', isSelected: true },
  ],
}

describe('DwaAccordion', () => {
  it('renders GWA header with title', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)

    expect(screen.getByText('Analyzing Data or Information')).toBeInTheDocument()
  })

  it('shows AI exposure score badge', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)

    expect(screen.getByText('72%')).toBeInTheDocument()
  })

  it('expands to show DWAs on click', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)

    const header = screen.getByRole('button')
    fireEvent.click(header)

    expect(screen.getByText('Analyze business data')).toBeVisible()
    expect(screen.getByText('Interpret statistical results')).toBeVisible()
  })

  it('shows selection state for each DWA', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} defaultOpen={true} />)

    const selectedCheckbox = screen.getByRole('checkbox', { name: /interpret statistical/i })
    expect(selectedCheckbox).toBeChecked()
  })

  it('calls onDwaToggle when checkbox clicked', () => {
    const onDwaToggle = vi.fn()
    render(<DwaAccordion group={gwaGroup} onDwaToggle={onDwaToggle} defaultOpen={true} />)

    const checkbox = screen.getByRole('checkbox', { name: /analyze business/i })
    fireEvent.click(checkbox)

    expect(onDwaToggle).toHaveBeenCalledWith('1', true)
  })

  it('shows selection count in header', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)

    expect(screen.getByText('1/2 selected')).toBeInTheDocument()
  })

  it('allows select all within group', () => {
    const onDwaToggle = vi.fn()
    render(<DwaAccordion group={gwaGroup} onDwaToggle={onDwaToggle} defaultOpen={true} />)

    const selectAllButton = screen.getByRole('button', { name: /select all/i })
    fireEvent.click(selectAllButton)

    expect(onDwaToggle).toHaveBeenCalledTimes(1)  // Unselected DWA
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/DwaAccordion.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/DwaAccordion.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/DwaAccordion.tsx
git commit -m "feat(discovery): add DwaAccordion with exposure scores and selection"
```

---

### Task 61: Analysis Step Page

**Files:**
- Create: `frontend/src/pages/discovery/AnalysisStep.tsx`
- Create: `frontend/src/hooks/useAnalysisResults.ts`
- Test: `frontend/tests/unit/discovery/AnalysisStep.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/AnalysisStep.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AnalysisStep } from '@/pages/discovery/AnalysisStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/analysis']}>
      <Routes>
        <Route path="/discovery/:sessionId/analysis" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AnalysisStep', () => {
  it('renders dimension tabs', async () => {
    renderWithRouter(<AnalysisStep />)

    expect(screen.getByRole('tab', { name: /role/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /department/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /geography/i })).toBeInTheDocument()
  })

  it('shows analysis results for selected dimension', async () => {
    renderWithRouter(<AnalysisStep />)

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('displays scores for each result', async () => {
    renderWithRouter(<AnalysisStep />)

    await waitFor(() => {
      expect(screen.getByText(/exposure:/i)).toBeInTheDocument()
      expect(screen.getByText(/impact:/i)).toBeInTheDocument()
      expect(screen.getByText(/priority:/i)).toBeInTheDocument()
    })
  })

  it('shows priority tier badges', async () => {
    renderWithRouter(<AnalysisStep />)

    await waitFor(() => {
      expect(screen.getByText('HIGH')).toBeInTheDocument()
    })
  })

  it('switches dimension on tab click', async () => {
    renderWithRouter(<AnalysisStep />)

    fireEvent.click(screen.getByRole('tab', { name: /department/i }))

    await waitFor(() => {
      expect(screen.getByText(/engineering/i)).toBeInTheDocument()
    })
  })

  it('allows filtering by priority tier', () => {
    renderWithRouter(<AnalysisStep />)

    const filterSelect = screen.getByRole('combobox', { name: /filter/i })
    fireEvent.change(filterSelect, { target: { value: 'HIGH' } })

    // Results should be filtered
    expect(screen.queryByText('LOW')).not.toBeInTheDocument()
  })

  it('shows loading state during analysis', () => {
    renderWithRouter(<AnalysisStep />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/AnalysisStep.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/AnalysisStep.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/AnalysisStep.tsx frontend/src/hooks/useAnalysisResults.ts
git commit -m "feat(discovery): add AnalysisStep page with dimension tabs"
```

---

### Task 62: Analysis Tabs Component

**Files:**
- Create: `frontend/src/components/features/discovery/AnalysisTabs.tsx`
- Create: `frontend/src/components/features/discovery/AnalysisResultCard.tsx`
- Test: `frontend/tests/unit/discovery/AnalysisTabs.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/AnalysisTabs.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AnalysisTabs } from '@/components/features/discovery/AnalysisTabs'

const results = {
  ROLE: [
    { id: '1', name: 'Engineer', exposureScore: 0.72, impactScore: 0.85, priorityTier: 'HIGH' },
  ],
  DEPARTMENT: [
    { id: '2', name: 'Engineering', exposureScore: 0.68, impactScore: 0.75, priorityTier: 'MEDIUM' },
  ],
}

describe('AnalysisTabs', () => {
  it('renders tabs for each dimension', () => {
    render(<AnalysisTabs results={results} onDimensionChange={vi.fn()} />)

    expect(screen.getByRole('tab', { name: /role/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /department/i })).toBeInTheDocument()
  })

  it('shows result count in tab', () => {
    render(<AnalysisTabs results={results} onDimensionChange={vi.fn()} />)

    expect(screen.getByText(/role \(1\)/i)).toBeInTheDocument()
  })

  it('renders results for active tab', () => {
    render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

    expect(screen.getByText('Engineer')).toBeInTheDocument()
  })

  it('calls onDimensionChange when tab clicked', () => {
    const onDimensionChange = vi.fn()
    render(<AnalysisTabs results={results} onDimensionChange={onDimensionChange} />)

    fireEvent.click(screen.getByRole('tab', { name: /department/i }))

    expect(onDimensionChange).toHaveBeenCalledWith('DEPARTMENT')
  })

  it('shows empty state when no results', () => {
    render(<AnalysisTabs results={{ ROLE: [] }} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

    expect(screen.getByText(/no results/i)).toBeInTheDocument()
  })

  it('sorts results by priority by default', () => {
    const multipleResults = {
      ROLE: [
        { id: '1', name: 'Low', priorityTier: 'LOW', priorityScore: 0.3 },
        { id: '2', name: 'High', priorityTier: 'HIGH', priorityScore: 0.9 },
      ],
    }
    render(<AnalysisTabs results={multipleResults} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

    const items = screen.getAllByTestId('analysis-result-card')
    expect(items[0]).toHaveTextContent('High')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/AnalysisTabs.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/AnalysisTabs.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/AnalysisTabs.tsx frontend/src/components/features/discovery/AnalysisResultCard.tsx
git commit -m "feat(discovery): add AnalysisTabs with dimension switching"
```

---

### Task 63: Roadmap Step Page

**Files:**
- Create: `frontend/src/pages/discovery/RoadmapStep.tsx`
- Create: `frontend/src/hooks/useRoadmap.ts`
- Test: `frontend/tests/unit/discovery/RoadmapStep.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/RoadmapStep.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RoadmapStep } from '@/pages/discovery/RoadmapStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/roadmap']}>
      <Routes>
        <Route path="/discovery/:sessionId/roadmap" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('RoadmapStep', () => {
  it('renders kanban columns for phases', async () => {
    renderWithRouter(<RoadmapStep />)

    expect(screen.getByText('NOW')).toBeInTheDocument()
    expect(screen.getByText('NEXT')).toBeInTheDocument()
    expect(screen.getByText('LATER')).toBeInTheDocument()
  })

  it('shows candidates in appropriate columns', async () => {
    renderWithRouter(<RoadmapStep />)

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('allows dragging candidates between phases', async () => {
    renderWithRouter(<RoadmapStep />)

    // Drag and drop functionality
    const card = await screen.findByText(/software engineer/i)
    expect(card.closest('[draggable]')).toHaveAttribute('draggable', 'true')
  })

  it('shows candidate scores on cards', async () => {
    renderWithRouter(<RoadmapStep />)

    await waitFor(() => {
      expect(screen.getByText(/priority: 0.92/i)).toBeInTheDocument()
    })
  })

  it('enables export options', () => {
    renderWithRouter(<RoadmapStep />)

    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
  })

  it('shows handoff button', () => {
    renderWithRouter(<RoadmapStep />)

    expect(screen.getByRole('button', { name: /send to intake/i })).toBeInTheDocument()
  })

  it('validates before handoff', async () => {
    renderWithRouter(<RoadmapStep />)

    fireEvent.click(screen.getByRole('button', { name: /send to intake/i }))

    await waitFor(() => {
      expect(screen.getByText(/confirm handoff/i)).toBeInTheDocument()
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/RoadmapStep.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/RoadmapStep.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/RoadmapStep.tsx frontend/src/hooks/useRoadmap.ts
git commit -m "feat(discovery): add RoadmapStep page with kanban and handoff"
```

---

### Task 64: Kanban Timeline Component

**Files:**
- Create: `frontend/src/components/features/discovery/KanbanTimeline.tsx`
- Create: `frontend/src/components/features/discovery/KanbanCard.tsx`
- Test: `frontend/tests/unit/discovery/KanbanTimeline.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/KanbanTimeline.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { KanbanTimeline } from '@/components/features/discovery/KanbanTimeline'

const items = [
  { id: '1', name: 'Data Analyst', phase: 'NOW', priorityScore: 0.92 },
  { id: '2', name: 'Engineer', phase: 'NEXT', priorityScore: 0.78 },
  { id: '3', name: 'Manager', phase: 'LATER', priorityScore: 0.55 },
]

describe('KanbanTimeline', () => {
  it('renders three phase columns', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)

    expect(screen.getByTestId('column-NOW')).toBeInTheDocument()
    expect(screen.getByTestId('column-NEXT')).toBeInTheDocument()
    expect(screen.getByTestId('column-LATER')).toBeInTheDocument()
  })

  it('places items in correct columns', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)

    const nowColumn = screen.getByTestId('column-NOW')
    expect(nowColumn).toHaveTextContent('Data Analyst')
  })

  it('shows column counts', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)

    expect(screen.getByText('NOW (1)')).toBeInTheDocument()
  })

  it('makes cards draggable', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)

    const card = screen.getByText('Data Analyst').closest('[draggable]')
    expect(card).toHaveAttribute('draggable', 'true')
  })

  it('calls onPhaseChange when dropped', () => {
    const onPhaseChange = vi.fn()
    render(<KanbanTimeline items={items} onPhaseChange={onPhaseChange} />)

    // Simulate drag and drop
    const card = screen.getByText('Data Analyst')
    const nextColumn = screen.getByTestId('column-NEXT')

    fireEvent.dragStart(card)
    fireEvent.drop(nextColumn)

    expect(onPhaseChange).toHaveBeenCalledWith('1', 'NEXT')
  })

  it('shows drop zone highlight on drag over', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)

    const nextColumn = screen.getByTestId('column-NEXT')
    fireEvent.dragEnter(nextColumn)

    expect(nextColumn).toHaveClass('ring-2')
  })

  it('renders empty column placeholder', () => {
    const singleItem = [{ id: '1', name: 'Test', phase: 'NOW', priorityScore: 0.9 }]
    render(<KanbanTimeline items={singleItem} onPhaseChange={vi.fn()} />)

    const laterColumn = screen.getByTestId('column-LATER')
    expect(laterColumn).toHaveTextContent(/drag items here/i)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/KanbanTimeline.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/KanbanTimeline.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/KanbanTimeline.tsx frontend/src/components/features/discovery/KanbanCard.tsx
git commit -m "feat(discovery): add KanbanTimeline with drag-and-drop phases"
```

---

### Task 65: Discovery Session List Page

**Files:**
- Create: `frontend/src/pages/discovery/DiscoverySessionList.tsx`
- Create: `frontend/src/hooks/useDiscoverySessions.ts`
- Test: `frontend/tests/unit/discovery/DiscoverySessionList.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/DiscoverySessionList.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DiscoverySessionList } from '@/pages/discovery/DiscoverySessionList'
import { MemoryRouter } from 'react-router-dom'

describe('DiscoverySessionList', () => {
  it('renders list of sessions', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/q1 discovery/i)).toBeInTheDocument()
    })
  })

  it('shows session status', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })
  })

  it('shows current step for each session', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/step 2 of 5/i)).toBeInTheDocument()
    })
  })

  it('allows creating new session', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    const createButton = screen.getByRole('button', { name: /new discovery/i })
    expect(createButton).toBeInTheDocument()
  })

  it('allows deleting a session', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    const deleteButton = await screen.findByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    await waitFor(() => {
      expect(screen.getByText(/confirm delete/i)).toBeInTheDocument()
    })
  })

  it('links to continue session', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    const continueLink = await screen.findByRole('link', { name: /continue/i })
    expect(continueLink).toHaveAttribute('href', expect.stringContaining('/discovery/'))
  })

  it('shows empty state when no sessions', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    // Mock empty response scenario
    await waitFor(() => {
      expect(screen.queryByText(/no sessions/i) || screen.queryByText(/q1 discovery/i)).toBeInTheDocument()
    })
  })

  it('supports pagination', async () => {
    render(
      <MemoryRouter>
        <DiscoverySessionList />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument()
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoverySessionList.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoverySessionList.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/discovery/DiscoverySessionList.tsx frontend/src/hooks/useDiscoverySessions.ts
git commit -m "feat(discovery): add DiscoverySessionList page with session management"
```

---

## Part 8: Integration & Polish (Tasks 66-70)

### Task 66: End-to-End Session Flow Test

**Files:**
- Create: `frontend/tests/e2e/discovery/session-flow.spec.ts`
- Test: (Playwright E2E test)

**Step 1: Write the failing test**

```typescript
// frontend/tests/e2e/discovery/session-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Discovery Session Flow', () => {
  test('completes full 5-step discovery workflow', async ({ page }) => {
    // Step 1: Create new session and upload file
    await page.goto('/discovery')
    await page.click('button:has-text("New Discovery")')

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('tests/fixtures/sample-hr-data.csv')
    await expect(page.locator('text=data.csv')).toBeVisible()
    await page.click('button:has-text("Continue")')

    // Step 2: Map roles
    await expect(page.locator('text=Map your roles')).toBeVisible()
    await page.click('button:has-text("Confirm all above 80%")')
    await page.click('button:has-text("Continue")')

    // Step 3: Select activities
    await expect(page.locator('text=Select activities')).toBeVisible()
    await page.click('button:has-text("Select high exposure")')
    await page.click('button:has-text("Continue")')

    // Step 4: Review analysis
    await expect(page.locator('text=Analysis')).toBeVisible()
    await expect(page.locator('[data-testid="analysis-result-card"]').first()).toBeVisible()
    await page.click('button:has-text("Continue")')

    // Step 5: Build roadmap and handoff
    await expect(page.locator('text=Roadmap')).toBeVisible()
    await expect(page.locator('[data-testid="column-NOW"]')).toBeVisible()
    await page.click('button:has-text("Send to Intake")')
    await page.click('button:has-text("Confirm")')

    // Verify handoff complete
    await expect(page.locator('text=Successfully submitted')).toBeVisible()
  })

  test('saves progress between steps', async ({ page }) => {
    await page.goto('/discovery/test-session/map-roles')
    await page.click('button:has-text("Confirm"):first')

    // Navigate away and back
    await page.goto('/discovery')
    await page.click('a:has-text("Continue")')

    // Verify progress preserved
    await expect(page.locator('[data-testid="confirmed-badge"]')).toBeVisible()
  })

  test('chat panel provides contextual help', async ({ page }) => {
    await page.goto('/discovery/test-session/activities')

    // Send message
    await page.fill('[aria-label="Message"]', 'What activities should I select?')
    await page.click('button:has-text("Send")')

    // Verify response
    await expect(page.locator('text=high AI exposure')).toBeVisible({ timeout: 10000 })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx playwright test tests/e2e/discovery/session-flow.spec.ts`
Expected: FAIL with navigation or element errors

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code - wire up routes and fix any integration issues)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx playwright test tests/e2e/discovery/session-flow.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/tests/e2e/discovery/
git commit -m "test(discovery): add E2E test for complete session flow"
```

---

### Task 67: Chat + UI Coordination

**Files:**
- Create: `discovery/api/src/discovery/services/context_service.py`
- Modify: `frontend/src/hooks/useDiscoveryChat.ts`
- Test: `discovery/api/tests/unit/services/test_context_service.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/services/test_context_service.py
import pytest
from uuid import uuid4

from discovery.services.context_service import ContextService


@pytest.fixture
def context_service():
    return ContextService()


def test_build_context_includes_current_step(context_service):
    """Context should include current step information."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="What should I do next?"
    )

    assert context["current_step"] == 2
    assert context["step_name"] == "Map Roles"


def test_build_context_includes_step_data(context_service):
    """Context should include relevant data for current step."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="Which activities are most important?"
    )

    assert "activities" in context
    assert "gwa_groups" in context["activities"]


def test_context_includes_selection_counts(context_service):
    """Context should include selection counts."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="How many have I selected?"
    )

    assert "selection_count" in context


def test_context_includes_analysis_summary(context_service):
    """Context should include analysis summary when on step 4+."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=4,
        user_message="Show me the top priorities"
    )

    assert "analysis_summary" in context
    assert "top_priorities" in context["analysis_summary"]


def test_suggests_quick_actions_based_on_context(context_service):
    """Should suggest relevant quick actions."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="I'm not sure about this mapping"
    )

    assert "suggested_actions" in context
    assert any("remap" in a["action"] for a in context["suggested_actions"])
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/services/test_context_service.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/services/test_context_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/services/context_service.py frontend/src/hooks/useDiscoveryChat.ts
git commit -m "feat(discovery): add ContextService for chat-UI coordination"
```

---

### Task 68: Error Boundary & Recovery

**Files:**
- Create: `frontend/src/components/features/discovery/DiscoveryErrorBoundary.tsx`
- Create: `frontend/src/hooks/useDiscoveryRecovery.ts`
- Test: `frontend/tests/unit/discovery/DiscoveryErrorBoundary.test.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/tests/unit/discovery/DiscoveryErrorBoundary.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DiscoveryErrorBoundary } from '@/components/features/discovery/DiscoveryErrorBoundary'

const ThrowError = () => {
  throw new Error('Test error')
}

describe('DiscoveryErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <DiscoveryErrorBoundary>
        <div>Content</div>
      </DiscoveryErrorBoundary>
    )

    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('catches errors and displays fallback UI', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <DiscoveryErrorBoundary>
        <ThrowError />
      </DiscoveryErrorBoundary>
    )

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('shows retry button', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <DiscoveryErrorBoundary>
        <ThrowError />
      </DiscoveryErrorBoundary>
    )

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('shows option to go back to session list', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <DiscoveryErrorBoundary>
        <ThrowError />
      </DiscoveryErrorBoundary>
    )

    expect(screen.getByRole('link', { name: /back to sessions/i })).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('logs error to console with session context', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <DiscoveryErrorBoundary sessionId="test-session">
        <ThrowError />
      </DiscoveryErrorBoundary>
    )

    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('preserves session state after retry', () => {
    // Recovery should attempt to restore last known good state
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    let shouldThrow = true

    const MaybeThrow = () => {
      if (shouldThrow) {
        shouldThrow = false
        throw new Error('First render error')
      }
      return <div>Recovered</div>
    }

    const { rerender } = render(
      <DiscoveryErrorBoundary>
        <MaybeThrow />
      </DiscoveryErrorBoundary>
    )

    fireEvent.click(screen.getByRole('button', { name: /retry/i }))

    expect(screen.getByText('Recovered')).toBeInTheDocument()
    consoleSpy.mockRestore()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoveryErrorBoundary.test.tsx`
Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code)

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- tests/unit/discovery/DiscoveryErrorBoundary.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/discovery/DiscoveryErrorBoundary.tsx frontend/src/hooks/useDiscoveryRecovery.ts
git commit -m "feat(discovery): add DiscoveryErrorBoundary with recovery"
```

---

### Task 69: Module Exports

**Files:**
- Modify: `discovery/api/src/discovery/__init__.py`
- Modify: `frontend/src/components/features/discovery/index.ts`
- Modify: `frontend/src/pages/discovery/index.ts`
- Test: `discovery/api/tests/unit/test_module_exports.py`

**Step 1: Write the failing test**

```python
# discovery/api/tests/unit/test_module_exports.py
import pytest


def test_discovery_module_exports_all_services():
    """Discovery module should export all services."""
    from discovery import (
        DiscoverySessionService,
        FileUploadService,
        ScoringService,
        OnetApiClient,
        OnetSyncJob,
    )

    assert DiscoverySessionService is not None
    assert FileUploadService is not None
    assert ScoringService is not None
    assert OnetApiClient is not None
    assert OnetSyncJob is not None


def test_discovery_module_exports_all_repositories():
    """Discovery module should export all repositories."""
    from discovery import (
        DiscoverySessionRepository,
        DiscoveryUploadRepository,
        DiscoveryRoleMappingRepository,
        DiscoveryActivitySelectionRepository,
        DiscoveryAnalysisResultRepository,
        AgentificationCandidateRepository,
    )

    assert DiscoverySessionRepository is not None
    assert DiscoveryUploadRepository is not None


def test_discovery_module_exports_all_models():
    """Discovery module should export all models."""
    from discovery import (
        DiscoverySession,
        DiscoveryUpload,
        DiscoveryRoleMapping,
        DiscoveryActivitySelection,
        DiscoveryAnalysisResult,
        AgentificationCandidate,
    )

    assert DiscoverySession is not None


def test_discovery_module_exports_orchestrator():
    """Discovery module should export orchestrator."""
    from discovery import DiscoveryOrchestrator

    assert DiscoveryOrchestrator is not None


def test_discovery_module_exports_subagents():
    """Discovery module should export all subagents."""
    from discovery import (
        UploadSubagent,
        MappingSubagent,
        ActivitySubagent,
        AnalysisSubagent,
        RoadmapSubagent,
    )

    assert UploadSubagent is not None


def test_discovery_module_exports_routers():
    """Discovery module should export router for mounting."""
    from discovery import discovery_router

    assert discovery_router is not None
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/unit/test_module_exports.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code - update __init__.py exports)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/unit/test_module_exports.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/src/discovery/__init__.py frontend/src/components/features/discovery/index.ts frontend/src/pages/discovery/index.ts
git commit -m "feat(discovery): add clean module exports"
```

---

### Task 70: Final Integration Test

**Files:**
- Create: `discovery/api/tests/integration/test_full_discovery_flow.py`
- Test: (Integration test with real DB)

**Step 1: Write the failing test**

```python
# discovery/api/tests/integration/test_full_discovery_flow.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from discovery.main import app
from discovery.config import settings


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_session(client):
    """Create a test session for integration tests."""
    response = await client.post(
        "/discovery/sessions",
        json={"organization_id": str(uuid4())}
    )
    return response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_discovery_flow(client, test_session):
    """Test complete 5-step discovery flow."""
    session_id = test_session["id"]

    # Step 1: Upload file
    with open("tests/fixtures/sample-hr-data.csv", "rb") as f:
        response = await client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("data.csv", f, "text/csv")}
        )
    assert response.status_code == 201
    upload_data = response.json()
    assert upload_data["row_count"] > 0

    # Step 2: Get and confirm role mappings
    response = await client.get(f"/discovery/sessions/{session_id}/role-mappings")
    assert response.status_code == 200
    mappings = response.json()
    assert len(mappings) > 0

    # Confirm high-confidence mappings
    response = await client.post(
        f"/discovery/sessions/{session_id}/role-mappings/confirm",
        json={"threshold": 0.8}
    )
    assert response.status_code == 200

    # Step 3: Select activities
    response = await client.get(f"/discovery/sessions/{session_id}/activities")
    assert response.status_code == 200

    # Select first DWA from each GWA
    activities = response.json()
    dwa_ids = []
    for gwa_key, gwa_data in activities.items():
        if gwa_data["dwas"]:
            dwa_ids.append(gwa_data["dwas"][0]["id"])

    response = await client.post(
        f"/discovery/sessions/{session_id}/activities/select",
        json={"dwa_ids": dwa_ids, "is_selected": True}
    )
    assert response.status_code == 200

    # Step 4: Trigger and get analysis
    response = await client.post(f"/discovery/sessions/{session_id}/analyze")
    assert response.status_code == 202

    response = await client.get(f"/discovery/sessions/{session_id}/analysis/ROLE")
    assert response.status_code == 200
    analysis = response.json()
    assert len(analysis["results"]) > 0

    # Step 5: Get roadmap and handoff
    response = await client.get(f"/discovery/sessions/{session_id}/roadmap")
    assert response.status_code == 200

    # Validate readiness
    response = await client.post(f"/discovery/sessions/{session_id}/handoff/validate")
    assert response.status_code == 200
    assert response.json()["is_ready"] is True

    # Submit to intake
    response = await client.post(
        f"/discovery/sessions/{session_id}/handoff",
        json={"priority_tier": "HIGH"}
    )
    assert response.status_code == 201
    assert "intake_request_id" in response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_integration(client, test_session):
    """Test chat integration with session context."""
    session_id = test_session["id"]

    response = await client.post(
        f"/discovery/sessions/{session_id}/chat",
        json={"message": "What should I do first?"}
    )

    assert response.status_code == 200
    chat_response = response.json()
    assert "response" in chat_response
    assert len(chat_response["response"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_integration(client, test_session):
    """Test export functionality."""
    session_id = test_session["id"]

    # Export as CSV
    response = await client.get(f"/discovery/sessions/{session_id}/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"

    # Export handoff bundle
    response = await client.get(f"/discovery/sessions/{session_id}/export/handoff")
    assert response.status_code == 200
    bundle = response.json()
    assert "session_summary" in bundle
    assert "roadmap" in bundle
```

**Step 2: Run test to verify it fails**

Run: `cd discovery/api && python -m pytest tests/integration/test_full_discovery_flow.py -v -m integration`
Expected: FAIL with integration errors

**Step 3: Write minimal implementation to make test pass**

(Implementer determines the code - fix any integration issues)

**Step 4: Run test to verify it passes**

Run: `cd discovery/api && python -m pytest tests/integration/test_full_discovery_flow.py -v -m integration`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/api/tests/integration/test_full_discovery_flow.py
git commit -m "test(discovery): add final integration test for complete flow"
```

---

## Phase 0 Complete Checklist

After completing all 70 tasks:

1. Run full test suite:
   ```bash
   cd /Users/dl9533/projects/amplify.ai/backend && python -m pytest tests/unit/modules/discovery/ tests/integration/discovery/ -v
   cd /Users/dl9533/projects/amplify.ai/frontend && npm test -- --watchAll=false
   ```

2. Run E2E tests:
   ```bash
   cd /Users/dl9533/projects/amplify.ai/frontend && npx playwright test tests/e2e/discovery/
   ```

3. Verify O*NET sync job runs successfully

4. Create final commit:
   ```bash
   git commit -m "feat(discovery): complete Phase 0 - Opportunity Discovery with O*NET integration"
   ```

---

## Part 9: API Configuration & Integration (Tasks 71-77)

### Task 71: Configuration Module with Pydantic Settings

**Files:**
- Create: `discovery/app/config.py`
- Test: `discovery/tests/unit/test_config.py`

**Step 1: Write the failing test**

```python
# discovery/tests/unit/test_config.py
"""Tests for configuration module."""
import os
import pytest
from unittest.mock import patch


def test_settings_loads_from_environment():
    """Test that settings loads from environment variables."""
    with patch.dict(os.environ, {
        "ONET_API_KEY": "test-onet-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test_db",
    }):
        from app.config import Settings
        settings = Settings()

        assert settings.onet_api_key == "test-onet-key"
        assert settings.anthropic_api_key == "test-anthropic-key"
        assert settings.postgres_host == "localhost"


def test_settings_database_url_property():
    """Test that database_url is constructed correctly."""
    with patch.dict(os.environ, {
        "ONET_API_KEY": "key",
        "ANTHROPIC_API_KEY": "key",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
    }):
        from app.config import Settings
        settings = Settings()

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"


def test_settings_onet_api_base_url_default():
    """Test O*NET API base URL has sensible default."""
    with patch.dict(os.environ, {
        "ONET_API_KEY": "key",
        "ANTHROPIC_API_KEY": "key",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
    }):
        from app.config import Settings
        settings = Settings()

        assert settings.onet_api_base_url == "https://services.onetcenter.org/ws/"


def test_settings_anthropic_model_default():
    """Test Anthropic model has sensible default."""
    with patch.dict(os.environ, {
        "ONET_API_KEY": "key",
        "ANTHROPIC_API_KEY": "key",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
    }):
        from app.config import Settings
        settings = Settings()

        assert settings.anthropic_model == "claude-sonnet-4-20250514"


def test_get_settings_returns_cached_instance():
    """Test that get_settings returns cached singleton."""
    from app.config import get_settings

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
```

**Step 2: Run test to verify it fails**

Run: `cd discovery && python -m pytest tests/unit/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.config'"

**Step 3: Write minimal implementation**

(Implementer determines the code)

config.py should include:
- Pydantic BaseSettings with environment variable support
- Database configuration (POSTGRES_*)
- Redis configuration (REDIS_URL)
- S3 configuration (S3_*, AWS_*)
- O*NET API configuration (ONET_API_KEY, ONET_API_BASE_URL)
- Anthropic configuration (ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
- Application settings (API_HOST, API_PORT, DEBUG, LOG_LEVEL)
- Computed properties: database_url, redis_url
- get_settings() function with lru_cache for singleton

**Step 4: Run test to verify it passes**

Run: `cd discovery && python -m pytest tests/unit/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/app/config.py discovery/tests/unit/test_config.py
git commit -m "feat(discovery): add configuration module with pydantic-settings"
```

---

### Task 72: Update .env.example with API Keys

**Files:**
- Modify: `discovery/.env.example`
- Test: (Manual verification)

**Step 1: Verify current .env.example exists**

Run: `cat discovery/.env.example`
Expected: Shows existing environment variables

**Step 2: Update .env.example with API keys**

Add the following to `discovery/.env.example`:

```bash
# =============================================================================
# Discovery Module Environment Variables
# =============================================================================

# -----------------------------------------------------------------------------
# Database (PostgreSQL)
# -----------------------------------------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=discovery
POSTGRES_PASSWORD=discovery_dev
POSTGRES_DB=discovery

# -----------------------------------------------------------------------------
# Cache (Redis)
# -----------------------------------------------------------------------------
REDIS_URL=redis://redis:6379/0

# -----------------------------------------------------------------------------
# Storage (S3 / LocalStack for development)
# -----------------------------------------------------------------------------
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET=discovery-uploads
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1

# -----------------------------------------------------------------------------
# O*NET API (https://services.onetcenter.org/developer/)
# Get your API key at: https://services.onetcenter.org/developer/registration
# -----------------------------------------------------------------------------
ONET_API_KEY=your_onet_api_key_here
ONET_API_BASE_URL=https://services.onetcenter.org/ws/

# -----------------------------------------------------------------------------
# Anthropic API (for AI chat/orchestrator)
# Get your API key at: https://console.anthropic.com/
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=true
LOG_LEVEL=INFO
```

**Step 3: Verify changes**

Run: `cat discovery/.env.example | grep -E "(ONET|ANTHROPIC)"`
Expected: Shows ONET_API_KEY, ONET_API_BASE_URL, ANTHROPIC_API_KEY, ANTHROPIC_MODEL

**Step 4: Commit**

```bash
git add discovery/.env.example
git commit -m "docs(discovery): update .env.example with O*NET and Anthropic API keys"
```

---

### Task 73: O*NET API Service Implementation

**Files:**
- Modify: `discovery/app/services/role_mapping_service.py`
- Create: `discovery/app/services/onet_client.py`
- Test: `discovery/tests/unit/services/test_onet_client.py`

**Step 1: Write the failing test**

```python
# discovery/tests/unit/services/test_onet_client.py
"""Tests for O*NET API client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


@pytest.fixture
def mock_settings():
    """Mock settings with test API key."""
    settings = MagicMock()
    settings.onet_api_key = "test-api-key"
    settings.onet_api_base_url = "https://services.onetcenter.org/ws/"
    return settings


@pytest.mark.asyncio
async def test_search_occupations(mock_settings):
    """Test searching for occupations by keyword."""
    from app.services.onet_client import OnetApiClient

    mock_response = {
        "occupation": [
            {"code": "15-1252.00", "title": "Software Developers"},
            {"code": "15-1251.00", "title": "Computer Programmers"},
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response_obj
        mock_client_class.return_value = mock_client

        client = OnetApiClient(mock_settings)
        results = await client.search_occupations("software developer")

        assert len(results) == 2
        assert results[0]["code"] == "15-1252.00"


@pytest.mark.asyncio
async def test_get_occupation_details(mock_settings):
    """Test getting occupation details by code."""
    from app.services.onet_client import OnetApiClient

    mock_response = {
        "code": "15-1252.00",
        "title": "Software Developers",
        "description": "Research, design, and develop computer software.",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response_obj
        mock_client_class.return_value = mock_client

        client = OnetApiClient(mock_settings)
        result = await client.get_occupation("15-1252.00")

        assert result["code"] == "15-1252.00"
        assert result["title"] == "Software Developers"


@pytest.mark.asyncio
async def test_get_work_activities(mock_settings):
    """Test getting work activities for an occupation."""
    from app.services.onet_client import OnetApiClient

    mock_response = {
        "element": [
            {"id": "4.A.1.a.1", "name": "Getting Information", "score": {"value": 4.5}},
            {"id": "4.A.2.a.1", "name": "Analyzing Data", "score": {"value": 4.2}},
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response_obj
        mock_client_class.return_value = mock_client

        client = OnetApiClient(mock_settings)
        results = await client.get_work_activities("15-1252.00")

        assert len(results) == 2
        assert results[0]["id"] == "4.A.1.a.1"


@pytest.mark.asyncio
async def test_api_authentication(mock_settings):
    """Test that API calls include proper authentication."""
    from app.services.onet_client import OnetApiClient

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = {"occupation": []}
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response_obj
        mock_client_class.return_value = mock_client

        client = OnetApiClient(mock_settings)
        await client.search_occupations("test")

        # Verify auth was passed
        call_kwargs = mock_client_class.call_args[1]
        assert "auth" in call_kwargs
```

**Step 2: Run test to verify it fails**

Run: `cd discovery && python -m pytest tests/unit/services/test_onet_client.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

(Implementer determines the code)

onet_client.py should include:
- OnetApiClient class with settings injection
- HTTP Basic Auth using API key as username
- search_occupations(keyword: str) -> List[dict]
- get_occupation(code: str) -> Optional[dict]
- get_work_activities(code: str) -> List[dict]
- get_tasks(code: str) -> List[dict]
- Error handling with custom exceptions
- Rate limiting awareness

**Step 4: Run test to verify it passes**

Run: `cd discovery && python -m pytest tests/unit/services/test_onet_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/app/services/onet_client.py discovery/tests/unit/services/test_onet_client.py
git commit -m "feat(discovery): implement O*NET API client with authentication"
```

---

### Task 74: Anthropic LLM Service for Chat

**Files:**
- Create: `discovery/app/services/llm_service.py`
- Modify: `discovery/app/services/chat_service.py`
- Test: `discovery/tests/unit/services/test_llm_service.py`

**Step 1: Write the failing test**

```python
# discovery/tests/unit/services/test_llm_service.py
"""Tests for LLM service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_settings():
    """Mock settings with test API key."""
    settings = MagicMock()
    settings.anthropic_api_key = "test-anthropic-key"
    settings.anthropic_model = "claude-sonnet-4-20250514"
    return settings


@pytest.mark.asyncio
async def test_generate_response(mock_settings):
    """Test generating a response from the LLM."""
    from app.services.llm_service import LLMService

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="This is a test response.")]

    with patch("anthropic.AsyncAnthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        service = LLMService(mock_settings)
        response = await service.generate_response(
            system_prompt="You are a helpful assistant.",
            user_message="Hello, how are you?"
        )

        assert response == "This is a test response."


@pytest.mark.asyncio
async def test_generate_response_with_context(mock_settings):
    """Test generating a response with conversation context."""
    from app.services.llm_service import LLMService

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Based on our previous discussion...")]

    with patch("anthropic.AsyncAnthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        service = LLMService(mock_settings)
        response = await service.generate_response(
            system_prompt="You are a helpful assistant.",
            user_message="What did we discuss?",
            conversation_history=[
                {"role": "user", "content": "Tell me about AI"},
                {"role": "assistant", "content": "AI is artificial intelligence..."},
            ]
        )

        assert "previous discussion" in response


@pytest.mark.asyncio
async def test_stream_response(mock_settings):
    """Test streaming a response from the LLM."""
    from app.services.llm_service import LLMService

    async def mock_stream():
        chunks = [
            MagicMock(type="content_block_delta", delta=MagicMock(text="Hello ")),
            MagicMock(type="content_block_delta", delta=MagicMock(text="world!")),
        ]
        for chunk in chunks:
            yield chunk

    with patch("anthropic.AsyncAnthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.stream.return_value.__aenter__.return_value = mock_stream()
        mock_anthropic.return_value = mock_client

        service = LLMService(mock_settings)
        chunks = []
        async for chunk in service.stream_response(
            system_prompt="You are helpful.",
            user_message="Say hello"
        ):
            chunks.append(chunk)

        assert "".join(chunks) == "Hello world!"


def test_llm_service_requires_api_key():
    """Test that service raises error without API key."""
    from app.services.llm_service import LLMService

    settings = MagicMock()
    settings.anthropic_api_key = None

    with pytest.raises(ValueError, match="API key"):
        LLMService(settings)
```

**Step 2: Run test to verify it fails**

Run: `cd discovery && python -m pytest tests/unit/services/test_llm_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

(Implementer determines the code)

llm_service.py should include:
- LLMService class with settings injection
- Anthropic client initialization with API key
- generate_response(system_prompt, user_message, conversation_history=None) -> str
- stream_response(system_prompt, user_message, conversation_history=None) -> AsyncIterator[str]
- Error handling for API failures
- Max tokens and temperature configuration

**Step 4: Run test to verify it passes**

Run: `cd discovery && python -m pytest tests/unit/services/test_llm_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/app/services/llm_service.py discovery/tests/unit/services/test_llm_service.py
git commit -m "feat(discovery): implement Anthropic LLM service for chat"
```

---

### Task 75: Update OnetService to Use Real API

**Files:**
- Modify: `discovery/app/services/role_mapping_service.py`
- Modify: `discovery/app/services/__init__.py`
- Test: `discovery/tests/unit/services/test_role_mapping_service.py`

**Step 1: Write the failing test**

```python
# Update discovery/tests/unit/services/test_role_mapping_service.py
"""Tests for role mapping service with real O*NET API."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_onet_client():
    """Mock O*NET API client."""
    client = AsyncMock()
    client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers", "relevance_score": 95},
        {"code": "15-1251.00", "title": "Computer Programmers", "relevance_score": 80},
    ]
    client.get_occupation.return_value = {
        "code": "15-1252.00",
        "title": "Software Developers",
        "description": "Research, design, and develop computer software.",
    }
    return client


@pytest.mark.asyncio
async def test_onet_service_search_uses_api_client(mock_onet_client):
    """Test that OnetService uses the API client for searches."""
    from app.services.role_mapping_service import OnetService

    service = OnetService(onet_client=mock_onet_client)
    results = await service.search("software developer")

    assert len(results) == 2
    assert results[0]["code"] == "15-1252.00"
    mock_onet_client.search_occupations.assert_called_once_with("software developer")


@pytest.mark.asyncio
async def test_onet_service_get_occupation_uses_api_client(mock_onet_client):
    """Test that OnetService uses the API client for occupation details."""
    from app.services.role_mapping_service import OnetService

    service = OnetService(onet_client=mock_onet_client)
    result = await service.get_occupation("15-1252.00")

    assert result["code"] == "15-1252.00"
    mock_onet_client.get_occupation.assert_called_once_with("15-1252.00")
```

**Step 2: Run test to verify it fails**

Run: `cd discovery && python -m pytest tests/unit/services/test_role_mapping_service.py -v`
Expected: FAIL (service still raises NotImplementedError)

**Step 3: Write minimal implementation**

(Implementer determines the code)

Update OnetService to:
- Accept OnetApiClient as dependency
- Implement search() using client.search_occupations()
- Implement get_occupation() using client.get_occupation()
- Add get_onet_service() dependency that creates client with settings

**Step 4: Run test to verify it passes**

Run: `cd discovery && python -m pytest tests/unit/services/test_role_mapping_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/app/services/role_mapping_service.py discovery/app/services/__init__.py
git add discovery/tests/unit/services/test_role_mapping_service.py
git commit -m "feat(discovery): connect OnetService to real O*NET API client"
```

---

### Task 76: Update ChatService to Use LLM

**Files:**
- Modify: `discovery/app/services/chat_service.py`
- Modify: `discovery/app/services/__init__.py`
- Test: `discovery/tests/unit/services/test_chat_service.py`

**Step 1: Write the failing test**

```python
# Update discovery/tests/unit/services/test_chat_service.py
"""Tests for chat service with real LLM."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    service = AsyncMock()
    service.generate_response.return_value = "I can help you with that!"
    return service


@pytest.fixture
def mock_context_service():
    """Mock context service for session context."""
    service = AsyncMock()
    service.get_session_context.return_value = {
        "current_step": 1,
        "step_name": "upload",
        "session_data": {},
    }
    return service


@pytest.mark.asyncio
async def test_chat_service_sends_message_to_llm(mock_llm_service, mock_context_service):
    """Test that ChatService uses LLM for responses."""
    from app.services.chat_service import ChatService

    session_id = uuid4()
    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    result = await service.send_message(session_id, "Hello!")

    assert result is not None
    assert result["response"] == "I can help you with that!"
    mock_llm_service.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_chat_service_includes_session_context(mock_llm_service, mock_context_service):
    """Test that chat includes session context in system prompt."""
    from app.services.chat_service import ChatService

    session_id = uuid4()
    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    await service.send_message(session_id, "What should I do?")

    call_args = mock_llm_service.generate_response.call_args
    system_prompt = call_args[1]["system_prompt"]
    assert "upload" in system_prompt.lower() or "step" in system_prompt.lower()


@pytest.mark.asyncio
async def test_chat_service_returns_quick_actions(mock_llm_service, mock_context_service):
    """Test that chat returns relevant quick actions."""
    from app.services.chat_service import ChatService

    session_id = uuid4()
    service = ChatService(
        llm_service=mock_llm_service,
        context_service=mock_context_service,
    )

    result = await service.send_message(session_id, "Hello!")

    assert "quick_actions" in result
    assert isinstance(result["quick_actions"], list)
```

**Step 2: Run test to verify it fails**

Run: `cd discovery && python -m pytest tests/unit/services/test_chat_service.py -v`
Expected: FAIL (service still raises NotImplementedError)

**Step 3: Write minimal implementation**

(Implementer determines the code)

Update ChatService to:
- Accept LLMService and ContextService as dependencies
- Implement send_message() using LLM with session context
- Build system prompt based on current step
- Return response with quick_actions based on step
- Implement get_history() using memory/storage
- Implement stream_response() for SSE

**Step 4: Run test to verify it passes**

Run: `cd discovery && python -m pytest tests/unit/services/test_chat_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add discovery/app/services/chat_service.py discovery/app/services/__init__.py
git add discovery/tests/unit/services/test_chat_service.py
git commit -m "feat(discovery): connect ChatService to Anthropic LLM"
```

---

### Task 77: Integration Test with Real APIs

**Files:**
- Create: `discovery/tests/integration/test_api_integration.py`
- Test: (Self-testing)

**Step 1: Write the integration test**

```python
# discovery/tests/integration/test_api_integration.py
"""Integration tests for API connectivity.

These tests require real API keys to be set in environment.
Skip if keys not available.
"""
import os
import pytest


pytestmark = pytest.mark.skipif(
    not os.getenv("ONET_API_KEY") or os.getenv("ONET_API_KEY") == "your_onet_api_key_here",
    reason="O*NET API key not configured"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onet_api_connectivity():
    """Test that O*NET API is reachable with valid credentials."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Search for a common occupation
    results = await client.search_occupations("software")

    assert len(results) > 0
    assert any("software" in r.get("title", "").lower() for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onet_get_occupation_details():
    """Test fetching specific occupation details."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Get Software Developers occupation
    result = await client.get_occupation("15-1252.00")

    assert result is not None
    assert result["code"] == "15-1252.00"
    assert "Software" in result["title"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onet_get_work_activities():
    """Test fetching work activities for an occupation."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    activities = await client.get_work_activities("15-1252.00")

    assert len(activities) > 0
    assert all("id" in a for a in activities)


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_anthropic_api_key_here",
    reason="Anthropic API key not configured"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_api_connectivity():
    """Test that Anthropic API is reachable with valid credentials."""
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    service = LLMService(settings)

    response = await service.generate_response(
        system_prompt="You are a helpful assistant. Respond with exactly: 'API connection successful'",
        user_message="Test connection"
    )

    assert "successful" in response.lower() or len(response) > 0


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_anthropic_api_key_here",
    reason="Anthropic API key not configured"
)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_service_end_to_end():
    """Test complete chat flow with real LLM."""
    from app.config import get_settings
    from app.services.llm_service import LLMService
    from app.services.chat_service import ChatService
    from app.services.context_service import ContextService
    from uuid import uuid4

    settings = get_settings()
    llm_service = LLMService(settings)
    context_service = ContextService()

    chat_service = ChatService(
        llm_service=llm_service,
        context_service=context_service,
    )

    session_id = uuid4()
    result = await chat_service.send_message(
        session_id,
        "What is the first step in the discovery process?"
    )

    assert result is not None
    assert "response" in result
    assert len(result["response"]) > 0
```

**Step 2: Run test to verify connectivity (if keys available)**

Run: `cd discovery && python -m pytest tests/integration/test_api_integration.py -v -m integration`
Expected: PASS if keys configured, SKIP if not

**Step 3: Document API key setup**

Add to README or inline comments explaining:
- How to get O*NET API key
- How to get Anthropic API key
- How to configure .env file

**Step 4: Commit**

```bash
git add discovery/tests/integration/test_api_integration.py
git commit -m "test(discovery): add integration tests for O*NET and Anthropic APIs"
```

---

**Next Phase:** [Phase 1: Foundation](phase-01-foundation.md)
