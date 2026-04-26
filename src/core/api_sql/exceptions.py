"""Custom exceptions for database operations."""


class DatabaseError(Exception):
    """Base exception for all database errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""


class QueryExecutionError(DatabaseError):
    """Raised when a SQL query fails to execute."""


class DatabaseFetchError(DatabaseError):
    """Raised when fetching results from a cursor fails."""
