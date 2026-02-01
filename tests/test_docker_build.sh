#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Testing Dockerfile builds..."

# Get the project root (parent of discovery directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# Test 1: Production Dockerfile exists
echo -n "Test 1: Checking Dockerfile exists... "
if [ -f "$PROJECT_ROOT/discovery/Dockerfile" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Dockerfile not found"
    exit 1
fi

# Test 2: Development Dockerfile exists
echo -n "Test 2: Checking Dockerfile.dev exists... "
if [ -f "$PROJECT_ROOT/discovery/Dockerfile.dev" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Dockerfile.dev not found"
    exit 1
fi

# Test 3: Dockerfile uses Python 3.12-slim
echo -n "Test 3: Checking Python 3.12-slim base image... "
if grep -q "python:3.12-slim" "$PROJECT_ROOT/discovery/Dockerfile"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Python 3.12-slim base image not found"
    exit 1
fi

# Test 4: Dockerfile creates non-root user
echo -n "Test 4: Checking non-root user creation... "
if grep -q "useradd\|adduser" "$PROJECT_ROOT/discovery/Dockerfile"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Non-root user creation not found"
    exit 1
fi

# Test 5: Dockerfile uses multi-stage build
echo -n "Test 5: Checking multi-stage build... "
STAGE_COUNT=$(grep -c "^FROM " "$PROJECT_ROOT/discovery/Dockerfile" || echo "0")
if [ "$STAGE_COUNT" -ge 2 ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Multi-stage build not found (need at least 2 FROM statements)"
    exit 1
fi

# Test 6: Dockerfile has HEALTHCHECK
echo -n "Test 6: Checking HEALTHCHECK instruction... "
if grep -q "HEALTHCHECK" "$PROJECT_ROOT/discovery/Dockerfile"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - HEALTHCHECK instruction not found"
    exit 1
fi

# Test 7: Dockerfile uses uvicorn as entrypoint
echo -n "Test 7: Checking uvicorn entrypoint... "
if grep -q "uvicorn" "$PROJECT_ROOT/discovery/Dockerfile"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - uvicorn entrypoint not found"
    exit 1
fi

# Test 8: Dockerfile exposes port 8001
echo -n "Test 8: Checking port 8001 exposure... "
if grep -q "EXPOSE 8001" "$PROJECT_ROOT/discovery/Dockerfile"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Port 8001 not exposed"
    exit 1
fi

# Test 9: Dockerfile.dev has reload flag for hot reload
echo -n "Test 9: Checking Dockerfile.dev has hot reload... "
if grep -q "\-\-reload" "$PROJECT_ROOT/discovery/Dockerfile.dev"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - Hot reload (--reload) not found in Dockerfile.dev"
    exit 1
fi

# Test 10: Build the production Dockerfile (syntax validation)
echo -n "Test 10: Building production Dockerfile... "
if docker build -t discovery-api-test -f "$PROJECT_ROOT/discovery/Dockerfile" "$PROJECT_ROOT/discovery/" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"

    # Test 11: Verify image was created
    echo -n "Test 11: Verifying image exists... "
    if docker images discovery-api-test | grep -q discovery-api-test; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC} - Image not found after build"
        exit 1
    fi

    # Cleanup
    echo -n "Cleaning up test image... "
    docker rmi discovery-api-test > /dev/null 2>&1
    echo -e "${GREEN}done${NC}"
else
    echo -e "${RED}FAIL${NC} - Docker build failed"
    echo "Build output:"
    docker build -t discovery-api-test -f "$PROJECT_ROOT/discovery/Dockerfile" "$PROJECT_ROOT/discovery/" 2>&1
    exit 1
fi

# Test 12: Build the development Dockerfile
echo -n "Test 12: Building development Dockerfile... "
if docker build -t discovery-api-dev-test -f "$PROJECT_ROOT/discovery/Dockerfile.dev" "$PROJECT_ROOT/discovery/" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"

    # Cleanup
    echo -n "Cleaning up dev test image... "
    docker rmi discovery-api-dev-test > /dev/null 2>&1
    echo -e "${GREEN}done${NC}"
else
    echo -e "${RED}FAIL${NC} - Development Docker build failed"
    echo "Build output:"
    docker build -t discovery-api-dev-test -f "$PROJECT_ROOT/discovery/Dockerfile.dev" "$PROJECT_ROOT/discovery/" 2>&1
    exit 1
fi

echo ""
echo -e "${GREEN}All Dockerfile build tests passed!${NC}"
