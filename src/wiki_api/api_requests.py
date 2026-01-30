#!/usr/bin/python3
""" """
import functools
import logging
from urllib.parse import urlencode

import requests

from ..config import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _load_session() -> requests.Session:
    Session = requests.Session()
    Session.headers.update({"User-Agent": settings.wikipedia.user_agent})
    return Session


def submitAPI(params, Code, family, printurl=False, **kwargs):
    # ---
    if Code.endswith("wiki"):
        Code = Code[:-4]
    # ---
    params["formatversion"] = 1
    params["utf8"] = 1
    params["format"] = "json"
    # ---
    if params.get("titles"):
        titles = params["titles"]
        if isinstance(titles, list):
            params["titles"] = "|".join(titles)
    # ---
    # himo API
    if family == "commons":
        family = "wikimedia"
    # ---
    mainurl = f"https://{Code}.{family}.org/w/api.php?"
    # ---
    encode_params = urlencode(params)
    # ---
    url = f"https://{Code}.{family}.org/w/api.php?{encode_params}"
    # ---
    url2 = url.replace("&format=json", "").replace("?format=json", "?")
    logger.debug(f"printboturl: {url2}")
    # ---
    Session = _load_session()
    # ---
    json1 = {}
    try:
        r22 = Session.post(mainurl, data=params, timeout=settings.wikipedia.default_timeout)

    except requests.exceptions.ReadTimeout:
        logger.debug(f"ReadTimeout: {mainurl}")

    except Exception as e:
        logger.warning(f"<<red>> Error submitting to API: {e}")

    try:
        json1 = r22.json()
    except Exception as e:
        logger.warning(f"<<red>> Error parsing API response: {e}")

    return json1
