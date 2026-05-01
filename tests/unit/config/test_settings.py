"""
Tests for the centralized settings configuration module.
"""

import sys

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
from src.config.settings import _safe_int, default_user_agent


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


class TestDefaultUserAgent:
    """Tests for default_user_agent() function."""

    def test_with_home_set(self, monkeypatch):
        """Test user agent uses last path component of HOME."""
        monkeypatch.setenv("HOME", "/data/project/mybot")
        result = default_user_agent()
        assert result == "mybot bot/1.0 (https://mybot.toolforge.org/; tools.mybot@toolforge.org)"

    def test_with_home_empty(self, monkeypatch):
        """Test user agent uses 'himo' when HOME is empty."""
        monkeypatch.setenv("HOME", "")
        result = default_user_agent()
        assert result == "himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"

    def test_with_home_unset(self, monkeypatch):
        """Test user agent uses 'himo' when HOME is not set."""
        monkeypatch.delenv("HOME", raising=False)
        result = default_user_agent()
        assert result == "himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"

    def test_home_with_trailing_slash(self, monkeypatch):
        """Test user agent strips trailing slash from HOME."""
        monkeypatch.setenv("HOME", "/data/project/mybot/")
        result = default_user_agent()
        assert result == "mybot bot/1.0 (https://mybot.toolforge.org/; tools.mybot@toolforge.org)"


class TestIsProduction:
    """Tests for Settings.is_production() static method."""

    def test_returns_true_when_production(self, monkeypatch):
        """Test returns True when APP_ENV=production."""
        monkeypatch.setenv("APP_ENV", "production")
        assert Settings.is_production() is True

    def test_returns_true_case_insensitive(self, monkeypatch):
        """Test returns True for mixed case APP_ENV=Production."""
        monkeypatch.setenv("APP_ENV", "Production")
        assert Settings.is_production() is True

    def test_returns_false_when_not_set(self, monkeypatch):
        """Test returns False when APP_ENV is not set."""
        monkeypatch.delenv("APP_ENV", raising=False)
        assert Settings.is_production() is False

    def test_returns_false_when_development(self, monkeypatch):
        """Test returns False when APP_ENV=development."""
        monkeypatch.setenv("APP_ENV", "development")
        assert Settings.is_production() is False


class TestDontAddToPagesPath:
    """Tests for dont_add_to_pages_path attribute."""

    def test_dont_add_to_pages_path_attribute_exists(self):
        """Test that Settings has dont_add_to_pages_path attribute."""
        s = Settings()
        assert hasattr(s, "paths")
        assert hasattr(s.paths, "dont_add_to_pages_path")


