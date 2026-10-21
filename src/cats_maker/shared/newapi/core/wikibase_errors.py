"""
Wikibase / Wikidata API error hierarchy.

Separates Wikibase-specific business errors from the MediaWiki error tree in
``exceptions.py``. Every subclass derives from :class:`WikibaseError` (which in
turn derives from :class:`~shared.newapi.core.exceptions.ApiError`), so they
plug straight into ``ApiResult.fail`` / ``to_api_result`` / ``unwrap`` without
any string sentinel.

**No side effects here.** Parsing never sleeps; the rate-limit wait (for a
retryable ``failed-save`` + ``actionthrottledtext``) lives in the caller /
retry policy, not in this parser. Likewise all detection is done via the stable
``code`` and ``messages[].name`` API contract, never via the translated
``info`` / ``html`` text.

Related links:
https://github.com/wikimedia/mediawiki-extensions-Wikibase/blob/master/repo/i18n/en.json

https://github.com//wikimedia/mediawiki/blob/master/includes/Api/i18n/ar.json

https://github.com/wikimedia/mediawiki-extensions-Wikibase/tree/master/repo/includes/Validators
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .exceptions import ApiError

logger = logging.getLogger(__name__)

# Every Wikibase code that does NOT start with "wikibase-". Codes beginning with
# "wikibase-" are routed by prefix in the ``parse_api_error`` dispatcher.
#
# ``missingparam`` is deliberately EXCLUDED: it is a generic MediaWiki code, not
# Wikibase-exclusive (see the consolidation plan §6.1). It is only handled as a
# Wikibase warning when the caller passes ``backend="wikibase"``.
#
# ``wikibase-api-invalid-json`` is intentionally NOT listed here: it is a
# *message name*, not a top-level ``code``. The dispatcher still routes payloads
# whose ``code`` starts with ``wikibase-`` into :func:`parse_wikibase_error`, and
# the parser catches the invalid-json case via ``messages[].name``.
WIKIBASE_CODES = {
    "origin-not-empty",
    "modification-failed",
    "failed-modify",
    "failed-save",
    "unresolved-redirect",
    "no-external-page",
    "no-such-entity-link",
}


class WikibaseError(ApiError):
    """Base for Wikibase/Wikidata API business errors (separate from MediaWiki).

    Adds two fields on top of :class:`ApiError`:
      * severity: "error" (default) or "warning" — maps the legacy "warn" sentinel.
      * reason:   free-form sub-reason (used by ModificationFailedError).

    Structured parameters (e.g. the label/description conflict triple
    lab/code/q) are preserved in ``raw_error`` (inherited from ApiError), never
    in a separate field — so nothing is lost when converting to an
    ``ApiResultError``.
    """

    def __init__(
        self,
        code: str,
        message: str = "",
        info: str = "",
        is_retryable: bool = False,
        raw_error: dict[str, Any] | None = None,
        severity: str = "error",
        reason: str = "",
    ) -> None:
        self.severity = severity
        self.reason = reason
        message = message

        if not message and raw_error and raw_error.get("info", ""):
            message = raw_error["info"]

        super().__init__(
            code=code,
            message=message,
            info=info,
            is_retryable=is_retryable,
            raw_error=raw_error,
        )


class OriginNotEmptyError(WikibaseError):
    """
    origin-not-empty: cannot create a redirect on a non-empty item.
    {
        "error": {
            "code": "origin-not-empty",
            "info": "Can't create redirect on non empty item Q65686922",
            "messages": [
                {
                    "name": "wikibase-api-origin-not-empty",
                    "parameters": ["Can't create redirect on non empty item Q65686922"],
                    "html": {"*": "Can't create redirect on non empty item Q65686922"},
                }
            ],
            "*": "",
        },
        "servedby": "mw2356",
    }
    """

    def __init__(self, message: str = "", raw_error: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="origin-not-empty",
            message=message or "Can't create redirect on non empty item",
            raw_error=raw_error,
        )


class WikibaseValidatorError(WikibaseError):
    """
    modification-failed with a recognized sub-reason.

    ``reason`` is one of: ``failed-modify``, ``label-equals-description``,
    ``label-description-conflict``.

    For a ``label-description-conflict`` the conflicting ``lang`` is parsed from
    the Wikibase message ``parameters`` (``[label, lang, entity]``) and exposed
    on ``self.lang`` so callers can skip that language without re-parsing the
    language-dependent ``info`` / ``html`` text.

    {
        "code": "modification-failed",
        "info": "Item [[Q116681602|Q116681602]] already has label 'منحوتة1' associated with language code ar, using the same description text.",
        "messages": [
            {
                "name": "wikibase-validator-label-with-description-conflict",
                "parameters": ["منحوتة1", "ar", "[[Q116681602|Q116681602]]"],
            }
        ],
    }
    {
        "code": "modification-failed",
        "info": "Label and description for language code ar can not have the same value.",
        "messages": [
            {
                "name": "wikibase-validator-label-equals-description",
                "parameters": ["ar"],
            }
        ],
    }
    """

    def __init__(
        self,
        reason: str = "",
        message: str = "",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        self.lang: str | None = None
        self.conflict_qid: str | None = None
        message = message

        if not message and raw_error and raw_error.get("info", ""):
            message = raw_error["info"]

        super().__init__(
            code="modification-failed",
            message=message or f"Modification failed: {reason}".rstrip(),
            raw_error=raw_error,
            reason=reason,
        )
        self.analyze_data()

    def analyze_data(self) -> None:
        messages_data = _messages_data(self.raw_error)
        if messages_data.get("wikibase-validator-label-with-description-conflict"):
            msg = messages_data["wikibase-validator-label-with-description-conflict"]
            params = msg.get("parameters", []) if isinstance(msg, dict) else []

            # Wikibase message parameters are [label, lang, entity]; the
            # conflicting language is at index 1.
            if len(params) > 1:
                self.lang = params[1]
                self.conflict_qid = self._parse_qid_link(params[2])

    def _parse_qid_link(self, qid_link: str) -> str:
        # Extract QID from [[Q...|Q...]] format, otherwise return the string as-is
        match = re.match(r"\[\[(Q\d+)(?:\|(Q\d+))?\]\]", qid_link)
        if match:
            return match.group(2) or match.group(1)
        return qid_link

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the object's attributes to a dictionary representation.
        """
        return {
            "code": self.code,
            "message": self.message,
            "is_retryable": self.is_retryable,
            "lang": self.lang,
            "reason": self.reason,
        }


