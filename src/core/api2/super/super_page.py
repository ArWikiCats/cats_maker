""" """

import logging
from copy import deepcopy
from dataclasses import dataclass

from ....config import settings
from ..api_utils import ASK_BOT, bot_May_Edit, change_codes
from .handel_errors import HandleErrors
from .models import (
    CategoriesData,
    Content,
    LinksData,
    Meta,
    RevisionsData,
    TemplateData,
)
from .super_login import Login

logger = logging.getLogger(__name__)


def find_edit_error(old: str, new: str) -> bool:
    conversion_phrases = ["#تحويل [["]
    for phrase in conversion_phrases:
        if phrase in old and phrase not in new:
            print(f"ar_err.py found ({phrase}) in old but not in new. return True")
            return True
    return False


class MainPage:
    def __init__(
        self,
        login_bot: Login,
        title: str,
        lang: str,
        family: str = "wikipedia",
    ) -> None:
        self.login_bot = login_bot
        self.user_login = login_bot.user_login
        self.title = title
        self.lang = change_codes.get(lang) or lang
        self.family = family
        self.endpoint = f"https://{self.lang}.{self.family}.org/w/api.php"
        self.text: str = ""
        self.newtext: str = ""
        self.ns: int | bool = False
        self.langlinks: dict = {}

        self.meta = Meta()
        self.content = Content()
        self.revisions_data = RevisionsData()
        self.links_data = LinksData()
        self.categories_data = CategoriesData()
        self.template_data = TemplateData()

        self.user: str = ""
        self._ask_bot = ASK_BOT()
        self._error_handler = HandleErrors()

    def false_edit(self) -> bool:
        if self.ns is False or self.ns != 0:
            return False
        if settings.bot.no_fa:
            return False
        if not self.text:
            self.text = self.get_text()
        if len(self.newtext) < 0.1 * len(self.text):
            text_err = f"Edit will remove 90% of the text. {len(self.newtext)} < 0.1 * {len(self.text)}"
            text_err += f"title: {self.title}, summary: {self.content.summary}"
            logger.warning("", text=text_err)
            return True
        if self.lang == "ar" and self.ns == 0:
            if find_edit_error(self.text, self.newtext):
                return True
        return False

    def find_create_data(self) -> dict:
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": self.title,
            "rvprop": "timestamp|ids|user",
            "rvslots": "*",
            "rvlimit": "1",
            "rvdir": "newer",
        }
        data = self.login_bot.post_params(params)
        pages = data.get("query", {}).get("pages", {})
        for _, v in pages.items():
            page_data = v.get("revisions", [{}])[0]
            if "parentid" in page_data and page_data["parentid"] == 0:
                self.meta.create_data = {
                    "timestamp": page_data["timestamp"],
                    "user": page_data.get("user", ""),
                    "anon": page_data.get("anon", False),
                }
            break
        return self.meta.create_data

    def get_text(self, redirects: bool = False) -> str:
        params = {
            "action": "query",
            "prop": "revisions|pageprops|flagged",
            "titles": self.title,
            "ppprop": "wikibase_item",
            "rvprop": "timestamp|content|user|ids",
            "rvslots": "*",
        }
        if redirects:
            params["redirects"] = 1
        data = self.login_bot.post_params(params)
        pages = data.get("query", {}).get("pages", {})

        for k, v in pages.items():
            if "ns" in v:
                self.ns = v["ns"]
            if "missing" in v or k == "-1":
                self.meta.Exists = False
            else:
                self.meta.Exists = True

            pageprops = v.get("pageprops", {})
            self.meta.wikibase_item = pageprops.get("wikibase_item") or self.meta.wikibase_item
            self.meta.flagged = v.get("flagged", False) is not False

            self.revisions_data.pageid = v.get("pageid") or self.revisions_data.pageid

            page_data = v.get("revisions", [{}])[0]
            self.text = page_data.get("slots", {}).get("main", {}).get("*", "")
            self.user = page_data.get("user") or self.user
            self.revisions_data.revid = page_data.get("revid") or self.revisions_data.revid
            self.revisions_data.timestamp = page_data.get("timestamp") or self.revisions_data.timestamp

            if "parentid" in page_data and page_data["parentid"] == 0:
                self.meta.create_data = {
                    "timestamp": page_data["timestamp"],
                    "user": page_data.get("user", ""),
                    "anon": page_data.get("anon", False),
                }
            break

        return self.text

    def get_qid(self) -> str:
        if not self.meta.wikibase_item:
            self.get_text()
        return self.meta.wikibase_item

    def _parse_categories(self, ta: dict) -> None:
        for cat in ta.get("categories", []):
            if "sortkey" in cat:
                del cat["sortkey"]
            tit = cat["title"]
            self.categories_data.all_categories_with_hidden[tit] = cat
            if cat.get("hidden") is True:
                self.categories_data.hidden_categories[tit] = cat
            else:
                del cat["hidden"]
                self.categories_data.categories[tit] = cat

    def _parse_langlinks(self, ta: dict) -> None:
        if ta.get("langlinks", []) != []:
            self.langlinks = {ll["lang"]: ll.get("*") or ll.get("title") for ll in ta.get("langlinks", [])}

    def _parse_templates(self, ta: dict) -> None:
        if ta.get("templates", []) != []:
            self.template_data.templates_API = [t["title"] for t in ta.get("templates", [])]

    def get_infos(self) -> None:
        params = {
            "action": "query",
            "titles": self.title,
            "prop": "categories|langlinks|templates|linkshere|iwlinks|info",
            "clprop": "sortkey|hidden",
            "cllimit": "max",
            "lllimit": "max",
            "tllimit": "max",
            "lhlimit": "max",
            "iwlimit": "max",
            "formatversion": "2",
            "tlnamespace": "10",
        }
        data = self.login_bot.post_params(params)
        ta = data.get("query", {}).get("pages", [{}])[0]

        if "ns" in ta:
            self.ns = ta["ns"]

        self.revisions_data.pageid = ta.get("pageid") or self.revisions_data.pageid
        self.content.length = ta.get("length") or self.content.length
        self.revisions_data.revid = ta.get("lastrevid") or self.revisions_data.revid
        self.revisions_data.touched = ta.get("touched") or self.revisions_data.touched

        self.meta.is_redirect = "redirect" in ta

        self._parse_categories(ta)
        self._parse_langlinks(ta)
        self._parse_templates(ta)

        self.links_data.links_here = ta.get("linkshere", [])
        self.links_data.iwlinks = ta.get("iwlinks", [])
        self.meta.info_loaded = True

    def get_redirect_target(self) -> str:
        params = {
            "action": "query",
            "titles": self.title,
            "prop": "info",
            "redirects": 1,
        }
        data = self.login_bot.post_params(params)
        redirects = data.get("query", {}).get("redirects", [{}])[0]
        return redirects.get("to", "")

    def get_extlinks(self) -> list:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extlinks",
            "titles": self.title,
            "formatversion": "2",
            "utf8": 1,
            "ellimit": "max",
        }
        links = []
        continue_params = {}
        d = 0

        while continue_params != {} or d == 0:
            d += 1
            if continue_params:
                params.update(continue_params)
            json1 = self.login_bot.post_params(params)
            continue_params = json1.get("continue", {})
            linkso = json1.get("query", {}).get("pages", [{}])[0].get("extlinks", [])
            links.extend(linkso)

        liste1 = sorted(set(x["url"] for x in links))
        self.links_data.extlinks = liste1
        return liste1

    def get_userinfo(self) -> dict:
        if not self.meta.userinfo:
            params = {
                "action": "query",
                "format": "json",
                "list": "users",
                "formatversion": "2",
                "usprop": "groups",
                "ususers": self.user,
            }
            data = self.login_bot.post_params(params)
            ff = data.get("query", {}).get("users", [{}])
            if ff:
                self.meta.userinfo = ff[0]
        return self.meta.userinfo

    def isRedirect(self) -> bool:
        if not self.meta.is_redirect:
            self.get_infos()
        return self.meta.is_redirect

    def isDisambiguation(self) -> bool:
        self.meta.is_Disambig = self.title.endswith("(توضيح)") or self.title.endswith("(disambiguation)")
        if self.meta.is_Disambig:
            logger.debug(f'<<lightred>> page "{self.title}" is Disambiguation / توضيح')
        return self.meta.is_Disambig

    def get_categories(self, with_hidden: bool = False) -> dict:
        if not self.meta.info_loaded:
            self.get_infos()
        if with_hidden:
            return self.categories_data.all_categories_with_hidden
        return self.categories_data.categories

    def get_hidden_categories(self) -> dict:
        if not self.categories_data.categories and not self.categories_data.hidden_categories:
            self.get_infos()
        return self.categories_data.hidden_categories

    def get_langlinks(self) -> dict:
        if not self.meta.info_loaded:
            self.get_infos()
        return self.langlinks

    def can_edit(self, script: str = "", delay: int = 0) -> bool:
        if self.family != "wikipedia":
            return True
        if not self.text:
            self.text = self.get_text()
        self.meta.can_be_edit = bot_May_Edit(
            text=self.text, title_page=self.title, botjob=script, page=self, delay=delay
        )
        return self.meta.can_be_edit

    def get_create_data(self) -> dict:
        if not self.meta.create_data:
            self.find_create_data()
        return self.meta.create_data

    def get_timestamp(self) -> str:
        if not self.revisions_data.timestamp:
            self.get_text()
        return self.revisions_data.timestamp

    def exists(self) -> bool:
        if not self.meta.Exists:
            self.get_text()
        if not self.meta.Exists:
            logger.debug(f'page "{self.title}" not in {self.lang}:{self.family}')
        return bool(self.meta.Exists)

    def namespace(self) -> int | bool:
        if self.ns is False:
            self.get_text()
        return self.ns

    def save(
        self,
        newtext: str = "",
        summary: str = "",
        nocreate: int = 1,
        minor: str = "0",
        tags: str = "",
        nodiff: bool = False,
    ) -> bool:
        self.newtext = newtext
        if summary:
            self.content.summary = summary

        if self.false_edit():
            return False

        message = f"Do you want to save this page? ({self.lang}:{self.title})"
        user = self.meta.username or getattr(self, "user_login", "")

        if not self._ask_bot.ask_put(
            nodiff=nodiff,
            newtext=newtext,
            text=self.text,
            message=message,
            job="save",
            username=user,
            summary=self.content.summary,
        ):
            return False

        params: dict = {
            "action": "edit",
            "title": self.title,
            "text": newtext,
            "summary": self.content.summary,
            "minor": minor,
            "nocreate": nocreate,
        }

        if nocreate != 1:
            del params["nocreate"]

        if self.revisions_data.revid:
            params["baserevid"] = self.revisions_data.revid

        if tags:
            params["tags"] = tags

        pop = self.login_bot.post_params(params, addtoken=True)

        if not pop:
            return False

        error = pop.get("error", {})
        edit = pop.get("edit", {})
        result = edit.get("result", "")

        if result.lower() == "success":
            self.text = newtext
            self.user = ""
            logger.warning(f"<<lightgreen>> ** true .. [[{self.lang}:{self.family}:{self.title}]] ")

            self.revisions_data.pageid = edit.get("pageid") or self.revisions_data.pageid
            self.revisions_data.revid = edit.get("newrevid") or self.revisions_data.revid
            self.revisions_data.newrevid = edit.get("newrevid") or self.revisions_data.newrevid
            self.revisions_data.touched = edit.get("touched") or self.revisions_data.touched
            self.revisions_data.timestamp = edit.get("newtimestamp") or self.revisions_data.timestamp

            return True

        if error != {}:
            print(pop)
            return self._error_handler.handle_err(error, function="Save", params=params)

        return False

    def Create(self, text: str = "", summary: str = "", nodiff: str = "", noask: bool = False) -> bool:
        self.newtext = text

        if not noask:
            message = f"Do you want to create this page? ({self.lang}:{self.title})"
            user = self.meta.username or getattr(self, "user_login", "")
            if not self._ask_bot.ask_put(
                nodiff=nodiff, newtext=text, message=message, job="create", username=user, summary=summary
            ):
                return False

        params = {
            "action": "edit",
            "title": self.title,
            "text": text,
            "summary": summary,
            "notminor": 1,
            "createonly": 1,
        }

        pop = self.login_bot.post_params(params, addtoken=True)

        if not pop:
            return False

        error = pop.get("error", {})
        edit = pop.get("edit", {})
        result = edit.get("result", "")

        if result.lower() == "success":
            self.text = text
            logger.warning(f"<<lightgreen>> ** true .. [[{self.lang}:{self.family}:{self.title}]] ")

            self.revisions_data.pageid = edit.get("pageid") or self.revisions_data.pageid
            self.revisions_data.revid = edit.get("newrevid") or self.revisions_data.revid
            self.revisions_data.touched = edit.get("touched") or self.revisions_data.touched
            self.revisions_data.newrevid = edit.get("newrevid") or self.revisions_data.newrevid
            self.revisions_data.timestamp = edit.get("newtimestamp") or self.revisions_data.timestamp

            return True

        if error != {}:
            print(pop)
            return self._error_handler.handle_err(error, function="Create", params=params)

        return False

    def post_continue(self, params: dict, action: str) -> list:
        logger.debug("_______________________")
        logger.debug(f", start. {action=}, links")

        Max = 500000
        results = []
        continue_params = {}
        d = 0

        while continue_params != {} or d == 0:
            params2 = deepcopy(params)
            d += 1

            if continue_params:
                for k, v in continue_params.items():
                    params2[k] = v

            json1 = self.login_bot.post_params(params2)

            if not json1:
                logger.debug(", json1 is empty. break")
                break

            continue_params = json1.get("continue", {})
            data = json1.get(action, {}).get("links", [])

            if not data:
                logger.debug("post continue, data is empty. break")
                break

            if Max <= len(results) and len(results) > 1:
                logger.debug(f"post continue, {Max=} <= {len(results)=}. break")
                break

            results.extend(data)

        logger.debug(f"post continue, {len(results)=}")
        return results

    def page_links(self) -> list:
        params = {
            "action": "parse",
            "prop": "links",
            "formatversion": "2",
            "page": self.title,
        }
        data = self.post_continue(params, "parse")
        self.links_data.links2 = data
        return self.links_data.links2


__all__ = [
    "MainPage",
]
