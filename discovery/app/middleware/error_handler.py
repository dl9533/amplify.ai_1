# discovery/app/middleware/error_handler.py
"""Global exception handlers."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    DiscoveryException,
    SessionNotFoundException,
    ValidationException,
    FileParseException,
    OnetApiError,
    OnetRateLimitError,
    AnalysisException,
)

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with FastAPI app."""

    @app.exception_handler(SessionNotFoundException)
    async def session_not_found_handler(request: Request, exc: SessionNotFoundException):
        return JSONResponse(
            status_code=404,
            content={
                "detail": exc.message,
                "type": "session_not_found",
                "session_id": exc.session_id,
            },
        )

    @app.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message,
                "type": "validation_error",
                "errors": exc.details,
            },
        )

    @app.exception_handler(FileParseException)
    async def file_parse_handler(request: Request, exc: FileParseException):
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.message,
                "type": "file_parse_error",
                "filename": exc.filename,
            },
        )

    @app.exception_handler(OnetRateLimitError)
    async def rate_limit_handler(request: Request, exc: OnetRateLimitError):
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=429,
            content={
                "detail": exc.message,
                "type": "rate_limit",
                "retry_after": exc.retry_after,
            },
            headers=headers,
        )

    @app.exception_handler(OnetApiError)
    async def onet_error_handler(request: Request, exc: OnetApiError):
        logger.error(f"O*NET API error: {exc.message}")
        return JSONResponse(
            status_code=502,
            content={
                "detail": "External API error. Please try again.",
                "type": "external_api_error",
            },
        )

    @app.exception_handler(DiscoveryException)
    async def discovery_error_handler(request: Request, exc: DiscoveryException):
        logger.error(f"Discovery error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": exc.message,
                "type": "discovery_error",
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred.",
                "type": "internal_error",
            },
        )