class ModificationFailedError(WikibaseError):
    """
    failed-modify
    {
        "error": {
            "code": "failed-modify",
            "info": "Attempted modification of the Item failed.",
            "extradata": ["Conflicting sitelinks for arwiki"],
            "messages": [
                {
                    "name": "wikibase-api-failed-modify",
                    "parameters": [],
                    "html": {"*": "Attempted modification of the Item failed."},
                }
            ],
            "*": ".",
        },
        "servedby": "mw2404",
    }
    """

    def __init__(
        self,
        reason: str = "",
        message: str = "",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="modification-failed",
            message=message or f"Modification failed: {reason}".rstrip(),
            raw_error=raw_error,
            reason=reason,
        )


class UnresolvedRedirectError(WikibaseError):
    """
    unresolved-redirect: the entity ID refers to a redirect, unsupported here.
    {
        "code": "unresolved-redirect",
        "info": "The given entity ID refers to a redirect, which is not supported in this context."
    }
    """

    def __init__(self, message: str = "", raw_error: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="unresolved-redirect",
            message=message or "The given entity ID refers to a redirect, which is not supported in this context.",
            raw_error=raw_error,
        )


class FailedSaveError(WikibaseError):
    """failed-save.

    Retryable **only** when the ``actionthrottledtext`` message name is present
    (the rate-limit case). A bare ``failed-save`` is a hard failure.
    """

    def __init__(
        self,
        is_retryable: bool = False,
        message: str = "",
        raw_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="failed-save",
            message=message or "The save has failed.",
            raw_error=raw_error,
            is_retryable=is_retryable,
        )


class NoExternalPageError(WikibaseError):
    """
    no-external-page: the external client site did not provide page info.
    {
        "code": "no-external-page",
        "info": 'The external client site "enwiki" did not provide page information for page "Category:Romanian male songwriters".',
        "messages": [{
            "name": "wikibase-api-no-external-page",
            "parameters": ["enwiki", "Category:Romanian male songwriters"],
            "html": { "*": "" }
        }]
    }
    """

    def __init__(self, message: str = "", raw_error: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="no-external-page",
            message=message or "The external client site did not provide page information",
            raw_error=raw_error,
        )


class InvalidJsonError(WikibaseError):
    """wikibase-api-invalid-json (detected via the message name, not text)."""

    def __init__(self, message: str = "", raw_error: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="wikibase-api-invalid-json",
            message=message or "Invalid JSON",
            raw_error=raw_error,
        )


class NoSuchEntityLinkError(WikibaseError):
    """
    no-such-entity-link: detected by its stable error code, not info text.
    { "error": {
        "code": "no-such-entity-link",
        "info": "Could not find an Item containing a sitelink to the provided site and page name.",
        "messages": [ {
            "name": "wikibase-api-no-such-entity-link",
            "parameters": [],
            "html": "..."
        } ]
    } }
    """

    def __init__(self, message: str = "", raw_error: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="no-such-entity-link",
            message=message or "Could not find an Item containing a sitelink to the provided site and page name.",
            raw_error=raw_error,
        )


