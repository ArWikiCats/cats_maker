#!/usr/bin/env python3 core8/pwb.py

import logging

from .get_bots import Get_item_descriptions_or_labels
from .wd_desc import work_api_desc
from .wd_sparql_bot import sparql_generator_url

logger = logging.getLogger(__name__)

# ---
translations = {
    "Wikimedia module": {  # Q4167836
        "ar": "وحدة ويكيميديا",
        "en": "Wikimedia module",
        "nl": "Wikimedia-module",
        "he": "יחידה של ויקימדיה",
        "bg": "Уикимедия модул",
    }
}


def work22(q, topic, translations):
    # ---
    keys = sorted([x for x in translations[topic].keys()])
    if "en" in keys:
        keys.append("en-gb")
        keys.append("en-ca")
    # ---
    ItemDescriptions = Get_item_descriptions_or_labels(q, "descriptions")
    # ---
    if not ItemDescriptions or not isinstance(ItemDescriptions, dict):
        ItemDescriptions = {}
    # ---
    ItemDesc_keys = list(ItemDescriptions.keys())
    # ---
    NewDesc = {}
    # ---
    for lang in keys:
        if lang not in ItemDesc_keys:
            # ---
            lang2 = lang
            if lang in ("en-ca", "en-gb"):
                lang2 = "en"
            # ---
            NewDesc[lang] = {"language": lang, "value": translations[topic][lang2]}
    # ---
    work_api_desc(NewDesc, q)


def mainfromQuarry(topic, Quarry, translations):
    # logger.info( '*<<lightyellow>> mainfromQuarry:' )
    # Quarry = 'SELECT ?item WHERE { ?item wdt:P31 wd:Q17633526.}'
    json = sparql_generator_url(Quarry)
    lenth = len(json)
    num = 0
    # ---
    for item in json:
        num += 1
        q = "item" in item and item["item"].split("/entity/")[1]
        logger.info(f'<<lightyellow>>*mainfromQuarry: {num}/{lenth} topic:"{topic}", q:"{q}".')
        work22(q, topic, translations)
