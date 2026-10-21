"""
Lag handling functionality

This module provides functions for handling lag in Wikidata API requests.
"""

from __future__ import annotations

import functools
import logging
import os
import re
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class LagHandlerMaxAttemptError(Exception):
    def __init__(self, max_attempt: int) -> None:
        self.code = "check_lags_max_attempts_exceeded"
        self.max_attempt = max_attempt
        self.msg = f"Max attempt reached: {max_attempt}"
        super().__init__(self.msg)


@functools.lru_cache(maxsize=1)
def get_session() -> requests.Session:
    session = requests.Session()
    headers = {"User-Agent": "Himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"}
    session.headers.update(headers)
    return session


def _check_lag_new_data(session, api_url) -> int | None:
    params: dict[str, Any] = {
        "action": "query",
        "format": "json",
        "maxlag": -1,
        "titles": "MediaWiki",
    }

    r4fttext = ""

    try:
        r4ft = session.post(api_url, data=params)
        r4fttext = r4ft.text
    except Exception as e:
        logger.warning(f"{e} - log Error writing")
        return None

    lag = re.match(r".*Waiting for [^ ]*: (\d+\.*\d*) seconds.*", r4fttext)

    if lag:
        return int(float(lag.group(1)))
    return None


class SharedLagHandler:
    LAG_CHANGED_COUNT = 0
    default_maxlag = 4
    current_lag = default_maxlag
    _lag_checks_time = time.time()
    first_time_checked = True

    @property
    def lag_checks_time(self) -> float:
        return SharedLagHandler._lag_checks_time

    def update_lag_checks_time(self) -> None:
        SharedLagHandler._lag_checks_time = time.time()

    @property
    def lag_value(self) -> int:
        return SharedLagHandler.current_lag

    def set_lag_value(self, value: int) -> None:
        logger.info("set new lag value: %s", str(value))
        SharedLagHandler.current_lag = value

    @property
    def lag_changed_count(self) -> int:
        return SharedLagHandler.LAG_CHANGED_COUNT

    def update_changed_count(self) -> None:
        SharedLagHandler.LAG_CHANGED_COUNT += 1  # type: ignore


class LagHandler(SharedLagHandler):
    def __init__(
        self,
        lang: str,
        is_testing_env: bool | None = None,
    ) -> None:
        self.session: requests.Session | None = None
        self.lang = lang

        if is_testing_env is None:
            is_testing_env = os.getenv("APP_ENV") == "testing"

        self.is_testing_env = is_testing_env

        # lang should be one of ("www", "test")
        self.api_url = f"https://{self.lang}.wikidata.org/w/api.php"

    @property
    def _skip_lag_test(self) -> bool:
        # no need to check for lag when using test wikidata site
        return self.lang == "test"

    @property
    def diff_time(self) -> int:
        return int(time.time() - self.lag_checks_time)

    def _should_we_check_for_lag(self) -> bool:
        if self.is_testing_env:
            return False

        if SharedLagHandler.first_time_checked:
            SharedLagHandler.first_time_checked = False
            return True

        if self.diff_time > 119:
            self.update_changed_count()
            self.update_lag_checks_time()
            logger.info(f"<<lightpurple>> LAG_CHANGED_COUNT: {self.lag_changed_count} diff_time: {self.diff_time}")
            return True

        return False

    # -------------------------
    # Public API
    # -------------------------

    def is_bad_lag(self, dont_do_lag_wait: bool) -> bool:
        if self._skip_lag_test:
            # no need to check for lag when using test wikidata site
            return False

        if dont_do_lag_wait and self.lag_value > 5:
            # we don't want to wait for lag. for scripts that need to run fast without sleep time.
            # we use it as `if is_bad_lag(dont_do_lag_wait) return {"success": False, "error_code": "bad_lag"}`
            return True

        # return false so the code will continue steps into check_lag_status function
        return False

    def check_lag_status(self) -> None:
        if self._skip_lag_test:
            # no need to check for lag when using test wikidata site
            return

        if not self.session:
            self.session = get_session()

        numb = 0

        max_attempt = 100
        attempt = 0

        while True:
            attempt += 1
            if attempt > max_attempt:
                # raise to solve infinite loop, example: lag = (10) > 5, numb=39416, self.diff_time=3, sleeptime=20
                logger.error(f"max attempt reached, {max_attempt=}")
                raise LagHandlerMaxAttemptError(max_attempt)

            if self._should_we_check_for_lag():
                new_value = _check_lag_new_data(self.session, self.api_url)
                if new_value:
                    self.set_lag_value(new_value)

            if self.lag_value < 5:
                break

            numb += 1

            sleeptime = self.lag_value * 2

            logger.info(f" lag = ({self.lag_value}) > 5, {numb=}, {self.diff_time=}, {sleeptime=}")

            time.sleep(sleeptime)

    def update_lag_value(self, lag_value_str: str) -> None:
        if self._skip_lag_test:
            # no need to check for lag when using test wikidata site
            return

        new_value = int(lag_value_str)

        if new_value != self.lag_value:
            self.set_lag_value(new_value)
            logger.info(f"<<lightpurple>> max lag: update to {self.lag_value} secound.")


__all__ = [
    "LagHandlerMaxAttemptError",
    "LagHandler",
]
