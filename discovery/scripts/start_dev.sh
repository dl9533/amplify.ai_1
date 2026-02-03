#!/bin/bash
# Start the Discovery development environment
# Usage: ./scripts/start_dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Discovery Development Environment"
echo "============================================="

cd "$PROJECT_DIR"

# Step 1: Start Docker services
echo ""
echo "📦 Starting Docker services (PostgreSQL, Redis, LocalStack)..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec discovery-postgres pg_isready -U discovery_user -d discovery_db > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Step 2: Run database migrations
echo ""
echo "🔄 Running database migrations..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
alembic upgrade head || echo "⚠️  Migrations may need setup - continuing..."

# Step 3: Seed test data
echo ""
echo "🌱 Seeding test data..."
python scripts/seed_data.py || echo "⚠️  Seed script may have issues - continuing..."

# Step 4: Create S3 bucket in LocalStack
echo ""
echo "🪣 Creating S3 bucket in LocalStack..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://discovery-documents 2>/dev/null || echo "Bucket may already exist"

echo ""
echo "============================================="
echo "✅ Development environment is ready!"
echo ""
echo "To start the backend:"
echo "  cd $PROJECT_DIR && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001"
echo ""
echo "To start the frontend:"
echo "  cd $PROJECT_DIR/frontend && npm run dev"
echo ""
echo "API docs: http://localhost:8001/docs"
echo "Frontend: http://localhost:5173"
