"""Unit tests for src/core/api_sql/db_pool.py module."""

import threading
from unittest.mock import MagicMock

import pymysql
import pytest

from src.core.api_sql.db_pool import DatabaseManager
from src.core.api_sql.exceptions import (
    DatabaseConnectionError,
    QueryExecutionError,
)


class TestDatabaseManagerSingleton:
    """Tests for the singleton behavior of DatabaseManager."""

    def test_returns_same_instance(self):
        # Reset singleton for test isolation
        DatabaseManager._instance = None
        a = DatabaseManager()
        b = DatabaseManager()
        assert a is b
        # Cleanup
        DatabaseManager._instance = None

    def test_thread_safe_creation(self):
        DatabaseManager._instance = None
        instances = []

        def create():
            instances.append(DatabaseManager())

        threads = [threading.Thread(target=create) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(inst is instances[0] for inst in instances)
        DatabaseManager._instance = None


class TestDatabaseManagerGetConnection:
    """Tests for DatabaseManager.get_connection context manager."""

    def test_raises_when_not_production(self, mocker):
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=False,
        )
        dm = DatabaseManager()
        with pytest.raises(DatabaseConnectionError, match="non-production"):
            with dm.get_connection("ar"):
                pass

    def test_opens_and_closes_connection(self, mocker):
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_connect = mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        with dm.get_connection("ar") as conn:
            assert conn is mock_conn

        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_closes_connection_on_exception(self, mocker):
        mock_conn = MagicMock()
        mock_conn.open = True
        mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        with pytest.raises(RuntimeError):
            with dm.get_connection("ar"):
                raise RuntimeError("boom")

        mock_conn.close.assert_called_once()

    def test_wraps_mysql_error_as_connection_error(self, mocker):
        mocker.patch(
            "pymysql.connect",
            side_effect=pymysql.MySQLError("conn refused"),
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        with pytest.raises(DatabaseConnectionError, match="Failed to connect"):
            with dm.get_connection("ar"):
                pass


class TestDatabaseManagerExecuteQuery:
    """Tests for DatabaseManager.execute_query."""

    def test_rejects_non_select(self):
        dm = DatabaseManager()
        with pytest.raises(ValueError, match="Only SELECT"):
            dm.execute_query("ar", "DELETE FROM page")

    def test_rejects_update(self):
        dm = DatabaseManager()
        with pytest.raises(ValueError, match="Only SELECT"):
            dm.execute_query("ar", "UPDATE page SET page_title='x'")

    def test_rejects_insert(self):
        dm = DatabaseManager()
        with pytest.raises(ValueError, match="Only SELECT"):
            dm.execute_query("ar", "INSERT INTO page VALUES (1)")

    def test_accepts_select_with_leading_whitespace(self, mocker):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.open = True

        mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        result = dm.execute_query("ar", "  SELECT 1")
        assert result == []

    def test_decodes_bytes_values(self, mocker):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"title": b"test_title", "ns": 14},
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.open = True

        mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        result = dm.execute_query("ar", "SELECT 1")
        assert result == [{"title": "test_title", "ns": 14}]

    def test_passes_params_to_cursor(self, mocker):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.open = True

        mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        dm.execute_query("ar", "SELECT 1 WHERE x = %s", ("val",))
        mock_cursor.execute.assert_called_once_with("SELECT 1 WHERE x = %s", ("val",))

    def test_wraps_mysql_error_as_query_error(self, mocker):
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = pymysql.MySQLError("bad query")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.open = True

        mocker.patch("pymysql.connect", return_value=mock_conn)
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.is_production",
            return_value=True,
        )
        mocker.patch(
            "src.core.api_sql.config.ConfigLoader.get_db_config",
            return_value=MagicMock(
                host="h",
                database="d",
                user_file_path="/f",
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            ),
        )

        dm = DatabaseManager()
        with pytest.raises(QueryExecutionError, match="Query failed"):
            dm.execute_query("ar", "SELECT 1")
