#!/usr/bin/python3
""" """

import logging
from typing import Any

from ..config import main_settings
from ..shared import AllAPIS

logger = logging.getLogger(__name__)

API_n_CALLS = {1: 0}


def submit_params(params, site_code: str) -> dict[str, Any]:
    site_api = AllAPIS.load(site_code, "wikipedia")
    return site_api.login_bot.client_request_safe(params)


def sub_cats_query(enlink, site_code, ctype: str = "") -> dict[str, Any]:
    if not enlink:
        return {}

    langcode = main_settings.en_site.code  # 'en'
    if site_code == "en":
        langcode = "ar"

    params: dict[str, Any] = {
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

    logger.info(f"API_n_CALLS {API_n_CALLS[1]} for {site_code}:{enlink}")

    try:
        data = submit_params(params, site_code)
    except Exception:
        logger.exception(
            "sub_cats_query failed: site_code=%s enlink=%s ctype=%s",
            site_code,
            enlink,
            ctype,
        )
        return {"error": f"Failed to query Wikipedia API for '{enlink}' on '{site_code}'", "categorymembers": {}}

    tablemember = {}

    pages = data.get("query", {}).get("pages", {})

    for _category, caca in pages.items():
        cate_title = caca["title"]
        tablemember[cate_title] = {}

        logger.debug(f"cate_title: {cate_title}")

        if "ns" in caca:
            tablemember[cate_title]["ns"] = caca["ns"]
            logger.debug(f"ns: {caca['ns']}")

        for fo in caca.get("langlinks", {}):
            tablemember[cate_title][fo["lang"]] = fo["*"]

    table = {"categorymembers": tablemember}

    return table


__all__ = [
    "submit_params",
    "sub_cats_query",
]
