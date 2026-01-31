#!/usr/bin/python3
"""
https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q4167836
https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=Q4167836

https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q42
https://doc.wikimedia.org/Wikibase/master/js/rest-api/#/items/getItem

"""

import functools
import logging

from ..config import settings
from . import NewHimoAPIBot

logger = logging.getLogger(__name__)

wd_cach = {}


@functools.lru_cache(maxsize=1)
def get_wd_api_bot():
    return NewHimoAPIBot(Mr_or_bot="bot", www="www")


def get_rest_result(url):
    return get_wd_api_bot().get_rest_result(url)


def Get_one_qid_info(qid, only=None):
    """Retrieve information for a given Wikidata entity.

    This function fetches detailed information about a specific Wikidata
    entity identified by its QID. It retrieves various properties such as
    labels, descriptions, aliases, sitelinks, and statements. If a specific
    property is requested through the `only` parameter, the function will
    return only that property. The results are cached for efficiency.

    Args:
        qid (str): The QID of the Wikidata entity to retrieve information for.
        only (str?): A specific property to retrieve. Must be one of
            "sitelinks", "labels", "descriptions", "aliases", or "statements".

    Returns:
        dict: A dictionary containing the requested information about the entity,
            including labels, descriptions, aliases, sitelinks, statements, and
            the QID itself.
    """

    # ---
    key_c = tuple([qid, only])
    # ---
    if key_c in wd_cach:
        return wd_cach[key_c]
    # ---
    props = ["sitelinks", "labels", "descriptions", "aliases", "statements"]
    # ---
    main_table = {
        "labels": {},
        "descriptions": {},
        "aliases": {},
        "sitelinks": {},
        "statements": {},
        "qid": qid,
    }
    # ---
    url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{qid}"
    # ---
    if only in props:
        url += "/" + only
    # ---
    if settings.debug_config.print_url:
        logger.info(url)
    # ---
    result = get_rest_result(url)
    # ---
    if only in props:
        result = {only: result}
    # ---
    main_table["labels"] = result.get("labels", {})
    main_table["descriptions"] = result.get("descriptions", {})
    main_table["aliases"] = result.get("aliases", {})
    # ---
    main_table["sitelinks"] = {x: v["title"] for x, v in result.get("sitelinks", {}).items()}
    # ---
    main_table["statements"] = result.get("statements", {})
    # ---
    # if only in props: main_table = main_table[only]
    # ---
    wd_cach[key_c] = main_table
    # ---
    return main_table


def Get_item_infos(qids):
    # ---
    logger.info(f" {len(qids)=}")
    # ---
    table = {}
    # ---
    for qid in qids:
        # ---
        logger.info(f" work for one qid: {qid}")
        # ---
        table[qid] = Get_one_qid_info(qid)
    # ---
    return table


def Get_P373(qid):
    # ---
    infos = Get_one_qid_info(qid)
    # ---
    value = infos.get("statements", {}).get("P373", [{}])[0].get("value", {}).get("content", "")
    # ---
    if not value:
        value = infos.get("sitelinks", {}).get("commonswiki", "").replace("Category:", "")
    # ---
    return value
