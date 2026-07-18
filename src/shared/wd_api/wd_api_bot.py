#!/usr/bin/python3
"""
https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q4167836
https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=Q4167836

https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q42
https://doc.wikimedia.org/Wikibase/master/js/rest-api/#/items/getItem


"""

import logging
from functools import lru_cache
from typing import Any

from ...shared.api_page import load_main_api

logger = logging.getLogger(__name__)


def submitWikidataParams(params) -> dict[str, Any]:
    wikidata_api = load_main_api("www", "wikidata")
    return wikidata_api.login_bot.client_request_safe(params)


def format_sitelinks(sitelinks) -> dict[str, Any]:
    return {x["site"]: x["title"] for d, x in sitelinks.items()}


def format_labels_descriptions(labels: dict[str, Any]) -> dict[str, Any]:
    return {x["language"]: x["value"] for _, x in labels.items()}


def Get_infos_wikidata(params) -> dict[str, Any]:
    table = {"labels": {}, "sitelinks": {}, "q": ""}

    json1 = submitWikidataParams(params)

    if not json1:
        return table

    success = json1.get("success", False)
    if not success or success != 1:
        return table

    entities = json1.get("entities", {})

    if "-1" in entities:
        return table

    props = params.get("props", "").split("|") if params.get("props") else []

    for q, qprop in entities.items():
        table["q"] = q

        table["labels"] = format_labels_descriptions(qprop.get("labels", {}))

        table["sitelinks"] = format_sitelinks(qprop.get("sitelinks", {}))

        for x in props:
            if x in qprop and x not in table:
                table[x] = qprop[x]

    return table


@lru_cache(maxsize=5000)
def Get_Sitelinks_From_wikidata(
    site,
    title,
) -> dict[str, Any]:
    sitewiki = site
    if site.find("wiki") == -1:
        sitewiki = f"{site}wiki"

    params: dict[str, Any] = {
        "action": "wbgetentities",
        "props": "sitelinks",
        # "props": "sitelinks|templates",
        "sites": sitewiki,
        "titles": title,
        "normalize": 1,
        # "tlnamespace": "10",
        # "tllimit": "max",
        # "tltemplates": "Template:Category redirect",
    }

    table = Get_infos_wikidata(params)

    return table


def Get_Sitelinks_from_qid(ids) -> dict[str, Any]:
    params: dict[str, Any] = {
        "action": "wbgetentities",
        "props": "sitelinks",
        "normalize": 1,
        "ids": ids,
    }

    table = Get_infos_wikidata(params)

    return table


def Get_P373_API(q, titles: str = "", sites: str = "") -> Any:
    """
    Retrieve the P373 value from the Wikidata API.
    """

    # url =https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q805&utf8=1&property=P31&format=json

    P = "P373"

    params: dict[str, Any] = {
        "action": "wbgetentities",
        "props": "sitelinks|claims",
        "ids": q,
    }

    if q == "" and titles and sites:
        del params["ids"]
        # params["ids"] = ids
        params["sites"] = sites
        params["titles"] = titles

    json1 = submitWikidataParams(params) or {}

    mainvalue = ""

    if not json1:
        return ""

    entities = json1.get("entities", {})
    for jj in entities:
        commonswiki = entities[jj].get("sitelinks", {}).get("commonswiki", {}).get("title", "")
        if commonswiki:
            mainvalue = commonswiki.replace("Category:", "")
            return mainvalue

        claims = entities[jj].get("claims", {}).get(P, {})
        for claim in claims:
            datavalue = claim.get("mainsnak", {}).get("datavalue", {})
            _type = datavalue.get("type", False)
            value = datavalue.get("value", "")
            if _type == "string" and value:
                logger.info(value)
                return value

    return mainvalue
