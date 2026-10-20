#!/usr/bin/python3
"""

# from .groups_bots.edit_groups import build_editgroups_summary

"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

Dir = Path(__file__).parent

# get the code from json file
file = Dir / "editgroups.json"

main_keys = {
    "newitems",
    "setsitelink",
    "catelabels",
    "wbremovereferences",
    "wbsetreference",
    "others",
}


def read_it() -> dict:
    data = {}

    logger.debug("editgroups read_it:")

    try:
        with open(file, encoding="utf-8") as f:
            data = json.loads(f.read())
    except BaseException:
        logger.info(f"{file} error")

    return data


def dump_it(data) -> None:
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    except BaseException:
        logger.info(f"{file} error")


def make_new_data() -> dict[str, str]:

    logger.debug("editgroup data:")

    data = {}

    for k in main_keys:
        new_str = f"{random.randrange(0, 2**48):x}"
        data[k] = new_str

    dump_it(data)

    return data


def load_from_file() -> dict:

    try:
        # get file change date
        file_date = os.path.getmtime(file)
        file_date = datetime.fromtimestamp(file_date).strftime("%Y-%b-%d")

        todaydate = datetime.now().strftime("%Y-%b-%d")
        # date_after_7 = (datetime.now() + timedelta(days=8)).strftime("%Y-%b-%d")

        # if the diff date > 1 week then return {}
        diff = (datetime.strptime(todaydate, "%Y-%b-%d") - datetime.strptime(file_date, "%Y-%b-%d")).days

        logger.debug(f"{file} diff:{diff}")

        if diff > 7:
            return {}
    except Exception:
        logger.info("<<lightred>> File not found, creating new list.")

    return read_it()


def get_tage_table() -> dict[str, str]:
    if not file.exists():
        return make_new_data()

    data = load_from_file()
    if not data:
        data = make_new_data()

    return data


def generate_edit_group_link(tags_table: dict[str, str]) -> str:
    fafo_rand = tags_table.get("others") or f"{random.randrange(0, 2**48):x}"
    return f"([[:toollabs:editgroups/b/CB/{fafo_rand}|details]])"


def build_editgroups_summary(username: str, data, editgroups, tage) -> str:

    tage_table_for_bot = get_tage_table()

    excluded_actions = [
        "wbsearchentities",
        "edit",
    ]

    if editgroups:
        return f"([[:toollabs:editgroups/b/CB/{editgroups}|details]])"

    action = data.get("action") or ""
    if username.find("bot") != -1:
        if action not in excluded_actions and not action.startswith("wbget"):
            if tage and tage in tage_table_for_bot:
                return f"([[:toollabs:editgroups/b/CB/{tage_table_for_bot[tage]}|details]])"

    elif "editgroups" in sys.argv:
        return generate_edit_group_link(tage_table_for_bot)

    return ""


__all__ = [
    "read_it",
    "dump_it",
    "make_new_data",
    "load_from_file",
    "build_editgroups_summary",
]