def _messages_data(err: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build a ``{name: message}`` map from a Wikibase ``messages`` list.

    Reads ``messages[].name`` (the stable, language-independent contract) and
    never the ``info`` / ``html`` text.
    """
    if not err:
        return {}

    out: dict[str, Any] = {}
    messages = err.get("messages") or []
    if isinstance(messages, list):
        for m in messages:
            if isinstance(m, dict) and "name" in m:
                out[m["name"]] = m

    return out


def failed_modify_errors(error_dict: dict[str, Any]) -> WikibaseError:
    err_info = error_dict.get("info", "")
    messages_data = _messages_data(error_dict)

    if messages_data.get("wikibase-api-failed-modify"):
        return ModificationFailedError(
            reason="failed-modify",
            message=err_info,
            raw_error=error_dict,
        )

    # Unrecognized modification failure: non-fatal warning.
    return WikibaseError(
        code="failed-modify",
        message=err_info or "Attempted modification of the Item failed.",
        raw_error=error_dict,
        severity="warning",
    )


def modification_failed_error(error_dict: dict[str, Any]) -> WikibaseError:
    err_info = error_dict.get("info", "")
    messages_data = _messages_data(error_dict)

    if messages_data.get("wikibase-validator-label-equals-description"):
        return WikibaseValidatorError(
            reason="label-equals-description",
            raw_error=error_dict,
        )

    if messages_data.get("wikibase-validator-label-with-description-conflict"):
        return WikibaseValidatorError(
            reason="label-description-conflict",
            raw_error=error_dict,
        )

    # Unrecognized modification failure: non-fatal warning.
    return WikibaseError(
        code="modification-failed",
        message=err_info or "Attempted modification of the Item failed.",
        raw_error=error_dict,
        severity="warning",
    )


def parse_wikibase_error(error_dict: dict[str, Any]) -> WikibaseError:
    """
    Parse a Wikibase API error dict into a typed :class:`WikibaseError`.

    Pure: no I/O, no ``time.sleep``. Rate-limit detection uses the stable
    ``messages[].name == "actionthrottledtext"`` signal, never the translated
    ``info`` / ``html`` text.
    """
    err_code = error_dict.get("code", "")
    err_info = error_dict.get("info", "")
    messages_data = _messages_data(error_dict)

    if err_code == "origin-not-empty":
        return OriginNotEmptyError(
            message=err_info,
            raw_error=error_dict,
        )

    if err_code == "missingparam":
        # Generic MediaWiki code reached only from the Wikibase path. Non-fatal.
        # {"error":{"code":"missingparam","info":"The \"token\" parameter must be set.","*":""},"servedby":"mw2350"}
        return WikibaseError(
            code="missingparam",
            message=err_info or "A required parameter is missing.",
            raw_error=error_dict,
            severity="warning",
        )

    if err_code == "modification-failed":
        return modification_failed_error(error_dict)

    if err_code == "failed-modify":
        return failed_modify_errors(error_dict)

    if err_code == "unresolved-redirect":
        return UnresolvedRedirectError(
            message=err_info,
            raw_error=error_dict,
        )

    if err_code == "failed-save":
        # {'code': 'failed-save', 'info': 'The save has failed.', 'messages': [{'name': 'wikibase-api-failed-save', 'parameters': [], 'html': {'*': 'لم ينجح الحفظ.'}}, {'name': 'actionthrottledtext', 'parameters': [], 'html': {'*': '...'}}], '*': ''}
        # failed-save alone is a hard failure; failed-save + actionthrottledtext
        # in messages is the retryable (rate-limit) case.
        is_retryable = bool(messages_data.get("actionthrottledtext"))
        return FailedSaveError(
            is_retryable=is_retryable,
            message=err_info,
            raw_error=error_dict,
        )

    if err_code == "no-external-page":
        return NoExternalPageError(
            message=err_info,
            raw_error=error_dict,
        )

    if err_code == "no-such-entity-link":
        return NoSuchEntityLinkError(
            message=err_info,
            raw_error=error_dict,
        )

    if messages_data.get("wikibase-api-invalid-json"):
        return InvalidJsonError(
            message=err_info,
            raw_error=error_dict,
        )

    # Unknown Wikibase code: generic, non-retryable.
    return WikibaseError(
        code=err_code or "unknown",
        message=err_info,
        raw_error=error_dict,
    )


__all__ = [
    "WIKIBASE_CODES",
    "WikibaseError",
    "OriginNotEmptyError",
    "ModificationFailedError",
    "UnresolvedRedirectError",
    "FailedSaveError",
    "NoExternalPageError",
    "InvalidJsonError",
    "NoSuchEntityLinkError",
    "parse_wikibase_error",
    "WikibaseValidatorError",
]
