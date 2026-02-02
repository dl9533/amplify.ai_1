# discovery/app/middleware/error_handler.py
"""Global exception handlers."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AnalysisException,
    DiscoveryException,
    FileParseException,
    HandoffException,
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    OnetApiError,
    OnetAuthError,
    OnetNotFoundError,
    OnetRateLimitError,
    SessionNotFoundException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with FastAPI app."""

    @app.exception_handler(SessionNotFoundException)
    async def session_not_found_handler(request: Request, exc: SessionNotFoundException):
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"Session not found: {exc.session_id}",
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

    @app.exception_handler(AnalysisException)
    async def analysis_error_handler(request: Request, exc: AnalysisException):
        logger.error(f"Analysis error: {exc.message}", extra={"details": exc.details})
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Analysis processing failed. Please try again.",
                "type": "analysis_error",
            },
        )

    @app.exception_handler(HandoffException)
    async def handoff_error_handler(request: Request, exc: HandoffException):
        logger.error(f"Handoff error: {exc.message}", extra={"details": exc.details})
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Handoff to Build phase failed. Please try again.",
                "type": "handoff_error",
            },
        )

    @app.exception_handler(OnetRateLimitError)
    async def onet_rate_limit_handler(request: Request, exc: OnetRateLimitError):
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "type": "rate_limit",
                "retry_after": exc.retry_after,
            },
            headers=headers,
        )

    @app.exception_handler(OnetAuthError)
    async def onet_auth_error_handler(request: Request, exc: OnetAuthError):
        logger.error(f"O*NET authentication error: {exc.message}")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "External service temporarily unavailable.",
                "type": "service_unavailable",
            },
        )

    @app.exception_handler(OnetNotFoundError)
    async def onet_not_found_handler(request: Request, exc: OnetNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"O*NET resource not found: {exc.resource}" if exc.resource else "O*NET resource not found",
                "type": "onet_not_found",
            },
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

    @app.exception_handler(LLMRateLimitError)
    async def llm_rate_limit_handler(request: Request, exc: LLMRateLimitError):
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(int(exc.retry_after))
        return JSONResponse(
            status_code=429,
            content={
                "detail": "AI service rate limit exceeded. Please try again later.",
                "type": "llm_rate_limit",
                "retry_after": exc.retry_after,
            },
            headers=headers,
        )

    @app.exception_handler(LLMAuthError)
    async def llm_auth_error_handler(request: Request, exc: LLMAuthError):
        logger.error(f"LLM authentication error: {exc.message}")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "AI service temporarily unavailable.",
                "type": "service_unavailable",
            },
        )

    @app.exception_handler(LLMConnectionError)
    async def llm_connection_error_handler(request: Request, exc: LLMConnectionError):
        logger.error(f"LLM connection error: {exc.message}")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "AI service temporarily unavailable.",
                "type": "service_unavailable",
            },
        )

    @app.exception_handler(LLMError)
    async def llm_error_handler(request: Request, exc: LLMError):
        logger.error(f"LLM error: {exc.message}")
        return JSONResponse(
            status_code=502,
            content={
                "detail": "AI service error. Please try again.",
                "type": "llm_error",
            },
        )

    @app.exception_handler(DiscoveryException)
    async def discovery_error_handler(request: Request, exc: DiscoveryException):
        # Log the full error details server-side, but return generic message to client
        logger.error(f"Discovery error: {exc.message}", extra={"details": exc.details})
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An error occurred processing your request.",
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
