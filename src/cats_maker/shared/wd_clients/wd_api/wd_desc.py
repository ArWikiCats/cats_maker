#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import sys

from .. import WikidataClient

logger = logging.getLogger(__name__)

# [[Topic:Xr8nyeau0ysm1zop]]
langs_to_del = [
    "en-gb",
    "en-ca",
    "de-at",
    "de-ch",
    "zh-cn",
    "zh-sg",
    "zh-my",
    "zh-hk",
    "zh-mo",
    "zh-tw",
]


def _clear_ignored_langs_keys(d: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    for key in langs_to_del:
        if key in d:
            del d[key]
    return d


def _are_all_keys_skippable(keys: list[str]) -> bool:
    lang_to_skip = ["tg-latn", "en-gb", "en-ca"]
    if all(lang in lang_to_skip for lang in keys):
        return True
    return False


def _load_value(new_desc_data: dict[str, dict[str, str]]) -> str:
    if "ar" in new_desc_data:
        return new_desc_data["ar"]["value"]

    for key, data in new_desc_data.items():
        return f"{data['value']}@{key}"

    return ""


def _clean_fix_keys(lang_keys: list[str], fixlang: list[str]) -> list[str]:
    for fix in fixlang:
        if fix not in lang_keys:
            fixlang.remove(str(fix))
    return fixlang


def _process_query_descriptions(
    new_desc_data: dict[str, dict[str, str]],
    qid: str,
    attempt: int,
    fixlang: list[str] | None,
) -> None:
    """
    Process and update descriptions for a given query ID.
    """
    if fixlang is None:
        fixlang = []

    queries_list: list = []

    fixlang = _clean_fix_keys(list(new_desc_data.keys()), fixlang)

    for x in new_desc_data.keys():
        if x not in fixlang:
            queries_list.append(x)

    queries_list.sort()

    data = {"descriptions": new_desc_data}

    summary = ""

    if "workibrahem" not in sys.argv:
        summary = "Bot: "

        if queries_list:
            summary += f"- Add descriptions:({len(queries_list)} langs)."

        if fixlang:
            fixed = ",".join(fixlang)

            summary = f"{summary}- fix descriptions:({len(fixlang)}: {str(fixed)})."

        logger.info(summary)

    if queries_list == [] and fixlang == []:
        logger.info("  *** no addedlangs")
        return None

    value = _load_value(new_desc_data)

    logger.info(f'* wwdesc "{qid}" try number:"{attempt}"')
    logger.info(f'len new_desc_data:"{len(new_desc_data)}", len queries_list:"{len(queries_list)}"')

    logger.info(f'*work_api_desc {str(qid)} "{value}": try "{attempt}"')

    wd_api = WikidataClient.load()

    edit_result = wd_api.new_mult_des_2(qid, data=data, summary=summary)

    success = edit_result.is_ok

    if success:
        logger.info(f"<<lightgreen>> **{qid} true. {summary}")
        return None

    err = edit_result.error

    if err is None:
        return None

    if err.code == "modification-failed":
        # Label/description conflict: skip the conflicting language and retry.
        lang = getattr(err, "lang", "") or ""
        if lang and lang in new_desc_data:
            logger.info(f'skiping language: "{lang}"')
            NewDesc2 = {k: v for k, v in new_desc_data.items() if k != lang}
            attempt += 1
            logger.info(f"<<lightred>> try {attempt} again after removing conflicting lang ")
            return _process_query_descriptions(NewDesc2, qid, attempt, fixlang)

        logger.info(f"<<lightred>> modification-failed without conflicting lang: {err.message}")

    elif err.code == "wikibase-api-invalid-json":
        logger.info('<<lightred>> - "wikibase-api-invalid-json" ')
        logger.info(new_desc_data)

    elif getattr(err, "is_retryable", False):
        # Rate-limit (failed-save + actionthrottledtext message). The retry
        # and wait are already handled by the caller (WdDescriptions sleeps
        # on is_retryable and re-drives the request), so no extra wait here.
        logger.info('<<lightred>> "actionthrottledtext" -> rate-limited (retry handled by caller) ')
    else:
        logger.info(f"<<lightred>> wikibase error: {err.code} / {err.message}")


def update_descriptions(
    new_desc_data: dict[str, dict[str, str]],
    qid: str,
    fixlang: list | None = None,
) -> None:
    new_desc_data = _clear_ignored_langs_keys(new_desc_data)

    langes = list(new_desc_data.keys())

    if _are_all_keys_skippable(langes):
        logger.info(f'work_api_desc:"{qid}" only {", ".join(langes)}, Skipp... ')
        return None

    if len(langes) == 1:
        lang = langes[0]

        onedesc = new_desc_data[lang]["value"]
        logger.info(f'work_api_desc:"{qid}" only one desc"{lang}:{onedesc}"')

        wd_api = WikidataClient.load()

        wd_api.des_api(qid, onedesc, lang)

        return None

    return _process_query_descriptions(new_desc_data, qid, 1, fixlang)


def update_item_descriptions(
    q: str,
    topic: str,
    translations: dict[str, dict[str, str]],
) -> None:

    keys = sorted(translations[topic].keys())
    if "en" in keys:
        keys.append("en-gb")
        keys.append("en-ca")

    wd_api = WikidataClient.load()

    item_descriptions = wd_api.get_item_descriptions_or_labels(q, "descriptions")

    if not item_descriptions:
        item_descriptions = {}

    itemdesc_keys = list(item_descriptions.keys())

    new_desc_data = {}

    for lang in keys:
        if lang not in itemdesc_keys:
            lang2 = lang
            if lang in ("en-ca", "en-gb"):
                lang2 = "en"

            new_desc_data[lang] = {"language": lang, "value": translations[topic][lang2]}

    update_descriptions(new_desc_data, q)


__all__ = [
    "update_descriptions",
    "update_item_descriptions",
]
