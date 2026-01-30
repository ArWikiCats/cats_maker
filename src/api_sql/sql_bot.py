""" """

import logging
import re
import time
from datetime import datetime

from pymysql.converters import escape_string

from . import wiki_sql
from .mysql_client import make_sql_connect
from .wiki_sql import ns_text_tab_ar

logger = logging.getLogger(__name__)


def decode_bytes(x):
    if isinstance(x, bytes):
        x = x.decode("utf-8")
    return x


def fetch_arcat_titles(arcatTitle):
    # ---
    if not arcatTitle:
        return []
    # ---
    if not wiki_sql.GET_SQL():
        return []
    # ---
    arcatTitle = re.sub(r"تصنيف:", "", arcatTitle)
    arcatTitle = re.sub(r" ", "_", arcatTitle)
    logger.debug(f"arcatTitle : {arcatTitle}")
    # ---
    arcatTitle = escape_string(arcatTitle)
    # ---
    ar_queries = f"""
        SELECT page_title, page_namespace
        FROM page
        JOIN categorylinks
        JOIN langlinks
        WHERE cl_to = "{arcatTitle}"
        AND cl_from = page_id
        AND page_id = ll_from
        AND ll_lang = "en"
        GROUP BY page_title ;"""
    # ---
    host, dbs_p = wiki_sql.make_labsdb_dbs_p("ar")
    # ---
    ar_results = make_sql_connect(ar_queries, db=dbs_p, host=host) or []
    # ---
    arcats = []
    # ---
    if not ar_results or len(ar_results) == 0:
        return arcats
    # ---
    for ra in ar_results:
        # ---
        title = ra["page_title"]
        title = re.sub(r" ", "_", title)
        # ---
        ns = ra["page_namespace"]
        # ---
        if ns_text_tab_ar.get(str(ns)):
            title = f"{ns_text_tab_ar.get(str(ns))}:{title}"
        # ---
        arcats.append(str(title))
    # ---
    logger.debug(f"arcats: {len(arcats)} {arcatTitle}")
    # ---
    return arcats


def Make_sql(queries, wiki="") -> list:
    encats = []
    # ---
    start = time.perf_counter()
    # ---
    if not wiki_sql.GET_SQL():
        return []
    # ---
    if not wiki:
        wiki = "enwiki"
    # ---
    host, dbs_p = wiki_sql.make_labsdb_dbs_p(wiki)
    # ---
    logger.info(queries)
    # ---
    start_time = datetime.now().strftime("%Y-%b-%d  %H:%M:%S")
    logger.debug(f'<<yellow>> API/sql_py Make_sql 1 db:"{dbs_p}". {start_time}')
    # ---
    en_results = make_sql_connect(queries, host=host, db=dbs_p) or []
    # ---
    for raw in en_results:
        tit = decode_bytes(raw[0])
        tit = re.sub(r" ", "_", tit)
        encats.append(tit)
    # ---
    delta = time.perf_counter() - start
    # ---
    logger.debug(f'API/sql_py Make_sql len(encats) = "{len(encats)}", in {delta} seconds')
    # ---
    encats.sort()
    # ---
    return encats


def get_exclusive_category_titles(encatTitle, arcatTitle) -> list:
    # ---
    logger.debug(f"<<yellow>> sql . MySQLdb_finder {encatTitle}: ")
    # ---
    if not wiki_sql.GET_SQL():
        return []
    # ---
    start = time.perf_counter()
    # ---
    encats = fetch_encat_titles(encatTitle)
    # ---
    arcats = fetch_arcat_titles(arcatTitle)
    # ---
    logger.debug(f">> {encatTitle=}, <<yellow>> {len(encats):,} <<default>> {len(arcats):,} ")
    # ---
    final_cat = [x for x in encats if x not in arcats]
    # ---
    delta = time.perf_counter() - start
    # ---
    logger.info(
        f'sql_bot.py: get_exclusive_category_titles len(final_cat) = "{len(final_cat)}", in {delta:.2f} seconds'
    )
    # ---
    return final_cat


def fetch_encat_titles(encatTitle: str) -> list:
    item = str(encatTitle).replace("category:", "").replace("Category:", "").replace(" ", "_")
    item = item.replace("[[en:", "").replace("]]", "")
    # ---
    item = escape_string(item)
    # ---
    queries = f"""SELECT ll_title , page_namespace  FROM page JOIN categorylinks JOIN langlinks
        WHERE cl_to = "{item}" AND cl_from=page_id AND page_id =ll_from AND ll_lang = "ar"
        GROUP BY ll_title ;"""
    # ---
    encats = Make_sql(queries)
    # ---
    return encats


def find_sql(enpageTitle):
    # ---
    logger.info(f"find_sql, enpageTitle:'{enpageTitle}'")
    # ---
    if not wiki_sql.GET_SQL():
        return []
    # ---
    fapages = get_exclusive_category_titles(enpageTitle, "")
    # ---
    if not fapages:
        return []
    # ---
    listenpageTitle = []
    # ---
    for numbrr, pages in enumerate(fapages, 1):
        # ---
        if not pages.strip():
            continue
        # ---
        pages = pages.replace("_", " ")
        # ---
        listenpageTitle.append(pages)
        # ---
        if numbrr < 30:
            logger.info("<<lightgreen>> Adding " + pages + " to fa lists from en category. <<default>>")
    # ---
    return listenpageTitle
