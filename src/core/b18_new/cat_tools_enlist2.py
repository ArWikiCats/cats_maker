#!/usr/bin/python3
""" """

import logging

from ...config import settings
from ..c18_new.cat_tools2 import Categorized_Page_Generator
from ..wiki_api import find_LCN, get_arpage_inside_encat, sub_cats_query

logger = logging.getLogger(__name__)


def get_ar_list_from_encat(cat, code="ar", typee="cat", return_list=True):
    """
    Retrieve a list of category members from a specified category.
    """

    if cat.startswith("Category:"):
        cat = cat.replace("Category:", "")

    if cat.startswith("تصنيف:"):
        cat = cat.replace("تصنيف:", "")

    ctype = "subcat" if typee == "cat" else "page" if typee == "page" else ""

    subcategories_result = sub_cats_query("Category:" + cat, code, ctype=ctype)

    categorymembers = subcategories_result.get("categorymembers", {}) if subcategories_result else {}

    return categorymembers


def MakeLitApiWay(encat, Type="cat"):
    """
    Generate a list of page titles based on the provided category.
    """

    if not encat:
        logger.info("<<lightblue>> No encat")
        return False

    logger.info("<<lightgreen>>* MakeLit ApiWay: ")
    # count = 0
    # encat = encat.replace('[[', '').replace(']]', '').replace('Category:', '').replace('category:', '').strip()
    encat = encat.replace("[[", "").replace("]]", "").replace("Category:", "").replace("category:", "").strip()

    gent_faso_list = Categorized_Page_Generator(encat, Type)

    UUX = get_arpage_inside_encat("Category:" + encat)

    if UUX:
        logger.info("arpage inside_encat: " + (",a: ".join(UUX)))
        for x in UUX:
            gent_faso_list.append(x.replace("_", " "))

    listenpageTitle = []
    logger.info(f" MakeLitApi: Way lenth : {len(gent_faso_list)}")
    for i in range(0, len(gent_faso_list), 50):
        liste = gent_faso_list[i : i + 50]

        gent_listu = "|".join(liste)

        gent_sasa = find_LCN(gent_listu, prop="langlinks", first_site_code=settings.EEn_site.code)
        if gent_sasa:
            for p_w in gent_sasa:
                logger.debug(f'find "{p_w}" page_work in gent_sasa ')
                logger.debug(gent_sasa[p_w])
                if ("langlinks" in gent_sasa[p_w]) and ("ar" in gent_sasa[p_w]["langlinks"]):
                    arpagetitle = gent_sasa[p_w]["langlinks"]["ar"]

                    logger.debug(f'find "{p_w}" page_work in gent_sasa arpagetitle: {arpagetitle}')

                    listenpageTitle.append(arpagetitle)

    return listenpageTitle
