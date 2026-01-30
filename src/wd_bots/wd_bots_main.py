#!/usr/bin/python3
"""
!
"""
import json
import logging
import re

from ..config import settings
from .qs_bot import QS_line, QS_New_API
from .utils import lag_bot
from .utils.out_json import outbot_json, outbot_json_bot
from .wd_login_wrap import log_in_wikidata
from .wd_newapi_bot import WD_API

logger = logging.getLogger(__name__)

Main_User = {1: ""}
Save_2020_wd = {1: False}


def ask_put(s):
    yes_answer = ["y", "a", "", "Y", "A", "all", "aaa"]

    sa = input(s)
    if sa not in yes_answer:
        print(" bot: wrong answer")
        return False
    if sa == "a" or sa == "A":
        return "a"
    return True


class NewHimoAPIBot:
    def __init__(self, Mr_or_bot="bot", www="www"):
        # ---
        self.login_bot = log_in_wikidata(Mr_or_bot=Mr_or_bot, www=www)
        # ---
        self.wdapi_new = WD_API(self.login_bot, Mr_or_bot=Mr_or_bot)
        # ---
        self.get_rest_result = self.wdapi_new.get_rest_result
        # ---
        self.outbot_json_bot = outbot_json_bot
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
            logger.debug(f' **Sitelink_API: enlink:"{ensite}:{enlink}" {wiki}:{title}')
        else:
            logger.debug(f' **Sitelink_API: Qid:"{Qid}" {wiki}:{title}')
        # ---
        # save the edit
        # ---
        if Qid.strip() == "" and enlink == "":
            logger.debug(f'<<lightred>> **Sitelink_API: False: Qid == "" {wiki}:{title}.')
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
            logger.debug("Labels_API Qid == '' ")
            return False
        # ---
        if label == "" and not remove:
            logger.debug("Labels_API label == '' and remove = False ")
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
            logger.debug("Labels_API r4 == {} ")
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

    def Des_API(self, Qid, desc, lang, ask="", rea=True, nowait=False):
        """Set the description for a given item in a specified language.

        This function updates the description of an item identified by its Qid
        in the specified language. It checks for lag conditions and prompts the
        user for confirmation if certain conditions are met. If the description
        is empty, it logs an error message. The function also handles potential
        warnings and retries the operation if necessary.

        Args:
            Qid (str): The identifier of the item whose description is to be set.
            desc (str): The new description to be assigned to the item.
            lang (str): The language code in which the description is to be set.
            ask (str?): A flag to prompt the user for confirmation. Defaults to an empty string.
            rea (bool?): A flag indicating whether to retry the operation on failure. Defaults to
                True.
            nowait (bool?): A flag indicating whether to wait for a response. Defaults to False.

        Returns:
            bool: True if the description was successfully set, False otherwise.
        """

        # ---
        if lag_bot.bad_lag(nowait):
            return ""
        # ---
        if not desc.strip():
            logger.debug("<<red>> Des_API desc is empty.")
            return
        # ---
        # save the edit
        out = (
            f'def Des_API: {Qid} description:"{lang}"@{desc}, maxlag:{lag_bot.FFa_lag[1]}, sleep({lag_bot.newsleep[1]})'
        )
        # ---
        if not Save_2020_wd[1] and (ask is True or settings.bot.ask):
            # ---
            sa = ask_put(
                f'<<lightyellow>> bot.py Add desc:<<lightyellow>>"{lang}:{desc}"<<default>> for {Qid} Yes or No ? {Main_User[1]} '
            )
            if not sa:
                return False
            # ---
            if sa == "a":
                logger.debug("<<lightgreen>> ---------------------------------")
                logger.debug("<<lightgreen>> bot.py save all without asking.")
                logger.debug("<<lightgreen>> ---------------------------------")
                Save_2020_wd[1] = True
        # ---
        r4 = self.session_post(
            params={
                "action": "wbsetdescription",
                "id": Qid,
                "language": lang,
                "value": desc,
            }
        )
        # ---
        if not r4:
            return False
        # ---
        cf = outbot_json(r4, fi=out, NoWait=nowait)
        # ---
        if cf == "warn":
            logger.warning(str(r4))
        # ---
        if cf == "reagain":
            if rea:
                return self.Des_API(Qid, desc, lang, rea=False)
            elif settings.category.descqs:
                qsline = f'{Qid}|D{lang}|"{desc}"'
                QS_line(qsline, user="Mr.Ibrahembot")

    def New_Mult_Des_2(self, q, data2, summary, ret, ask=False, rea=True, nowait=False, tage="", return_result=False):
        # ---
        if lag_bot.bad_lag(nowait):
            return ""
        # ---
        logger.debug(f"<<lightblue>> bot.New_Mult_Des_2:q:{q}")
        # ---
        if not Save_2020_wd[1] and (ask is True or settings.bot.ask):
            logger.debug(f"<<lightyellow>> summary:{summary}")
            # ---
            sa = ask_put(
                f'<<lightyellow>> New_Mult_Des_2 "{q}" <<lightgreen>> (Yes or No ?)<<default>> ,{Main_User[1]} '
            )
            if not sa:
                return False
            # ---
            if sa == "a":
                logger.debug("<<lightgreen>> ---------------------------------")
                logger.debug("<<lightgreen>> bot.py save all without asking.")
                logger.debug("<<lightgreen>> ---------------------------------")
                Save_2020_wd[1] = True
        # ---
        if isinstance(data2, dict):
            data2 = json.JSONEncoder().encode(data2)
        # ---
        paramse = {
            "action": "wbeditentity",
            "id": q,
            "summary": summary,
            "data": str(data2),
        }
        # ---
        r4 = self.session_post(params=paramse, tage=tage)
        # ---
        summary2 = f"New_Mult_Des_2: {summary}"
        # ---
        if not r4:
            return False
        # ---
        cf = outbot_json(r4, fi=summary2, NoWait=nowait)
        # ---
        if cf == "warn":
            logger.warning(str(r4))
        # ---
        if cf is True:
            logger.warning(
                f"<<lightgreen>> ** true. lag_bot.newsleep[1].sleep({lag_bot.newsleep[1]}), maxlag:({lag_bot.FFa_lag[1]})"
            )
        else:
            # ---
            if cf == "reagain" and rea:
                return self.New_Mult_Des_2(
                    q, data2, summary, ret, rea=False, tage=tage, return_result=(return_result or ret)
                )
        # ---
        if ret or return_result:
            return str(r4)
        # ---
        return False

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
            return QS_New_API(data2)
        # ---
        if cf == "warn":
            logger.warning(str(r4))
        # ---
        if returnid:
            Qid = False
            if cf is True:
                if "entity" in r4 and "id" in r4["entity"]:
                    Qid = r4["entity"]["id"]
                    logger.debug(f'<<lightgreen>> bot.py New_API: returnid:"{Qid}" ')
            return Qid
        # ---
        return str(r4)


__all__ = [
    "NewHimoAPIBot",
]
