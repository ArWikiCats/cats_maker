"""Shared constants for the service package."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Wiki code → database name special cases
# ---------------------------------------------------------------------------
WIKI_ALIASES: dict[str, str] = {
    "wikidata": "wikidatawiki",
    "be-x-old": "be_x_old",
    "be_tarask": "be_x_old",
    "be-tarask": "be_x_old",
}

# Suffixes that should never have "wiki" appended
SUFFIXED_WIKIS: frozenset[str] = frozenset({"wiktionary"})

# ---------------------------------------------------------------------------
# Namespace label tables
# ---------------------------------------------------------------------------
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
# Database connection templates
# ---------------------------------------------------------------------------
ANALYTICS_DB_TEMPLATE: str = "{wiki}.analytics.db.svc.wikimedia.cloud"
DATABASE_SUFFIX: str = "_p"
REPLICA_CNF_FILENAME: str = "replica.my.cnf"

__all__ = [
    "ANALYTICS_DB_TEMPLATE",
    "DATABASE_SUFFIX",
    "NS_TEXT_AR",
    "NS_TEXT_EN",
    "REPLICA_CNF_FILENAME",
    "SUFFIXED_WIKIS",
    "WIKI_ALIASES",
]
