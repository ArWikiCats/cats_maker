#!/usr/bin/python3
"""
Wikidata functions for cats_maker_new bot
"""
import functools
import logging

from . import NewHimoAPIBot

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_wd_api_bot() -> NewHimoAPIBot:
    return NewHimoAPIBot(Mr_or_bot="bot", www="www")


def add_label(qid, ar_title) -> None:
    get_wd_api_bot().Labels_API(qid, ar_title, "ar", True, nowait=True, tage="catelabels")


def makejson(property, numeric):
    # ---
    if numeric:
        numeric = numeric.replace("Q", "")
        Q = f"Q{numeric}"
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": property,
                "datavalue": {
                    "value": {
                        "entity-type": "item",
                        "numeric-id": numeric,
                        "id": Q,
                    },
                    "type": "wikibase-entityid",
                },
                "datatype": "wikibase-item",
            },
            "type": "statement",
            "rank": "normal",
        }


def Make_New_item(artitle, entitle, family=""):
    logger.debug(f'<<lightgreen>>* :ar:"{artitle}", english:"{entitle}".')

    enwiki = "enwiki"
    arwiki = "arwiki"

    if family and family != "wikipedia":
        enwiki = f"en{family}"
        arwiki = f"ar{family}"

    data = {
        "sitelinks": {enwiki: {"site": enwiki, "title": entitle}, arwiki: {"site": arwiki, "title": artitle}},
        "labels": {"ar": {"language": "ar", "value": artitle}, "en": {"language": "en", "value": entitle}},
        "claims": {"P31": [makejson("P31", "Q4167836")]},
    }

    summary = f"Bot: New item from [[w:en:{entitle}|{enwiki}]]/[[w:ar:{artitle}|{arwiki}]]."

    new_item_id = get_wd_api_bot().New_API(data, summary, returnid=True, nowait=True, tage="newitems")

    if new_item_id and new_item_id.startswith("Q"):
        return True
    return False


def Log_to_wikidata(ar, enca, qid):
    if qid:
        get_wd_api_bot().Sitelink_API(qid, ar, "arwiki", nowait=True)
        get_wd_api_bot().Labels_API(qid, ar, "ar", False, nowait=True, tage="catelabels")

    else:
        cd = get_wd_api_bot().Sitelink_API("", ar, "arwiki", enlink=enca, ensite="enwiki", nowait=True)
        if cd is not True:
            Make_New_item(ar, enca, family="wikipedia")
