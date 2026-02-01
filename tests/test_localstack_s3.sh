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
