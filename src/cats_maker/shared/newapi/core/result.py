"""
Unified result envelope for the SERVICE / business layer of newapi.

NOT for the transport layer: ``requests_handler`` and ``api_client`` keep
returning raw dicts and raising exceptions. ``ApiResult`` is what service
functions return, and ``to_dict()`` gives a stable shape for ANY consumer
(CLI, Toolforge job, worker, future external API, tests) — not just HTTP.

Serialized envelope is ALWAYS nested (never spreads data into the top level):
    {"success": true,  "data": {...}, "error": null}
    {"success": false, "data": {},    "error": {"code": ..., "message": ..., "details": ...}}
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .result_error import ApiResultError, ApiResultExceptionError


@dataclass(slots=True)
class ApiResult:
    success: bool
    data: Any = None
    error: ApiResultError | None = None

    def __post_init__(self) -> None:
        # A failure must always explain itself; never leave error == None
        # (so unwrap() can never raise with a None error).
        if not self.success and self.error is None:
            self.error = ApiResultError(code="UNKNOWN_ERROR", message="Unknown error")

    # NOTE: there is NO ``error_code`` field. The single source of truth is
    # ``error.code``; ``error_code`` below is only a compatibility property.

    # ── factories ───────────────────────────────────────
    @classmethod
    def ok(cls, data: Any = None) -> ApiResult:
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str | None = None, error: Any = None, data: Any = None) -> ApiResult:
        # A failure must explain itself: default when nothing is provided.
        err = (
            ApiResultError.from_anything(code, error)
            if (code is not None or error is not None)
            else ApiResultError(code="UNKNOWN_ERROR", message="Unknown error")
        )
        # ``data`` is allowed on failures too (carries the raw response or other
        # context) while the envelope stays always-nested.
        return cls(success=False, data=data, error=err)

    # ── convenience ─────────────────────────────────────
    @property
    def is_ok(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success

    @property
    def error_code(self) -> str | None:
        """Compatibility view: the error code, or None when there is no error."""
        return self.error.code if self.error else None

    # ── transforms (Result pattern) ─────────────────────
    def map(self, func: Callable[[Any], Any]) -> ApiResult:
        """Apply ``func`` to ``data`` on success; pass failures through.
        Preserves subclass type via ``type(self)``."""
        if not self.success:
            return self
        return type(self).ok(func(self.data))

    def map_error(self, func: Callable[[ApiResultError], Any]) -> ApiResult:
        """Transform the failure error while preserving the original error code
        UNLESS the mapper returns a ApiResultError (which then carries its own code).
        Preserves subclass type via ``type(self)``."""
        if self.success or self.error is None:
            return self
        new_error = func(self.error)
        if isinstance(new_error, ApiResultError):
            return type(self)(success=False, error=new_error)
        return type(self).fail(code=self.error.code, error=new_error)

    # ── unwrap / value (raise on failure) ───────────────
    def unwrap(self) -> Any:
        if not self.success:
            # error is guaranteed non-None by __post_init__ on failures.
            raise ApiResultExceptionError(self.error)  # pyright: ignore[reportArgumentType]
        return self.data

    @property
    def value(self) -> Any:
        """Alias for :meth:`unwrap` (raises on failure)."""
        return self.unwrap()

    def unwrap_or(self, default: Any) -> Any:
        """Return ``data`` on success, otherwise ``default``."""
        return self.data if self.success else default

    # ── serialized forms ────────────────────────────────
    def to_dict(self) -> dict[str, Any]:
        """Always-nested envelope. Never spreads ``data`` into the top level."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error.to_dict() if self.error else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | Any) -> ApiResult:
        """Wrap legacy dicts (flat) AND the new nested envelope into ApiResult."""
        if not isinstance(payload, dict) or not payload:
            return cls.fail(code="empty_response")

        if payload.get("success"):
            # ``data`` may be a list / str / number / dict — accept any type.
            if "data" in payload:
                return cls(success=True, data=payload["data"])
            data = {k: v for k, v in payload.items() if k not in ("success", "error", "error_code", "data")} or None
            return cls(success=True, data=data)

        # failure: support BOTH shapes
        #  - new: {"success": false, "error": {"code": ..., "message": ...}}
        #  - old: {"success": false, "error_code": "...", "error": "..."}
        raw_error = payload.get("error")
        if isinstance(raw_error, dict):
            err = ApiResultError.from_anything(raw_error.get("code"), raw_error)
        else:
            err = ApiResultError.from_anything(payload.get("error_code"), raw_error)
        data = {k: v for k, v in payload.items() if k not in ("success", "error", "error_code", "data")} or None
        return cls(success=False, data=data, error=err)

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"ApiResult.ok({self.data!r})"
        return f"ApiResult.fail(code={self.error_code!r}, error={self.error!r})"


__all__ = [
    "ApiResult",
    "ApiResultError",
    "ApiResultExceptionError",
]
