"""Custom exceptions for database operations."""


class DatabaseError(Exception):
    """Base exception for all database errors."""

    def __init__(self, message: str, original_exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = original_exception


class DatabaseConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""

    pass


class QueryExecutionError(DatabaseError):
    """Raised when a SQL query fails to execute."""

    pass


class DatabaseFetchError(DatabaseError):
    """Raised when fetching results from a cursor fails."""


class ConfigurationError(DatabaseError):
    """Raised when required configuration is missing or invalid."""

    pass
