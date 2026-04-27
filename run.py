""" """

import json
import logging
import os
import sys
from pathlib import Path

import requests

from src.config import settings
from src.mk_cats import create_categories_from_list

logger = logging.getLogger(__name__)

# Optional external integration - configure via environment variable
new_all = None
external_path = os.getenv("CATS_MAKER_EXTERNAL_PATH", "D:/categories_bot/make2_new")
if external_path and Path(external_path).exists():
    sys.path.append(external_path)

try:
    from new_all import work_bot as new_all  # type: ignore
except ImportError:
    logger.warning("Failed to import new_all")
    new_all = None

# Enable ask mode by default - now done via settings
settings.bot.ask = True
settings.debug = True

# base_logger.setLevel("ERROR")
logger.setLevel("DEBUG" if settings.debug else "INFO")

new_all_tab = {1: False}


def new_all_work_on_title(title, **Kwargs):
    if new_all:
        new_all.work_on_title(title=title, dont_create=True, **Kwargs)


def get_url_result(url):
    headers = {"User-Agent": "Himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"}
    try:
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return ""


def get_result(num):
    url = f"https://quarry.wmcloud.org/run/{str(num)}/output/0/json"

    result = get_url_result(url)

    rows = []

    try:
        jsons = json.loads(result)
        rows = jsons["rows"]
    except json.decoder.JSONDecodeError:
        logging.warning(f" json.decoder.JSONDecodeError url {url}")

    return rows


def get_quarry_result(number, get_rows=None):
    logger.info(f"Get quarry result from number: {number}")

    results = get_result(number)

    if get_rows == 1:
        return [x[0] for x in results]

    if get_rows == 2:
        return {x[0]: x[1] for x in results}

    return results


def main():
    categories_list = []

    for arg in sys.argv:
        argn, _, value = arg.partition(":")

        if argn.startswith("-"):
            argn = argn[1:]

        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:357357
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:231528
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:299753
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:475921
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:320152
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 quarry:300040
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 encat:Department_stores_of_the_United_States
        # python3 core8/pwb.py I:/core/bots/cats_maker_new/run.py -depth:5 encat:1988_war_films

        if argn == "quarry":
            List = get_quarry_result(value)
            for cat in List:
                categories_list.append(cat)
            logger.info(f"Add {len(List)} cat from get_quarry_result to categories_list.")

        elif argn == "encat":
            categories_list.append(value)

    categories_list = [f"Category:{x}" if not x.startswith("Category:") else x for x in categories_list]
    if categories_list:
        logger.info(f"categories_list work with {len(categories_list)} cats.")
        create_categories_from_list(categories_list, callback=new_all_work_on_title)


if __name__ == "__main__":
    main()
