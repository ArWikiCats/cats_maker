""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from .api_formatter import ApiFormatData

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ResultError:
    """
    Normalized error carried by a failed ParsedApiResponse.
    """

    code: str
    message: str
    details: Any | None = None

    @classmethod
    def from_anything(cls, code: str | None, error: Any) -> ResultError:
        """
        Create an ResultError instance from various input types.
        """
        if isinstance(error, ResultError):
            return error

        if isinstance(error, Exception):
            return cls(code=code or type(error).__name__, message=str(error))

        # str or anything else -> treat as a message (never empty)
        return cls(
            code=code or "UNKNOWN_ERROR",
            message="Unknown error" if error is None else str(error),
        )

    def __repr__(self) -> str:
        return f"ResultError(code={self.code!r}, message={self.message})"


@dataclass
class ParsedApiResponse:
    """Represents the complete parsed API response containing mapping of page titles to their details."""

    success: bool
    results: dict[str, PageParseResult] = field(default_factory=dict)
    cats_without_langlinks: list[str] = field(default_factory=list)
    error: ResultError | None = None

    # ── factories ───────────────────────────────────────
    @classmethod
    def ok(cls, data: Any = None) -> ParsedApiResponse:
        return cls(success=True, results=data)

    @classmethod
    def fail(
        cls,
        code: str | None = None,
        error: Any = None,
        data: Any = None,
    ) -> ParsedApiResponse:
        # A failure must explain itself: default when nothing is provided.
        err = ResultError.from_anything(code, error)
        return cls(success=False, results=data, error=err)

    def results_to_dict(self) -> dict[str, Any]:
        if not self.results:
            return {}
        return {x.title: x for x in self.results.values()}

    def results_to_json(self) -> dict[str, Any]:
        if not self.results:
            return {}
        return {x.title: x.to_json() for x in self.results.values()}

    def list_clean_titles(self) -> set[str]:
        if not self.results:
            return set()
        return {cat.clean_title for cat in self.results.values()}

    def list_en_already_in_ar_page(self) -> list[str]:
        if not self.results:
            return []
        return [
            category_data.langlinks["en"]
            for category_data in self.results.values()
            if category_data.langlinks.get("en", "")
        ]

    @classmethod
    def from_json(cls, data: dict[str, PageParseResult]) -> ParsedApiResponse:
        return cls.ok(data)

    @classmethod
    def load(
        cls,
        query: dict[str, Any],
        page_title: str,
        site_code: str,
    ) -> ParsedApiResponse:
        # Get the pages from the query
        pages = query["pages"]

        results: dict[str, PageParseResult] = {}

        with_langlink = without_langlink = 0
        cats_without_langlinks: list[str] = []

        # Pages data has different formats in formatversion 1 and 2
        # V1: {"pages": { "-1": { "ns": 0, "title": "342342423423423434", "missing": "" }, }
        # V2: {"pages": [ { "ns": 0, "title": "342342423423423434", "missing": true }, }
        for page_data in pages:  # formatversion 2 pages is a list
            # Get the category title
            title = page_data["title"]

            # Initialize dataclass instance for this page
            page_result = PageParseResult.load(page_data)
            if page_result.langlinks:
                with_langlink += 1
            else:
                without_langlink += 1
                cats_without_langlinks.append(title)

            results[title] = page_result

        logger.debug(
            f"{site_code}:{page_title} → {len(pages)} total, {with_langlink} with links, {without_langlink} without"
        )
        return cls(
            success=True,
            results=results,
            cats_without_langlinks=cats_without_langlinks,
        )


@dataclass
class PageParseResult:
    """Represents the parsed data for an individual page or category."""

    title: str
    exists: bool | None = None
    ns: int | None = None
    redirect: str | None = None
    categories: dict[str, dict[str, Any]] = field(default_factory=dict)
    templates: list[str] = field(default_factory=list)
    langlinks: dict[str, str] = field(default_factory=dict)

    @property
    def clean_title(self) -> str:
        return self.title.replace("_", " ").strip()

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json_or_none(cls, json_data: dict[str, Any]) -> PageParseResult | None:
        """
        Load a PageParseResult from json data exported from the to_json method.
        """
        if isinstance(json_data, PageParseResult):
            return json_data

        try:
            if "title" not in json_data:
                logger.warning(json_data)
                raise ValueError("Invalid json data for PageParseResult")
            return cls(
                title=json_data["title"],
                exists=json_data.get("exists"),
                ns=json_data.get("ns"),
                redirect=json_data.get("redirect"),
                categories=json_data.get("categories", []),
                templates=json_data.get("templates", []),
            )
        except Exception as e:
            logger.error(f"Error loading PageParseResult from json: {e}")
            return None

    @classmethod
    def load(cls, page_data: dict[str, Any]) -> PageParseResult:
        """
        Load a PageParseResult from a dictionary.

        # Pages data has differ format in both formatversion 1 and 2
        # V1: {"pages": { "-1": { "ns": 0, "title": "342342423423423434", "missing": "" }, }
        # V2: {"pages": [ { "ns": 0, "title": "342342423423423434", "missing": true }, }
        """
        api_formatter = ApiFormatData()

        page_result = cls(
            title=page_data["title"],
            # exists=missing is False,
            ns=page_data.get("ns"),
            categories=api_formatter.extract_category_map(page_data.get("categories", [])),
            templates=api_formatter.extract_template_titles(page_data.get("templates", [])),
            langlinks=api_formatter.map_langlinks_to_titles(page_data.get("langlinks", [])),
        )
        missing = page_data.get("missing") in (True, "")
        if missing is True:
            page_result.exists = False
        else:
            page_result.exists = True

        logger.debug(f"ns: {page_result.ns}")
        logger.debug(f"templates: {page_result.templates}")
        return page_result


__all__ = [
    "ParsedApiResponse",
    "PageParseResult",
]
