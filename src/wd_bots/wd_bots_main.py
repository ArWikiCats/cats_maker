#!/usr/bin/python3
"""
!
"""
import functools
import json
import logging
import re
import time

from ..config import settings
from ..new_api.pagenew import password, username
from ..new_api.super.super_login import Login
from .utils import lag_bot
from .utils.out_json import outbot_json

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


class WD_API:
    def __init__(self, login_bot, Mr_or_bot="bot"):
        # ---
        self.login_bot = login_bot
        # ---
        self.lang = "test" if settings.wikidata.test_mode else "www"
        self.family = "wikidata"
        # ---
        self.usernamex = self.login_bot.user_login
        # ---
        logger.warning(f"<<lightgreen>> WD_API: {Mr_or_bot}, {self.usernamex=} \n")

    def handle_err_wd(self, error: dict, function: str = "", params: dict = None):
        """Handle errors related to the specified function.

        This method processes an error dictionary returned from an API call,
        extracting relevant error codes and information. It outputs error
        messages based on the error code and may modify the provided parameters.
        The function handles specific error codes such as 'abusefilter-
        disallowed', 'no-such-entity', 'protectedpage', 'articleexists', and
        'maxlag', providing appropriate responses for each case.

        Args:
            error (dict): A dictionary containing error information from the API.
            function (str?): The name of the function that encountered the error.
                Defaults to an empty string.
            params (dict?): A dictionary of parameters that may be modified
                based on the error. Defaults to None.

        Returns:
            Union[str, bool]: Returns a string indicating the error type for specific
                errors or False for others.

        Raises:
            Exception: If the 'raise' argument is present in the command line arguments,
                an exception is raised with the error information.
        """

        # ---
        # {'error': {'code': 'articleexists', 'info': 'The article you tried to create has been created already.', '*': 'See https://ar.wikipedia.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.'}, 'servedby': 'mw1425'}
        # ---
        err_code = error.get("code", "")
        err_info = error.get("info", "")
        # ---
        tt = f"<<lightred>>{function} ERROR: <<defaut>>code:{err_code}."
        logger.debug(tt)
        # ---["protectedpage", 'تأخير البوتات 3 ساعات', False]
        if err_code == "abusefilter-disallowed":
            # ---
            # oioioi = {'error': {'code': 'abusefilter-disallowed', 'info': 'This', 'abusefilter': {'id': '169', 'description': 'تأخير البوتات 3 ساعات', 'actions': ['disallow']}, '*': 'See https'}, 'servedby': 'mw1374'}
            # ---
            abusefilter = error.get("abusefilter", "")
            description = abusefilter.get("description", "")
            logger.debug(f"<<lightred>> ** abusefilter-disallowed: {description} ")
            if description in [
                "تأخير البوتات 3 ساعات",
                "تأخير البوتات 3 ساعات- 3 من 3",
                "تأخير البوتات 3 ساعات- 1 من 3",
                "تأخير البوتات 3 ساعات- 2 من 3",
            ]:
                return False
            return description
        # ---
        if err_code == "no-such-entity":
            logger.debug("<<lightred>> ** no-such-entity. ")
            return False
        # ---
        if err_code == "protectedpage":
            logger.debug("<<lightred>> ** protectedpage. ")
            # return "protectedpage"
            return False
        # ---
        if err_code == "articleexists":
            logger.debug("<<lightred>> ** article already created. ")
            return "articleexists"
        # ---
        if err_code == "maxlag":
            logger.debug("<<lightred>> ** maxlag. ")
            return False
        # ---
        params["data"] = {}
        logger.debug(f"<<lightred>>{function} ERROR: <<defaut>>info: {err_info}, {params=}")

    def post_params(self, params, Type="get", addtoken=False, GET_CSRF=True, files=None, do_error=False, max_retry=0):
        # ---
        return self.login_bot.post_params(
            params, Type=Type, addtoken=addtoken, GET_CSRF=GET_CSRF, files=files, do_error=do_error, max_retry=max_retry
        )

    def post_continue(
        self, params, action, _p_="pages", p_empty=None, Max=500000, first=False, _p_2="", _p_2_empty=None
    ):
        return self.login_bot.post_continue(
            params, action, _p_=_p_, p_empty=p_empty, Max=Max, first=first, _p_2=_p_2, _p_2_empty=_p_2_empty
        )

    def post_to_newapi(self, params={}, data={}, tage="", editgroups="", max_retry=0, **kwargs):
        # ---
        if not params and data:
            params = data
        # ---
        params = self.filter_data(params, tage=tage, editgroups=editgroups)
        # ---
        results = self.post_params(params, do_error=False)
        # ---
        if results.get("servedby"):
            results["servedby"] = ""
        # ---
        error = results.get("error", {})
        error_code = error.get("code", "")
        # ---
        if error_code == "maxlag" and max_retry < 4:
            self.lag_work(error)
            # ---
            logger.debug(f"<<purple>>: <<red>> lag work: {max_retry=}")
            # ---
            return self.post_to_newapi(params=params, tage=tage, editgroups=editgroups, max_retry=max_retry + 1)
        # ---
        if error:
            # ---
            er = self.handle_err_wd(error, function="", params=params)
            # ---
            logger.debug(f"<<purple>>: <<red>> handle_err_wd: {er}")
            # return er
        # ---
        success = results.get("success", 0)
        # ---
        if success == 1:
            # ---
            # {"entity":{"sitelinks":{"arwiki":{}},"id":"Q97928551","type":"item","lastrevid":1242627521,"nochange":""},"success":1}
            # ---
            if lag_bot.newsleep[1] != 0:
                logger.warning(f"<<lightgreen>> ** true. sleep({lag_bot.newsleep[1]})")
                time.sleep(lag_bot.newsleep[1])
            else:
                logger.debug("<<lightgreen>> ** true.")
            # return True
        # ---
        return results

    def filter_data(self, data, editgroups, tage):
        # ---
        lag_bot.do_lag()
        # ---
        if "maxlag" not in data:
            data["maxlag"] = lag_bot.FFa_lag[1] + 1
        # ---
        data["format"] = "json"
        data["utf8"] = 1
        # ---
        if "summary" in data:
            if self.usernamex.find("bot") == -1:
                del data["summary"]
        # ---
        data.setdefault("formatversion", 1)
        # ---
        return data

    def lag_work(self, err):
        # ---
        _ixix = {
            "error": {
                "code": "maxlag",
                "info": "Waiting for wdqs1006: 3.2333333333333 seconds lagged.",
                "host": "wdqs1006",
                "lag": 3.333333333333334,
                "type": "wikibase-queryservice",
                "queryserviceLag": 194,
            },
            "servedby": "",
        }
        # ---
        lag_bot.find_lag(err)
        # ---
        return "reagain"

    def _pages_with_prop(self, post_continue, pwppropname="unlinkedwikibase_id", pwplimit=None, Max=None):
        # ---
        params = {
            "action": "query",
            "format": "json",
            "list": "pageswithprop",
            "utf8": 1,
            "formatversion": "2",
            "pwplimit": "max",
            "pwppropname": "unlinkedwikibase_id",
            "pwpprop": "title|value",
        }
        # ---
        if pwplimit and pwplimit.isdigit():
            params["pwplimit"] = pwplimit
        # ---
        if pwppropname != "":
            params["pwppropname"] = pwppropname
        # ---
        results = post_continue(params, "query", _p_="pageswithprop", p_empty=[], Max=Max)
        # ---
        logger.debug(f"pageswithprop len(results) = {len(results)}")
        # ---
        return results

    def format_labels_descriptions(self, labels):
        return {x["language"]: x["value"] for _, x in labels.items()}


class NewHimoAPIBot:
    def __init__(self, Mr_or_bot="bot", www="www"):
        # ---
        self.login_bot = log_in_wikidata(www=www)
        # ---
        self.wdapi_new = WD_API(self.login_bot, Mr_or_bot=Mr_or_bot)
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
