"""
Custom exception types for the application.

These exceptions provide more specific error handling and better
error messages for different failure scenarios.
"""


class CloudVelousException(Exception):
    """Base exception for all application-specific errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DatabaseOperationError(CloudVelousException):
    """Raised when a database operation fails."""
    pass


class SessionNotFoundError(CloudVelousException):
    """Raised when a training session is not found."""
    pass


class ChunkNotFoundError(CloudVelousException):
    """Raised when a knowledge chunk is not found."""
    pass


class WorkflowNotFoundError(CloudVelousException):
    """Raised when a workflow vector is not found."""
    pass


class ValidationError(CloudVelousException):
    """Raised when input validation fails."""
    pass


class BulkOperationError(CloudVelousException):
    """Raised when a bulk operation fails."""
    pass


class EmbeddingOperationError(CloudVelousException):
    """Raised when an embedding operation fails."""
    pass


class RateLimitExceededError(CloudVelousException):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(CloudVelousException):
    """Raised when authentication fails."""
    pass

