#!/usr/bin/python3
""" """
import logging

from pymysql.converters import escape_string

from ..api_sql import GET_SQL, sql_new, sql_new_title_ns
from ..c18_new.cats_tools.ar_from_en2 import fetch_ar_titles_based_on_en_category
from ..config import settings
from .cat_tools_enlist2 import get_ar_list_from_cat

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

    # ---
    ar_cat2 = arcat.replace(" ", "_").replace("تصنيف:", "")
    ar_cat2 = escape_string(ar_cat2)
    # ---
    qia_ar = f"""select page_title, page_namespace
        from page, categorylinks
        where cl_from = page_id
        and cl_to = "{ar_cat2}"
    """
    # ---
    ar_list = []
    # ---
    if us_sql is True and GET_SQL():
        # ---
        ar_list = sql_new_title_ns(qia_ar, wiki="arwiki", t1="page_title", t2="page_namespace")
    else:
        ar_list = get_ar_list_from_cat(arcat, code="ar", typee="", return_list=True)
    # ---
    logger.info(f"<<lightgreen>> lenth ar_list:{len(ar_list)}")
    # ---
    return ar_list


def get_ar_list_from_en(encat, us_sql=True, wiki="en"):
    # ---
    encat2 = encat.replace(" ", "_").replace("Category:", "").replace("category:", "")
    encat2 = escape_string(encat2)
    # ---
    nss = "0, 10, 14"
    # ---
    if settings.query.ns_no_10:
        nss = "0, 14"
    # ---
    if settings.query.ns_only_14:
        nss = "14"
    # ---
    en_qua = f"""
        select DISTINCT ll_title
            from page p1,categorylinks cla, langlinks
            where p1.page_id = ll_from
            and p1.page_namespace in ({nss})
            and cla.cl_to = "{encat2}"
            and ll_lang = 'ar'
            and cla.cl_from = p1.page_id
    """
    # ---
    if us_sql is True and GET_SQL():
        en_list_table = sql_new(en_qua, wiki=f"{wiki}wiki")
        en_list = [x.get("ll_title") for x in en_list_table if x.get("ll_title")]
    else:
        en_list = fetch_ar_titles_based_on_en_category(encat, wiki=wiki)
    # ---
    en_list = [x.replace("_", " ") for x in en_list]
    # ---
    return en_list


def do_sql(encat, arcat, us_sql=True, wiki="en"):
    # ---
    ar_list = get_ar_list(arcat, us_sql=us_sql)
    # ---
    en_list = get_ar_list_from_en(encat, us_sql=us_sql, wiki=wiki)
    # ---
    arlist_from_en = [x for x in en_list if x not in ar_list]
    # ---
    logger.info(f"<<lightgreen>> lenth arlist_from_en:{len(arlist_from_en)}")
    # ---
    return arlist_from_en


def make_ar_list_newcat2(arcat, encat, us_sql=False, wiki="en"):
    # ---
    encat = encat.replace("Category:Category:", "Category:")
    encat = encat.replace("category:", "").replace("Category:", "").replace("Catégorie:", "")
    encat = encat.replace("_", " ")
    # ---
    arcat = arcat.replace("تصنيف:تصنيف:", "").replace("تصنيف:", "").replace("_", " ")
    # ---
    result = do_sql(encat, arcat, us_sql=us_sql, wiki=wiki)
    # ---
    return result
