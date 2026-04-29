"""
Tests for the centralized settings configuration module.
"""

import pytest

from src.config import (
    CategoryConfig,
    DatabaseConfig,
    Settings,
    WikidataConfig,
    WikipediaConfig,
    WikiSiteInfo,
    settings,
)
from src.config.settings import _safe_int


class TestSafeInt:
    """Tests for _safe_int helper function."""

    def test_valid_integer_string(self):
        """Test valid integer string is converted."""

        assert _safe_int("42", 0) == 42

    def test_invalid_string_returns_default(self):
        """Test invalid string returns default value."""

        assert _safe_int("invalid", 10) == 10

    def test_empty_string_returns_default(self):
        """Test empty string returns default value."""

        assert _safe_int("", 5) == 5

    def test_none_returns_default(self):
        """Test None returns default value."""

        assert _safe_int(None, 15) == 15

    def test_float_string_returns_default(self):
        """Test float string returns default value."""

        assert _safe_int("3.14", 20) == 20


class TestWikipediaConfig:
    """Tests for WikipediaConfig dataclass."""

    def test_default_ar_family(self):
        """Test default Arabic family is wikipedia."""

        config = WikipediaConfig()
        assert config.ar_family == "wikipedia"

    def test_default_ar_code(self):
        """Test default Arabic code is ar."""

        config = WikipediaConfig()
        assert config.ar_code == "ar"

    def test_default_en_family(self):
        """Test default English family is wikipedia."""

        config = WikipediaConfig()
        assert config.en_family == "wikipedia"

    def test_default_en_code(self):
        """Test default English code is en."""

        config = WikipediaConfig()
        assert config.en_code == "en"

    def test_default_timeout(self):
        """Test default timeout is 10."""

        config = WikipediaConfig()
        assert config.default_timeout == 10

    def test_custom_values(self):
        """Test custom values can be set."""

        config = WikipediaConfig(
            ar_family="wikiquote",
            ar_code="ar",
            en_family="wikiquote",
            en_code="en",
            user_agent="Custom Agent",
            default_timeout=30,
        )
        assert config.ar_family == "wikiquote"
        assert config.en_family == "wikiquote"
        assert config.user_agent == "Custom Agent"
        assert config.default_timeout == 30


class TestWikidataConfig:
    """Tests for WikidataConfig dataclass."""

    def test_default_endpoint(self):
        """Test default Wikidata endpoint."""

        config = WikidataConfig()
        assert config.endpoint == "https://www.wikidata.org/w/api.php"

    def test_default_sparql_endpoint(self):
        """Test default SPARQL endpoint."""

        config = WikidataConfig()
        assert config.sparql_endpoint == "https://query.wikidata.org/sparql"

    def test_default_timeout(self):
        """Test default timeout is 30."""

        config = WikidataConfig()
        assert config.timeout == 30

    def test_default_maxlag(self):
        """Test default maxlag is 5."""

        config = WikidataConfig()
        assert config.maxlag == 5

    def test_custom_endpoint(self):
        """Test custom endpoint can be set."""

        config = WikidataConfig(endpoint="https://test.wikidata.org/w/api.php")
        assert config.endpoint == "https://test.wikidata.org/w/api.php"


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_default_host_is_none(self):
        """Test default host is None."""

        config = DatabaseConfig()
        assert config.host is None

    def test_default_port(self):
        """Test default port is 3306."""

        config = DatabaseConfig()
        assert config.port == 3306

    def test_default_use_sql(self):
        """Test default use_sql is True."""

        config = DatabaseConfig()
        assert config.use_sql is True

    def test_custom_host(self):
        """Test custom host can be set."""

        config = DatabaseConfig(host="localhost")
        assert config.host == "localhost"


class TestSettings:
    """Tests for Settings dataclass."""

    def test_has_wikipedia_config(self):
        """Test Settings has wikipedia config."""

        s = Settings()
        assert isinstance(s.wikipedia, WikipediaConfig)

    def test_has_wikidata_config(self):
        """Test Settings has wikidata config."""

        s = Settings()
        assert isinstance(s.wikidata, WikidataConfig)

    def test_has_database_config(self):
        """Test Settings has database config."""

        s = Settings()
        assert isinstance(s.database, DatabaseConfig)

    def test_default_range_limit(self):
        """Test default range_limit is 5."""

        s = Settings()
        assert s.range_limit == 5

    def test_default_debug(self):
        """Test default debug is False."""

        s = Settings()
        assert s.debug is False

    def test_default_log_level(self):
        """Test default log_level is INFO."""

        s = Settings()
        assert s.log_level == "INFO"


