#!/usr/bin/python3
""" """
import logging

from ..api_sql import GET_SQL, get_exclusive_category_titles
from ..config import settings
from .sql_cat import make_ar_list_newcat2
from .sql_cat_checker import validate_categories_for_new_cat

logger = logging.getLogger(__name__)

pages_in_arcat_toMake = {}


def extract_fan_page_titles(enpageTitle) -> list:
    fapages = []

    if GET_SQL() and settings.database.use_sql:
        cat2 = enpageTitle.replace("Category:", "").replace("category:", "").strip()
        fapages = get_exclusive_category_titles(cat2, "") or []

    logger.info(f"<<lightgreen>>Adding {len(fapages)} pages to fapage lists<<default>>")
    return fapages


def get_listenpageTitle(artitle, enpageTitle1) -> list[str]:
    # ---
    enpageTitle = enpageTitle1.strip()
    # ---
    listenpageTitle = []
    # ---
    if validate_categories_for_new_cat(artitle, enpageTitle1, wiki="en"):
        listenpageTitle = make_ar_list_newcat2(artitle, enpageTitle1, us_sql=True) or []
    # ---
    if not listenpageTitle:
        fapages = extract_fan_page_titles(enpageTitle)
        listenpageTitle.extend(fapages)
    # ---
    if enpageTitle in pages_in_arcat_toMake:
        logger.info(f'<<lightgreen>> pages_in_arcat_toMake Adding for cats: "{enpageTitle}" : ')
        listenpageTitle.extend(pages_in_arcat_toMake[enpageTitle])
    # ---
    listenpageTitle = list(set(listenpageTitle))
    listenpageTitle = [x for x in listenpageTitle if isinstance(x, str) and x != ""]
    # ---
    return listenpageTitle
