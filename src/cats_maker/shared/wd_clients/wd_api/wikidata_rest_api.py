#!/usr/bin/python3
"""
Wikidata REST API client.

https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q4167836
https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=Q4167836

https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q42
https://doc.wikimedia.org/Wikibase/master/js/rest-api/#/items/getItem

New code should use :class:`WikidataRestClient`.
The module-level functions at the bottom are a backward-compatibility layer
that delegates to a shared default client.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class WikidataRestClient:
    """Client for the Wikidata REST API with a per-instance cache."""

    BASE_URL = "https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items"
    PROPS = ("sitelinks", "labels", "descriptions", "aliases", "statements")

    def __init__(
        self,
        base_url: str | None = None,
        session: requests.Session | None = None,
        timeout: float | None = 30,
    ) -> None:
        """
        Args:
            base_url: Override the REST endpoint (useful for tests or other wikis).
            session: Optional ``requests.Session``. When omitted, ``requests.get`` is used.
            timeout: Request timeout in seconds (``None`` disables it).
        """
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.session = session
        self.timeout = timeout
        self.cache: dict[tuple[str, str], dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Low-level
    # ------------------------------------------------------------------
    def get_rest_result(self, url: str) -> dict:
        """Send a GET request and return the JSON body, or ``{}`` on any request error."""
        getter = self.session.get if self.session else requests.get
        try:
            response = getter(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as errh:
            logger.error(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logger.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logger.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logger.error(f"OOps: Something Else: {err}")
        return {}

    def clear_cache(self) -> None:
        self.cache.clear()

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------
    def get_one_qid_info(self, qid: str, only: str | None = None) -> dict[str, Any]:
        """Retrieve labels, descriptions, aliases, sitelinks and statements of one item.

        Args:
            qid: The QID of the entity.
            only: Fetch just one of "sitelinks", "labels", "descriptions",
                "aliases" or "statements". The other keys stay empty.

        Results are cached per ``(qid, only)``.
        """
        key_c = (qid, str(only))
        if key_c in self.cache:
            return self.cache[key_c]

        main_table: dict[str, Any] = {
            "labels": {},
            "descriptions": {},
            "aliases": {},
            "sitelinks": {},
            "statements": {},
            "qid": qid,
        }

        url = f"{self.base_url}/{qid}"
        if only in self.PROPS:
            url += "/" + only

        logger.debug(url)

        result = self.get_rest_result(url)
        if only in self.PROPS:
            result = {only: result}

        main_table["labels"] = result.get("labels", {})
        main_table["descriptions"] = result.get("descriptions", {})
        main_table["aliases"] = result.get("aliases", {})
        main_table["sitelinks"] = {x: v["title"] for x, v in result.get("sitelinks", {}).items()}
        main_table["statements"] = result.get("statements", {})

        self.cache[key_c] = main_table
        return main_table

    def get_item_infos(self, qids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch full info for several items, keyed by QID."""
        logger.info(f"get_item_infos {len(qids)=}")
        table: dict[str, dict[str, Any]] = {}
        for qid in qids:
            logger.info(f"get_item_infos work for one qid: {qid}")
            table[qid] = self.get_one_qid_info(qid)
        return table

    def get_p373(self, qid: str) -> str:
        """Return the Commons category (P373), falling back to the commonswiki sitelink."""
        infos = self.get_one_qid_info(qid)
        value = infos.get("statements", {}).get("P373", [{}])[0].get("value", {}).get("content", "")
        if not value:
            value = infos.get("sitelinks", {}).get("commonswiki", "").replace("Category:", "")
        return value

    def get_descriptions_or_labels(self, qid: str, ty: str = "descriptions") -> dict[str, Any]:
        """Return the item's ``descriptions`` or ``labels``.

        Any value other than "labels" falls back to "descriptions".
        """
        if ty not in ("descriptions", "labels"):
            ty = "descriptions"
        return self.get_one_qid_info(qid)[ty]

    def get_claim(self, qid: str = "", prop: str = "") -> str:
        """Return the content of the first statement of ``prop``, or ``""``."""
        statements = self.get_one_qid_info(qid, only="statements").get("statements", {})
        logger.info(f"{len(statements)=}")

        claims = statements.get(prop, [])
        if claims:
            return claims[0].get("value", {}).get("content", "")
        return ""


# ----------------------------------------------------------------------
# Backward-compatibility layer
# ----------------------------------------------------------------------
# Legacy functional API. Everything delegates to one shared default client.
_default_client = WikidataRestClient()

# Legacy name for the cache. It is the *same dict object* as the client's cache,
# so ``wd_cach.clear()`` and reads keep working. Rebinding the name
# (``wd_cach = {}``) will not affect the client; use ``wd_cach.clear()`` instead.
wd_cach = _default_client.cache


def get_default_client() -> WikidataRestClient:
    """Return the shared client used by the legacy functions."""
    return _default_client


def get_rest_result(url: str) -> dict:
    """Legacy wrapper for :meth:`WikidataRestClient.get_rest_result`."""
    return _default_client.get_rest_result(url)


def get_one_qid_info(qid: str, only=None) -> dict[str, dict[str, Any]]:
    """Legacy wrapper for :meth:`WikidataRestClient.get_one_qid_info`."""
    return _default_client.get_one_qid_info(qid, only=only)


def get_item_infos(qids: list[str]) -> dict[str, dict[str, dict[str, Any]]]:
    """Legacy wrapper for :meth:`WikidataRestClient.get_item_infos`."""
    return _default_client.get_item_infos(qids)


def get_p373(qid: str) -> str:
    """Legacy wrapper for :meth:`WikidataRestClient.get_p373`."""
    return _default_client.get_p373(qid)


def get_item_descriptions_or_labels_rest(
    q,
    ty: str = "descriptions or labels",
) -> dict[str, Any]:
    """Legacy wrapper for :meth:`WikidataRestClient.get_descriptions_or_labels`."""
    return _default_client.get_descriptions_or_labels(q, ty)


def get_claim_api_rest(q: str = "", p: str = "") -> str:
    """Legacy wrapper for :meth:`WikidataRestClient.get_claim`."""
    return _default_client.get_claim(q, p)


__all__ = [
    "WikidataRestClient",
    "get_default_client",
    "wd_cach",
    # legacy functional API
    "get_rest_result",
    "get_one_qid_info",
    "get_item_infos",
    "get_p373",
    "get_item_descriptions_or_labels_rest",
    "get_claim_api_rest",
]
