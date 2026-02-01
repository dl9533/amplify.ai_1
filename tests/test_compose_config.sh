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

# Store compose config output for validation
COMPOSE_CONFIG=$(docker compose -f discovery/docker-compose.yml config)

# Check health check configurations exist for all services
echo "Checking health check configurations..."
for service in api postgres redis localstack; do
  # Extract service block and check for healthcheck
  if ! echo "$COMPOSE_CONFIG" | sed -n "/^  ${service}:/,/^  [a-z]/p" | grep -q "healthcheck:"; then
    echo "ERROR: Service '$service' missing healthcheck configuration"
    exit 1
  fi
done
echo "All services have health check configurations."

# Check network configuration exists
echo "Checking network configuration..."
echo "$COMPOSE_CONFIG" | grep -q "^networks:" || { echo "ERROR: No network configuration found"; exit 1; }
echo "$COMPOSE_CONFIG" | grep -q "discovery-network" || { echo "ERROR: discovery-network not defined"; exit 1; }
echo "Network configuration verified."

# Check volume declarations exist
echo "Checking volume declarations..."
echo "$COMPOSE_CONFIG" | grep -q "^volumes:" || { echo "ERROR: No volume declarations found"; exit 1; }
echo "$COMPOSE_CONFIG" | grep -q "postgres-data:" || { echo "ERROR: postgres-data volume not declared"; exit 1; }
echo "$COMPOSE_CONFIG" | grep -q "redis-data:" || { echo "ERROR: redis-data volume not declared"; exit 1; }
echo "$COMPOSE_CONFIG" | grep -q "localstack-data:" || { echo "ERROR: localstack-data volume not declared"; exit 1; }
echo "Volume declarations verified."

echo "Docker Compose config validation passed!"
