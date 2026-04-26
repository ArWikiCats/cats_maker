#!/usr/bin/python3
"""
https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q4167836
https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=Q4167836

https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q42
https://doc.wikimedia.org/Wikibase/master/js/rest-api/#/items/getItem


"""
import logging
from functools import lru_cache

from ..wiki_api import submitAPI

logger = logging.getLogger(__name__)


def submitWikidataParams(params):
    return submitAPI(params, "www", "wikidata")


def format_sitelinks(sitelinks):
    return {x["site"]: x["title"] for d, x in sitelinks.items()}


def format_labels_descriptions(labels):
    return {x["language"]: x["value"] for _, x in labels.items()}


def Get_infos_wikidata(params):

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
    ssite="",
    ids="",
    return_main_table=False,
):

    sitewiki = site
    if site.find("wiki") == -1:
        sitewiki = f"{site}wiki"

    params = {
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

    if ids:
        params["ids"] = ids
        del params["sites"]
        del params["titles"]

    table = Get_infos_wikidata(params)

    if return_main_table:
        return table

    if table:
        table["site"] = sitewiki

    ssite2 = ssite
    if not ssite.endswith("wiki"):
        ssite2 += "wiki"

    if ssite:
        sitelinks = table.get("sitelinks", {})
        result = sitelinks.get(ssite) or sitelinks.get(ssite2) or ""
        return result

    return table


def Get_Sitelinks_from_qid(ssite="", ids=""):
    return Get_Sitelinks_From_wikidata("", "", ssite=ssite, ids=ids)


def Get_P373_API(q, titles="", sites=""):
    """Retrieve the P373 value from the Wikidata API.

    This function constructs a request to the Wikidata API to fetch entities
    based on the provided identifier (q). It retrieves the sitelinks and
    claims associated with the entity and specifically looks for the P373
    property, which is used to link to Wikimedia Commons categories. If the
    identifier is not provided, it can use titles and sites to fetch
    relevant data.

    Args:
        q (str): The identifier for the Wikidata entity.
        titles (str?): Titles to search for if no identifier is provided.
        sites (str?): Sites to filter the search if no identifier is provided.

    Returns:
        str: The P373 value (Wikimedia Commons category title) if found,
            otherwise an empty string.
    """

    # url =https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q805&utf8=1&property=P31&format=json

    P = "P373"

    params = {
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
