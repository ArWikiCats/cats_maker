""" """

import json
import logging
from typing import Any

import requests

from ....config import settings

logger = logging.getLogger(__name__)


class ParamsHelper:
    def __init__(self) -> None:
        self.lang = getattr(self, "lang", "")
        self.family = getattr(self, "family", "")
        self.username = getattr(self, "username", "")
        self.url_o_print = getattr(self, "url_o_print", "")

    def params_w(self, params: dict) -> dict:
        params = dict(params)
        if (
            self.family == "wikipedia"
            and self.lang == "ar"
            and params.get("summary")
            and self.username.find("bot") == -1
        ):
            params["summary"] = ""

        params["bot"] = 1

        if "minor" in params and params["minor"] == "":
            params["minor"] = 1

        if self.family != "toolforge":
            if (
                params["action"] in ["edit", "create", "upload", "delete", "move"]
                or params["action"].startswith("wb")
                or self.family == "wikidata"
            ):
                if not settings.bot.no_login and self.username:
                    params["assertuser"] = self.username

        return params

    def parse_data(self, req0: requests.Response | dict) -> dict:
        try:
            data = req0 if isinstance(req0, dict) else req0.json()

            if data.get("error", {}).get("*", "").find("mailing list") > -1:
                data["error"]["*"] = ""
            if data.get("servedby"):
                data["servedby"] = ""

            return data
        except Exception as e:
            logger.warning(f"<<red>> Error parsing response data: {e}")
            text = str(getattr(req0, "text", "").strip())

        valid_text = text.startswith("{") and text.endswith("}")

        if not text or not valid_text:
            return {}

        try:
            return json.loads(text)
        except Exception as e:
            logger.warning(e)

        return {}


__all__ = [
    "ParamsHelper",
]