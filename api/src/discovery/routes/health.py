"""Health check endpoints for Discovery API."""

from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from discovery import __version__
from discovery.config import get_settings

router = APIRouter(tags=["health"])


class DependencyStatus(BaseModel):
    """Status of a single dependency."""

    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    dependencies: dict[str, DependencyStatus] | None = None


async def check_postgres() -> DependencyStatus:
    """Check PostgreSQL connectivity."""
    try:
        # Import here to avoid circular imports and allow app to start without DB
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        settings = get_settings()
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        await engine.dispose()
        return DependencyStatus(status="healthy")
    except Exception as e:
        return DependencyStatus(status="unhealthy", message=str(e))


async def check_redis() -> DependencyStatus:
    """Check Redis connectivity."""
    try:
        settings = get_settings()
        client = redis.from_url(settings.redis_url)

        await client.ping()
        await client.aclose()
        return DependencyStatus(status="healthy")
    except Exception as e:
        return DependencyStatus(status="unhealthy", message=str(e))


async def check_s3() -> DependencyStatus:
    """Check S3 connectivity."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        settings = get_settings()

        # Build client kwargs
        client_kwargs: dict[str, Any] = {
            "region_name": settings.aws_region,
        }

        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        s3_client = boto3.client("s3", **client_kwargs)

        # Try to head the bucket (check if it exists and we have access)
        try:
            s3_client.head_bucket(Bucket=settings.s3_bucket)
            return DependencyStatus(status="healthy")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "404":
                return DependencyStatus(
                    status="unhealthy", message=f"Bucket '{settings.s3_bucket}' not found"
                )
            return DependencyStatus(status="unhealthy", message=str(e))
    except Exception as e:
        return DependencyStatus(status="unhealthy", message=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(
    detailed: bool = Query(default=False, description="Include dependency status")
) -> HealthResponse:
    """Health check endpoint.

    Returns service status and optionally dependency health.
    Used for Docker HEALTHCHECK and load balancer health probes.
    """
    response = HealthResponse(status="healthy", version=__version__)

    if detailed:
        postgres_status = await check_postgres()
        redis_status = await check_redis()
        s3_status = await check_s3()

        response.dependencies = {
            "postgres": postgres_status,
            "redis": redis_status,
            "s3": s3_status,
        }

        # If any dependency is unhealthy, mark overall status as degraded
        if any(
            dep.status == "unhealthy"
            for dep in [postgres_status, redis_status, s3_status]
        ):
            response.status = "degraded"

    return response


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Kubernetes readiness probe.

    Checks if the service can handle requests by verifying
    critical dependencies are available.

    Returns 200 if ready, 503 if not ready.
    """
    postgres_status = await check_postgres()
    redis_status = await check_redis()

    # Service is ready only if critical dependencies are healthy
    if postgres_status.status == "unhealthy" or redis_status.status == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "postgres": postgres_status.model_dump(),
                "redis": redis_status.model_dump(),
            },
        )

    return {"status": "ready"}
