"""Wikidata SPARQL client."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError

from SPARQLWrapper import JSON, SPARQLWrapper

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now().strftime("%Y-%b-%d  %H:%M:%S")


class WikidataSPARQLClient:
    """Small client for running SPARQL queries against Wikidata.

    Args:
        endpoint_url: SPARQL endpoint address.
        timeout: Request timeout in seconds.
        user_agent: Custom user agent. Built from the Python version if omitted.
        sparql_client: SPARQLWrapper
    """

    DEFAULT_ENDPOINT = "https://query.wikidata.org/sparql"

    def __init__(
        self,
        endpoint_url: str = DEFAULT_ENDPOINT,
        timeout: int = 30,
        user_agent: str | None = None,
        sparql_client: SPARQLWrapper | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.user_agent = user_agent or (f"WDQS-example Python/{sys.version_info[0]}.{sys.version_info[1]}")
        self.sparql_client = sparql_client or SPARQLWrapper(self.endpoint_url, agent=self.user_agent)

    # ------------------------------------------------------------------
    def get_data(self, query: str) -> dict[str, Any]:
        """Run a query and return the raw JSON result (empty dict on failure)."""
        self.sparql_client.setQuery(query)
        self.sparql_client.setReturnFormat(JSON)
        self.sparql_client.setTimeout(self.timeout)

        data: Any | dict[str, Any] = {}
        try:
            data = self.sparql_client.query().convert()
        except HTTPError:
            logger.error("HTTPError")
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
            logger.error("get query failed")
        except Exception as e:
            logger.error(e)

        self.sparql_client.resetQuery()

        return data

    # ------------------------------------------------------------------
    def get_items(self, query: str) -> list[str]:
        """Return the sorted Q-ids found in the ``?item`` variable."""
        logger.info(query)

        data = self.get_data(query)
        if not data:
            return []

        bindings = data.get("results", {}).get("bindings", [])

        found: list[str] = []
        for result in bindings:
            value = result.get("item", {}).get("value", "")
            if "/entity/" in value:
                found.append(value.split("/entity/")[1])

        found.sort()
        items = [q for q in found if q.startswith("Q")]

        logger.info(f"{len(found)} items found, {len(items)} items append, {_now()}")
        return items

    # ------------------------------------------------------------------
    def get_rows(self, query: str) -> list[dict[str, str]]:
        """Return rows as dicts; every selected variable is present in each row."""
        data = self.get_data(query)
        if not data:
            return []

        variables = sorted(data.get("head", {}).get("vars", []))
        bindings = data.get("results", {}).get("bindings", [])

        rows = [{v: result.get(v, {}).get("value", "") for v in variables} for result in bindings]

        logger.info(f"#get_rows: {len(rows)} items found. {_now()}")
        return rows

    # ------------------------------------------------------------------
    def get_big_results(
        self,
        query: str,
        offset: int = 0,
        limit: int | str = 5000,
        all_limit: int = 0,
        single_page: bool = False,
    ) -> list[dict[str, str]]:
        """Fetch results page by page using LIMIT/OFFSET.

        Args:
            query: SPARQL query without LIMIT/OFFSET.
            offset: Starting offset.
            limit: Page size (0 means 5000).
            all_limit: Total rows cap (0 means no cap).
            single_page: Stop after the first page (replaces the old
                ``"nokeep" in sys.argv`` check).
        """
        limit = int(limit) or 5000
        offset = int(offset)

        if 0 < all_limit <= limit:
            limit = all_limit

        results: list[dict[str, str]] = []
        current_offset = offset

        while True:
            paged = f"{query}\n limit {limit}"
            if current_offset:
                paged += f" offset {current_offset}"

            logger.info(f'limit:"{limit}"\t offset:"{current_offset}"')

            page = self.get_rows(paged)
            results.extend(page)
            current_offset += limit

            if all_limit and current_offset >= all_limit:
                break
            if not page or single_page:
                break

        return results


__all__ = [
    "WikidataSPARQLClient",
]
