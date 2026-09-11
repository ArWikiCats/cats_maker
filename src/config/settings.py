"""
Centralized settings configuration for the project.

This module provides dataclass-based configuration for all project settings,
including Wikipedia, Wikidata, and database configurations.

Example:
    >>> from src.config import settings
    >>> print(settings.wikipedia.ar_code)
    'ar'
    >>> print(settings.wikidata.endpoint)
    'https://www.wikidata.org/w/api.php'
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    load_dotenv("$HOME/.env")


def _safe_int(value: str | None, default: int) -> int:
    """Safely convert string to int, returning default on failure."""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_bool(value: str | None, default: bool = False) -> bool:
    """Safely convert string to bool."""
    if not value:
        return default
    return value.lower() in ("true", "1", "yes")


def default_user_agent() -> str:
    home = (os.getenv("HOME") or "").rstrip("/")
    tool = home.rsplit("/", 1)[-1] or "himo"
    return f"{tool} bot/1.0 (https://{tool}.toolforge.org/; tools.{tool}@toolforge.org)"


@dataclass(frozen=True)
class Paths:
    cookies_dir: str | None
    dont_add_to_pages_path: str | None
    arwikicats_path: str | None

    @classmethod
    def load(cls) -> Paths:
        """
        Load Paths configuration from environment variables."""
        return cls(
            cookies_dir=os.getenv("COOKIES_DIR"),
            dont_add_to_pages_path=os.getenv("DONT_ADD_TO_PAGES_PATH"),
            arwikicats_path=os.getenv("ARWIKICATS_PATH"),
        )


@dataclass
class WikipediaConfig:
    """Configuration for Wikipedia API connections.

    Attributes:
        ar_family: Arabic Wikipedia family (default: "wikipedia")
        ar_code: Arabic Wikipedia language code (default: "ar")
        en_family: English Wikipedia family (default: "wikipedia")
        en_code: English Wikipedia language code (default: "en")
        user_agent: User agent string for API requests
        default_timeout: Default timeout for API requests in seconds
    """

    ar_family: str = "wikipedia"
    ar_code: str = "ar"
    en_family: str = "wikipedia"
    en_code: str = "en"
    user_agent: str = field(default_factory=default_user_agent)
    default_timeout: int = 10

    @classmethod
    def load(cls) -> WikipediaConfig:
        """
        Load Wikipedia configuration from environment variables."""
        return cls(
            ar_family=os.getenv("WIKIPEDIA_AR_FAMILY") or "wikipedia",
            ar_code=os.getenv("WIKIPEDIA_AR_CODE") or "ar",
            en_family=os.getenv("WIKIPEDIA_EN_FAMILY") or "wikipedia",
            en_code=os.getenv("WIKIPEDIA_EN_CODE") or "en",
            user_agent=os.getenv("WIKIPEDIA_USER_AGENT") or default_user_agent(),
            default_timeout=_safe_int(os.getenv("WIKIPEDIA_TIMEOUT"), 10),
        )


@dataclass
class WikidataConfig:
    """Configuration for Wikidata API connections.

    Attributes:
        endpoint: Wikidata API endpoint URL
        sparql_endpoint: SPARQL query endpoint URL
        timeout: Default timeout for Wikidata requests
        maxlag: Maximum lag for Wikidata API requests
        test_mode: Whether to use test.wikidata.org
    """

    endpoint: str = "https://www.wikidata.org/w/api.php"
    sparql_endpoint: str = "https://query.wikidata.org/sparql"
    timeout: int = 30
    maxlag: int = 5
    test_mode: bool = False

    @classmethod
    def load(cls) -> WikidataConfig:
        """
        Load Wikidata configuration from environment variables."""
        return cls(
            endpoint=os.getenv("WIKIDATA_ENDPOINT") or "https://www.wikidata.org/w/api.php",
            sparql_endpoint=os.getenv("WIKIDATA_SPARQL_ENDPOINT") or "https://query.wikidata.org/sparql",
            timeout=_safe_int(os.getenv("WIKIDATA_TIMEOUT"), 30),
            maxlag=_safe_int(os.getenv("WIKIDATA_MAXLAG"), 5),
        )


@dataclass
class ApiClientConfig:
    """Configuration for the API client.

    Attributes:
        max_retries: Maximum number of retries for API requests
        backoff_base: Base delay for exponential backoff
        maxlag_header: Header name for server maxlag retry-after
    """

    max_retries: int = 5
    backoff_base: int = 1
    maxlag_header: str = "Retry-After"

    @classmethod
    def load(cls) -> ApiClientConfig:
        """
        Load API client configuration from environment variables."""
        return cls(
            max_retries=_safe_int(os.getenv("API_CLIENT_MAX_RETRIES"), 5),
            backoff_base=_safe_int(os.getenv("API_CLIENT_BACKOFF_BASE"), 1),
            maxlag_header=os.getenv("API_CLIENT_MAXLAG_HEADER") or "Retry-After",
        )


@dataclass
class DatabaseConfig:
    """
    Configuration for database connections.
    """

    user: str = ""
    password: str = ""
    host: str | None = None
    port: int = 3306
    use_sql: bool = True
    cache_ttl: int = 60 * 60 * 24 * 7  # 1 week

    @classmethod
    def load(cls) -> DatabaseConfig:
        """
        Load Database configuration from environment variables."""
        return cls(
            host=os.getenv("DATABASE_HOST") or "",
            port=_safe_int(os.getenv("DATABASE_PORT"), 3306),
            user=os.getenv("TOOL_REPLICA_USER") or "",
            password=os.getenv("TOOL_REPLICA_PASSWORD") or "",
            cache_ttl=_safe_int(os.getenv("TOOL_REPLICA_CACHE_TTL"), 60 * 60 * 24 * 7),
            use_sql=_safe_bool(os.getenv("DATABASE_USE_SQL"), False),
        )

    def has_db_data(self) -> bool:
        return bool(self.user and self.password)


@dataclass
class DebugConfig:
    """Configuration for debug and logging options.

    Attributes:
        print_url: Print API URLs for debugging
        do_post: Force POST requests for debugging
    """

    print_url: bool = False
    do_post: bool = False

    @classmethod
    def load(cls) -> DebugConfig:
        return cls()


@dataclass
class BotConfig:
    """Configuration for bot behavior.

    Attributes:
        ask: Ask for confirmation before making changes
        no_diff: Don't show diff when asking for confirmation
        show_diff: Force show diff when asking for confirmation
        no_false_edit: Dont check if the edit is false edit
        force_edit: Force bot edit (bypass nobots check)
        no_login: Disable login assertion
        no_cookies: Disable cookie storage
    """

    ask: bool = False
    no_diff: bool = False
    show_diff: bool = False
    no_false_edit: bool = False
    force_edit: bool = False
    no_login: bool = False
    no_cookies: bool = False

    @classmethod
    def load(cls) -> BotConfig:
        return cls()


@dataclass
class CategoryConfig:
    """Configuration for category processing.

    Attributes:
        stubs: Process stub categories
        make_new_cat: Create new categories
        keep: Keep categories despite template restrictions
        we_try: Enable we_try mode for category processing
        no_dontadd: Disable don't-add list fetching
        test_add: Force test mode for dontadd list
        test_mode: Enable test mode
        work_fr: Work with French Wikipedia as fallback
        descqs: Use QuickStatements for descriptions
        min_members: Minimum number of members required to create a category
    """

    stubs: bool = False
    make_new_cat: bool = True
    keep: bool = False
    we_try: bool = True
    no_dontadd: bool = False
    test_add: bool = False
    test_mode: bool = False
    work_fr: bool = False
    descqs: bool = False
    min_members: int = 10

    @classmethod
    def load(cls) -> CategoryConfig:
        return cls(
            min_members=_safe_int(os.getenv("MIN_MEMBERS"), 10),
        )


@dataclass
class QueryConfig:
    """Configuration for query parameters.

    Attributes:
        offset: Starting offset for queries
        depth: Depth limit for category traversal
        to_limit: Upper limit for results
        ns_no_10: Exclude namespace 10 from results
        ns_only_14: Only include namespace 14 in results
    """

    offset: int = 0
    depth: int = 0
    to_limit: int = 10000
    ns_no_10: bool = False
    ns_only_14: bool = False

    @classmethod
    def load(cls) -> QueryConfig:
        return cls()


@dataclass
class SiteConfig:
    """Configuration for alternative site settings.

    Attributes:
        custom_family: Custom wiki family (e.g., wikiquote, wikisource)
        custom_lang: Custom language code for en site
        secondary_lang: Secondary language to use (e.g., fr)
        secondary_family: Family for secondary language
        use_secondary: Whether to use secondary language site
    """

    custom_family: str = ""
    custom_lang: str = ""
    secondary_lang: str = ""
    secondary_family: str = ""
    use_secondary: bool = False

    @classmethod
    def load(cls) -> SiteConfig:
        return cls()


@dataclass
class WikiSiteInfo:
    """Configuration for a wiki site with family and code.

    Attributes:
        family: Wiki family (e.g., "wikipedia", "commons", "wikiquote")
        code: Language/site code (e.g., "en", "ar", "commons")
        use: Whether this site is enabled for use
    """

    family: str = "wikipedia"
    code: str = "en"
    use: bool = False

    @classmethod
    def load(cls) -> WikiSiteInfo:
        return cls()

    def __getitem__(self, key):
        """
        Support dictionary-like access for backward compatibility."""
        if key == "family":
            return self.family
        elif key == "code":
            return self.code
        elif key == "use":
            return self.use
        elif key == 1:
            return self.use
        raise KeyError(key)

    def __contains__(self, key) -> bool:
        """
        Support 'in' operator for backward compatibility."""
        return key in ("family", "code", "use", 1)


@dataclass
class Settings:
    """Main settings container for all project configurations.

    This class aggregates all configuration dataclasses and provides
    global settings that apply across the project.

    Attributes:
        wikipedia: Wikipedia API configuration
        wikidata: Wikidata API configuration
        database: Database connection configuration
        debug_config: Debug and logging options
        bot: Bot behavior configuration
        category: Category processing configuration
        query: Query parameters configuration
        site: Alternative site settings
        range_limit: Maximum number of iterations for category processing
        debug: Enable debug mode
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    wikipedia: WikipediaConfig
    wikidata: WikidataConfig
    api_client: ApiClientConfig
    database: DatabaseConfig
    debug_config: DebugConfig
    bot: BotConfig
    category: CategoryConfig
    query: QueryConfig
    site: SiteConfig
    paths: Paths

    # Global settings
    range_limit: int = 5
    debug: bool = False
    log_level: str = "INFO"

    @staticmethod
    def is_production() -> bool:
        """
        Check if the application is running in production mode."""
        return os.getenv("APP_ENV", "").lower() == "production"

    @property
    def en_site(self) -> WikiSiteInfo:
        """
        Get the English/source site configuration.

        Returns computed site info based on commons, custom_family, and custom_lang settings.
        """
        if self.site.custom_family:
            return WikiSiteInfo(family=self.site.custom_family, code="en", use=True)
        if self.site.custom_lang:
            return WikiSiteInfo(family="wikipedia", code=self.site.custom_lang, use=True)
        return WikiSiteInfo(family=self.wikipedia.en_family, code=self.wikipedia.en_code, use=False)

    @property
    def ar_site(self) -> WikiSiteInfo:
        """
        Get the Arabic/target site configuration.

        Returns computed site info based on custom_family settings.
        """
        if self.site.custom_family:
            return WikiSiteInfo(family=self.site.custom_family, code="ar", use=True)
        return WikiSiteInfo(family=self.wikipedia.ar_family, code=self.wikipedia.ar_code, use=False)

    @property
    def fr_site(self) -> WikiSiteInfo:
        """
        Get the secondary/French site configuration.

        Returns computed site info based on secondary language settings.
        """
        if self.site.use_secondary:
            return WikiSiteInfo(
                family=self.site.secondary_family or "wikipedia", code=self.site.secondary_lang or "fr", use=True
            )
        return WikiSiteInfo(family="", code="fr", use=False)

    def _process_argv(self) -> None:
        """
        Process command-line arguments for configuration overrides."""
        for arg in sys.argv:
            arg_name, _, value = arg.partition(":")

            # Range limit
            if arg_name == "-range" and value:
                self.range_limit = _safe_int(value, self.range_limit)

            # Debug mode
            if arg_name in ("DEBUG", "-debug", "--debug"):
                self.debug = True

            # SQL usage
            if arg_name == "-nosql":
                self.database.use_sql = False
            if arg_name == "usesql":
                self.database.use_sql = True

            # Wikidata test environment
            if arg_name in ("testwikidata", "-testwikidata", "wikidata_test"):
                self.wikidata.endpoint = "https://test.wikidata.org/w/api.php"
                self.wikidata.test_mode = True

            # Maxlag configuration
            if arg_name == "maxlag2":
                self.wikidata.maxlag = 1

            # Debug config
            if arg_name == "printurl":
                self.debug_config.print_url = True
            if arg_name == "dopost":
                self.debug_config.do_post = True

            # Bot config
            if arg_name == "ask":
                self.bot.ask = True
            if arg_name == "nodiff":
                self.bot.no_diff = True
            if arg_name == "diff":
                self.bot.show_diff = True
            if arg_name == "nofa":
                self.bot.no_false_edit = True
            if arg_name in ("botedit", "editbot"):
                self.bot.force_edit = True
            if arg_name == "nologin":
                self.bot.no_login = True
            if arg_name == "nocookies":
                self.bot.no_cookies = True

            # Category config
            if arg_name in ("-stubs", "stubs"):
                self.category.stubs = True
            if arg_name in ("-dontMakeNewCat", "-dontmakenewcat"):
                self.category.make_new_cat = False
            if arg_name == "keep":
                self.category.keep = True
            if arg_name == "-We_Try":
                self.category.we_try = True
            if arg_name == "-nowetry":
                self.category.we_try = False
            if arg_name == "nodontadd":
                self.category.no_dontadd = True
            if arg_name == "testadd":
                self.category.test_add = True
            if arg_name == "test":
                self.category.test_mode = True
            if arg_name == "workfr":
                self.category.work_fr = True
            if arg_name == "descqs":
                self.category.descqs = True

            if arg_name in ("-minmembers", "-min-members") and value:
                self.category.min_members = _safe_int(value, self.category.min_members)

            # Query config
            if arg_name in ("-offset", "-off") and value:
                self.query.offset = _safe_int(value, self.query.offset)
            if arg_name == "depth" and value:
                self.query.depth = _safe_int(value, self.query.depth)
            if arg_name in ("to", "-to") and value:
                self.query.to_limit = _safe_int(value, self.query.to_limit)

            if arg_name == "nons10":
                self.query.ns_no_10 = True
            if arg_name == "ns:14":
                self.query.ns_only_14 = True

            # Site config
            if arg_name in ("-family", "family") and value:
                if value in ("wikiquote", "wikisource"):
                    self.site.custom_family = value

            if arg_name in ("-uselang", "uselang") and value:
                self.site.custom_lang = value
                self.category.make_new_cat = False

            if arg_name in ("-slang", "slang") and value:
                self.site.secondary_lang = value
                self.site.secondary_family = "wikipedia"
                self.site.use_secondary = True
                self.category.make_new_cat = False

        # Calculate to_limit with offset if both are set
        if self.query.to_limit != 0:
            self.query.to_limit = self.query.to_limit + self.query.offset

    @classmethod
    def load(cls) -> Settings:
        """
        Build a Settings instance from each sub-config's own load(),
        """
        settings = cls(
            wikipedia=WikipediaConfig.load(),
            wikidata=WikidataConfig.load(),
            api_client=ApiClientConfig.load(),
            database=DatabaseConfig.load(),
            debug_config=DebugConfig.load(),
            bot=BotConfig.load(),
            category=CategoryConfig.load(),
            query=QueryConfig.load(),
            site=SiteConfig.load(),
            paths=Paths.load(),
            range_limit=_safe_int(os.getenv("RANGE_LIMIT"), 5),
            debug=_safe_bool(os.getenv("DEBUG"), False),
            log_level=os.getenv("LOG_LEVEL") or "INFO",
        )
        settings._process_argv()
        return settings


# Global settings instance
main_settings = Settings.load()
