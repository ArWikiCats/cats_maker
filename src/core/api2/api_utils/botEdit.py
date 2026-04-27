""" """

import datetime
import logging
from functools import lru_cache

import wikitextparser as wtp

from ....config import settings

logger = logging.getLogger(__name__)

STOP_EDIT_TEMPLATES: dict[str, list[str]] = {
    "all": ["تحرر", "قيد التطوير", "يحرر", "تطوير مقالة"],
    "تعريب": ["لا للتعريب"],
    "تقييم آلي": ["لا للتقييم الآلي"],
    "reftitle": ["لا لعنونة مرجع غير معنون"],
    "fixref": ["لا لصيانة المراجع"],
    "cat": ["لا للتصنيف المعادل"],
    "stub": ["لا لتخصيص البذرة"],
    "tempcat": ["لا لإضافة صناديق تصفح معادلة"],
    "portal": ["لا لربط البوابات المعادل", "لا لصيانة البوابات"],
}

BOT_USERNAME = "Mr.Ibrahembot"


@lru_cache(maxsize=512)
def extract_templates_and_params(text: str) -> list[dict]:
    result = []
    parsed = wtp.parse(text)
    for template in parsed.templates:
        params = {}
        for param in getattr(template, "arguments"):
            value = str(param.value)
            key = str(param.name).strip()
            params[key] = value
        name = str(template.normal_name()).strip()
        result.append(
            {
                "name": f"قالب:{name}",
                "namestrip": name,
                "params": params,
                "item": template.string,
            }
        )
    return result


class BotEditChecker:
    __slots__ = ("_bot_cache", "_created_cache")

    def __init__(self) -> None:
        self._bot_cache: dict[str, dict[str, bool]] = {}
        self._created_cache: dict[str, bool] = {}

    def _handle_nobots_template(
        self, params: dict, title_page: str, botjob: str, _template: str
    ) -> bool:
        if not params:
            logger.debug(f"<<lightred>> botEdit.py: the page has temp:({_template}), botjob:{botjob} skipp.")
            self._bot_cache.setdefault(botjob, {})[title_page] = False
            return False
        elif params.get("1"):
            lst = [x.strip() for x in params.get("1", "").split(",")]
            if "all" in lst or BOT_USERNAME in lst:
                logger.debug(f"<<lightred>> botEdit.py: the page has temp:({_template}), botjob:{botjob} skipp.")
                self._bot_cache.setdefault(botjob, {})[title_page] = False
                return False
        self._bot_cache.setdefault(botjob, {})[title_page] = True
        return True

    def _handle_bots_template(
        self, params: dict, title_page: str, botjob: str, title: str
    ) -> bool:
        if not params:
            self._bot_cache.setdefault(botjob, {})[title_page] = False
            return False
        else:
            logger.debug(f"botEdit.py title:({title}), params:({str(params)}).")
            allow = params.get("allow")
            if allow:
                value = [x.strip() for x in allow.split(",")]
                sd = "all" in value or BOT_USERNAME in value
                if not sd:
                    logger.debug(f"<<lightred>>botEdit.py Template:({title}) has |allow={','.join(value)}.")
                else:
                    logger.warning(f"<<lightgreen>>botEdit.py Template:({title}) has |allow={','.join(value)}.")
                self._bot_cache.setdefault(botjob, {})[title_page] = sd
                return sd
            deny = params.get("deny")
            if deny:
                value = [x.strip() for x in deny.split(",")]
                sd = "all" not in value and BOT_USERNAME not in value
                if not sd:
                    logger.debug(f"<<lightred>>botEdit.py Template:({title}) has |deny={','.join(value)}.")
                self._bot_cache.setdefault(botjob, {})[title_page] = sd
                return sd
        self._bot_cache.setdefault(botjob, {})[title_page] = True
        return True

    def bot_May_Edit_do(self, text: str = "", title_page: str = "", botjob: str = "all") -> bool:
        if settings.bot.force_edit:
            return True
        if botjob in ["", "fixref|cat|stub|tempcat|portal"]:
            botjob = "all"
        if botjob not in self._bot_cache:
            self._bot_cache[botjob] = {}
        if title_page in self._bot_cache[botjob]:
            return self._bot_cache[botjob][title_page]
        templates = extract_templates_and_params(text)
        all_stop = STOP_EDIT_TEMPLATES["all"]
        for temp in templates:
            _name, namestrip, params, _template = (
                temp["name"],
                temp["namestrip"],
                temp["params"],
                temp["item"],
            )
            title = namestrip
            restrictions = STOP_EDIT_TEMPLATES.get(botjob, [])
            if title in restrictions or title in all_stop:
                logger.debug(f"<<lightred>> botEdit.py: the page has temp:({title}), botjob:{botjob} skipp.")
                self._bot_cache.setdefault(botjob, {})[title_page] = False
                return False
            if title.lower() == "nobots":
                return self._handle_nobots_template(params, title_page, botjob, _template)
            elif title.lower() == "bots":
                return self._handle_bots_template(params, title_page, botjob, title)
        self._bot_cache.setdefault(botjob, {})[title_page] = True
        return True


_default_checker = BotEditChecker()


def check_create_time(page, title_page: str) -> bool:
    if title_page in _default_checker._created_cache:
        return _default_checker._created_cache[title_page]
    ns = page.namespace()
    lang = page.lang
    if ns != 0 or lang != "ar":
        return True
    now = datetime.datetime.now(datetime.timezone.utc)
    create_data = page.get_create_data()
    delay_hours = 3
    if create_data.get("timestamp"):
        create_time = create_data["timestamp"]
        ts_c_time = datetime.datetime.strptime(create_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        diff = (now - ts_c_time).total_seconds() / (60 * 60)
        user = create_data.get("user", "")
        wait_time = delay_hours - diff
        if diff < delay_hours:
            logger.debug(f"<<yellow>>Page:{title_page} create at ({create_time}).")
            logger.debug(f"<<invert>>Page Created before {diff:.2f} hours by: {user}, wait {wait_time:.2f}H.")
            return False
    return True


def check_last_edit_time(page, title_page: str, delay: int) -> bool:
    userinfo = page.get_userinfo()
    if "bot" in userinfo.get("groups", []):
        return True
    timestamp = page.get_timestamp()
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        ts_time = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        diff_minutes = (now - ts_time).total_seconds() / 60
        wait_time = delay - diff_minutes
        if diff_minutes < delay:
            logger.debug(f"<<yellow>>Page:{title_page} last edit ({timestamp}).")
            logger.debug(
                f"<<invert>>Page Last edit before {delay} minutes, Wait {wait_time:.2f} minutes. title:{title_page}"
            )
            return False
    return True


def bot_May_Edit(
    text: str = "",
    title_page: str = "",
    botjob: str = "all",
    page=None,
    delay: int = 0,
) -> bool:
    check_it = _default_checker.bot_May_Edit_do(text=text, title_page=title_page, botjob=botjob)
    if page and check_it:
        if delay and isinstance(delay, int):
            ns = page.namespace()
            lang = page.lang
            if ns != 0 or lang != "ar":
                return check_it
            check_time = check_last_edit_time(page, title_page, delay)
            if not check_time:
                return False
        check_create = check_create_time(page, title_page)
        _default_checker._created_cache[title_page] = check_create
        if not check_create:
            return False
    return check_it


__all__ = [
    "bot_May_Edit",
    "check_create_time",
    "check_last_edit_time",
    "extract_templates_and_params",
]