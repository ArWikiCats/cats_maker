#!/usr/bin/python3
"""
Wikidata functions for cats_maker_new bot
"""

import functools
import json
import logging
import re
import time

from ..new_api import ALL_APIS, load_main_api
from .lag_bot import is_wd_lag_high
from .wd_bots_main import WD_API

logger = logging.getLogger(__name__)


def outbot_json_bot(err):
    text = str(err)

    err_code = err.get("code", "")
    err_info = err.get("info", "")

    extradata = err.get("extradata", [""])
    messages = err.get("messages", [{}])[0]
    msg_name = messages.get("name", "")

    msg_html = ""
    if isinstance(messages.get("html", {}), dict):
        msg_html = messages.get("html", {}).get("*", "")

    err_wait = "احترازًا من الإساء، يُحظر إجراء هذا الفعل مرات كثيرة في فترةٍ زمنية قصيرة، ولقد تجاوزت هذا الحد"

    if err_code == "origin-not-empty":
        logger.debug(f"<<lightred>> msg_html: {msg_html} ")
        logger.debug(f"<<lightred>> err_info: {err_info} ")
        return err_code

    if err_code == "missingparam":
        logger.debug(f"<<lightred>> err_info: {err_info} ")
        return "warn"

    elif err_code in ["modification-failed", "failed-modify"]:
        logger.debug(f"<<lightred>> err_info: {err_info} ")

        if msg_name == "wikibase-api-failed-modify":
            logger.debug(f"<<lightred>>err msg_name: {msg_name}")
            logger.debug(f"<<lightred>>\t: {extradata}")
            return msg_name

        if msg_name == "wikibase-validator-label-equals-description":
            logger.debug(f"<<lightred>>err msg_name: {msg_name}")
            logger.debug(f"<<lightred>>\t: {msg_html}")
            return msg_name

        if msg_name == "wikibase-validator-label-with-description-conflict":
            logger.debug("<<lightred>>same description:")

            lab, code, q = messages.get("parameters", [])

            logger.debug(f"<<lightred>>\t: lab:{lab}, code:{code}, q:{q}")

            return "same description"
        return "warn"
    elif err_code == "unresolved-redirect":
        logger.debug("<<lightred>> - unresolved-redirect")
        return "unresolved-redirect"

    elif err_code == "failed-save":
        if err_wait in text:
            logger.debug(f'<<lightred>> "{err_wait} time.sleep(5) " ')
            time.sleep(5)
            return "reagain"

        logger.debug(f'<<lightred>> - "{err_code}" ')
        logger.debug(text)
        return False
    elif err_code == "no-external-page":
        logger.debug(f'<<lightred>> - "{err_code}" ')
        logger.debug(text)
        return False

    else:
        if "wikibase-api-invalid-json" in text:
            logger.debug('<<lightred>> - "wikibase-api-invalid-json" ')
            logger.debug(text)
            return "wikibase-api-invalid-json"

        elif "Could not find an Item containing a sitelink to the provided site and page name" in text:
            logger.debug(
                "<<lightred>> ** error. : Could not find an Item containing a sitelink to the provided site and page name "
            )
            return "Could not find an Item containing a sitelink to the provided site and page name"
        else:
            return err_code


def outbot_json(js_text, fi="", line=""):
    success = js_text.get("success", 0)

    if success == 1:
        logger.warning(f"<<lightgreen>> ** true. {fi}")

        return True

    err = js_text.get("error", {})

    if not err:
        return "warn"

    if fi:
        logger.debug(f"<<lightred>> ** error. : {fi} ")

    if line:
        logger.debug(f"<<lightpurple>> ** line. : {line} ")

    return outbot_json_bot(err)


@functools.lru_cache(maxsize=1024)
def get_session_post(www="www") -> ALL_APIS:
    api = load_main_api(lang=www, family="wikidata")
    return WD_API(api.login_bot)


