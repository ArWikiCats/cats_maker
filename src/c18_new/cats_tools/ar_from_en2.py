#!/usr/bin/python3
""" """
import logging

from ...config import settings
from ...new_api.pagenew import load_main_api
from ...wiki_api import find_LCN

logger = logging.getLogger(__name__)


def get_ar_list_title_from_en_list(enlist, wiki="en"):
    # ---
    new_ar_list = []
    # ---
    en_done = []
    # ---
    for i in range(0, len(enlist), 50):
        liste = enlist[i : i + 50]
        part_list = "|".join(liste)
        if part_list:
            if part_list.startswith("|"):
                part_list = part_list[len("|") :]
            # ---
            sito_code = settings.EEn_site.code
            # ---
            if wiki == "fr":
                sito_code = settings.FR_site.code
            # ---
            new_list = find_LCN(part_list, prop="langlinks", lllang="ar", first_site_code=sito_code)
            # ---
            if new_list:
                for p_w in new_list:
                    # ---
                    if "langlinks" in new_list[p_w] and "ar" in new_list[p_w]["langlinks"]:
                        arpagetitle = new_list[p_w]["langlinks"]["ar"]
                        # ---
                        logger.debug(f"<<lightblue>>Adding {arpagetitle} to ar lists {p_w}<<default>>")
                        new_ar_list.append(arpagetitle)
                        en_done.append(arpagetitle.replace("_", " "))
    # ---
    logger.info(f"<<lightyellow>> , <<lightblue>>lenth of new_ar_list:{len(new_ar_list)}")
    # ---
    return new_ar_list


def en_category_members(enpageTitle, wiki="en"):
    # ---
    logger.info(f"<<lightyellow>> from category: {enpageTitle} <<default>>")
    # ---
    namespace_ids = [0, 14, 100]
    # ---
    api = load_main_api(wiki)
    cat_members = api.CatDepth(enpageTitle, depth=0, ns="all", without_lang="", with_lang="ar", tempyes=[])
    # ---
    en_titles = []
    # ---
    for title in cat_members:
        if int(cat_members[title]["ns"]) in namespace_ids:
            en_titles.append(title)
    # ---
    return en_titles


def fetch_ar_titles_based_on_en_category(enpageTitle, wiki="en"):
    # ---
    en_titles = en_category_members(enpageTitle, wiki=wiki)
    # ---
    new_ar_list = get_ar_list_title_from_en_list(en_titles, wiki=wiki)
    # ---
    return new_ar_list
