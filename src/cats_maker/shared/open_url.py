#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)
_session = requests.Session()
_session.headers.update({"User-Agent": "Himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"})


class GetUrl:
    def __init__(self, url: str, timeout: int = 10) -> None:
        self.start = time.time()
        self.url = url
        self.html = ""
        self.session = _session
        self.timeout = timeout

    def open_it(self) -> str:
        if not self.url:
            logger.info('self.url == ""')
            return ""

        logger.debug(f"{self.url}")

        try:
            req = self.session.get(self.url, timeout=self.timeout)

            if 500 <= req.status_code < 600:
                logger.info(f"received {req.status_code} status from {req.url}")
                self.html = ""
            else:
                self.html = req.text

        except requests.exceptions.ReadTimeout:
            logger.info(f"ReadTimeout: {self.url}")

        except Exception:
            logger.exception("Exception:", exc_info=True)

        return self.html


def geturl(url: str, maxsleeps: int = 0) -> str:
    bot = GetUrl(url)
    return bot.open_it()


def open_the_url(url: str, maxsleeps: int = 0) -> str:
    bot = GetUrl(url)
    return bot.open_it()


def open_json_url(url: str, maxsleeps: int = 0, **kwargs) -> Any:
    bot = GetUrl(url)
    js_text = bot.open_it()
    try:
        return json.loads(js_text)
    except Exception:
        return {}


__all__ = [
    "GetUrl",
    "geturl",
    "open_the_url",
    "open_json_url",
]
