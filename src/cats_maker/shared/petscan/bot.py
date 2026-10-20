#!/usr/bin/python3
"""
PetScan client refactored with a class-based design and best practices.

This module provides a clean interface for interacting with the PetScan
tool (petscan.wmflabs.org), replacing the loose functions from the
original script.
"""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

from ..namespace_handler import EN_NAMESPACES, ar_ns_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generic, stateless helper functions
# ---------------------------------------------------------------------------


def _decode_and_format(text: str) -> str:
    """Replace spaces with underscores, then URL-encode the text."""
    text = text.replace(" ", "_")
    try:
        # urllib.parse.quote automatically encodes special characters
        # such as '–' into '%E2%80%93'
        return urllib.parse.quote(text)
    except Exception:
        logger.exception("Failed to encode text: %s", text)
        return text


def _remove_prefix(title: str) -> str:
    """Remove template/category namespace prefixes (in multiple languages)."""
    prefixes = ("template:", "Template:", "قالب:", "تصنيف:", "Category:")
    for prefix in prefixes:
        title = title.replace(prefix, "")
    return title


# ---------------------------------------------------------------------------
# Typed representation of the PetScan query parameters
# ---------------------------------------------------------------------------


@dataclass
class PetScanParams:
    """Typed, structured set of parameters accepted by the PetScan API.

    Building a dataclass instead of a loose dict makes the shape of a
    PetScan query explicit, IDE-friendly, and easy to unit test.
    """

    language: str | None = None
    project: str = "wikipedia"
    combination: str = "union"
    wikidata_item: str = "any"
    sitelinks_no: str = ""
    sitelinks_yes: str = ""
    depth: str = "0"
    templates_yes: str = ""
    links_to_all: str = ""
    categories: str = ""
    wikidata_prop_item_use: str = ""
    wpiu: str = ""
    namespaces: list[str] = field(default_factory=list)

    # Fixed defaults required by the PetScan API on every request.
    show_redirects: str = "no"
    format: str = "json"
    common_wiki: str = "cats"
    output_compatability: str = "catscan"

    def to_query_dict(self) -> dict[str, Any]:
        """Flatten this dataclass into the key/value pairs PetScan expects.

        `namespaces` needs the special `ns%5B<id>%5D=1` key format, so it
        is popped out of the auto-generated dict and expanded separately
        instead of being sent as a literal `namespaces` key.
        """
        query: dict[str, Any] = asdict(self)
        namespaces = query.pop("namespaces")

        for ns in namespaces:
            query[f"ns%5B{ns}%5D"] = 1

        return query


# ---------------------------------------------------------------------------
# Query builder: turns raw user input into a PetScanParams instance
# ---------------------------------------------------------------------------


@dataclass
class PetScanQueryBuilder:
    """Builds a `PetScanParams` instance from raw, loosely-typed input."""

    raw: dict[str, Any] = field(default_factory=dict)

    def _clean_list(self, key: str) -> list[str]:
        """Return a cleaned list (without template/category prefixes) for a key."""
        values = self.raw.get(key) or []
        return [_remove_prefix(v) for v in values]

    def _encode_list(self, values: list[str]) -> str:
        return "%0D%0A".join(_decode_and_format(v) for v in values)

    def _resolve_project(self) -> str:
        project = self.raw.get("family", "")
        if project == "commons":
            return "wikimedia"
        return project or "wikipedia"

    def _resolve_wikidata_props(self) -> tuple[str, str]:
        for key, mode in (("yesprops", "all"), ("noprops", "none"), ("anyprops", "any")):
            props = self.raw.get(key)
            if props:
                return ",".join(props), mode
        return "", ""

    def build(self) -> PetScanParams:
        """Build the final `PetScanParams` sent to the PetScan API."""
        wikidata_prop_item_use, wpiu = self._resolve_wikidata_props()

        categories = self._clean_list("category_yes")

        return PetScanParams(
            language=self.raw.get("language") or self.raw.get("lang"),
            project=self._resolve_project(),
            combination=self.raw.get("combination", "union"),
            wikidata_item=self.raw.get("WD_item") or self.raw.get("wikidata_item", "any"),
            sitelinks_no=self.raw.get("sitelinks_no", ""),
            sitelinks_yes=self.raw.get("sitelinks_yes", ""),
            depth=self.raw.get("depth", "0"),
            templates_yes=self._encode_list(self._clean_list("templates_yes")),
            links_to_all=self._encode_list(self.raw.get("links_to_all", [])),
            categories=self._encode_list(categories) if categories else "",
            wikidata_prop_item_use=wikidata_prop_item_use,
            wpiu=wpiu,
            namespaces=list(self.raw.get("ns", [])),
        )

    @classmethod
    def from_raw_query(cls, raw: dict[str, Any]) -> PetScanParams:
        return cls(raw).build()