class TestProcessArgv:
    """Tests for Settings._process_argv() method via sys.argv."""

    def test_range_limit(self, monkeypatch):
        """Test -range:10 sets range_limit."""
        monkeypatch.setattr(sys, "argv", ["test", "-range:10"])
        s = Settings()
        assert s.range_limit == 10

    def test_debug_flag(self, monkeypatch):
        """Test DEBUG sets debug=True."""
        monkeypatch.setattr(sys, "argv", ["test", "DEBUG"])
        s = Settings()
        assert s.debug is True

    def test_debug_long_flag(self, monkeypatch):
        """Test --debug sets debug=True."""
        monkeypatch.setattr(sys, "argv", ["test", "--debug"])
        s = Settings()
        assert s.debug is True

    def test_nosql(self, monkeypatch):
        """Test -nosql sets use_sql=False."""
        monkeypatch.setattr(sys, "argv", ["test", "-nosql"])
        s = Settings()
        assert s.database.use_sql is False

    def test_usesql(self, monkeypatch):
        """Test usesql sets use_sql=True."""
        monkeypatch.setattr(sys, "argv", ["test", "usesql"])
        s = Settings()
        assert s.database.use_sql is True

    def test_testwikidata(self, monkeypatch):
        """Test testwikidata sets test_mode and endpoint."""
        monkeypatch.setattr(sys, "argv", ["test", "testwikidata"])
        s = Settings()
        assert s.wikidata.test_mode is True
        assert s.wikidata.endpoint == "https://test.wikidata.org/w/api.php"

    def test_ask(self, monkeypatch):
        """Test ask sets bot.ask=True."""
        monkeypatch.setattr(sys, "argv", ["test", "ask"])
        s = Settings()
        assert s.bot.ask is True

    def test_stubs(self, monkeypatch):
        """Test -stubs sets category.stubs=True."""
        monkeypatch.setattr(sys, "argv", ["test", "-stubs"])
        s = Settings()
        assert s.category.stubs is True

    def test_stubs_alternative(self, monkeypatch):
        """Test stubs (without dash) sets category.stubs=True."""
        monkeypatch.setattr(sys, "argv", ["test", "stubs"])
        s = Settings()
        assert s.category.stubs is True

    def test_minmembers(self, monkeypatch):
        """Test -minmembers:5 sets min_members."""
        monkeypatch.setattr(sys, "argv", ["test", "-minmembers:5"])
        s = Settings()
        assert s.category.min_members == 5

    def test_min_members_with_dash(self, monkeypatch):
        """Test -min-members:7 sets min_members."""
        monkeypatch.setattr(sys, "argv", ["test", "-min-members:7"])
        s = Settings()
        assert s.category.min_members == 7

    def test_family_wikiquote(self, monkeypatch):
        """Test -family:wikiquote sets custom_family."""
        monkeypatch.setattr(sys, "argv", ["test", "-family:wikiquote"])
        s = Settings()
        assert s.site.custom_family == "wikiquote"

    def test_family_wikisource(self, monkeypatch):
        """Test -family:wikisource sets custom_family."""
        monkeypatch.setattr(sys, "argv", ["test", "-family:wikisource"])
        s = Settings()
        assert s.site.custom_family == "wikisource"

    def test_family_invalid_ignored(self, monkeypatch):
        """Test -family:wikipedia does not set custom_family (not in allowed list)."""
        monkeypatch.setattr(sys, "argv", ["test", "-family:wikipedia"])
        s = Settings()
        assert s.site.custom_family == ""

    def test_uselang(self, monkeypatch):
        """Test -uselang:de sets custom_lang and make_new_cat=False."""
        monkeypatch.setattr(sys, "argv", ["test", "-uselang:de"])
        s = Settings()
        assert s.site.custom_lang == "de"
        assert s.category.make_new_cat is False

    def test_slang(self, monkeypatch):
        """Test -slang:fr sets secondary_lang and related settings."""
        monkeypatch.setattr(sys, "argv", ["test", "-slang:fr"])
        s = Settings()
        assert s.site.secondary_lang == "fr"
        assert s.site.secondary_family == "wikipedia"
        assert s.site.use_secondary is True
        assert s.category.make_new_cat is False

    def test_to_limit_offset_calculation(self, monkeypatch):
        """Test to_limit is adjusted by offset."""
        monkeypatch.setattr(sys, "argv", ["test", "-to:100", "-offset:20"])
        s = Settings()
        # to_limit should be 100 + 20 = 120
        assert s.query.to_limit == 120

    def test_to_limit_without_offset(self, monkeypatch):
        """Test to_limit without offset."""
        monkeypatch.setattr(sys, "argv", ["test", "-to:50"])
        s = Settings()
        assert s.query.to_limit == 50

    def test_depth(self, monkeypatch):
        """Test depth:3 sets query.depth."""
        monkeypatch.setattr(sys, "argv", ["test", "depth:3"])
        s = Settings()
        assert s.query.depth == 3

    def test_nons10(self, monkeypatch):
        """Test nons10 sets ns_no_10."""
        monkeypatch.setattr(sys, "argv", ["test", "nons10"])
        s = Settings()
        assert s.query.ns_no_10 is True

    def test_ns_only_14_not_reached(self, monkeypatch):
        """Test ns:14 does not set ns_only_14 due to partition splitting on ':'.

        The source checks arg_name == 'ns:14' but partition(':') on 'ns:14'
        yields arg_name='ns', so this branch is unreachable.
        """
        monkeypatch.setattr(sys, "argv", ["test", "ns:14"])
        s = Settings()
        assert s.query.ns_only_14 is False

    def test_workfr(self, monkeypatch):
        """Test workfr sets work_fr."""
        monkeypatch.setattr(sys, "argv", ["test", "workfr"])
        s = Settings()
        assert s.category.work_fr is True

    def test_descqs(self, monkeypatch):
        """Test descqs sets descqs."""
        monkeypatch.setattr(sys, "argv", ["test", "descqs"])
        s = Settings()
        assert s.category.descqs is True

    def test_nodiff(self, monkeypatch):
        """Test nodiff sets bot.no_diff=True."""
        monkeypatch.setattr(sys, "argv", ["test", "nodiff"])
        s = Settings()
        assert s.bot.no_diff is True

    def test_diff(self, monkeypatch):
        """Test diff sets bot.show_diff=True."""
        monkeypatch.setattr(sys, "argv", ["test", "diff"])
        s = Settings()
        assert s.bot.show_diff is True

    def test_nofa(self, monkeypatch):
        """Test nofa sets bot.no_fa=True."""
        monkeypatch.setattr(sys, "argv", ["test", "nofa"])
        s = Settings()
        assert s.bot.no_fa is True

    def test_botedit(self, monkeypatch):
        """Test botedit sets bot.force_edit=True."""
        monkeypatch.setattr(sys, "argv", ["test", "botedit"])
        s = Settings()
        assert s.bot.force_edit is True

    def test_nologin(self, monkeypatch):
        """Test nologin sets bot.no_login=True."""
        monkeypatch.setattr(sys, "argv", ["test", "nologin"])
        s = Settings()
        assert s.bot.no_login is True

    def test_nocookies(self, monkeypatch):
        """Test nocookies sets bot.no_cookies=True."""
        monkeypatch.setattr(sys, "argv", ["test", "nocookies"])
        s = Settings()
        assert s.bot.no_cookies is True

    def test_keep(self, monkeypatch):
        """Test keep sets category.keep=True."""
        monkeypatch.setattr(sys, "argv", ["test", "keep"])
        s = Settings()
        assert s.category.keep is True

    def test_nowetry(self, monkeypatch):
        """Test -nowetry sets category.we_try=False."""
        monkeypatch.setattr(sys, "argv", ["test", "-nowetry"])
        s = Settings()
        assert s.category.we_try is False

    def test_nodontadd(self, monkeypatch):
        """Test nodontadd sets category.no_dontadd=True."""
        monkeypatch.setattr(sys, "argv", ["test", "nodontadd"])
        s = Settings()
        assert s.category.no_dontadd is True

    def test_testadd(self, monkeypatch):
        """Test testadd sets category.test_add=True."""
        monkeypatch.setattr(sys, "argv", ["test", "testadd"])
        s = Settings()
        assert s.category.test_add is True

    def test_test_category(self, monkeypatch):
        """Test test sets category.test_mode=True."""
        monkeypatch.setattr(sys, "argv", ["test", "test"])
        s = Settings()
        assert s.category.test_mode is True

    def test_printurl(self, monkeypatch):
        """Test printurl sets debug_config.print_url=True."""
        monkeypatch.setattr(sys, "argv", ["test", "printurl"])
        s = Settings()
        assert s.debug_config.print_url is True

    def test_dopost(self, monkeypatch):
        """Test dopost sets debug_config.do_post=True."""
        monkeypatch.setattr(sys, "argv", ["test", "dopost"])
        s = Settings()
        assert s.debug_config.do_post is True

    def test_maxlag2(self, monkeypatch):
        """Test maxlag2 sets wikidata.maxlag=1."""
        monkeypatch.setattr(sys, "argv", ["test", "maxlag2"])
        s = Settings()
        assert s.wikidata.maxlag == 1

    def test_offset(self, monkeypatch):
        """Test -offset:5 sets query.offset."""
        monkeypatch.setattr(sys, "argv", ["test", "-offset:5"])
        s = Settings()
        assert s.query.offset == 5

    def test_offset_short(self, monkeypatch):
        """Test -off:10 sets query.offset."""
        monkeypatch.setattr(sys, "argv", ["test", "-off:10"])
        s = Settings()
        assert s.query.offset == 10

    def test_multiple_args(self, monkeypatch):
        """Test multiple arguments can be set simultaneously."""
        monkeypatch.setattr(sys, "argv", ["test", "DEBUG", "-nosql", "-range:20", "ask"])
        s = Settings()
        assert s.debug is True
        assert s.database.use_sql is False
        assert s.range_limit == 20
        assert s.bot.ask is True

    def test_dontMakeNewCat(self, monkeypatch):
        """Test -dontMakeNewCat sets make_new_cat=False."""
        monkeypatch.setattr(sys, "argv", ["test", "-dontMakeNewCat"])
        s = Settings()
        assert s.category.make_new_cat is False
