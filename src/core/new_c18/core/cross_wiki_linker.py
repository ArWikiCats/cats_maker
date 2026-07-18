#!/usr/bin/python3
"""Cross-wiki linker — refactored from english_page_title.py."""

from __future__ import annotations

import logging
import re

from ....config import main_settings
from ...wd_bots import Get_Sitelinks_from_qid, Get_Sitelinks_From_wikidata
from ...wiki_api import find_LCN
from ..utils.text import extract_wikidata_qid

logger = logging.getLogger(__name__)

_EN_PAGE_BLACKLIST = {"sandbox"}


def resolve_via_wikidata(text: str, link: str, firstsite_code: str, second_site_code: str) -> str | None:
    """Attempt to resolve a cross-wiki link by extracting a QID from wikitext."""
    qid = extract_wikidata_qid(text)

    if not qid or not qid.startswith("Q"):
        logger.debug(">> No valid qid found in text.")
        return None

    logger.debug(f">> get qid from text: {qid}")
    data = Get_Sitelinks_from_qid(ids=qid)
    sitelinks = data.get("sitelinks", {})

    table: dict[str, str] = {}
    for x in sitelinks:
        x2 = re.sub(r"wiki$", "", x)
        table[x2] = sitelinks[x]

    result = table.get(second_site_code, "")
    logger.debug(f">> table: result : {result}")

    if not result:
        logger.debug(">> No link found for the specified site code.")
        return None

    if "#" in result:
        logger.debug(">> Link contains '#', indicating a section link.")
        return None

    return result


def resolve_via_api(link: str, firstsite_code: str, second_site_code: str, text: str = "") -> str | None:
    """Resolve a cross-wiki link via the MediaWiki API + Wikidata fallback.

    Returns the target page title, or None if no link exists.
    """
    logger.debug(f">> english_page_link {firstsite_code}:{link}")
    link = link.replace("[[", "").replace("]]", "").replace("en:", "").replace("ar:", "")
    link1 = link.replace("_", " ")

    sasa = find_LCN(link, prop="categories|langlinks", first_site_code=firstsite_code) or {}
    logger.debug(f">> sasa: {len(sasa)=}")

    results = ""

    if sasa and link1 in sasa:
        if "langlinks" in sasa[link1]:
            results = sasa[link1]["langlinks"].get(second_site_code, "")
            ar_to_match = sasa[link1]["langlinks"].get(firstsite_code, "")

            if ar_to_match and ar_to_match != link1:
                logger.info(f">> ar_to_match:({ar_to_match}) != ar:({link1}).")
                return None

    if text and not results:
        match = re.search(r"\[\[en:(Category\:.+?)\]\]", text)
        if match:
            logger.info(f"FindEngInArwiki: {match.group(1)}.")
            results = match.group(1)

    sitelinks2: dict[str, str] = {}

    if results:
        tavr = Get_Sitelinks_From_wikidata("enwiki", results)
        if tavr and "sitelinks" in tavr:
            sitelinks2 = tavr["sitelinks"]
    else:
        tavr = Get_Sitelinks_From_wikidata(firstsite_code + "wiki", link)
        if tavr and "sitelinks" in tavr:
            sitelinks2 = tavr["sitelinks"]
            logger.info("sitelinks 2020.")

    for x in sitelinks2:
        x2 = re.sub(r"wiki$", "", x)

        if firstsite_code == x2:
            link1_other = sitelinks2[firstsite_code]
            if link1 != link1_other:
                logger.info(f"link1 ({link1}) != link1_other ({link1_other}).")
                return None

        logger.info(f" ({results}).")
        return results

    return None


def get_page_link(link: str, firstsite_code: str, second_site_code: str, text: str = "") -> str | None:
    """Thin orchestrator: try wikidata first, then API fallback."""
    if text:
        result = resolve_via_wikidata(text, link, firstsite_code, second_site_code)
        if result:
            return result

    return resolve_via_api(link, firstsite_code, second_site_code, text)


def get_en_link_from_ar_text(title: str, site: str, sitetarget: str) -> str:
    """Fetch English (or other target) interwiki link for an Arabic page via Wikidata."""
    enpage = Get_Sitelinks_From_wikidata(site, title)
    if not enpage:
        return ""

    sitetarget2 = sitetarget
    if not sitetarget.endswith("wiki"):
        sitetarget2 += "wiki"

    sitelinks = enpage.get("sitelinks", {})
    eng_interwiki = sitelinks.get(sitetarget) or sitelinks.get(sitetarget2) or ""

    if eng_interwiki:
        logger.debug(f"{eng_interwiki}")

    return eng_interwiki


def get_english_page_title(
    englishlink: str | None,
    pagetitle: str,
    text_new: str,
    ar_page_langlinks: dict[str, str],
) -> tuple[str, str]:
    """Determine the best English (or French) page title for a given Arabic page.

    Returns:
        A tuple of (page_title, source_wiki_code).
    """
    en = englishlink or ""
    ar_site = "ar"
    en_site = "en"
    fr_site = "fr"
    new_site = en_site

    if not en:
        en2 = ar_page_langlinks.get(en_site, "")
        if en2:
            en = en2
        else:
            en = get_en_link_from_ar_text(pagetitle, ar_site, en_site)

    if not en:
        en = get_page_link(pagetitle, en_site, en_site, text=text_new) or ""

    if (not en) and main_settings.category.work_fr:
        logger.info(f"no en for {pagetitle}")
        logger.info(ar_page_langlinks)

        fr_page_title = ar_page_langlinks.get(fr_site, "")
        if not fr_page_title:
            fr_page_title = get_page_link(pagetitle, en_site, fr_site, text=text_new) or ""

        if not fr_page_title:
            logger.info("no fr_page_title")
            return "", ""

        en = fr_page_title
        new_site = fr_site
        logger.info("find cat from frwiki.....")

    if en:
        lower_en = en.lower()
        for item in _EN_PAGE_BLACKLIST:
            if item in lower_en:
                logger.info(f"en {en} in blacklist")
                return "", ""

    return en, new_site