# ---------------------------------------------------------------------------
# HTTP client for talking to PetScan
# ---------------------------------------------------------------------------


class PetScanClient:
    """Responsible only for sending the request to PetScan and returning the raw reply."""

    BASE_URL = "https://petscan.wmflabs.org/?doit=Do_it"
    USER_AGENT = "Himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"
    TIMEOUT = 10

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": self.USER_AGENT})

    def _build_url(self, params: dict[str, Any]) -> str:
        url = self.BASE_URL
        for key, value in params.items():
            if value:
                url += f"&{key}={value}"
        return url

    def fetch(self, params: PetScanParams) -> dict[str, Any]:
        """Send the request to PetScan and return the JSON reply (or {} on failure)."""
        url = self._build_url(params.to_query_dict())
        logger.debug(url)

        try:
            response = self._session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            logger.exception("Failed to connect to PetScan: %s", url)
            return {}
        except ValueError:
            logger.exception("PetScan response is not valid JSON: %s", url)
            return {}

        if not data:
            logger.info("Empty response from PetScan: %s", url)
            return {}

        return data


# ---------------------------------------------------------------------------
# PetScan result parsing
# ---------------------------------------------------------------------------


class PetScanResultParser:
    """Turns the raw PetScan reply into a {page_title: page_data} dict."""

    def __init__(self, lang_code: str | None) -> None:
        self.lang_code = lang_code
        self._ns_table = self._resolve_ns_table(lang_code)

    @staticmethod
    def _resolve_ns_table(lang_code: str | None) -> dict[int, str]:
        if lang_code == "en":
            return EN_NAMESPACES
        return {}

    @staticmethod
    def _extract_pages(raw_result: dict[str, Any]) -> list[dict[str, Any]]:
        return list(raw_result.get("*", [{}])[0].get("a", {}).get("*", []))

    def _build_title(self, page: dict[str, Any]) -> str:
        title = page.get("title", "").replace("_", " ")
        namespace = page.get("namespace", "")
        if self.lang_code == "ar":
            return ar_ns_handler.get_full_title(title, namespace)

        ns_text = self._ns_table.get(int(namespace)) or page.get("nstext", "")
        if ns_text:
            title = f"{ns_text}:{title}"
        return title

    def parse(self, raw_result: dict[str, Any]) -> dict[str, Any]:
        pages = self._extract_pages(raw_result)
        parsed: dict[str, Any] = {}

        for page in pages:
            title = self._build_title(page)
            parsed[title] = {
                "touched": page.get("touched", ""),
                "Q": page.get("q", ""),
                "ns": page.get("namespace", ""),
                "len": page.get("len", 0),
                "title": title,
            }

        return parsed


# ---------------------------------------------------------------------------
# Public facade tying everything together
# ---------------------------------------------------------------------------


class PetScanService:
    """Public facade for running a full PetScan query: build -> fetch -> parse."""

    def __init__(self, client: PetScanClient | None = None) -> None:
        self._client = client or PetScanClient()

    def search(self, raw_query: dict[str, Any]) -> dict[str, Any]:
        """Run a full PetScan query and return the resulting pages dict."""
        params = PetScanQueryBuilder.from_raw_query(raw=raw_query)

        raw_result = self._client.fetch(params)
        if not raw_result:
            return {}

        parser = PetScanResultParser(lang_code=params.language)
        results = parser.parse(raw_result)

        logger.info(
            "PetScan (%s:%s): found %d page(s).",
            params.language,
            params.project,
            len(results),
        )
        return results


__all__ = [
    "PetScanParams",
    "PetScanQueryBuilder",
    "PetScanClient",
    "PetScanResultParser",
    "PetScanService",
]
