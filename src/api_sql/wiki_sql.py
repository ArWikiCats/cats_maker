#!/usr/bin/python3
""" """
import functools
import logging
import os
import sys
import time

from . import mysql_client

logger = logging.getLogger(__name__)

ns_text_tab_ar = {
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

ns_text_tab_en = {
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


@functools.lru_cache(maxsize=1)
def GET_SQL() -> bool:
    dir1 = "/mnt/nfs/labstore-secondary-tools-project/"
    dir2 = "/data/project/"

    if not os.path.isdir(dir1) and not os.path.isdir(dir2) or os.path.isdir("I:/core/bots"):
        return False

    return True


def add_nstext_to_title(title, ns, lang="ar"):
    """Add namespace text to a title based on the provided namespace and
    language.

    This function modifies the given title by prepending the corresponding
    namespace text based on the provided namespace identifier (ns) and
    language. If the namespace is "0", the original title is returned
    unchanged. The function retrieves the appropriate namespace text from
    predefined mappings based on the specified language. If no matching
    namespace text is found, a debug message is logged.

    Args:
        title (str): The original title to which the namespace text will be added.
        ns (str): The namespace identifier used to fetch the corresponding namespace text.
        lang (str?): The language code for fetching the namespace text. Defaults to "ar".

    Returns:
        str: The modified title with the namespace text prepended, or the original
            title if ns is "0".
    """

    # ---
    new_title = title
    # ---
    if str(ns) == "0":
        return new_title
    # ---
    ns_text = ns_text_tab_ar.get(str(ns))
    if lang != "ar":
        ns_text = ns_text_tab_en.get(str(ns))
    # ---
    if not ns_text:
        logger.debug(f"no ns_text for {str(ns)}")
    # ---
    if title and ns:
        new_title = f"{ns_text}:{title}"
    # ----
    return new_title


def make_labsdb_dbs_p(wiki):
    """Generate host and database name for a given wiki.

    This function takes a wiki name as input, processes it to conform to
    specific naming conventions, and generates the corresponding host and
    database name. It handles certain predefined wiki names by mapping them
    to standardized formats. The function ensures that the resulting names
    are suitable for use in a database connection context.

    Args:
        wiki (str): The name of the wiki, which may include a suffix or hyphens.

    Returns:
        tuple: A tuple containing the host string and the database name string.
    """
    # host, dbs_p = make_labsdb_dbs_p('ar')
    # ---
    if wiki.endswith("wiki"):
        wiki = wiki[:-4]
    # ---
    wiki = wiki.replace("-", "_")
    # ---
    databases = {
        "wikidata": "wikidatawiki",
        "be-x-old": "be_x_old",
        "be_tarask": "be_x_old",
        "be-tarask": "be_x_old",
    }
    # ---
    wiki = databases.get(wiki, wiki)
    # ---
    valid_ends = [
        "wiktionary",
    ]
    # ---
    if not (any((wiki.endswith(x)) for x in valid_ends)) and wiki.find("wiki") == -1:
        wiki = f"{wiki}wiki"
    # ---
    dbs = wiki
    # ---
    host = f"{wiki}.analytics.db.svc.wikimedia.cloud"
    # ---
    dbs_p = f"{dbs}_p"
    # ---
    return host, dbs_p


def sql_new(queries, wiki="", values=[]):
    # ---
    logger.debug(f"wiki_sql.py wiki '{wiki}'")
    # ---
    host, dbs_p = make_labsdb_dbs_p(wiki)
    # ---
    logger.info(queries)
    # ---
    if not GET_SQL():
        logger.info("no GET_SQL()")
        return []
    # ---
    start = time.perf_counter()
    # ---
    rows = mysql_client.make_sql_connect(queries, db=dbs_p, host=host, values=values)
    # ---
    delta = time.perf_counter() - start
    # ---
    logger.info(f'wiki_sql.py len(encats) = "{len(rows)}", in {delta:.2f} seconds')
    # ---
    return rows


def sql_new_title_ns(queries, wiki="", t1="page_title", t2="page_namespace"):
    """Generate a list of new titles based on SQL query results.

    This function processes the results of SQL queries to create a list of
    new titles by combining page titles with their corresponding namespaces.
    It first checks if the provided wiki string ends with "wiki" and removes
    it if necessary. Then, it retrieves the rows from the SQL query results
    and constructs new titles using the specified title and namespace keys.
    If a title or namespace is missing, it appends the original row to the
    new list and logs a debug message.

    Args:
        queries (str): The SQL queries to execute.
        wiki (str?): The wiki identifier. Defaults to an empty string.
        t1 (str?): The key for the page title in the row. Defaults to "page_title".
        t2 (str?): The key for the page namespace in the row. Defaults to "page_namespace".

    Returns:
        list: A list of new titles generated from the SQL query results.
    """

    # ---
    lang = wiki
    # ---
    if lang.endswith("wiki"):
        lang = lang[:-4]
    # ---
    rows = sql_new(queries, wiki=wiki)
    # ---
    if not t1:
        t1 = "page_title"
    if not t2:
        t2 = "page_namespace"
    # ---
    newlist = []
    # ---
    for row in rows:
        title = row.get(t1)
        ns = row.get(t2)
        # ---
        new_title = title
        # ---
        if title and ns:
            new_title = add_nstext_to_title(title, ns, lang=lang)
        # ---
        if new_title:
            newlist.append(new_title)
        else:
            logger.debug(f"xa {str(row)}")
            newlist.append(row)
    # ---
    return newlist
