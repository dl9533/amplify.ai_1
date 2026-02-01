#!/bin/bash
set -e

echo "=========================================="
echo "PostgreSQL Initialization Test"
echo "=========================================="

# Configuration
MAX_RETRIES=30
RETRY_INTERVAL=2
COMPOSE_FILE="discovery/docker-compose.yml"

# Cleanup function
cleanup() {
    echo ""
    echo "[INFO] Cleaning up containers..."
    docker compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
}

# Set trap for cleanup on exit
trap cleanup EXIT

echo ""
echo "[STEP 1] Starting PostgreSQL container..."
docker compose -f "$COMPOSE_FILE" up -d postgres

echo ""
echo "[STEP 2] Waiting for PostgreSQL to be ready..."
retries=0
while [ $retries -lt $MAX_RETRIES ]; do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U discovery -d discovery > /dev/null 2>&1; then
        echo "[OK] PostgreSQL is ready after $((retries * RETRY_INTERVAL)) seconds"
        break
    fi
    retries=$((retries + 1))
    if [ $retries -eq $MAX_RETRIES ]; then
        echo "[FAIL] PostgreSQL failed to become ready after $((MAX_RETRIES * RETRY_INTERVAL)) seconds"
        exit 1
    fi
    echo "[INFO] Waiting for PostgreSQL... (attempt $retries/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

echo ""
echo "[STEP 3] Verifying database connection..."
if docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U discovery -d discovery -c "SELECT 1" > /dev/null 2>&1; then
    echo "[OK] Database connection successful"
else
    echo "[FAIL] Could not connect to database"
    exit 1
fi

echo ""
echo "[STEP 4] Checking uuid-ossp extension..."
if docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U discovery -d discovery -c "SELECT uuid_generate_v4();" > /dev/null 2>&1; then
    echo "[OK] uuid-ossp extension is working"
else
    echo "[FAIL] uuid-ossp extension not available"
    exit 1
fi

echo ""
echo "[STEP 5] Checking pg_trgm extension..."
if docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U discovery -d discovery -c "SELECT similarity('test', 'test');" > /dev/null 2>&1; then
    echo "[OK] pg_trgm extension is working"
else
    echo "[FAIL] pg_trgm extension not available"
    exit 1
fi

echo ""
echo "[STEP 6] Checking discovery schema..."
if docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U discovery -d discovery -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'discovery';" | grep -q discovery; then
    echo "[OK] Discovery schema exists"
else
    echo "[FAIL] Discovery schema not found"
    exit 1
fi

echo ""
echo "=========================================="
echo "PostgreSQL initialization test PASSED!"
echo "=========================================="
