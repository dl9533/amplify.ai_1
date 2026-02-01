"""O*NET API exception classes.

This module defines custom exceptions for O*NET API error handling,
providing specific exception types for different error conditions.
"""


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
