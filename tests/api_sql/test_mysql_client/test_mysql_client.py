"""
Tests for src/api_sql/mysql_client.py

اختبارات لملف mysql_client.py - استعلامات SQL

This module tests:
- _sql_connect_pymysql() - Connect and execute SQL queries
"""

from unittest.mock import MagicMock

import pymysql.cursors
import pytest

from src.core.api_sql.mysql_client import _sql_connect_pymysql


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
    """Tests for _sql_connect_pymysql function."""

    def test_uses_dict_cursor_when_requested(self, mock_mysql_connection):
        """Test that _sql_connect_pymysql uses DictCursor."""
        _, mock_cursor, mock_connect = mock_mysql_connection
        mock_cursor.fetchall.return_value = [{"col": "value"}]

        _sql_connect_pymysql("SELECT 1", db="test", host="localhost")

        # Check that DictCursor was used
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["cursorclass"] == pymysql.cursors.DictCursor

    def test_executes_query_with_values(self, mock_mysql_connection):
        """Test that _sql_connect_pymysql passes values to execute."""
        _, mock_cursor, _ = mock_mysql_connection
        mock_cursor.fetchall.return_value = []

        _sql_connect_pymysql("SELECT * FROM table WHERE id = %s", db="test", host="localhost", values=(123,))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM table WHERE id = %s", (123,))

    def test_returns_fetchall_results(self, mock_mysql_connection):
        """Test that _sql_connect_pymysql returns fetchall results."""
        _, mock_cursor, _ = mock_mysql_connection
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

        result = _sql_connect_pymysql("SELECT 1", db="test", host="localhost")

        assert result == [("row1",), ("row2",)]

    def test_sets_charset_to_utf8mb4(self, mock_mysql_connection):
        """Test that _sql_connect_pymysql uses utf8mb4 charset."""
        _, _, mock_connect = mock_mysql_connection

        _sql_connect_pymysql("SELECT 1", db="test", host="localhost")

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["charset"] == "utf8mb4"

    def test_enables_autocommit(self, mock_mysql_connection):
        """Test that _sql_connect_pymysql enables autocommit."""
        _, _, mock_connect = mock_mysql_connection

        _sql_connect_pymysql("SELECT 1", db="test", host="localhost")

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["autocommit"] is True