def add_labels(
    qid,
    label,
    lang,
):
    if is_wd_lag_high():
        return ""

    if not qid:
        logger.debug(" Qid == '' ")
        return False

    if label == "":
        logger.debug(" label == '' and remove = False ")
        return False

    # save the edit
    out = f'{qid} label:"{lang}"@{label}.'
    wd_api = get_session_post()
    r4 = wd_api.post_to_newapi(
        params={
            "action": "wbsetlabel",
            "id": qid,
            "language": lang,
            "value": label,
        },
    )

    if not r4:
        logger.debug(" r4 == {} ")
        return False

    text = str(r4)
    if ("using the same description text" in text) and ("associated with language code" in text):
        info = (r4.get("error") or {}).get("info", "")
        m = re.search(r"(Q\d+)", str(info))
        if m:
            logger.debug(f"<<lightred>>API: same label item: {m.group(1)}")

    success = r4.get("success", 0)
    if success == 1:
        logger.warning("<<lightgreen>> ** true.")
        return True

    d = outbot_json(r4, fi=out)

    if d == "warn":
        logger.warning(str(r4))


def add_sitelinks_to_wikidata(
    qid,
    title,
    wiki,
    enlink="",
    ensite="",
    returnid=False,
    return_text=False,
):
    if is_wd_lag_high():
        return ""

    if not wiki.endswith("wiki") and wiki.find("wiki") == -1 and wiki.find("wiktionary") == -1:
        wiki = f"{wiki}wiki"

    if enlink:
        logger.debug(f' **: enlink:"{ensite}:{enlink}" {wiki}:{title}')
    else:
        logger.debug(f' **: Qid:"{qid}" {wiki}:{title}')

    # save the edit

    if qid.strip() == "" and enlink == "":
        logger.debug(f'<<lightred>> **: False: Qid == "" {wiki}:{title}.')
        return False

    paramse = {
        "action": "wbsetsitelink",
        "linktitle": title,
        "linksite": wiki,
    }

    out = f'Added link to "{qid}" [{wiki}]:"{title}"'

    if qid:
        paramse["id"] = qid
    else:
        out = f'Added link to "{ensite}:{enlink}" [{wiki}]:"{title}"'
        paramse["title"] = enlink
        paramse["site"] = ensite

    wd_api = get_session_post()
    r4 = wd_api.post_to_newapi(params=paramse)

    if not r4:
        return False

    success = r4.get("success", 0)
    if success == 1:
        logger.warning(f"<<lightgreen>> true {out}")
        if enlink and returnid:
            ido = re.match(r".*\"id\"\:\"(Q\d+)\".*", str(r4))
            if ido:
                return ido.group(1)
        else:
            return True

    d = outbot_json(r4, fi=out)

    if return_text:
        return str(r4)

    if d == "warn":
        logger.warning(str(r4))

    return d


def create_new_item(
    data2,
    summary,
    returnid=False,
):
    """
    Create a new item in the API with the provided data and summary.
    """

    if is_wd_lag_high():
        return ""

    data = json.JSONEncoder().encode(data2)

    wd_api = get_session_post()
    r4 = wd_api.post_to_newapi(
        params={
            "action": "wbeditentity",
            "new": "item",
            "summary": summary,
            "data": data,
        },
    )

    if not r4:
        return False

    success = r4.get("success", 0)

    if success != 1:
        return False

    logger.warning("<<lightgreen>> ** true.")

    if returnid:
        if "entity" in r4 and "id" in r4["entity"]:
            qid = r4["entity"]["id"]
            logger.debug(f'<<lightgreen>> bot.py : returnid:"{qid}" ')
            return qid

    return True


def makejson(property, numeric):
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


def log_to_wikidata_qid(artitle, qid) -> None:
    add_sitelinks_to_wikidata(qid, artitle, "arwiki")
    add_labels(qid, artitle, "ar")


def log_to_wikidata(artitle, entitle) -> None:
    cd = add_sitelinks_to_wikidata("", artitle, "arwiki", enlink=entitle, ensite="enwiki")

    if cd is True:
        return True

    logger.debug(f'<<lightgreen>>* :ar:"{artitle}", english:"{entitle}".')

    enwiki = "enwiki"
    arwiki = "arwiki"

    data = {
        "sitelinks": {enwiki: {"site": enwiki, "title": entitle}, arwiki: {"site": arwiki, "title": artitle}},
        "labels": {"ar": {"language": "ar", "value": artitle}, "en": {"language": "en", "value": entitle}},
        "claims": {"P31": [makejson("P31", "Q4167836")]},
    }

    summary = f"Bot: New item from [[w:en:{entitle}|{enwiki}]]/[[w:ar:{artitle}|{arwiki}]]."

    new_item_id = create_new_item(data, summary, returnid=True)
    return new_item_id
