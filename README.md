# Amplify.AI Platform

Enterprise AI agent management and opportunity discovery platform.

## Project Structure

```
amplify.ai_1/
├── discovery/          # Discovery Module - O*NET opportunity discovery service
├── backend/            # Main backend application (modular monolith)
├── api/                # Discovery API package (distributable)
├── docs/               # Project documentation and planning
├── docker/             # Docker configuration (Postgres, LocalStack init)
├── tests/              # E2E and integration tests
├── docker-compose.yml  # Production-like stack configuration
└── docker-compose.dev.yml  # Development overrides
```

## Modules

### Discovery Module (`discovery/`)

O*NET-powered opportunity discovery using an orchestrator + subagent architecture. Analyzes job roles and tasks to identify automation and AI opportunities.

**Features:**
- 5-step wizard workflow (Upload → Map Roles → Activities → Analysis → Roadmap)
- LLM-powered semantic role-to-O*NET mapping
- LOB-aware industry matching
- Multi-dimension analysis (role, task, LOB, geography, department)
- PDF/Excel/JSON export capabilities

See [discovery/README.md](discovery/README.md) for detailed documentation.

### Backend (`backend/`)

Main backend application integrating discovery and other modules. Uses a modular architecture with services, repositories, and models.

### API Package (`api/`)

Distributable Python package for the Discovery API. Packaged for installation via pip.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dl9533/amplify.ai_1.git
   cd amplify.ai_1
   ```

2. Copy environment files:
   ```bash
   cp .env.example .env
   cp discovery/.env.example discovery/.env
   ```

3. Start the development stack:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

4. Access the services:
   - Discovery API: http://localhost:8001
   - Discovery Frontend: http://localhost:5173
   - PostgreSQL: localhost:5433
   - Redis: localhost:6380

### Running Tests

```bash
# Backend tests
docker-compose exec api pytest

# Frontend tests
cd discovery/frontend && npm test

# E2E tests
cd discovery/frontend && npm run test:e2e
```

### Code Quality

```bash
# Python linting
docker-compose exec api ruff check .
docker-compose exec api ruff format .

# TypeScript linting
cd discovery/frontend && npm run lint
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/frontend-design-principles.md](docs/frontend-design-principles.md) | UI/UX design system and component guidelines |
| [docs/implementation-tracking.md](docs/implementation-tracking.md) | Phase 0 task tracking and workflow |
| [discovery/docs/backend-workflow-overview.md](discovery/docs/backend-workflow-overview.md) | 5-step wizard backend architecture |
| [docs/plans/](docs/plans/) | Design documents and implementation plans |

## Architecture

The platform uses a microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMPLIFY.AI PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           DISCOVERY SERVICE (discovery/)                 │    │
│  │  • FastAPI backend (port 8001)                          │    │
│  │  • React 18 frontend (port 5173)                        │    │
│  │  • Orchestrator + Subagent pattern                      │    │
│  │  • O*NET integration                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               INFRASTRUCTURE                             │    │
│  │  • PostgreSQL 16 (primary database)                     │    │
│  │  • Redis 7 (caching)                                    │    │
│  │  • S3/LocalStack (file storage)                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Environment Variables

See [.env.example](.env.example) for the complete list of environment variables.

Key variables:
- `POSTGRES_*` - Database connection settings
- `REDIS_URL` - Redis cache connection
- `S3_*` / `AWS_*` - Object storage configuration
- `ONET_API_USERNAME` - O*NET API credentials
- `ANTHROPIC_API_KEY` - LLM integration

## License

Proprietary - All rights reserved.
