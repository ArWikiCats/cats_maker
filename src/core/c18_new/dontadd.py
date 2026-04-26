#!/usr/bin/python3
""" """

import functools
import json
import logging
import os
import stat
from datetime import datetime
from pathlib import Path

from ...config import settings
from ..api_sql import GET_SQL, sql_new_title_ns

logger = logging.getLogger(__name__)

Dir = Path(__file__).parent.parent.parent
filename_json = Dir / "textfiles/Dont_add_to_pages.json"

filename_json.parent.mkdir(parents=True, exist_ok=True)

statgroup = stat.S_IRWXU | stat.S_IRWXG


def load_json(filename, empty_data="list"):
    data = {} if empty_data == "dict" else []

    if settings.category.test_mode:
        logger.debug(f"temps_params.py, jsonfile: {filename}")

    if not os.path.isfile(filename):
        logger.warning(f"File not found: {filename}")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.chmod(filename, statgroup)
        except Exception as e:
            logger.warning(e)

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(e)

    return data


def log_to_file(data, filename):
    delete = False

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            logger.info(f"<<green>> wrote to {filename}")
    except PermissionError:
        logger.error(f"<<red>> PermissionError writing to {filename}")
        delete = True
    except Exception as e:
        logger.warning(f"<<red>> Error writing to {filename}: {e}")

    if delete:
        try:
            os.remove(filename)

            logger.info(f"<<lightgreen>> deleted {filename}")

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f)
                logger.info(f"<<green>> wrote to {filename}")

            os.chmod(filename, statgroup)
        except Exception as e:
            logger.warning(f"<<red>> Error deleting/writing to {filename}: {e}")


def from_sql():
    queries = """select page_title, page_namespace
        from page, templatelinks, linktarget
        where page_id = tl_from
        and page_namespace in (0, 10)
        and tl_target_id = lt_id
        and lt_namespace = 10
        and lt_title = "لا_للتصنيف_المعادل"
        ;"""

    cats = []

    if GET_SQL():
        cats = sql_new_title_ns(queries, wiki="ar", t1="page_title", t2="page_namespace")

    return cats


def get_pages_nocat():
    data = {}

    if settings.category.no_dontadd or settings.category.test_mode:
        return data

    if not settings.category.test_add:
        if str(Dir).find("/data/project/") == -1 and str(Dir).find("/mnt/") == -1:
            logger.info("dont get dontadd list in local server")
            return data

    # logger.info("makenew to Dont_add_to_pages...")

    encats = from_sql()

    data = encats

    if not data:
        logger.info("Dont_add_to_pages is empty")
        return data

    logger.info(f"len Dont_add_to_pages : {len(data)}")

    log_to_file(data, filename_json)

    return data


@functools.lru_cache(maxsize=1)
def Dont_add_to_pages_def():
    data = load_json(filename_json)
    date = ""

    if filename_json.exists():
        # Get the time of last modification
        last_modified_time = os.path.getmtime(filename_json)

        date = datetime.fromtimestamp(last_modified_time).strftime("%Y-%m-%d")

    today = datetime.today().strftime("%Y-%m-%d")

    if date != today or not data:
        logger.info(f"<<purple>> last modified: {date} , today: {today}, len: {len(data)} ")
        data = get_pages_nocat()

    return data
