#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging

from .open_url import open_the_url

logger = logging.getLogger(__name__)


def get_result(num: int) -> list:
    url = f"https://quarry.wmcloud.org/run/{str(num)}/output/0/json"

    result = open_the_url(url)

    rows: list = []

    try:
        jsons = json.loads(result)
        rows = jsons["rows"]
    except json.decoder.JSONDecodeError:
        logger.info(f" json.decoder.JSONDecodeError url {url}")

    return rows


def get_quarry_results(number: int, get_rows=None) -> list | dict:

    results = get_result(number)

    if get_rows == 1:
        return [x[0] for x in results]

    if get_rows == 2:
        return {x[0]: x[1] for x in results}

    return results


__all__ = [
    "get_result",
    "get_quarry_results",
]
