"""
Wikipedia / Wikimedia SQL helpers.

Public API
----------
GET_SQL            – returns True only in production (APP_ENV=production).
add_nstext_to_title – prepend namespace prefix to a page title.
make_labsdb_dbs_p  – resolve (host, db_p) for a given wiki name.
sql_new            – run a raw query against a wiki replica and return rows.
sql_new_title_ns   – like sql_new but maps rows → "Namespace:Title" strings.
"""

import functools
import logging
import os

from ..helps import function_timer
from .mysql_client import make_sql_connect_silent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Namespace label tables
# ---------------------------------------------------------------------------
_WIKI_ALIASES: dict[str, str] = {
    "wikidata": "wikidatawiki",
    "be-x-old": "be_x_old",
    "be_tarask": "be_x_old",
    "be-tarask": "be_x_old",
}

_SUFFIXED_WIKIS = {"wiktionary"}  # wikis that already carry their own suffix


NS_TEXT_AR: dict[str, str] = {
    "0": "",
    "1": "نقاش",
    "2": "مستخدم",
    "3": "نقاش المستخدم",
    "4": "ويكيبيديا",
    "5": "نقاش ويكيبيديا",
    "6": "ملف",
    "7": "نقاش الملف",
    "10": "قالب",
    "11": "نقاش القالب",
    "12": "مساعدة",
    "13": "نقاش المساعدة",
    "14": "تصنيف",
    "15": "نقاش التصنيف",
    "100": "بوابة",
    "101": "نقاش البوابة",
    "828": "وحدة",
    "829": "نقاش الوحدة",
    "2600": "موضوع",
    "1728": "فعالية",
    "1729": "نقاش الفعالية",
}

NS_TEXT_EN: dict[str, str] = {
    "0": "",
    "1": "Talk",
    "2": "User",
    "3": "User talk",
    "4": "Project",
    "5": "Project talk",
    "6": "File",
    "7": "File talk",
    "8": "MediaWiki",
    "9": "MediaWiki talk",
    "10": "Template",
    "11": "Template talk",
    "12": "Help",
    "13": "Help talk",
    "14": "Category",
    "15": "Category talk",
    "100": "Portal",
    "101": "Portal talk",
    "828": "Module",
    "829": "Module talk",
}


# ---------------------------------------------------------------------------
# Environment flag
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def GET_SQL() -> bool:
    """Return True when running in production (APP_ENV == 'production')."""
    return os.getenv("APP_ENV", "") == "production"


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------


def add_nstext_to_title(title: str, ns: str | int, lang: str = "ar") -> str:
    """Prepend the namespace label to *title*.

    Returns *title* unchanged when namespace is 0 or the label is unknown.
    """
    ns_key = str(ns)
    if not title:
        return ""

    if ns_key == "0":
        return title

    table = NS_TEXT_AR if lang == "ar" else NS_TEXT_EN
    prefix = table.get(ns_key)

    if not prefix:
        logger.debug("No namespace label for ns=%s lang=%s", ns_key, lang)
        return title

    return f"{prefix}:{title}"


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
    wiki = _WIKI_ALIASES.get(wiki, wiki)

    # Append "wiki" unless the name already contains it or is a known suffixed wiki
    if "wiki" not in wiki and not any(wiki.endswith(s) for s in _SUFFIXED_WIKIS):
        wiki = f"{wiki}wiki"

    host = f"{wiki}.analytics.db.svc.wikimedia.cloud"
    return host, f"{wiki}_p"


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


@function_timer
def sql_new_title_ns(
    query: str,
    wiki: str = "",
    title_key: str = "page_title",
    ns_key: str = "page_namespace",
    values: tuple | list | None = None,
) -> list[str]:
    """Run *query* and convert each row to a "Namespace:Title" string.

    Rows missing either field are skipped with a debug log.
    """
    lang = wiki.removesuffix("wiki") if wiki.endswith("wiki") else wiki
    rows = sql_new(query, wiki=wiki, values=values or ())

    titles: list[str] = []
    for row in rows:
        title = row.get(title_key)
        ns = row.get(ns_key)

        if not title or ns is None:
            logger.debug("sql_new_title_ns: skipping incomplete row: %s", row)
            continue

        titles.append(add_nstext_to_title(title, ns, lang=lang))

    return titles


__all__ = [
    "GET_SQL",
    "add_nstext_to_title",
    "make_labsdb_dbs_p",
    "sql_new",
    "sql_new_title_ns",
    "NS_TEXT_AR",
    "NS_TEXT_EN",
]
