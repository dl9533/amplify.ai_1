# Discovery Module

O*NET-powered opportunity discovery using an orchestrator + subagent architecture. Runs as a standalone service with its own API, database, and caching layer.

## Purpose

This module enables intelligent discovery of automation and AI opportunities by:
- Analyzing job roles and tasks using O*NET occupational data
- Identifying high-value automation candidates
- Providing structured recommendations for capability development

## 5-Step Discovery Workflow

```
┌─────────┐    ┌──────────┐    ┌────────────┐    ┌──────────┐    ┌─────────┐
│ Upload  │───►│ Map Roles│───►│ Activities │───►│ Analysis │───►│ Roadmap │
│ (CSV)   │    │ (O*NET)  │    │ (DWAs)     │    │ (Scores) │    │ (Plan)  │
└─────────┘    └──────────┘    └────────────┘    └──────────┘    └─────────┘
```

1. **Upload**: Upload workforce CSV/Excel, auto-detect columns, map to schema
2. **Map Roles**: LLM-powered semantic mapping of job titles to O*NET occupations
3. **Activities**: Review and select Detailed Work Activities (DWAs) for each role
4. **Analysis**: Calculate AI exposure scores, aggregate by dimensions
5. **Roadmap**: Generate prioritized candidates for agent development

## Quick Start

### Development Setup

1. Navigate to the discovery module:
   ```bash
   cd discovery
   ```

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - Backend API: http://localhost:8001
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8001/docs

### Running Locally (without Docker)

Backend:
```bash
cd discovery
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Frontend:
```bash
cd discovery/frontend
npm install
npm run dev
```

## Architecture

### Orchestrator + Subagent Pattern

```
┌──────────────────────────────────────────────────────────────────┐
│                     DISCOVERY ORCHESTRATOR                        │
│  • Manages single conversation thread                             │
│  • Routes to appropriate subagent based on current_step          │
│  • Maintains session state and context                            │
└─────────────────────────────┬────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Upload Agent  │     │ Mapping Agent │     │ Roadmap Agent │
│ (Step 1)      │     │ (Step 2)      │     │ (Step 5)      │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| `app/agents/` | Subagent implementations (upload, mapping, activity, analysis, roadmap) |
| `app/services/` | Business logic (role mapping, analysis, scoring, export) |
| `app/repositories/` | Database access layer |
| `app/routers/` | FastAPI route handlers |
| `app/models/` | SQLAlchemy ORM models |
| `frontend/` | React 18 + TypeScript + Vite frontend |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL hostname | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | Database user | `discovery` |
| `POSTGRES_PASSWORD` | Database password | `discovery_dev` |
| `POSTGRES_DB` | Database name | `discovery` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `S3_ENDPOINT_URL` | S3-compatible endpoint | `http://localstack:4566` |
| `S3_BUCKET` | S3 bucket name | `discovery-uploads` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `test` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `test` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `ONET_API_USERNAME` | O*NET API key | - |
| `ONET_API_BASE_URL` | O*NET API base URL | `https://services.onetcenter.org/ws/` |
| `ANTHROPIC_API_KEY` | Anthropic API key for LLM | - |
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8001` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create discovery session
- `GET /api/v1/sessions/{id}` - Get session details
- `PATCH /api/v1/sessions/{id}` - Update session

### Upload
- `POST /api/v1/sessions/{id}/upload` - Upload workforce file
- `GET /api/v1/sessions/{id}/upload` - Get upload details

### Role Mapping
- `GET /api/v1/sessions/{id}/role-mappings` - List role mappings
- `POST /api/v1/sessions/{id}/role-mappings/generate` - Generate mappings with LLM
- `PATCH /api/v1/role-mappings/{id}` - Update mapping (confirm/remap)

### Activities
- `GET /api/v1/sessions/{id}/activities` - Get DWA selections
- `PATCH /api/v1/sessions/{id}/activities` - Update selections

### Analysis
- `GET /api/v1/sessions/{id}/analysis` - Get analysis results
- `GET /api/v1/sessions/{id}/analysis/by-role` - Analysis grouped by role

### Export
- `GET /api/v1/sessions/{id}/export/pdf` - Export as PDF
- `GET /api/v1/sessions/{id}/export/excel` - Export as Excel

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests with coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/backend-workflow-overview.md](docs/backend-workflow-overview.md) | Detailed backend flow for each step |
| [docs/plans/](docs/plans/) | Feature design and implementation plans |
| [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) | Code review findings and fixes |

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0+ (async)
- PostgreSQL 16
- Redis 7
- Alembic (migrations)
- Anthropic Claude (LLM)

**Frontend:**
- React 18
- TypeScript 5
- Vite
- TailwindCSS 3.4
- React Router v7

**Infrastructure:**
- Docker & Docker Compose
- LocalStack (S3 mock)
- pytest + Playwright (testing)
