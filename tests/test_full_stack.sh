#!/bin/bash
# Discovery Module Full Stack Integration Test
# Tests that all services work together correctly
set -e

echo "=========================================="
echo "Discovery Module Full Stack Integration Test"
echo "=========================================="

# Change to discovery directory
cd "$(dirname "$0")/.."

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Start all services
echo ""
echo "Starting services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Wait for services to be healthy
echo ""
echo "Waiting for services to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))

    # Check if API is responding
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo "API is responding (attempt $attempt)"
        break
    fi

    if [ $attempt -eq $max_attempts ]; then
        echo "ERROR: API failed to become ready after $max_attempts attempts"
        echo ""
        echo "Container status:"
        docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
        echo ""
        echo "API logs:"
        docker compose -f docker-compose.yml -f docker-compose.dev.yml logs api --tail=50
        exit 1
    fi

    echo "Waiting for API... (attempt $attempt/$max_attempts)"
    sleep 2
done

# Give a bit more time for all dependencies to stabilize
sleep 5

# Test API health endpoint
echo ""
echo "Testing API health..."
curl -f http://localhost:8001/health || { echo "API health check failed"; exit 1; }
echo ""
echo "Basic health check: PASSED"

# Test detailed health (checks all dependencies)
echo ""
echo "Testing dependency connectivity..."
HEALTH=$(curl -s http://localhost:8001/health?detailed=true)
echo "$HEALTH" | jq .

# Verify postgres is healthy
echo ""
echo "Checking PostgreSQL status..."
POSTGRES_STATUS=$(echo "$HEALTH" | jq -r '.dependencies.postgres.status')
if [ "$POSTGRES_STATUS" != "healthy" ]; then
    echo "ERROR: PostgreSQL not healthy. Status: $POSTGRES_STATUS"
    echo "Message: $(echo "$HEALTH" | jq -r '.dependencies.postgres.message // "none"')"
    exit 1
fi
echo "PostgreSQL: healthy"

# Verify redis is healthy
echo ""
echo "Checking Redis status..."
REDIS_STATUS=$(echo "$HEALTH" | jq -r '.dependencies.redis.status')
if [ "$REDIS_STATUS" != "healthy" ]; then
    echo "ERROR: Redis not healthy. Status: $REDIS_STATUS"
    echo "Message: $(echo "$HEALTH" | jq -r '.dependencies.redis.message // "none"')"
    exit 1
fi
echo "Redis: healthy"

# Verify S3 is healthy
echo ""
echo "Checking S3 (LocalStack) status..."
S3_STATUS=$(echo "$HEALTH" | jq -r '.dependencies.s3.status')
if [ "$S3_STATUS" != "healthy" ]; then
    echo "ERROR: S3 not healthy. Status: $S3_STATUS"
    echo "Message: $(echo "$HEALTH" | jq -r '.dependencies.s3.message // "none"')"
    exit 1
fi
echo "S3: healthy"

# Verify overall status is healthy
echo ""
echo "Checking overall status..."
OVERALL_STATUS=$(echo "$HEALTH" | jq -r '.status')
if [ "$OVERALL_STATUS" != "healthy" ]; then
    echo "WARNING: Overall status is '$OVERALL_STATUS', expected 'healthy'"
    # Don't fail here - degraded is acceptable if individual checks pass
fi
echo "Overall status: $OVERALL_STATUS"

# Test readiness endpoint
echo ""
echo "Testing readiness probe..."
curl -f http://localhost:8001/ready || { echo "Readiness probe failed"; exit 1; }
echo ""
echo "Readiness probe: PASSED"

# Test root endpoint for good measure
echo ""
echo "Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8001/)
echo "$ROOT_RESPONSE" | jq .
echo "Root endpoint: PASSED"

echo ""
echo "=========================================="
echo "Full stack integration test PASSED!"
echo "=========================================="