class TestSettingsEnvVars:
    """Tests for Settings environment variable processing."""

    def test_env_wikipedia_ar_code(self, monkeypatch):
        """Test WIKIPEDIA_AR_CODE environment variable."""
        monkeypatch.setenv("WIKIPEDIA_AR_CODE", "arz")

        s = Settings()
        assert s.wikipedia.ar_code == "arz"

    def test_env_wikidata_endpoint(self, monkeypatch):
        """Test WIKIDATA_ENDPOINT environment variable."""
        monkeypatch.setenv("WIKIDATA_ENDPOINT", "https://custom.wikidata.org/api")

        s = Settings()
        assert s.wikidata.endpoint == "https://custom.wikidata.org/api"

    def test_env_database_use_sql_true(self, monkeypatch):
        """Test DATABASE_USE_SQL environment variable with true."""
        monkeypatch.setenv("DATABASE_USE_SQL", "true")

        s = Settings()
        assert s.database.use_sql is True

    def test_env_database_use_sql_false(self, monkeypatch):
        """Test DATABASE_USE_SQL environment variable with false."""
        monkeypatch.setenv("DATABASE_USE_SQL", "false")

        s = Settings()
        assert s.database.use_sql is False

    def test_env_range_limit(self, monkeypatch):
        """Test RANGE_LIMIT environment variable."""
        monkeypatch.setenv("RANGE_LIMIT", "10")

        s = Settings()
        assert s.range_limit == 10

    def test_env_debug_true(self, monkeypatch):
        """Test DEBUG environment variable with true."""
        monkeypatch.setenv("DEBUG", "true")

        s = Settings()
        assert s.debug is True

    def test_env_log_level(self, monkeypatch):
        """Test LOG_LEVEL environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        s = Settings()
        assert s.log_level == "DEBUG"


class TestGlobalSettings:
    """Tests for the global settings instance."""

    def test_settings_instance_exists(self):
        """Test that global settings instance exists."""

        assert settings is not None

    def test_settings_is_settings_type(self):
        """Test that global settings is Settings type."""

        assert isinstance(settings, Settings)

    def test_settings_has_default_wikipedia(self):
        """Test settings has default Wikipedia config."""

        assert settings.wikipedia.ar_code == "ar"
        assert settings.wikipedia.en_code == "en"

    def test_settings_has_default_wikidata(self):
        """Test settings has default Wikidata config."""

        assert settings.wikidata.endpoint == "https://www.wikidata.org/w/api.php"

    def test_settings_has_default_database(self):
        """Test settings has default Database config."""

        assert settings.database.port == 3306


class TestModuleExports:
    """Tests for module exports."""

    def test_exports_settings(self):
        """Test settings is exported."""

        assert settings is not None

    def test_exports_settings_class(self):
        """Test Settings class is exported."""

        assert Settings is not None

    def test_exports_wikipedia_config(self):
        """Test WikipediaConfig is exported."""

        assert WikipediaConfig is not None

    def test_exports_wikidata_config(self):
        """Test WikidataConfig is exported."""

        assert WikidataConfig is not None

    def test_exports_database_config(self):
        """Test DatabaseConfig is exported."""

        assert DatabaseConfig is not None


class TestWikiSiteInfo:
    """Tests for WikiSiteInfo dataclass."""

    def test_default_values(self):
        """Test default values for WikiSiteInfo."""

        info = WikiSiteInfo()
        assert info.family == "wikipedia"
        assert info.code == "en"
        assert info.use is False

    def test_custom_values(self):
        """Test custom values for WikiSiteInfo."""

        info = WikiSiteInfo(family="commons", code="commons", use=True)
        assert info.family == "commons"
        assert info.code == "commons"
        assert info.use is True

    def test_getitem_family(self):
        """Test dictionary-like access for family."""

        info = WikiSiteInfo(family="wikiquote", code="en")
        assert info.family == "wikiquote"

    def test_getitem_code(self):
        """Test dictionary-like access for code."""

        info = WikiSiteInfo(family="wikipedia", code="fr")
        assert info.code == "fr"

    def test_getitem_use(self):
        """Test dictionary-like access for use."""

        info = WikiSiteInfo(use=True)
        assert info.use is True

    def test_getitem_key_1(self):
        """Test dictionary-like access for key 1 (alias for use)."""

        info = WikiSiteInfo(use=True)
        assert info[1] is True

    def test_getitem_invalid_key(self):
        """Test dictionary-like access raises KeyError for invalid key."""

        info = WikiSiteInfo()
        with pytest.raises(KeyError):
            _ = info["invalid"]

    def test_contains_family(self):
        """Test 'in' operator for family."""

        info = WikiSiteInfo()
        assert "family" in info

    def test_contains_code(self):
        """Test 'in' operator for code."""

        info = WikiSiteInfo()
        assert "code" in info

    def test_contains_use(self):
        """Test 'in' operator for use."""

        info = WikiSiteInfo()
        assert "use" in info

    def test_contains_key_1(self):
        """Test 'in' operator for key 1."""

        info = WikiSiteInfo()
        assert 1 in info

    def test_not_contains_invalid(self):
        """Test 'in' operator returns False for invalid key."""

        info = WikiSiteInfo()
        assert "invalid" not in info


class TestEEnSiteProperty:
    """Tests for Settings.EEn_site property."""

    def test_default_values(self):
        """Test default EEn_site values."""

        s = Settings()
        assert s.EEn_site.family == "wikipedia"
        assert s.EEn_site.code == "en"

    def test_custom_family(self):
        """Test EEn_site with custom_family."""

        s = Settings()
        s.site.custom_family = "wikiquote"
        assert s.EEn_site.family == "wikiquote"
        assert s.EEn_site.code == "en"

    def test_custom_lang(self):
        """Test EEn_site with custom_lang."""

        s = Settings()
        s.site.custom_lang = "de"
        assert s.EEn_site.family == "wikipedia"
        assert s.EEn_site.code == "de"


class TestAArSiteProperty:
    """Tests for Settings.AAr_site property."""

    def test_default_values(self):
        """Test default AAr_site values."""

        s = Settings()
        assert s.AAr_site.family == "wikipedia"
        assert s.AAr_site.code == "ar"

    def test_custom_family(self):
        """Test AAr_site with custom_family."""

        s = Settings()
        s.site.custom_family = "wikiquote"
        assert s.AAr_site.family == "wikiquote"
        assert s.AAr_site.code == "ar"


class TestFRSiteProperty:
    """Tests for Settings.FR_site property."""

    def test_default_values(self):
        """Test default FR_site values."""

        s = Settings()
        assert s.FR_site.code == "fr"
        assert s.FR_site.use is False

    def test_secondary_site(self):
        """Test FR_site with secondary language."""

        s = Settings()
        s.site.use_secondary = True
        s.site.secondary_lang = "es"
        s.site.secondary_family = "wikipedia"
        assert s.FR_site.code == "es"
        assert s.FR_site.family == "wikipedia"
        assert s.FR_site.use is True


class TestCategoryConfig:
    """Tests for CategoryConfig dataclass."""

    def test_default_min_members(self):
        """Test default min_members is 10."""

        config = CategoryConfig()
        assert config.min_members == 10  # Default value

    def test_custom_min_members(self):
        """Test custom min_members can be set."""

        config = CategoryConfig(min_members=10)
        assert config.min_members == 10

    def test_min_members_zero(self):
        """Test min_members can be set to 0."""

        config = CategoryConfig(min_members=0)
        assert config.min_members == 0

    def test_default_stubs(self):
        """Test default stubs is False."""

        config = CategoryConfig()
        assert config.stubs is False

    def test_default_make_new_cat(self):
        """Test default make_new_cat is True."""

        config = CategoryConfig()
        assert config.make_new_cat is True


class TestMinMembersEnvVar:
    """Tests for MIN_MEMBERS environment variable."""

    def test_env_min_members(self, monkeypatch):
        """Test MIN_MEMBERS environment variable."""
        monkeypatch.setenv("MIN_MEMBERS", "10")

        s = Settings()
        assert s.category.min_members == 10

    def test_env_min_members_zero(self, monkeypatch):
        """Test MIN_MEMBERS environment variable with zero."""
        monkeypatch.setenv("MIN_MEMBERS", "0")

        s = Settings()
        assert s.category.min_members == 0

    def test_env_min_members_invalid(self, monkeypatch):
        """Test MIN_MEMBERS environment variable with invalid value uses default."""
        monkeypatch.setenv("MIN_MEMBERS", "invalid")

        s = Settings()
        assert s.category.min_members == 10  # Default value
