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

### Task 29-38: Remaining Agent Tasks

Following the same TDD pattern, implement:

- **Task 29:** Agent Memory Service - working/episodic/semantic memory operations
- **Task 30:** Upload Subagent - file parsing, column detection
- **Task 31:** Mapping Subagent - role to O*NET matching
- **Task 32:** Activity Subagent - DWA selection management
- **Task 33:** Analysis Subagent - score calculations, insight generation
- **Task 34:** Roadmap Subagent - prioritization, timeline generation
- **Task 35:** Discovery Orchestrator - routes to subagents, manages session
- **Task 36:** Brainstorming Interaction Handler - one question at a time
- **Task 37:** Chat Message Formatter - formats agent responses
- **Task 38:** Quick Action Chip Generator - generates choice chips

---

## Part 6: API Endpoints (Tasks 39-48)

Following the same TDD pattern, implement:

- **Task 39:** Discovery Session Router - CRUD endpoints
- **Task 40:** Upload Endpoint - POST /discovery/sessions/{id}/upload
- **Task 41:** Role Mapping Endpoints - GET/PUT role mappings
- **Task 42:** Activity Selection Endpoints - GET/PUT activity selections
- **Task 43:** Analysis Endpoints - GET analysis by dimension
- **Task 44:** Roadmap Endpoints - GET/PUT roadmap items
- **Task 45:** Chat/Message Endpoint - POST message, GET history
- **Task 46:** Export Endpoints - GET export as CSV/PDF
- **Task 47:** Handoff to Build Endpoint - POST send to intake
- **Task 48:** Wire Up to Main App - register router

---

## Part 7: Frontend Components (Tasks 49-65)

Following the same TDD pattern (vitest), implement:

- **Task 49:** Discovery Layout Component
- **Task 50:** Step Indicator Component
- **Task 51:** Chat Panel Component
- **Task 52:** Quick Action Chips Component
- **Task 53:** Upload Step Page
- **Task 54:** File Drop Zone Component
- **Task 55:** Column Mapping Preview
- **Task 56:** Map Roles Step Page
- **Task 57:** Role Mapping Card Component
- **Task 58:** O*NET Search Autocomplete
- **Task 59:** Activities Step Page
- **Task 60:** DWA Accordion Component
- **Task 61:** Analysis Step Page
- **Task 62:** Analysis Tabs Component
- **Task 63:** Roadmap Step Page
- **Task 64:** Kanban Timeline Component
- **Task 65:** Discovery Session List Page

---

## Part 8: Integration & Polish (Tasks 66-70)

- **Task 66:** End-to-End Session Flow Test
- **Task 67:** Chat + UI Coordination
- **Task 68:** Error Boundary & Recovery
- **Task 69:** Module Exports
- **Task 70:** Final Integration Test

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

**Next Phase:** [Phase 1: Foundation](phase-01-foundation.md)
