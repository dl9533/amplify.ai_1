# Discovery Module

The Discovery Module provides O*NET-powered opportunity discovery using an orchestrator + subagent architecture. It runs as a standalone service with its own API, database, and caching layer.

## Purpose

This module enables intelligent discovery of automation and AI opportunities by:
- Analyzing job roles and tasks using O*NET occupational data
- Identifying high-value automation candidates
- Providing structured recommendations for capability development

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Development Setup

> **Note:** The `docker-compose.yml` file will be created in Task 0.3 (Infrastructure Setup). For now, you can run the module directly with Python or wait for the infrastructure task to complete.

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Start the services (once docker-compose.yml is available):
   ```bash
   docker-compose up -d
   ```

3. The API will be available at `http://localhost:8001`

### Production Setup

For production deployments:

1. Configure environment variables with production values:
   - Use secure passwords for `POSTGRES_PASSWORD`
   - Set `DEBUG=false`
   - Configure real AWS credentials for S3
   - Set appropriate `LOG_LEVEL` (e.g., `WARNING` or `ERROR`)

2. Use production-grade PostgreSQL and Redis instances

3. Configure O*NET API credentials:
   - Register at https://services.onetcenter.org/
   - Set `ONET_API_USERNAME` with your API key

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
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8001` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Architecture

The module uses an orchestrator + subagent pattern:
- **Orchestrator**: Coordinates discovery workflows and manages subagent execution
- **Subagents**: Specialized agents for specific discovery tasks (O*NET lookup, task analysis, etc.)

## Development

### Running Tests

```bash
docker-compose exec api pytest
```

### Code Quality

```bash
docker-compose exec api ruff check .
docker-compose exec api ruff format .
```
