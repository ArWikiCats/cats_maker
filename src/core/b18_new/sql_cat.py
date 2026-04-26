#!/usr/bin/python3
""" """

import logging

from ...config import settings
from ..api_sql_new import add_namespace_prefix
from ..api_sql_new.db_pool import db_manager
from ..c18_new.cats_tools.ar_from_en2 import fetch_ar_titles_based_on_en_category
from ..new_api import load_main_api

logger = logging.getLogger(__name__)


def get_ar_list(arcat, us_sql=True):
    """Retrieve a list of Arabic pages from a specified category.

    This function generates a SQL query to fetch page titles and namespaces
    from the specified Arabic category. It can either execute the query
    against a SQL database or retrieve the list using an alternative method
    based on the `us_sql` flag. If SQL execution is enabled and the SQL
    connection is available, it will use that method; otherwise, it will
    fall back to a different retrieval approach.

    Args:
        arcat (str): The category name from which to retrieve the Arabic pages.
        us_sql (bool): A flag indicating whether to use SQL for retrieval.
            Defaults to True.

    Returns:
        list: A list of page titles from the specified Arabic category.
    """

    # Clean category name (no SQL injection risk - just string manipulation)
    ar_cat2 = arcat.replace(" ", "_").replace("تصنيف:", "")

    # Use parameterized query to prevent SQL injection
    qia_ar = """
    SELECT page_title, page_namespace
        FROM page
        JOIN categorylinks ON cl_from = page_id
        JOIN linktarget ON cl_target_id = lt_id
        WHERE lt_title = %s
        AND lt_namespace = 14
    """

    ar_list = []

    if us_sql is True:
        try:
            # Pass category as parameter to prevent SQL injection
            rows = db_manager.execute_query(wiki="arwiki", query=qia_ar, params=(ar_cat2,))
            ar_list = [add_namespace_prefix(r["page_title"], r["page_namespace"], lang="ar") for r in rows]
        except Exception as e:
            logger.error(f"SQL error in get_ar_list: {e}")
            ar_list = []

    if not ar_list:
        api = load_main_api("ar")
        cat_members = api.CatDepth("Category:" + arcat, depth=0, ns="all")

        ar_list = list(cat_members.keys())

    logger.info(f"<<lightgreen>> lenth ar_list:{len(ar_list)}")

    return ar_list


def get_ar_list_from_en(encat, us_sql=True, wiki="en"):
    # Clean category name (no SQL injection risk - just string manipulation)
    encat2 = encat.replace(" ", "_").replace("Category:", "").replace("category:", "")

    # Validate and build namespace list - use tuple for parameterized query
    nss = "0, 10, 14"

    if settings.query.ns_no_10:
        nss = "0, 14"

    if settings.query.ns_only_14:
        nss = "14"

    # Use parameterized query to prevent SQL injection
    # Note: nss is validated against known safe values above, not user input
    en_qua = f"""
        SELECT DISTINCT ll_title
            FROM page p1
            JOIN categorylinks cla ON cla.cl_from = p1.page_id
            JOIN linktarget lt ON cla.cl_target_id = lt.lt_id
            JOIN langlinks ON p1.page_id = ll_from
            WHERE p1.page_namespace IN ({nss})
            AND lt.lt_namespace = 14
            AND lt.lt_title = %s
            AND ll_lang = 'ar'
    """
    en_list = []
    if us_sql is True:
        try:
            # Pass category as parameter to prevent SQL injection
            en_list_table = db_manager.execute_query(wiki=f"{wiki}wiki", query=en_qua, params=(encat2,))
            en_list = [x.get("ll_title") for x in en_list_table if x.get("ll_title")]
        except Exception as e:
            logger.error(f"SQL error in get_ar_list_from_en: {e}")
            en_list = []

    if not en_list:
        en_list = fetch_ar_titles_based_on_en_category(encat, wiki=wiki)

    en_list = [x.replace("_", " ") for x in en_list]

    return en_list


def do_sql(encat, arcat, us_sql=True, wiki="en"):
    ar_list = get_ar_list(arcat, us_sql=us_sql)

    en_list = get_ar_list_from_en(encat, us_sql=us_sql, wiki=wiki)

    arlist_from_en = [x for x in en_list if x not in ar_list]

    logger.info(f"<<lightgreen>> lenth arlist_from_en:{len(arlist_from_en)}")

    return arlist_from_en


def make_ar_list_newcat2(arcat, encat, us_sql=False, wiki="en"):
    encat = encat.replace("Category:Category:", "Category:")
    encat = encat.replace("category:", "").replace("Category:", "").replace("Catégorie:", "")
    encat = encat.replace("_", " ")

    arcat = arcat.replace("تصنيف:تصنيف:", "").replace("تصنيف:", "").replace("_", " ")

    result = do_sql(encat, arcat, us_sql=us_sql, wiki=wiki)

    return result
