"""

Related links:
https://github.com/wikimedia/mediawiki-extensions-Wikibase/blob/master/repo/i18n/en.json

https://github.com//wikimedia/mediawiki/blob/master/includes/Api/i18n/ar.json


"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import ApiError


@dataclass(slots=True)
class ApiResultError:
    """Normalized error carried by a failed ApiResult.

    Replaces the free-form ``error: Any`` so a failure always looks the same,
    whether it started as a string, a dict, or an exception. ``details`` is Any
    (not forced to dict) so validation error lists are allowed.

    ``is_retryable`` mirrors the same flag on the :class:`~.exceptions.ApiError`
    hierarchy so callers can decide whether to retry without re-parsing the raw
    error. It defaults to ``False``.
    """

    code: str
    message: str
    details: Any | None = None
    is_retryable: bool = False
    lang: str = ""
    reason: str = ""

    @classmethod
    def from_anything(cls, code: str | None, error: Any) -> ApiResultError:
        """
        Create an ApiResultError instance from various input types.

        This class method provides a flexible factory for constructing an `ApiResultError`
        by inspecting the type of the `error` argument:
        - If `error` is already an `ApiResultError`, it is returned directly.
        - If `error` is an `Exception`, its type name and string representation are used.
        - If `error` is a `dict`, it tolerates legacy shapes (extracting 'message', 'error',
          or 'info' for the message, and mapping remaining keys to 'details').
        - For any other type (including `str` or `None`), it is treated as a raw message string.

        Args:
            code (str | None): An optional error code. If None, a default code is derived
                               based on the type of the `error` argument.
            error (Any): The error source, which can be an Exception, dict, str, None,
                         or any other object.

        Returns:
            ApiResultError: A fully constructed ApiResultError instance.
        """
        if isinstance(error, ApiResultError):
            return error

        # ApiError (and its WikibaseError subclasses) carry rich fields. Preserve
        # the code, message, retryability and (for Wikibase) the sub-reason so
        # callers can branch on them.
        if isinstance(error, ApiError):
            return cls(
                code=code or error.code,
                message=error.message,
                details=error.raw_error or None,
                is_retryable=error.is_retryable,
                lang=getattr(error, "lang", ""),
                reason=getattr(error, "reason", ""),
            )

        if isinstance(error, Exception):
            return cls(code=code or type(error).__name__, message=str(error))

        if isinstance(error, dict):
            # Tolerate many legacy shapes: message / error / info.
            message = error.get("message") or error.get("error") or error.get("info") or str(error)
            return cls(
                code=code or error.get("code", ""),
                message=message,
                details={k: v for k, v in error.items() if k not in ("code", "message", "info", "error")} or None,
            )

        # str or anything else -> treat as a message (never empty)
        return cls(
            code=code or "UNKNOWN_ERROR",
            message="Unknown error" if error is None else str(error),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the object's attributes to a dictionary representation.
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "is_retryable": self.is_retryable,
            "lang": self.lang,
            "reason": self.reason,
        }


class ApiResultExceptionError(Exception):
    """
    Raised by ApiResult.unwrap() on a failed result, carrying the ApiResultError
    so callers can catch it specifically.
    """

    def __init__(self, error: ApiResultError) -> None:
        self.error = error
        super().__init__(error.message)


__all__ = [
    "ApiResultError",
    "ApiResultExceptionError",
]
