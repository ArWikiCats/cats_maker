#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
from typing import Any

from .wikidata_sparql import WikidataSPARQLClient

logger = logging.getLogger(__name__)


def _add_prop(x: str, qua: str) -> str:

    if not x.strip():
        return qua

    qua = qua.replace("#sr1", f'(GROUP_CONCAT(?{x}zllabel; SEPARATOR = "@") AS ?{x})\n#sr1')
    qua = qua.replace("#sr2", "optional {" + f"?item wdt:{x} ?{x}z." + "}\n#sr2")
    qua = qua.replace("#sr3", f"?{x}z rdfs:label ?{x}zllabel.\n#sr3")

    return qua


def _create_query(properties: list[str], qids: list[str]) -> str:
    qu1_qid = """
        SELECT DISTINCT
        ?page
        (concat(strafter(str(?item),"/entity/")) as ?q )
        #(GROUP_CONCAT(?P27zllabel; SEPARATOR = "@") AS ?P27)
        #sr1
        WHERE {
            VALUES ?item { %s }
            #?item wdt:P27 ?P27z.
            #sr2
            ?article schema:about ?item ; schema:isPartOf <https://ar.wikipedia.org/> ;  schema:name ?page .
            SERVICE wikibase:label {
                bd:serviceParam wikibase:language "ar,en" .
                #?P27z rdfs:label ?P27zllabel.
                #sr3
            }
        }
        GROUP BY ?item ?page
    """

    qui = qu1_qid % " ".join([f"wd:{q}" for q in qids])

    for x in properties:
        qui = _add_prop(x, qui)
    return qui


def get_properties_label(properties: list[str], qids: list[str]) -> list[dict[str, str]]:

    qui = _create_query(properties, qids)

    wdo: list[dict[str, str]] = WikidataSPARQLClient().get_rows(qui)

    return wdo


def get_properties_for_qids(
    properties: list[str],
    q_list: dict[str, Any],
) -> dict[str, Any]:

    q_to_page = {q: p for p, q in q_list.items()}

    wikidata_lists = {}

    for i in range(0, len(q_list), 50):
        vgh = dict(list(q_list.items())[i : i + 50])

        qids = [q for x, q in vgh.items()]

        wd_result: list[dict[str, str]] = get_properties_label(properties, qids)

        for tab in wd_result:
            if tab.get("q"):
                qid = tab["q"]
                tab["page"] = q_to_page.get(qid, "")
                wikidata_lists[qid] = tab

    return wikidata_lists


__all__ = [
    "get_properties_label",
    "get_properties_for_qids",
]
