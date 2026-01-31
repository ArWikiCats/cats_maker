#!/usr/bin/python3
"""
!
"""
import functools
import json
import logging
import re
from .utils import lag_bot
from .utils.out_json import outbot_json
from .wd_newapi_bot import WD_API
from ..new_api.pagenew import password, username
from ..new_api.super.super_login import Login

logger = logging.getLogger(__name__)

User_tables_bot = {
    "username": username,
    "password": password,
}


@functools.lru_cache(maxsize=1)
def log_in_wikidata(www="www"):
    # ---
    username = User_tables_bot.get("username")
    # ---
    login_bot = Login(www, family="wikidata")
    # ---
    logger.debug(f"### <<purple>> make new bot for ({www}.wikidata.org|{username})")
    # ---
    login_bot.add_users({"wikidata": User_tables_bot}, lang=www)
    # ---
    return login_bot


class NewHimoAPIBot:
    def __init__(self, Mr_or_bot="bot", www="www"):
        # ---
        self.login_bot = log_in_wikidata(www=www)
        # ---
        self.wdapi_new = WD_API(self.login_bot, Mr_or_bot=Mr_or_bot)
        # ---
        self.get_rest_result = self.wdapi_new.get_rest_result
        # ---
        self.outbot_json = outbot_json
        self.session_post = self.wdapi_new.post_to_newapi

    def Sitelink_API(self, Qid, title, wiki, enlink="", ensite="", nowait=False, returnid=False, return_text=False):
        # ---
        if lag_bot.bad_lag(nowait):
            return ""
        # ---
        if not wiki.endswith("wiki") and wiki.find("wiki") == -1 and wiki.find("wiktionary") == -1:
            wiki = f"{wiki}wiki"
        # ---
        if enlink:
            logger.debug(f' **: enlink:"{ensite}:{enlink}" {wiki}:{title}')
        else:
            logger.debug(f' **: Qid:"{Qid}" {wiki}:{title}')
        # ---
        # save the edit
        # ---
        if Qid.strip() == "" and enlink == "":
            logger.debug(f'<<lightred>> **: False: Qid == "" {wiki}:{title}.')
            return False
        # ---
        paramse = {
            "action": "wbsetsitelink",
            "linktitle": title,
            "linksite": wiki,
        }
        # ---
        out = f'Added link to "{Qid}" [{wiki}]:"{title}"'
        # ---
        if Qid:
            paramse["id"] = Qid
        else:
            out = f'Added link to "{ensite}:{enlink}" [{wiki}]:"{title}"'
            paramse["title"] = enlink
            paramse["site"] = ensite
        # ---
        r4 = self.session_post(params=paramse, tage="setsitelink")
        # ---
        if not r4:
            return False
        # ---
        d = outbot_json(r4, fi=out, NoWait=nowait)
        # ---
        if d is True:
            logger.warning(f"<<lightgreen>> true {out}")
            if enlink and returnid:
                ido = re.match(r".*\"id\"\:\"(Q\d+)\".*", str(r4))
                if ido:
                    return ido.group(1)
            else:
                return True
        # ---
        if return_text:
            return str(r4)
        # ---
        if d == "warn":
            logger.warning(str(r4))
        # ---
        return d

    def Labels_API(
        self, Qid, label, lang, ret, Or_Alii=False, change_des=False, number=0, nowait=False, tage="", remove=False
    ):
        # ---
        if lag_bot.bad_lag(nowait):
            return ""
        # ---
        if not Qid:
            logger.debug(" Qid == '' ")
            return False
        # ---
        if label == "" and not remove:
            logger.debug(" label == '' and remove = False ")
            return False
        # ---
        # save the edit
        out = f'{Qid} label:"{lang}"@{label}.'
        if number:
            out = f'{number} {Qid} label:"{lang}"@{label}.'
        r4 = self.session_post(
            params={
                "action": "wbsetlabel",
                "id": Qid,
                "language": lang,
                "value": label,
            },
            tage=tage,
        )
        # ---
        if not r4:
            logger.debug(" r4 == {} ")
            return False
        # ---
        text = str(r4)
        if ("using the same description text" in text) and ("associated with language code" in text):
            item2 = re.search(r"(Q\d+)", str(r4["error"]["info"])).group(1)
            logger.debug(f"<<lightred>>API: same label item: {item2}")
            if change_des is True:
                self.find_des_and_replace(Qid, label, lang)
            elif Or_Alii is True:
                self.Alias_API(Qid, [label], lang, ret)
        if ret:
            return text
        # ---
        d = outbot_json(r4, fi=out, NoWait=nowait)
        # ---
        if d == "warn":
            logger.warning(str(r4))

    def New_API(self, data2, summary, RRE=0, returnid=False, nowait=False, tage=""):
        """Create a new item in the API with the provided data and summary.

        This function sends a request to create a new item in the API using the
        provided data and summary. It first checks for any lag issues and then
        processes the input data. If the request is successful, it handles the
        response accordingly. If the response indicates a need to retry, it
        calls another API function. The function can also return the ID of the
        newly created item if requested.

        Args:
            data2 (any): The data to be sent to the API for creating a new item.
            summary (str): A summary or description of the new item.
            RRE (int?): A retry counter for handling specific response cases. Defaults to 0.
            returnid (bool?): If True, returns the ID of the created item. Defaults to False.
            nowait (bool?): If True, indicates that the function should not wait for a response.
                Defaults to False.
            tage (str?): An optional tag for the request. Defaults to an empty string.

        Returns:
            str or bool: The response from the API as a string if successful,
                False if the request failed, or the ID of the created item if returnid
                is True.
        """
        # ---
        if lag_bot.bad_lag(nowait):
            return ""
        # ---
        data = json.JSONEncoder().encode(data2)
        # ---
        r4 = self.session_post(
            params={
                "action": "wbeditentity",
                "new": "item",
                "summary": summary,
                "data": data,
            },
            tage=tage,
        )
        # ---
        if not r4:
            return False
        # ---
        cf = outbot_json(r4, fi=summary, NoWait=nowait)
        if cf == "reagain" and RRE == 0:
            return self.New_API(data2, summary, RRE=1, returnid=returnid, nowait=nowait, tage=tage)
        # ---
        if cf == "warn":
            logger.warning(str(r4))
        # ---
        if returnid:
            Qid = False
            if cf is True:
                if "entity" in r4 and "id" in r4["entity"]:
                    Qid = r4["entity"]["id"]
                    logger.debug(f'<<lightgreen>> bot.py : returnid:"{Qid}" ')
            return Qid
        # ---
        return str(r4)


__all__ = [
    "NewHimoAPIBot",
]
