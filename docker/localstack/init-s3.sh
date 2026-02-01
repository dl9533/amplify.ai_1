#!/bin/bash
# LocalStack S3 Initialization Script
# This script runs after LocalStack is ready (via /etc/localstack/init/ready.d)

set -e

echo "Initializing LocalStack S3..."

# Wait for S3 service to be fully ready
max_retries=30
retry_count=0
while ! awslocal s3 ls > /dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "ERROR: S3 service not ready after $max_retries retries"
        exit 1
    fi
    echo "Waiting for S3 service... (attempt $retry_count/$max_retries)"
    sleep 1
done

echo "S3 service is ready"

# Create the discovery-uploads bucket
BUCKET_NAME="discovery-uploads"

if awslocal s3 ls "s3://${BUCKET_NAME}" > /dev/null 2>&1; then
    echo "Bucket ${BUCKET_NAME} already exists"
else
    echo "Creating bucket: ${BUCKET_NAME}"
    awslocal s3 mb "s3://${BUCKET_NAME}"
fi

# Configure CORS policy for frontend uploads
echo "Configuring CORS policy for ${BUCKET_NAME}..."
awslocal s3api put-bucket-cors --bucket "${BUCKET_NAME}" --cors-configuration '{
    "CORSRules": [
        {
            "AllowedOrigins": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag", "x-amz-meta-custom-header"],
            "MaxAgeSeconds": 3600
        }
    ]
}'

echo "LocalStack S3 initialization complete!"
echo "Bucket ${BUCKET_NAME} is ready for use"

# List buckets to confirm
echo "Available buckets:"
awslocal s3 ls
