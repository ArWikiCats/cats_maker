#!/usr/bin/python3
"""
Wikidata functions for cats_maker_new bot
"""

import functools
import json
import logging
from typing import Any

from ...shared.api_page import load_login_bot
from .wd_bots_main import WdAPI

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def get_session_post(www: str = "www") -> WdAPI:
    login_bot = load_login_bot(lang=www, family="wikidata")
    return WdAPI(login_bot)


def post_wd_params(params) -> bool:
    try:
        wd_api_se = get_session_post()
        result = wd_api_se.post_to_newapi(params=params)

        success = result.get("success", 0)
        if success == 1:
            logger.warning("** true.")
            return True

    except Exception as e:
        logger.error(f"** error. : {e}")

    return False


def add_labels(
    qid,
    label: str,
    lang,
) -> bool:
    if not qid:
        logger.debug(" qid == '' ")
        return False

    if label == "":
        logger.debug(" label == '' and remove = False ")
        return False

    # save the edit
    out = f'{qid} label:"{lang}"@{label}.'

    result = post_wd_params(
        {
            "action": "wbsetlabel",
            "id": qid,
            "language": lang,
            "value": label,
        }
    )

    if not result:
        return False

    logger.info(out)
    return True


def add_sitelinks_to_wikidata(
    qid,
    title,
    wiki,
    enlink: str = "",
    ensite: str = "",
) -> bool:
    if not wiki.endswith("wiki") and wiki.find("wiki") == -1 and wiki.find("wiktionary") == -1:
        wiki = f"{wiki}wiki"

    if enlink:
        logger.debug(f' **: enlink:"{ensite}:{enlink}" {wiki}:{title}')
    else:
        logger.debug(f' **: qid:"{qid}" {wiki}:{title}')

    if qid.strip() == "" and enlink == "":
        logger.debug(f'**: False: qid == "" {wiki}:{title}.')
        return False

    params: dict[str, Any] = {
        "action": "wbsetsitelink",
        "linktitle": title,
        "linksite": wiki,
    }

    out = f'Added link to "{qid}" [{wiki}]:"{title}"'

    if qid:
        params["id"] = qid
    else:
        out = f'Added link to "{ensite}:{enlink}" [{wiki}]:"{title}"'
        params["title"] = enlink
        params["site"] = ensite

    result = post_wd_params(params)

    if not result:
        return False

    logger.info(out)
    return True


def create_new_item(
    data2,
    summary,
) -> bool:
    """
    Create a new item in the API with the provided data and summary.
    """

    data = json.JSONEncoder().encode(data2)

    result = post_wd_params(
        {
            "action": "wbeditentity",
            "new": "item",
            "summary": summary,
            "data": data,
        }
    )

    if not result:
        return False

    return True


def makejson(property, numeric) -> dict[str, Any]:
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


def log_to_wikidata_qid(artitle, qid) -> None:
    add_sitelinks_to_wikidata(qid, artitle, "arwiki")
    add_labels(qid, artitle, "ar")


def log_to_wikidata(artitle, entitle) -> None | str:
    cd = add_sitelinks_to_wikidata("", artitle, "arwiki", enlink=entitle, ensite="enwiki")

    if cd is True:
        return None

    logger.debug(f'* :ar:"{artitle}", english:"{entitle}".')

    enwiki = "enwiki"
    arwiki = "arwiki"

    data = {
        "sitelinks": {enwiki: {"site": enwiki, "title": entitle}, arwiki: {"site": arwiki, "title": artitle}},
        "labels": {"ar": {"language": "ar", "value": artitle}, "en": {"language": "en", "value": entitle}},
        "claims": {"P31": [makejson("P31", "Q4167836")]},
    }

    summary = f"Bot: New item from [[w:en:{entitle}|{enwiki}]]/[[w:ar:{artitle}|{arwiki}]]."

    create_new_item(data, summary)
