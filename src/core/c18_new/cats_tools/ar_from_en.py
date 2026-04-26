#!/usr/bin/python3
""" """

import logging

from ....config import settings
from ...api_sql_new import CategoryComparator
from ...b18_new import get_ar_list_from_encat
from ...wiki_api import find_LCN, get_arpage_inside_encat
from ..cat_tools2 import Categorized_Page_Generator

logger = logging.getLogger(__name__)


def retrieve_ar_list_from_category(encat, enpageTitle):
    gent_faso_list = Categorized_Page_Generator(enpageTitle, "all")

    fetchedarpages = get_arpage_inside_encat("Category:" + enpageTitle)

    if fetchedarpages:
        logger.info("arpage inside_encat: " + (",a: ".join(fetchedarpages)))
        for x in fetchedarpages:
            gent_faso_list.append(x.replace("_", " "))

    logger.info(f" make_ar_list_from_en_cat lenth : {len(gent_faso_list)}")
    new_ll = Get_ar_list_from_en_list(gent_faso_list)
    return new_ll


def clean_category_input(encat):
    encat = (
        encat.replace("[[", "")
        .replace("]]", "")
        .replace("Category:", "")
        .replace("category:", "")
        .replace("category talk:", "")
        .strip()
    )
    encat = encat.replace("Catégorie:", "")
    return encat


def make_ar_list_from_en_cat(encat):
    """Generate a list of categorized pages from an English category string.

    This function takes an English category string, processes it to remove
    unnecessary prefixes and suffixes, and attempts to generate a list of
    categorized pages associated with that category. If the input category
    is empty, it returns False. The function also checks if the category can
    be found in a SQL database and falls back to generating the list using
    other methods if necessary.

    Args:
        encat (str): The English category string to process.

    Returns:
        list: A list of unique categorized page titles derived from the input
        category. If the input category is empty, it returns False.
    """

    if not encat:
        logger.info("<<lightblue>> No encat")
        return False

    logger.info(f'<<lightgreen>>* : cat:"{encat}" ')
    # count = 0
    encat = clean_category_input(encat)

    enpageTitle = encat
    logger.debug("cat: " + encat)

    if settings.database.use_sql:
        comparator = CategoryComparator()
        listenpageTitle2 = comparator.get_exclusive_category_titles(enpageTitle, "")
        listenpageTitle2 = [x.replace("_", " ") for x in listenpageTitle2]
    else:
        listenpageTitle2 = retrieve_ar_list_from_category(enpageTitle)

    if not listenpageTitle2:
        # {'Yemen': {'ns': 0, 'ar': 'اليمن'}, 'Outline of Yemen': {'ns': 0, 'ar': 'مخطط اليمن'}, ... }
        gent_faso_list = get_ar_list_from_encat(encat, code="en", typee="all")
        listenpageTitle2 = [x["ar"] for x in gent_faso_list.values() if x.get("ar")]

    listenpageTitle = list(set(listenpageTitle2))

    if len(listenpageTitle) == 0:
        logger.info("<<lightblue>> No cats listenpageTitle = [] ")

    logger.info(f"<<lightblue>> end of , lenth:{len(listenpageTitle)}")
    return listenpageTitle


def Get_ar_list_from_en_list(enlist):
    new_ar_list = []
    en_done = []

    for i in range(0, len(enlist), 50):
        liste = enlist[i : i + 50]
        part_list = "|".join(liste)
        if part_list:
            if part_list.startswith("|"):
                part_list = part_list[len("|") :]

            new_list = find_LCN(part_list, prop="langlinks", lllang="ar", first_site_code=settings.EEn_site.code)

            if new_list:
                for p_w in new_list:
                    arpagetitle = ""
                    if "langlinks" in new_list[p_w] and "ar" in new_list[p_w]["langlinks"]:
                        arpagetitle = new_list[p_w]["langlinks"]["ar"]

                    if arpagetitle:
                        logger.debug(f"<<lightblue>>Adding {arpagetitle} to ar lists {p_w}")

                        new_ar_list.append(arpagetitle)
                        en_done.append(p_w.replace("_", " "))

    logger.info(f"<<lightyellow>> , <<lightblue>>lenth of new_ar_list:{len(new_ar_list)}")

    new_ar_list = list(set(new_ar_list))

    return new_ar_list
