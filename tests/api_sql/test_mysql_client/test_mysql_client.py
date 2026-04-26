"""
Tests for src/core/api_sql/mysql_client.py

اختبارات لملف mysql_client.py - استعلامات SQL

This module tests:
- _run_query() - Connect and execute SQL queries
"""

from unittest.mock import MagicMock

import pymysql.cursors
import pytest

from src.core.api_sql.mysql_client import _run_query


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
