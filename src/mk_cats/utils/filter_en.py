""" """

import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

BBlcak = [
    "Disambiguation",
    "wikiproject",
    "sockpuppets",
    "without a source",
    "images for deletion",
]

blcak_starts = [
    "Clean-up",
    "Cleanup",
    "Uncategorized",
    "Unreferenced",
    "Unverifiable",
    "Unverified",
    "Wikipedia",
    "Wikipedia articles",
    "Articles about",
    "Articles containing",
    "Articles covered",
    "Articles lacking",
    "Articles needing",
    "Articles prone",
    "Articles requiring",
    "Articles slanted",
    "Articles sourced",
    "Articles tagged",
    "Articles that",
    "Articles to",
    "Articles with",
    "use ",
    "User pages",
    "Userspace",
]


@lru_cache(maxsize=128)
def filter_cat(cat):
    for x in BBlcak:
        if cat.lower().find(x) != -1:
            logger.debug(f"<<lightred>> find ({x}) in cat")
            return False

    cat2 = cat.lower().replace("category:", "")

    for x in blcak_starts:
        if cat2.startswith(x.lower()):
            logger.debug(f"<<lightred>> cat.startswith({x})")
            return False

    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    for x in months:
        # match the end of cat like month \d+
        matt = rf"^.*? from {x.lower()} \d+$"
        if re.match(matt, cat2):
            logger.debug(f"<<lightred>> cat.match({matt})")
            return False

    return True
