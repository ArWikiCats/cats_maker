""" """

import logging
import time
from functools import lru_cache

from ....config import settings
from .bot import CategoryDepth

logger = logging.getLogger(__name__)

SITECODE = "en"
FAMILY = "wikipedia"


@lru_cache(maxsize=256)
def title_process(title, sitecode):
    # ---
    prefixes = {"ar": "تصنيف:", "en": "Category:", "www": "Category:"}
    # ---
    start_prefixes = prefixes.get(sitecode)
    # ---
    if start_prefixes and not title.startswith(start_prefixes):
        title = start_prefixes + title
    # ---
    return title


def args_group(title, kwargs):
    # ---
    args2 = {
        "title": title,
        "depth": None,
        "ns": None,
        "nslist": None,
        "onlyns": None,
        "without_lang": None,
        "with_lang": None,
        "tempyes": None,
        "props": None,
        "only_titles": None,
    }
    # ---
    for k, v in kwargs.items():
        if k not in args2 or args2[k] is None:
            args2[k] = v
    # ---
    return args2


def subcatquery(login_bot, title, sitecode=SITECODE, family=FAMILY, **kwargs):
    # ---
    print_s = kwargs.get("print_s", True)
    # ---
    get_revids = kwargs.get("get_revids", False)
    # ---
    title = title_process(title, sitecode)
    # ---
    args2 = args_group(title, kwargs)
    # ---
    if print_s:
        logger.debug(
            f"<<lightyellow>> catdepth_new.py sub cat query for {sitecode}:{title}, depth:{args2['depth']}, ns:{args2['ns']}, onlyns:{args2['onlyns']}"
        )
    # ---
    start = time.perf_counter()
    # ---
    bot = CategoryDepth(login_bot, title, **kwargs)
    # ---
    result = bot.subcatquery_()
    # ---
    if get_revids:
        result = bot.get_revids()
    # ---
    delta = time.perf_counter() - start
    # ---
    if print_s:
        lenpages = bot.get_len_pages()
        # ---
        logger.debug(
            f"<<lightblue>>catdepth_new.py: find {len(result)} pages({args2['ns']}) in {sitecode}:{title}, depth:{args2['depth']} in {delta:.2f} seconds | {lenpages=}"
        )
    # ---
    return result
