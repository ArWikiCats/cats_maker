"""Custom exceptions for the cats_maker_new project."""


class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class QueryExecutionError(DatabaseError):
    """Raised when a query fails to execute."""

    pass


class DatabaseFetchError(DatabaseError):
    """Raised when fetching results from a query fails."""

    pass
