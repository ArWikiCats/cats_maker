"""
Lag handling functionality

This module provides functions for handling lag in Wikidata API requests.
"""

import functools
import logging
import re
import time

import requests

from ...config import settings

logger = logging.getLogger(__name__)

newsleep = {1: 1}

maxlag = settings.wikidata.maxlag

FFa_lag = {1: maxlag, 2: maxlag}
Find_Lag = {}
Find_Lag_o = {1: True}
Find_Lag[2] = time.time()
Find_Lag[3] = 0


@functools.lru_cache(maxsize=1)
def _load_session() -> requests.Session:
    session = requests.session()
    headers = {"User-Agent": settings.wikipedia.user_agent}
    session.headers.update(headers)
    return session


def post_request_for_lag() -> int:
    r4fttext = ""

    params = {
        "action": "query",
        "format": "json",
        "maxlag": -1,
        "titles": "MediaWiki",
    }

    session = _load_session()

    try:
        r4ft = session.post(settings.wikidata.endpoint, data=params)
        r4fttext = r4ft.text

    except Exception as e:
        logger.warning(e, "log Error writing")

    lag = re.match(r".*Waiting for [^ ]*: (\d+\.*\d*) seconds.*", r4fttext)

    if not lag:
        return 0

    result = int(float(lag.group(1)))

    return result


def find_lag(err) -> None:

    lagese = int(err.get("lag", "0"))

    if lagese != FFa_lag[1]:
        FFa_lag[1] = lagese
        logger.debug(f"<<lightpurple>> max lag: sleep for {FFa_lag[1]} secound.")
    else:
        logger.debug(f"<<lightpurple>> lagese == FFa_lag[1] ({FFa_lag[1]})")

    logger.debug(f"<<lightred>> max lag: sleep for {lagese+1} secound.")

    time.sleep(FFa_lag[1] + 1)


def make_sleep_def():

    frr = int(time.time() - Find_Lag[2])

    if Find_Lag_o[1] or frr > 119:

        Find_Lag_o[1] = False

        Find_Lag[3] += 1
        Find_Lag[2] = time.time()

        lag = post_request_for_lag()

        if lag != 0:
            FFa_lag[1] = int(float(lag))
            logger.debug(f"<<lightpurple>> bot.py {Find_Lag[3]} find lag:{float(lag)}, frr:{frr}")

    fain = 0

    if FFa_lag[1] != FFa_lag[2]:

        fain = FFa_lag[1]

        logger.debug(f"<<lightpurple>> bot.py : {fain=}")

        FFa_lag[2] = FFa_lag[1]

        if FFa_lag[1] <= 1 or FFa_lag[1] <= 2:
            fain = 0

        elif FFa_lag[1] <= 3 or FFa_lag[1] <= 4:
            fain = 1

        elif FFa_lag[1] <= 5 or FFa_lag[1] <= 6:
            fain = 2

        elif FFa_lag[1] <= 7 or FFa_lag[1] <= 8:
            fain = 3

        elif FFa_lag[1] <= 9 or FFa_lag[1] <= 10:
            fain = 4

    if newsleep[1] != fain:
        logger.debug(f"change newsleep from {newsleep[1]} to {fain}, <<lightpurple>> max lag:{FFa_lag[1]}.")
        newsleep[1] = fain


def do_lag():
    GG = False

    numb = 0

    make_sleep_def()

    if FFa_lag[1] > 5:
        GG = True

    # while FFa_lag[1] > 5:
    while GG is True:
        numb += 1

        sleeptime = FFa_lag[1] * 2

        diff = int(time.time() - Find_Lag[2])

        logger.debug(f" lag = ({FFa_lag[1]}) > 5, {numb=}, {diff=}, {sleeptime=}")

        make_sleep_def()

        time.sleep(sleeptime)

        if FFa_lag[1] < 5:
            GG = False
        else:
            GG = False


def bad_lag(nowait):

    if settings.wikidata.test_mode:
        return False

    if nowait and FFa_lag[1] > 5:
        return True

    return False


__all__ = [
    "bad_lag",
    "do_lag",
]
