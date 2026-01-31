#!/usr/bin/python3
""" """
import logging

from ..c18_new.cat_tools2 import Categorized_Page_Generator
from ..config import settings
from ..wiki_api import find_LCN, get_arpage_inside_encat, get_cache_L_C_N, sub_cats_query

logger = logging.getLogger(__name__)


def get_ar_list_from_cat(cat, code="ar", typee="cat", return_list=True):
    """Retrieve a list of category members from a specified category.

    This function queries a category based on the provided category name and
    retrieves its members. The type of members retrieved can be specified
    through the `typee` parameter, which determines whether to fetch
    subcategories or pages. The results are returned as a list of keys
    representing the members of the specified category.

    Args:
        cat (str): The name of the category to query.
        code (str?): The language code for the query. Defaults to "ar".
        typee (str?): The type of members to retrieve, either "cat" for
            subcategories or "page" for pages. Defaults to "cat".
        return_list (bool?): A flag indicating whether to return
            the list of members. Defaults to True.

    Returns:
        list: A list of keys representing the members of the specified category.
    """

    # ---
    lista = []
    # ---
    if cat.startswith("Category:"):
        cat = cat.replace("Category:", "")
    # ---
    if cat.startswith("تصنيف:"):
        cat = cat.replace("تصنيف:", "")
    # ---
    ctype = "subcat" if typee == "cat" else "page" if typee == "page" else ""
    # ---
    subcategories_result = sub_cats_query("Category:" + cat, code, ctype=ctype)
    # ---
    categorymembers = subcategories_result.get("categorymembers", {}) if subcategories_result else {}
    # ---
    if categorymembers:
        lista = list(categorymembers)
    # ---
    return lista


def MakeLitApiWay(enpageTitle, Type="cat"):
    """Generate a list of page titles based on the provided category.

    This function takes a category title and generates a list of related
    page titles by utilizing categorized page generation tools. It processes
    the input title to remove unnecessary formatting and checks for existing
    categorized pages. If no pages are found, it attempts to retrieve them
    from an alternative source. The resulting list of page titles is
    returned if successful; otherwise, it returns False.

    Args:
        enpageTitle (str): The title of the category for which to generate related page titles.
        Type (str?): The type of categorization to use. Defaults to "cat".

    Returns:
        list: A list of generated page titles related to the specified category, or
        False if no titles could be generated.
    """

    listenpageTitle = []
    # ---
    encat = enpageTitle
    if not encat:
        logger.info("<<lightblue>> No enpageTitle")
        return False
    # ---
    logger.info("<<lightgreen>>* MakeLit ApiWay: ")
    # count = 0
    # encat = encat.replace('[[', '').replace(']]', '').replace('Category:', '').replace('category:', '').strip()
    encat = encat.replace("[[", "").replace("]]", "").replace("Category:", "").replace("category:", "").strip()
    # ---
    gent_faso_list = Categorized_Page_Generator(encat, Type)
    # ---
    UUX = get_arpage_inside_encat("Category:" + encat)
    # ---
    if UUX:
        logger.info("arpage inside_encat: " + (",a: ".join(UUX)))
        for x in UUX:
            gent_faso_list.append(x.replace("_", " "))
    # ---
    if not gent_faso_list:
        gent_faso_list = get_ar_list_from_cat(encat, code="en", typee=Type)
    # ---
    logger.info(f" MakeLitApi: Way lenth : {len(gent_faso_list)}")
    if len(gent_faso_list) == 0:
        logger.info(f'<<lightblue>> MakeLit ApiWay: No cats gent_faso_list == ["{len(gent_faso_list)}"] ')
        return False
    # ---
    for i in range(0, len(gent_faso_list), 50):
        liste = gent_faso_list[i : i + 50]
        # ---
        gent_listu = "|".join(liste)
        # ---
        if not gent_listu:
            continue
        # ---
        if gent_listu.startswith("|"):
            gent_listu = gent_listu[len("|") :]
        # ---
        gent_sasa = find_LCN(gent_listu, prop="langlinks", first_site_code=settings.EEn_site.code)
        # ---
        if gent_sasa:
            for p_w in gent_sasa:
                # ---
                arpagetitle = False
                # if p_w in gent_sasa:
                # if (p_w in gent_sasa) and ('langlinks' in gent_sasa[p_w]) and ("ar" in gent_sasa[p_w]):
                logger.debug(f'find "{p_w}" page_work in gent_sasa ')
                logger.debug(gent_sasa[p_w])
                if ("langlinks" in gent_sasa[p_w]) and ("ar" in gent_sasa[p_w]["langlinks"]):
                    arpagetitle = gent_sasa[p_w]["langlinks"]["ar"]
                    # logger.debug(f'<<lightgreen>> find ar link for "{p_w}" :' )
                    logger.debug(f'find "{p_w}" page_work in gent_sasa arpagetitle: {arpagetitle}')
                    logger.debug(gent_sasa[p_w]["langlinks"]["ar"])
                else:
                    tubb22 = (p_w, settings.EEn_site.code, "ar", "en_links")
                    # ---
                    if get_cache_L_C_N(tubb22):
                        logger.debug(
                            '>> 2019:get_cache_L_C_N tubb22: "{}":  = {}:{}'.format(
                                p_w, settings.EEn_site.code, get_cache_L_C_N(tubb22)
                            )
                        )
                        arpagetitle = get_cache_L_C_N(tubb22)

                if arpagetitle is False:
                    logger.debug("arpagetitle is False")
                else:
                    logger.debug("<<lightblue>>Adding " + arpagetitle + " to fapage lists " + p_w + "<<default>>")
                    listenpageTitle.append(arpagetitle)
        # ---
    # if not listenpageTitle:
    if len(listenpageTitle) == 0:
        logger.info(f'<<lightblue>> MakeLit ApiWay : No cats listenpageTitle == ["{len(listenpageTitle)}"] ')
        return False
    # ---
    return listenpageTitle
