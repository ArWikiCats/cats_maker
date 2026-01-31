"""

from ..tools_bots.temp_bot import templatequery, templatequerymulti

"""

import logging
from collections import defaultdict

from ...wiki_api import find_LCN, get_cache_L_C_N, set_cache_L_C_N

logger = logging.getLogger(__name__)

templatequery_cache = defaultdict(dict)

SKIP_CATEGORIES = ["تصنيف:أشخاص على قيد الحياة", "تصنيف:أشخاص أحياء"]


def _get_from_cache(enlink, sitecode):
    # ---
    tup = (enlink, sitecode, "templates")
    # ---
    site_cache = templatequery_cache[sitecode]
    # ---
    if enlink in site_cache:
        return site_cache[enlink], tup, site_cache
    # --- Check external cache
    cached = get_cache_L_C_N(tup)
    # ---
    if cached is not None:
        site_cache[enlink] = cached
    # ---
    return cached, tup, site_cache


def templatequery(enlink, sitecode="ar"):
    # ---
    if enlink in SKIP_CATEGORIES:
        return False
    # ---
    cached, tup, site_cache = _get_from_cache(enlink, sitecode)
    # ---
    if cached is not None:
        return cached
    # ---
    logger.debug(f"<<lightblue>> {sitecode}:{enlink} . ")
    # ---
    # prop= "templates|langlinks"
    prop = "templates"
    # ---
    sasa = find_LCN(enlink, prop=prop, first_site_code=sitecode)
    # ---
    templates = sasa.get(enlink, {}).get("templates") if sasa else None
    # ---
    result = templates if templates else False
    # ---
    site_cache[enlink] = result
    set_cache_L_C_N(tup, result)
    # ---
    return result


def templatequerymulti(enlink, sitecode):
    # ---
    if enlink in SKIP_CATEGORIES:
        return False
    # ---
    cached, tup, site_cache = _get_from_cache(enlink, sitecode)
    # ---
    if cached is not None:
        return cached
    # ---
    logger.info(f"<<lightblue>> templatequery {sitecode}:{enlink} . ")
    # ---
    # prop= "templates|langlinks"
    prop = "templates"
    # ---
    sasa = find_LCN(enlink, prop=prop, first_site_code=sitecode)
    # ---
    result = sasa if sasa else False
    # ---
    site_cache[enlink] = result
    set_cache_L_C_N(tup, result)
    # ---
    return result
