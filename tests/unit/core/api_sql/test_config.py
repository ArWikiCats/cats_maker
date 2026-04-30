"""Unit tests for src/core/api_sql/config.py module."""

from pathlib import Path

import pytest

from src.core.api_sql.config import ConfigLoader, DatabaseConfig
from src.core.api_sql.exceptions import ConfigurationError


class TestDatabaseConfig:
    """Tests for the DatabaseConfig frozen dataclass."""

    def test_default_values(self):
        cfg = DatabaseConfig(host="h", database="d", user_file_path=Path("/f"))
        assert cfg.connect_timeout == 10
        assert cfg.read_timeout == 30
        assert cfg.charset == "utf8mb4"

    def test_frozen(self):
        cfg = DatabaseConfig(host="h", database="d", user_file_path=Path("/f"))
        with pytest.raises(AttributeError):
            cfg.host = "other"  # type: ignore[misc]

    def test_custom_values(self):
        cfg = DatabaseConfig(
            host="myhost",
            database="mydb",
            user_file_path=Path("/cnf"),
            connect_timeout=5,
            read_timeout=60,
            charset="latin1",
        )
        assert cfg.connect_timeout == 5
        assert cfg.read_timeout == 60
        assert cfg.charset == "latin1"


class TestConfigLoaderGetDbConfig:
    """Tests for ConfigLoader.get_db_config."""

    def test_raises_when_cnf_missing(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=False)
        with pytest.raises(ConfigurationError, match="Replica config file not found"):
            ConfigLoader.get_db_config("ar")

    def test_simple_wiki_code(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("ar")
        assert cfg.host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert cfg.database == "arwiki_p"

    def test_wiki_code_with_wiki_suffix(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("enwiki")
        assert cfg.host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert cfg.database == "enwiki_p"

    def test_wikidata_alias(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("wikidata")
        assert cfg.host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert cfg.database == "wikidatawiki_p"

    def test_hyphen_replaced_with_underscore(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("be-x-old")
        assert "be_x_old" in cfg.host
        assert "be_x_old" in cfg.database

    def test_wiktionary_not_double_suffixed(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("enwiktionary")
        assert cfg.host == "enwiktionary.analytics.db.svc.wikimedia.cloud"
        assert cfg.database == "enwiktionary_p"

    def test_user_file_path_points_to_home(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("ar")
        assert cfg.user_file_path.name == "replica.my.cnf"

    def test_be_tarask_alias(self, mocker):
        mocker.patch("pathlib.Path.exists", return_value=True)
        cfg = ConfigLoader.get_db_config("be-tarask")
        assert "be_x_old" in cfg.host


class TestConfigLoaderIsProduction:
    """Tests for ConfigLoader.is_production."""

    def test_returns_true_when_production(self, mocker):
        mocker.patch("os.getenv", return_value="production")
        assert ConfigLoader.is_production() is True

    def test_returns_true_case_insensitive(self, mocker):
        mocker.patch("os.getenv", return_value="Production")
        assert ConfigLoader.is_production() is True

    def test_returns_false_when_empty(self, mocker):
        mocker.patch("os.getenv", return_value="")
        assert ConfigLoader.is_production() is False

    def test_returns_false_when_not_set(self, mocker):
        mocker.patch("os.getenv", return_value="")
        assert ConfigLoader.is_production() is False

    def test_returns_false_for_other_value(self, mocker):
        mocker.patch("os.getenv", return_value="staging")
        assert ConfigLoader.is_production() is False
