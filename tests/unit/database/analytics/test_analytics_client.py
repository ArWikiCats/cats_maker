from dataclasses import dataclass
from unittest.mock import MagicMock
import pytest

from src.cats_maker.database.analytics.client import WikiReplicaDB
from src.cats_maker.database.analytics.maps import MapsData
from src.cats_maker.config import Settings


class FakeWikiMapsStore:
    def load_local_wikimap(self, file_name) -> MapsData:
        return MapsData(last_cache_update=0, data={})

    def save_wikimap(
        self,
        file_name: str,
        data: dict,
    ) -> None:
        return


@dataclass
class MockWikiResolutionDeps:
    ensure_connection: MagicMock
    select: MagicMock


@pytest.fixture
def mock_wiki_resolution_deps(monkeypatch: pytest.MonkeyPatch) -> MockWikiResolutionDeps:
    """Bundle fixture replacing stacked @patch decorators for wiki resolution tests."""
    mock_ensure = MagicMock()
    mock_select = MagicMock()

    monkeypatch.setattr(
        "src.cats_maker.database.analytics.replica_db.WikiReplicaBaseDB._ensure_connection", mock_ensure
    )
    monkeypatch.setattr("src.cats_maker.database.analytics.replica_db.WikiReplicaBaseDB.select", mock_select)

    return MockWikiResolutionDeps(
        ensure_connection=mock_ensure,
        select=mock_select,
    )


class TestToolforgeWikiReplicaResolution:
    def test_toolforge_wiki_replica_resolution(
        self,
        mock_wiki_resolution_deps: MockWikiResolutionDeps,
        monkeypatch: pytest.MonkeyPatch,
    ):
        from src.cats_maker.database.analytics.maps import WikiReplicaMaps

        monkeypatch.setenv("TOOL_REPLICA_USER", "someuser")
        monkeypatch.setenv("TOOL_REPLICA_PASSWORD", "zz")
        monkeypatch.setattr("sys.argv", ["script_name"])  # avoid a stray -nosql flag
        Settings._instance = None
        settings = Settings.get_instance()

        mock_wiki_resolution_deps.select.return_value = [
            {"lang": "ar", "dbname": "arwiki", "url": "ar.wikipedia.org", "slice": "s1.labsdb"},
            {"lang": "en", "dbname": "enwiki", "url": "en.wikipedia.org", "slice": "s2.labsdb"},
        ]

        maps = WikiReplicaMaps(
            save_new_data=False,
            store=FakeWikiMapsStore(),  # pyright: ignore[reportArgumentType]
            settings=settings,
        )
        db = WikiReplicaDB(
            wiki_identifier="arwiki",
            settings=settings,
            maps=maps,
            safe_load=True,
        )
        assert db.dbname == "arwiki_p"
        assert db.host == "s1.analytics.db.svc.wikimedia.cloud"

        db2 = WikiReplicaDB(
            wiki_identifier="en",
            settings=settings,
            maps=maps,
            safe_load=True,
        )
        assert db2.dbname == "enwiki_p"
        assert db2.host == "s2.analytics.db.svc.wikimedia.cloud"


class TestSqlCapability:
    def test_can_use_sql(self, monkeypatch):

        # Test when environment variable is not present
        monkeypatch.delenv("TOOL_REPLICA_USER", raising=False)
        Settings._instance = None
        assert WikiReplicaDB.can_use_sql() is False

    def test_can_use_sql2(self, monkeypatch):

        # Test command-line arguments override (nosql)
        monkeypatch.setattr("sys.argv", ["script_name", "-nosql"])
        Settings._instance = None
        assert WikiReplicaDB.can_use_sql() is False

    def test_can_use_sql3(self, monkeypatch):

        # Test when environment variable is present
        monkeypatch.setenv("TOOL_REPLICA_USER", "someuser")
        monkeypatch.setenv("TOOL_REPLICA_PASSWORD", "zz")
        Settings._instance = None
        assert WikiReplicaDB.can_use_sql() is True

    def test_can_use_sql4(self, monkeypatch):

        monkeypatch.setenv("TOOL_REPLICA_USER", "someuser")
        monkeypatch.setenv("TOOL_REPLICA_PASSWORD", "zz")

        # Test command-line arguments override (use_sql)
        monkeypatch.setattr("sys.argv", ["script_name", "-use_sql"])
        Settings._instance = None
        assert WikiReplicaDB.can_use_sql() is True
