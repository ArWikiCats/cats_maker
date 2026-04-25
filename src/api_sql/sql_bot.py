""" """

import logging
import re

from ..helps import function_timer
from .mysql_client import make_sql_connect_silent
from .wiki_sql import GET_SQL, make_labsdb_dbs_p, ns_text_tab_ar

logger = logging.getLogger(__name__)


def decode_bytes(x):
    if isinstance(x, bytes):
        x = x.decode("utf-8")
    return x


def fetch_arcat_titles(arcatTitle):

    if not arcatTitle:
        return []

    if not GET_SQL():
        return []

    arcatTitle = re.sub(r"تصنيف:", "", arcatTitle)
    arcatTitle = re.sub(r" ", "_", arcatTitle)
    logger.debug(f"arcatTitle : {arcatTitle}")

    # Use parameterized query to prevent SQL injection
    ar_queries = """
        SELECT page_title, page_namespace
        FROM page
        JOIN categorylinks
        JOIN linktarget ON cl_target_id = lt_id
        JOIN langlinks
        WHERE lt_title = %s
        AND lt_namespace = 14
        AND cl_from = page_id
        AND page_id = ll_from
        AND ll_lang = "en"
        GROUP BY page_title
        """

    host, dbs_p = make_labsdb_dbs_p("ar")

    # Pass category as parameter to prevent SQL injection
    ar_results = make_sql_connect_silent(ar_queries, db=dbs_p, host=host, values=(arcatTitle,)) or []

    arcats = []

    for ra in ar_results:

        title = re.sub(r" ", "_", ra["page_title"])

        ns = ra["page_namespace"]

        if ns_text_tab_ar.get(str(ns)):
            title = f"{ns_text_tab_ar.get(str(ns))}:{title}"

        arcats.append(str(title))

    logger.debug(f"arcats: {len(arcats)} {arcatTitle}")

    return arcats


@function_timer
def get_exclusive_category_titles(encatTitle, arcatTitle) -> list:

    logger.debug(f"<<yellow>> sql . MySQLdb_finder {encatTitle}: ")

    if not GET_SQL():
        return []

    encats = fetch_encat_titles(encatTitle)

    arcats = fetch_arcat_titles(arcatTitle)

    logger.debug(f">> {encatTitle=}, <<yellow>> {len(encats):,} <<default>> {len(arcats):,} ")

    final_cat = [x for x in encats if x not in arcats]

    logger.info(f'sql_bot.py: len(final_cat) = "{len(final_cat)}"')

    return final_cat


@function_timer
def fetch_encat_titles(encatTitle: str) -> list:
    item = str(encatTitle).replace("category:", "").replace("Category:", "").replace(" ", "_")
    item = item.replace("[[en:", "").replace("]]", "")

    queries = """
        SELECT ll_title, page_namespace
        FROM page
        JOIN categorylinks
        JOIN linktarget ON cl_target_id = lt_id
        JOIN langlinks
        WHERE lt_title = %s
        AND lt_namespace = 14
        AND cl_from = page_id
        AND page_id = ll_from
        AND ll_lang = "ar"
        GROUP BY ll_title
    """

    encats = []

    if not GET_SQL():
        return []

    host, dbs_p = make_labsdb_dbs_p("enwiki")

    logger.info(queries)

    logger.debug(f'<<yellow>> db:"{dbs_p=}". {host=}')

    en_results = make_sql_connect_silent(queries, host=host, db=dbs_p, values=(item,))

    for raw in en_results:
        encats.append(raw["ll_title"])

    logger.debug(f'len(encats) = "{len(encats)}"')

    encats.sort()

    return encats


def find_sql(enpageTitle):

    logger.info(f", enpageTitle:'{enpageTitle}'")

    if not GET_SQL():
        return []

    fapages = get_exclusive_category_titles(enpageTitle, "")

    if not fapages:
        return []

    listenpageTitle = []

    for numbrr, pages in enumerate(fapages, 1):

        if not pages.strip():
            continue

        pages = pages.replace("_", " ")

        listenpageTitle.append(pages)

        if numbrr < 30:
            logger.info(f"<<lightgreen>> Adding {pages} to fa lists from en category.")

    return listenpageTitle
