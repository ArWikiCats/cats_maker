#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
from typing import Any

from ....newapi import ApiResult
from ....newapi.core.wikibase_errors import parse_wikibase_error

logger = logging.getLogger(__name__)


class ResponseHandler:
    def __init__(self) -> None:
        pass

    @staticmethod
    def handle_response(r4: dict[str, Any] | None, out: str = "") -> ApiResult:
        """
        Wrap a raw Wikibase API response in an ``ApiResult`` envelope.

        Errors are parsed into a typed ``WikibaseError`` (subclass of the
        ``ApiError`` hierarchy) and carried in ``ApiResult.error`` — no string
        sentinel. The raw response is preserved in ``data["r4"]`` for callers
        that need the original payload.
        """
        if not r4:
            return ApiResult.fail(code="no_response")

        success = r4.get("success", 0)
        if success is True or success == 1:
            logger.info(f"<<lightgreen>> ** true. {out}")
            return ApiResult.ok(data=r4)

        err = r4.get("error", {})
        if not err:
            logger.error("response not success, and no error: %s", str(r4))
            return ApiResult.fail(code="unknown_error", data={"r4": r4})

        error_obj = parse_wikibase_error(err)

        return ApiResult.fail(
            code=error_obj.code or "unknown_error",
            error=error_obj,
            data={"r4": r4},
        )


__all__ = [
    "ResponseHandler",
]
