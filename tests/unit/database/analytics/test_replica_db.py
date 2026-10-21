from unittest.mock import MagicMock
import pytest

from src.cats_maker.database.analytics.replica_db import WikiReplicaBaseDB


@pytest.fixture
def mock_pymysql_connect(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture replacing pymysql.connect patch."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_connect = MagicMock(return_value=mock_conn)
    monkeypatch.setattr("pymysql.connect", mock_connect)
    return mock_connect


class TestWikiReplicaBaseDB:
    def test_wiki_replica_db_select(self, mock_pymysql_connect):
        mock_conn = mock_pymysql_connect.return_value
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [{"col": "val"}]

        db = WikiReplicaBaseDB("testdb", "localhost", "user", "pass")
        result = db.select("SELECT * FROM table")

        assert result == [{"col": "val"}]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table", None)
