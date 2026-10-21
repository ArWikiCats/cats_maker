"""
Unified exception hierarchy for ``newapi``.

Single source of truth for **all** newapi exceptions. There used to be two
parallel modules (``core/exceptions.py`` and ``api_client/exceptions.py``); they
are now unified under one root, ``NewApiExceptionError``:

* ``ApiError`` (+ subclasses such as ``ArticleExistsError``) describe **business**
  outcomes returned by the MediaWiki API.
* ``WikiClientError`` (+ subclasses such as ``CSRFError``) describe **transport**
  failures at the HTTP / client layer.

Error-handling policy (see also ``result.to_api_result``):

* Transport / network / auth failures  -> **stay raised** (``WikiClientError``
  tree). A ``requests.Timeout`` or a persistent ``CSRFError`` is a real,
  retryable failure that the caller must handle explicitly.
* Expected business outcomes         -> **become** ``ApiResult.fail``
  (``ApiError`` tree). ``page_not_found``, ``invalid_summary``,
  ``permission_denied`` etc. are normal results, not exceptions.

``api_client/exceptions.py`` remains only as a backwards-compatible re-export.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .result import ApiResult

logger = logging.getLogger(__name__)


class NewApiExceptionError(Exception):
    """
    Base exception for all mw_api errors.

    All custom exceptions in the library should inherit from this class.
    """

    def __init__(self, message: str = "", code: str = "") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ApiError(NewApiExceptionError):
    """
    Exception for MediaWiki API errors.

    Represents errors returned by the MediaWiki API.

    Attributes:
        code: The error code from the API (e.g., 'articleexists').
        message: Human-readable error message.
        info: Additional info from the API.
        is_retryable: Whether the operation can be retried.
    """

    def __init__(
        self,
        code: str,
        message: str,
        info: str = "",
        is_retryable: bool = False,
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        self.info = info
        self.is_retryable = is_retryable
        self.raw_error = raw_error or {}
        super().__init__(f"{code}: {message}", code=code)


ABUSEFILTER_ERRORS_FOR_DELAY = [
    "تأخير البوتات 3 ساعات",
    "تأخير البوتات 3 ساعات- 3 من 3",
    "تأخير البوتات 3 ساعات- 1 من 3",
    "تأخير البوتات 3 ساعات- 2 من 3",
]


class AbuseFilterError(ApiError):
    """
    Exception for abuse filter blocks.

    Raised when an edit is blocked by an abuse filter.

    Attributes:
        filter_id: The ID of the abuse filter that blocked the action.
        description: Description of the filter rule.
    """

    def __init__(
        self,
        description: str,
        filter_id: str = "",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        self.filter_id = filter_id
        self.description = description
        super().__init__(
            code="abusefilter-disallowed",
            message=description,
            info=f"Filter ID: {filter_id}",
            is_retryable=False,
            raw_error=raw_error,
        )

    def is_delay(self) -> bool:
        return any(delay in self.description for delay in ABUSEFILTER_ERRORS_FOR_DELAY)


class MaxLagError(ApiError):
    """
    Exception for database lag errors.

    Raised when the database replication lag is too high.
    This is a retryable error.

    Attributes:
        lag: The current replication lag in seconds.
    """

    def __init__(
        self,
        lag: int = 0,
        message: str = "Data base lag is too high",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        self.lag = lag
        super().__init__(
            code="maxlag",
            message=message,
            info=f"Lag: {lag} seconds",
            is_retryable=True,
            raw_error=raw_error,
        )


class ArticleExistsError(ApiError):
    """
    Exception when trying to create an article that already exists.
    API Result example:
        {
            "error": {
                "code": "articleexists",
                "info": "The article you tried to create has been created already.",
                "*": "See ..."
            },
            "servedby": "mw1425"
        }
    """

    def __init__(
        self,
        message: str = "The article you tried to create has been created already.",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="articleexists",
            message=message,
            is_retryable=False,
            raw_error=raw_error,
        )


class NoSuchEntityError(ApiError):
    """
    Exception when a Wikidata entity does not exist.
    """

    def __init__(
        self,
        message: str = "The entity does not exist.",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="no-such-entity",
            message=message,
            is_retryable=False,
            raw_error=raw_error,
        )


class ProtectedPageError(ApiError):
    """
    Exception when trying to edit a protected page.
    """

    def __init__(
        self,
        message: str = "The page is protected.",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="protectedpage",
            message=message,
            is_retryable=False,
            raw_error=raw_error,
        )


class InvalidTokenError(ApiError):
    """
    Exception for invalid CSRF token.

    This is a retryable error - the token should be refreshed.
    """

    def __init__(
        self,
        message: str = "Invalid CSRF token.",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="badtoken", message=message, is_retryable=True, raw_error=raw_error)


class AuthenticationError(NewApiExceptionError):
    """
    Exception for authentication failures.
    """

    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(message, code="auth_failed")


class ValidationError(NewApiExceptionError):
    """
    Exception for validation errors in input data.
    """

    def __init__(self, message: str, field: str = "") -> None:
        self.field = field
        super().__init__(message, code="validation_error")


# ---------------------------------------------------------------------------
# Transport / api_client exceptions (unified under the same root)
# ---------------------------------------------------------------------------
# These represent failures at the HTTP / transport layer (login, token refresh,
# network retries, cookies). They intentionally STAY raised -- they are NOT
# turned into an ApiResult. A ``requests.Timeout`` or a persistent ``CSRFError``
# is a real, retryable failure the caller must handle, not a normal business
# outcome.


class WikiClientError(NewApiExceptionError):
    """Base exception for all api_client / transport errors."""


class LoginError(WikiClientError):
    """Raised when credentials are rejected or the login flow fails."""


class CSRFError(WikiClientError):
    """Raised when a CSRF token remains invalid after all retries."""


class MaxlagError(WikiClientError):
    """Raised when server maxlag is not resolved after all attempts.

    NOTE: this is the *transport* maxlag (retry exhaustion), distinct from the
    business ``MaxLagError`` (an ``ApiError`` subclass) emitted by the MediaWiki
    API.
    """


class MaxRetriesExceededError(WikiClientError):
    """Raised when the generic retry cap is hit."""


class CookieError(WikiClientError):
    """Raised when the cookie file cannot be read or written."""


def to_api_result(exc: Exception) -> ApiResult:
    """
    Map a NEWAPI **business** exception (the ``ApiError`` hierarchy) to an
    ``ApiResult.fail``.

    Transport / network / auth exceptions (the ``WikiClientError`` hierarchy)
    are deliberately NOT mapped: they stay raised so the caller can retry or take
    a different recovery path. This encodes the project's error policy:

    * transport / network / auth  -> stay raised (``WikiClientError`` ...)
    * expected business outcomes  -> ``ApiResult.fail`` (``ApiError`` ...)

    Raises:
        TypeError: if ``exc`` is a transport exception or otherwise unknown.
    """
    from .result import ApiResult

    if isinstance(exc, ApiError):
        return ApiResult.fail(code=exc.code, error=exc.message)
    if isinstance(exc, WikiClientError):
        # Transport failures must remain exceptions, not silently become results.
        raise exc
    raise TypeError(f"Cannot convert {type(exc).__name__} to ApiResult")


_WIKIBASE_PREFIX = "wikibase"


def parse_api_error(error_dict: dict[str, Any], backend: str = "mediawiki") -> ApiError:
    """
    Parse an API error dictionary and return the appropriate exception.

    Single entry point for both MediaWiki and Wikibase/Wikidata errors. Wikibase
    codes (the ``wikibase-*`` prefix, the explicit ``WIKIBASE_CODES`` set, or any
    error produced by the Wikibase backend) are routed to
    :func:`wikibase_errors.parse_wikibase_error`; everything else goes through
    the MediaWiki branch ladder above.

    Args:
        error_dict: The error dictionary from the API response.
        backend: ``"mediawiki"`` (default) or ``"wikibase"``. Used to disambiguate
            generic codes (e.g. ``missingparam``) that are not Wikibase-exclusive
            on their own.

    Returns:
        An ApiError subclass instance (MediaWiki or Wikibase).
    """
    # Imported lazily to avoid a circular import (wikibase_errors imports ApiError).
    from .wikibase_errors import WIKIBASE_CODES, parse_wikibase_error

    err_code = error_dict.get("code", "")
    if err_code in WIKIBASE_CODES or err_code.startswith(_WIKIBASE_PREFIX) or backend == "wikibase":
        return parse_wikibase_error(error_dict)

    # ── MediaWiki branch ladder ─────────────────────────────────────────────
    err_info = error_dict.get("info", "")

    # Map error codes to exception classes
    if err_code == "abusefilter-disallowed":
        abusefilter = error_dict.get("abusefilter", {})
        description = abusefilter.get("description", "")
        filter_id = str(abusefilter.get("id", ""))
        return AbuseFilterError(description=description, filter_id=filter_id, raw_error=error_dict)

    if err_code == "maxlag":
        logger.error(" ** maxlag. ")
        lag = int(error_dict.get("lag", 0))
        return MaxLagError(lag=lag, message=err_info, raw_error=error_dict)

    if err_code == "articleexists":
        logger.error(" ** article already created. ")
        return ArticleExistsError(message=err_info, raw_error=error_dict)

    if err_code == "no-such-entity":
        logger.error(" ** no-such-entity. ")
        return NoSuchEntityError(message=err_info, raw_error=error_dict)

    if err_code == "protectedpage":
        logger.error(" ** protectedpage. ")
        return ProtectedPageError(message=err_info, raw_error=error_dict)

    if err_code == "badtoken" or err_info == "Invalid CSRF token.":
        return InvalidTokenError(message=err_info, raw_error=error_dict)

    # Generic API error for unknown codes
    return ApiError(code=err_code, message=err_info, is_retryable=False, raw_error=error_dict)


__all__ = [
    "NewApiExceptionError",
    "ApiError",
    "AbuseFilterError",
    "MaxLagError",
    "ArticleExistsError",
    "NoSuchEntityError",
    "ProtectedPageError",
    "InvalidTokenError",
    "AuthenticationError",
    "ValidationError",
    "WikiClientError",
    "LoginError",
    "CSRFError",
    "MaxlagError",
    "MaxRetriesExceededError",
    "CookieError",
    "to_api_result",
    "parse_api_error",
]
