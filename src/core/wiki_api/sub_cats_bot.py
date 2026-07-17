#!/usr/bin/python3
""" """

import logging
from typing import Any

from ...config import main_settings
from ...shared.api_page import load_main_api
from . import get_cache_L_C_N, set_cache_L_C_N

logger = logging.getLogger(__name__)

API_n_CALLS = {1: 0}


def submitParams(params, site_code: str) -> dict[str, Any]:
    site_api = load_main_api(site_code, "wikipedia")
    return site_api.login_bot.client_request_safe(params)


def sub_cats_query(enlink, sitecode, ctype: str = "") -> dict[str, Any]:
    if not enlink:
        return {}

    tup = (enlink, sitecode, "sub_cats_query")

    if get_cache_L_C_N(tup):
        return get_cache_L_C_N(tup) or {}

    langcode = main_settings.EEn_site.code  # 'en'
    if sitecode == "en":
        langcode = "ar"

    params = {
        "action": "query",
        "format": "json",
        "prop": "langlinks",
        "titles": enlink,
        "generator": "categorymembers",
        "utf8": 1,
        "lllang": langcode,
        "lllimit": "max",
        "gcmtitle": enlink,
        "gcmprop": "title",
        "gcmtype": "page|subcat",
        "gcmlimit": "max",
    }

    if ctype == "subcat":
        params["gcmtype"] = "subcat"

    if ctype == "page":
        params["gcmtype"] = "page"

    API_n_CALLS[1] += 1

    logger.info(f"API_n_CALLS {API_n_CALLS[1]} for {sitecode}:{enlink}")

    try:
        data = submitParams(params, sitecode)
    except Exception:
        logger.exception(
            "sub_cats_query failed: sitecode=%s enlink=%s ctype=%s",
            sitecode,
            enlink,
            ctype,
        )
        return {"error": f"Failed to query Wikipedia API for '{enlink}' on '{sitecode}'", "categorymembers": {}}

    tablemember = {}

    pages = data.get("query", {}).get("pages", {})

    for _category, caca in pages.items():
        cate_title = caca["title"]
        tablemember[cate_title] = {}

        logger.debug(f"cate_title: {cate_title}")

        if "ns" in caca:
            tablemember[cate_title]["ns"] = caca["ns"]
            set_cache_L_C_N((cate_title, sitecode, "ns"), caca["ns"])
            logger.debug(f"ns: {caca['ns']}")

        for fo in caca.get("langlinks", {}):
            result = fo["*"]
            tablemember[cate_title][fo["lang"]] = fo["*"]

            tubb = (cate_title, sitecode, fo["lang"], "en_links")
            set_cache_L_C_N(tubb, result)
            logger.debug(f'add {fo["lang"]}:"{result}" to {cate_title}')

            oppsite_tubb = (result, fo["lang"], sitecode, "en_links")
            logger.debug(f'add {sitecode}:"{cate_title}" to {result}')
            set_cache_L_C_N(oppsite_tubb, cate_title)

    table = {"categorymembers": tablemember}

    set_cache_L_C_N(tup, table)

    return table
