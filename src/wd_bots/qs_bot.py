#!/usr/bin/python3
"""
QS Bot - QuickStatements API wrapper

This module provides functions for working with the QuickStatements API.
"""

import functools
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from ..config import settings
from ..new_api.useraccount import qs_token, qs_tokenbot

logger = logging.getLogger(__name__)

Dir = Path(__file__).parent.parent
menet = datetime.now().strftime("%Y-%b-%d  %H:%M:%S")


@functools.lru_cache(maxsize=1)
def _load_session() -> requests.Session:
    Session = requests.Session()
    Session.headers.update({"User-Agent": settings.wikipedia.user_agent})
    return Session


def QS_New_API(data2):
    # ---
    CREATE = "CREATE||"
    for ss in data2.get("sitelinks", {}):
        dd = data2.get("sitelinks", {})
        tit = dd[ss]["title"]
        wik = dd[ss]["site"]
        wik2 = dd[ss]["site"].replace("wiki", "")
        CREATE += f'LAST|S{wik}|"{tit}"||'
        CREATE += f'LAST|L{wik2}|"{tit}"||'
    # ---
    claims = data2.get("claims", {})
    for Claim in claims:
        for P in claims[
            Claim
        ]:  # {'mainsnak': {'snaktype': 'value', 'property': 'P31', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': '4167836', 'id': 'Q4167836'}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'}, 'type': 'statement', 'rank': 'normal'}
            # logger.debug(P)
            value = P["mainsnak"]["datavalue"].get("value", {}).get("id", "")
            # value = P["datavalue"].get("value",{}).get("id","")
            if value:
                CREATE += f"LAST|{P['mainsnak']['property']}|{value}||"
    # ---
    CREATE = f"{CREATE}XX"
    CREATE = CREATE.replace("||XX", "")
    # ---
    menet = datetime.now().strftime("%Y-%b-%d  %H:%M:%S")
    # ---
    r2 = _load_session().post(
        "https://quickstatements.toolforge.org/api.php",
        data={
            "format": "v1",
            "action": "import",  # create
            # 'type': 'item',
            "compress": 1,
            "submit": 1,
            "batchname": menet,
            "username": "Mr. Ibrahem",
            "token": qs_token,
            "data": CREATE,
        },
    )
    # ---
    if not r2:
        return False
    # ---
    logger.debug(f"QS_New_API: {str(r2.text)}")


def QS_line(line, user="Mr. Ibrahem"):
    # ---
    # https://quickstatements.toolforge.org/api.php?format=v1&action=import&compress=1&submit=1&batchname=df&username=Mr.Ibrahembot&token=$2&data=Q24173161|Dar|"جين في متفطرة خراجية"
    # ---
    tokens = {
        "Mr. Ibrahem": qs_token,
        "Mr.Ibrahembot": qs_tokenbot,
    }
    # ---
    r2 = _load_session().post(
        "https://quickstatements.toolforge.org/api.php",
        data={
            "format": "v1",
            "action": "import",  # create
            # 'type': 'item',
            "compress": 1,
            "submit": 1,
            "batchname": menet,
            "username": user,
            "token": tokens.get(user),
            "data": line,
        },
    )
    # ---
    if not r2:
        return False
    # ---
    logger.debug(r2.text)
    # ---
    time.sleep(2)
