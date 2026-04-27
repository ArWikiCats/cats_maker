""" """

import logging

logger = logging.getLogger(__name__)


class HandleErrors:
    def handle_err(
        self,
        error: dict,
        function: str = "",
        params: dict | None = None,
        do_error: bool = True,
    ) -> dict | str | bool:
        err_code = error.get("code", "")
        err_info = error.get("info", "")

        if err_code == "abusefilter-disallowed":
            abusefilter = error.get("abusefilter", "")
            description = abusefilter.get("description", "") if isinstance(abusefilter, dict) else ""
            logger.debug(f"<<lightred>> ** abusefilter-disallowed: {description} ")
            if description in [
                "تأخير البوتات 3 ساعات",
                "تأخير البوتات 3 ساعات- 3 من 3",
                "تأخير البوتات 3 ساعات- 1 من 3",
                "تأخير البوتات 3 ساعات- 2 من 3",
            ]:
                return False
            return description

        if err_code == "no-such-entity":
            logger.debug("<<lightred>> ** no-such-entity. ")
            return False

        if err_code == "protectedpage":
            logger.debug("<<lightred>> ** protectedpage. ")
            return False

        if err_code == "articleexists":
            logger.debug("<<lightred>> ** article already created. ")
            return "articleexists"

        if err_code == "maxlag":
            logger.debug("<<lightred>> ** maxlag. ")
            return False

        if do_error:
            if params:
                params["data"] = {}
                params["text"] = {}
            logger.error(f"<<lightred>>{function} ERROR: <<defaut>>info: {err_info}, {params=}")
            from ....config import settings

            if settings.bot.raise_err:
                raise Exception(f"{function} ERROR: {err_info}")

        return error


__all__ = [
    "HandleErrors",
]