# -*- coding: utf-8 -*-

import os
from functools import lru_cache
from .ask_bot import ASK_BOT
from .botEdit import bot_May_Edit

change_codes = {
    "bat_smg": "bat-smg",
    "be-x-old": "be-tarask",
    "be_x_old": "be-tarask",
    "cbk_zam": "cbk-zam",
    "fiu_vro": "fiu-vro",
    "map_bms": "map-bms",
    "nb": "no",
    "nds_nl": "nds-nl",
    "roa_rup": "roa-rup",
    "zh_classical": "zh-classical",
    "zh_min_nan": "zh-min-nan",
    "zh_yue": "zh-yue",
}


@lru_cache(maxsize=1)
def default_user_agent():
    tool = os.getenv("HOME")
    tool = tool.split("/")[-1] if tool else "himo"
    # ---
    li = f"{tool} bot/1.0 (https://{tool}.toolforge.org/; tools.{tool}@toolforge.org)"
    # ---
    # logger.debug(f": {li}")
    # ---
    return li


__all__ = [
    "ASK_BOT",
    "change_codes",
    "default_user_agent",
    "bot_May_Edit",
]
