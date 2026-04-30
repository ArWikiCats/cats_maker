"""Unit tests for src/core/api_sql/exceptions.py module."""

import pytest

from src.core.api_sql.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseFetchError,
    QueryExecutionError,
)


class TestDatabaseError:
    """Tests for the base DatabaseError exception."""

    def test_message_stored(self):
        err = DatabaseError("something failed")
        assert str(err) == "something failed"

    def test_original_exception_default_none(self):
        err = DatabaseError("msg")
        assert err.original_exception is None

    def test_original_exception_stored(self):
        cause = RuntimeError("root cause")
        err = DatabaseError("msg", cause)
        assert err.original_exception is cause

    def test_is_exception_subclass(self):
        assert issubclass(DatabaseError, Exception)


class TestSubclassHierarchy:
    """All custom exceptions should inherit from DatabaseError."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            DatabaseConnectionError,
            QueryExecutionError,
            DatabaseFetchError,
            ConfigurationError,
        ],
    )
    def test_is_database_error_subclass(self, exc_cls):
        assert issubclass(exc_cls, DatabaseError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            DatabaseConnectionError,
            QueryExecutionError,
            DatabaseFetchError,
            ConfigurationError,
        ],
    )
    def test_can_be_raised_and_caught_as_database_error(self, exc_cls):
        with pytest.raises(DatabaseError):
            raise exc_cls("test")

    @pytest.mark.parametrize(
        "exc_cls",
        [
            DatabaseConnectionError,
            QueryExecutionError,
            DatabaseFetchError,
            ConfigurationError,
        ],
    )
    def test_inherits_original_exception(self, exc_cls):
        cause = ValueError("inner")
        err = exc_cls("outer", cause)
        assert err.original_exception is cause
        assert str(err) == "outer"
