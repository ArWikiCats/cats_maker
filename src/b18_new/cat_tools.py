#!/usr/bin/python3
"""
from .cat_tools import get_SubSub_value
"""
import logging

from ..config import settings
from ..utils.skip_cats import global_False_entemps as NO_Templates
from ..wiki_api import get_cache_L_C_N

logger = logging.getLogger(__name__)

SubSub = {}
# ---
# Define a blacklist for templates and names
templateblacklist = NO_Templates
# ---
nameblcklist = [
    "Current events",  # حدث جاري
    "Articles with",
    "Tracking",
    "articles",
    "Surnames",
    "Loanword",
    "Words and phrases",
    "Given names",
    "Human names",
    "stubs",  # بذرة
    "Nicknames",
]
# ---
if settings.category.stubs:
    nameblcklist.remove("stubs")


def get_SubSub_keys():
    """Retrieve the keys of the SubSub dictionary.

    This function accesses the SubSub dictionary and returns a list
    containing all the keys present in that dictionary. It is useful for
    obtaining a quick reference to the keys without needing to manipulate
    the dictionary directly.

    Returns:
        list: A list of keys in the SubSub dictionary.
    """
    return list(SubSub)


def get_SubSub_value(key):
    return SubSub.get(key)


def add_SubSub(List, hhh):
    for catj in List:
        logger.info(f"SubSub[{catj}].append( {hhh} )")
        catj_u = str(catj)
        if catj_u not in SubSub:
            SubSub[catj_u] = []
        SubSub[catj_u].append(hhh)


def work_in_one_cat(cat, tabcat, en_site_code, pagetitle, en_cate_list):
    Cat_pass = True
    # ---
    ar_cat_for_cat = tabcat.get("ar")
    # ---
    if not ar_cat_for_cat:
        tupl = (cat, en_site_code, "ar", "en_links")
        daaa = get_cache_L_C_N(tupl)
        if daaa:
            logger.info(f'\t<<lightpurple>> New way for "{cat}" find "{daaa}"')
            ar_cat_for_cat = daaa
    # ---
    if not ar_cat_for_cat:
        # ---
        logger.debug("\tno ar title...")
        # ---
        if cat not in SubSub:
            SubSub[cat] = []
        SubSub[cat].append(pagetitle)
        # ---
        return en_cate_list
    # ---
    if ar_cat_for_cat:
        # ---
        logger.debug(f"\tfind ar_cat_for_cat: {ar_cat_for_cat}")
        # ---
        for item in nameblcklist:
            if cat.lower().find(item.lower()) != -1:
                logger.debug(f"\tfind item {item} in cat.")
                Cat_pass = False
        # ---
        temples = tabcat.get("templates")
        if temples:
            for temp in temples:
                for black in templateblacklist:
                    if temp.lower().find(black.lower()) != -1:
                        logger.debug(f'\tfind black temp "{temp}" in cat.')
                        Cat_pass = False
                        return en_cate_list
        # ---
        if Cat_pass:
            en_cate_list.append(ar_cat_for_cat)
    # ---
    return en_cate_list
