"""
Tests for src/core/api_sql/db_pool.py

اختبارات لملف db_pool.py - استعلامات SQL

This module tests:
- _run_query() - Connect and execute SQL queries
"""

from unittest.mock import MagicMock

import pymysql
import pymysql.cursors
import pytest

from src.core.api_sql.db_pool import _decode, _is_select_query, _run_query, make_sql_connect_silent
from src.core.api_sql.exceptions import (
    DatabaseConnectionError,
    DatabaseFetchError,
    QueryExecutionError,
)


@pytest.fixture
def mock_mysql_connection(mocker):
    """Fixture to mock pymysql connection and cursor objects."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Setup context managers for connection and cursor
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False

    # Patch pymysql.connect
    mock_connect = mocker.patch("pymysql.connect", return_value=mock_conn)

    return mock_conn, mock_cursor, mock_connect


class TestSqlConnectPymysql:
    """Tests for _run_query function."""

    def test_uses_dict_cursor_when_requested(self, mock_mysql_connection):
        """Test that _run_query uses DictCursor."""
        _, mock_cursor, mock_connect = mock_mysql_connection
        mock_cursor.fetchall.return_value = [{"col": "value"}]

        _run_query("SELECT 1", db="test", host="localhost", values=None)

        # Check that DictCursor was used
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["cursorclass"] == pymysql.cursors.DictCursor

    def test_executes_query_with_values(self, mock_mysql_connection):
        """Test that _run_query passes values to execute."""
        _, mock_cursor, _ = mock_mysql_connection
        mock_cursor.fetchall.return_value = []

        _run_query("SELECT * FROM table WHERE id = %s", db="test", host="localhost", values=(123,))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM table WHERE id = %s", (123,))

    def test_returns_fetchall_results(self, mock_mysql_connection):
        """Test that _run_query returns fetchall results."""
        _, mock_cursor, _ = mock_mysql_connection
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

        result = _run_query("SELECT 1", db="test", host="localhost", values=None)

        assert result == [("row1",), ("row2",)]

    def test_sets_charset_to_utf8mb4(self, mock_mysql_connection):
        """Test that _run_query uses utf8mb4 charset."""
        _, _, mock_connect = mock_mysql_connection

        _run_query("SELECT 1", db="test", host="localhost", values=None)

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["charset"] == "utf8mb4"

    def test_enables_autocommit(self, mock_mysql_connection):
        """Test that _run_query enables autocommit."""
        _, _, mock_connect = mock_mysql_connection

        _run_query("SELECT 1", db="test", host="localhost", values=None)

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["autocommit"] is True

    def test_sets_connection_timeouts(self, mock_mysql_connection):
        """Test that _run_query configures connect_timeout and read_timeout."""
        _, _, mock_connect = mock_mysql_connection

        _run_query("SELECT 1", db="test", host="localhost", values=None)

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["connect_timeout"] == 10
        assert call_kwargs["read_timeout"] == 30

    def test_skips_fetchall_for_insert(self, mock_mysql_connection):
        """Test that _run_query does not call fetchall for INSERT statements."""
        _, mock_cursor, _ = mock_mysql_connection

        result = _run_query("INSERT INTO table VALUES (%s)", db="test", host="localhost", values=(1,))

        mock_cursor.fetchall.assert_not_called()
        assert result == []

    def test_skips_fetchall_for_update(self, mock_mysql_connection):
        """Test that _run_query does not call fetchall for UPDATE statements."""
        _, mock_cursor, _ = mock_mysql_connection

        result = _run_query("UPDATE table SET col=1", db="test", host="localhost", values=None)

        mock_cursor.fetchall.assert_not_called()
        assert result == []

    def test_skips_fetchall_for_delete(self, mock_mysql_connection):
        """Test that _run_query does not call fetchall for DELETE statements."""
        _, mock_cursor, _ = mock_mysql_connection

        result = _run_query("DELETE FROM table WHERE id=1", db="test", host="localhost", values=None)

        mock_cursor.fetchall.assert_not_called()
        assert result == []

    def test_skips_fetchall_for_whitespace_prefixed_insert(self, mock_mysql_connection):
        """Test that leading whitespace is handled when detecting non-SELECT."""
        _, mock_cursor, _ = mock_mysql_connection

        result = _run_query("  \nINSERT INTO table VALUES (1)", db="test", host="localhost", values=None)

        mock_cursor.fetchall.assert_not_called()
        assert result == []


class TestIsSelectQuery:
    """Tests for _is_select_query helper."""

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("SELECT * FROM table", True),
            ("select * from table", True),
            ("  SELECT * FROM table", True),
            ("\n\tSELECT * FROM table", True),
            ("INSERT INTO table VALUES (1)", False),
            ("UPDATE table SET col=1", False),
            ("DELETE FROM table WHERE id=1", False),
            ("", False),
            ("  ", False),
        ],
    )
    def test_detects_select_correctly(self, query, expected):
        assert _is_select_query(query) is expected


class TestRunQueryErrors:
    """Tests for _run_query exception handling."""

    def test_raises_database_connection_error(self, mocker):
        """Test that pymysql.connect failure raises DatabaseConnectionError."""
        mocker.patch("pymysql.connect", side_effect=pymysql.Error("connection refused"))

        with pytest.raises(DatabaseConnectionError):
            _run_query("SELECT 1", db="test", host="localhost", values=None)

    def test_raises_query_execution_error(self, mocker):
        """Test that cursor.execute failure raises QueryExecutionError."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = False
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        mock_cursor.execute.side_effect = pymysql.Error("syntax error")

        mocker.patch("pymysql.connect", return_value=mock_conn)

        with pytest.raises(QueryExecutionError):
            _run_query("SELECT 1", db="test", host="localhost", values=None)

    def test_raises_database_fetch_error(self, mocker):
        """Test that cursor.fetchall failure raises DatabaseFetchError."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = False
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        mock_cursor.fetchall.side_effect = pymysql.Error("fetch failed")

        mocker.patch("pymysql.connect", return_value=mock_conn)

        with pytest.raises(DatabaseFetchError):
            _run_query("SELECT 1", db="test", host="localhost", values=None)


class TestDecode:
    """Tests for _decode helper."""

    def test_decodes_valid_utf8_bytes(self):
        assert _decode(b"hello") == "hello"

    def test_decodes_arabic_utf8_bytes(self):
        assert _decode("مرحبا".encode("utf-8")) == "مرحبا"

    def test_returns_str_for_invalid_bytes(self):
        """Test fallback when bytes are not valid UTF-8."""
        invalid = b"\xff\xfe"
        result = _decode(invalid)
        assert result == str(invalid)


class TestMakeSqlConnectSilent:
    """Tests for make_sql_connect_silent public interface."""

    def test_returns_empty_list_for_empty_query(self):
        result = make_sql_connect_silent("", host="h", db="d")
        assert result == []

    def test_returns_decoded_rows_on_success(self, mocker):
        mocker.patch(
            "src.core.api_sql.db_pool._run_query",
            return_value=[{"col": b"value"}],
        )

        result = make_sql_connect_silent("SELECT 1", host="h", db="d")

        assert result == [{"col": "value"}]

    def test_returns_empty_list_on_database_error(self, mocker):
        from src.core.api_sql.exceptions import DatabaseConnectionError

        mocker.patch(
            "src.core.api_sql.db_pool._run_query",
            side_effect=DatabaseConnectionError("fail"),
        )

        result = make_sql_connect_silent("SELECT 1", host="h", db="d")

        assert result == []
