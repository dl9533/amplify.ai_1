"""Exception classes for the Discovery service.

This module defines custom exceptions for API error handling,
providing specific exception types for different error conditions.
"""
from typing import Any


class DiscoveryException(Exception):
    """Base exception for Discovery module."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SessionNotFoundException(DiscoveryException):
    """Session not found."""

    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id


class ValidationException(DiscoveryException):
    """Validation error."""
    pass


class FileParseException(DiscoveryException):
    """File parsing error."""

    def __init__(self, message: str, filename: str | None = None):
        super().__init__(message, {"filename": filename})
        self.filename = filename


class AnalysisException(DiscoveryException):
    """Analysis error."""
    pass


class HandoffException(DiscoveryException):
    """Handoff to Build error."""
    pass


class OnetApiError(Exception):
    """Base exception for O*NET API errors.

    This is the base class for all O*NET API related exceptions.
    It can be caught to handle any O*NET API error generically.

    Attributes:
        message: Human-readable error description.
        status_code: Optional HTTP status code that triggered the error.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error description.
            status_code: Optional HTTP status code that triggered the error.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OnetRateLimitError(OnetApiError):
    """Exception raised when O*NET API rate limit is exceeded.

    This exception indicates a 429 Too Many Requests response,
    signaling that the client should back off and retry later.

    Attributes:
        retry_after: Optional number of seconds to wait before retrying.
    """

    def __init__(
        self, message: str = "O*NET API rate limit exceeded", retry_after: int | None = None
    ) -> None:
        """Initialize the rate limit exception.

        Args:
            message: Human-readable error description.
            retry_after: Optional number of seconds to wait before retrying.
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class OnetAuthError(OnetApiError):
    """Exception raised when O*NET API authentication fails.

    This exception indicates a 401 Unauthorized response,
    typically due to an invalid or missing API key.
    """

    def __init__(self, message: str = "O*NET API authentication failed") -> None:
        """Initialize the authentication error.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message, status_code=401)


class OnetNotFoundError(OnetApiError):
    """Exception raised when an O*NET resource is not found.

    This exception indicates a 404 Not Found response,
    typically when requesting an invalid occupation code.

    Attributes:
        resource: Optional identifier of the resource that was not found.
    """

    def __init__(
        self, message: str = "O*NET resource not found", resource: str | None = None
    ) -> None:
        """Initialize the not found exception.

        Args:
            message: Human-readable error description.
            resource: Optional identifier of the resource that was not found.
        """
        super().__init__(message, status_code=404)
        self.resource = resource


class LLMError(Exception):
    """Base exception for LLM service errors.

    This is the base class for all LLM-related exceptions.
    It can be caught to handle any LLM error generically.

    Attributes:
        message: Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error description.
        """
        self.message = message
        super().__init__(self.message)


class LLMAuthError(LLMError):
    """Exception raised when LLM API authentication fails.

    This exception indicates an authentication error,
    typically due to an invalid or missing API key.
    """

    def __init__(self, message: str = "LLM API authentication failed") -> None:
        """Initialize the authentication error.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)


class LLMRateLimitError(LLMError):
    """Exception raised when LLM API rate limit is exceeded.

    This exception indicates that too many requests have been made
    and the client should back off and retry later.

    Attributes:
        retry_after: Optional number of seconds to wait before retrying.
    """

    def __init__(
        self, message: str = "LLM API rate limit exceeded", retry_after: float | None = None
    ) -> None:
        """Initialize the rate limit exception.

        Args:
            message: Human-readable error description.
            retry_after: Optional number of seconds to wait before retrying.
        """
        super().__init__(message)
        self.retry_after = retry_after


class LLMConnectionError(LLMError):
    """Exception raised when connection to LLM API fails.

    This exception indicates a network connectivity issue
    preventing communication with the LLM service.
    """

    def __init__(self, message: str = "Failed to connect to LLM API") -> None:
        """Initialize the connection error.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)
