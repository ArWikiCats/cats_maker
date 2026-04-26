"""
Wikipedia / Wikimedia SQL helpers.

Public API
----------
GET_SQL            – returns True only in production (APP_ENV=production).
add_namespace_prefix – prepend namespace prefix to a page title.
make_labsdb_dbs_p  – resolve (host, db_p) for a given wiki name.
sql_new            – run a raw query against a wiki replica and return rows.
"""

import functools
import logging
import os

from ..helps import function_timer
from .constants import (
    ANALYTICS_DB_TEMPLATE,
    DATABASE_SUFFIX,
    NS_TEXT_AR,
    NS_TEXT_EN,
    SUFFIXED_WIKIS,
    WIKI_ALIASES,
)
from .db_pool import make_sql_connect_silent
from .utils import add_namespace_prefix

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Environment flag
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def GET_SQL() -> bool:
    """Return True when running in production (APP_ENV == 'production')."""
    return os.getenv("APP_ENV", "") == "production"

# ---------------------------------------------------------------------------
# Host / DB resolution
# ---------------------------------------------------------------------------


def make_labsdb_dbs_p(wiki: str) -> tuple[str, str]:
    """Return (host, db_p) for *wiki*.

    Examples
    --------
    >>> make_labsdb_dbs_p("ar")
    ('arwiki.analytics.db.svc.wikimedia.cloud', 'arwiki_p')

    >>> make_labsdb_dbs_p("enwiki")
    ('enwiki.analytics.db.svc.wikimedia.cloud', 'enwiki_p')
    """
    wiki = wiki.removesuffix("wiki").replace("-", "_")
    wiki = WIKI_ALIASES.get(wiki, wiki)

    # Append "wiki" unless the name already contains it or is a known suffixed wiki
    if "wiki" not in wiki and not any(wiki.endswith(s) for s in SUFFIXED_WIKIS):
        wiki = f"{wiki}wiki"

    host = ANALYTICS_DB_TEMPLATE.format(wiki=wiki)
    return host, f"{wiki}{DATABASE_SUFFIX}"


# ---------------------------------------------------------------------------
# SQL runners
# ---------------------------------------------------------------------------


@function_timer
def sql_new(query: str, wiki: str = "", values: tuple | list = ()) -> list[dict]:
    """Execute *query* against the replica for *wiki* and return raw rows.

    Returns [] when not in production or on any database error.
    """
    if not GET_SQL():
        logger.info("sql_new: skipped (not in production)")
        return []

    host, db_p = make_labsdb_dbs_p(wiki)
    logger.debug("sql_new: wiki=%s host=%s db=%s", wiki, host, db_p)
    logger.info(query)

    rows = make_sql_connect_silent(query, host=host, db=db_p, values=tuple(values) if values else None)
    logger.info("sql_new: returned %d rows", len(rows))
    return rows


__all__ = [
    "GET_SQL",
    "add_namespace_prefix",
    "make_labsdb_dbs_p",
    "sql_new",
    "NS_TEXT_AR",
    "NS_TEXT_EN",
]
