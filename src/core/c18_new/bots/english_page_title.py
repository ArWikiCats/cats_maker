"""
Usage:
from ..bots.english_page_title import get_english_page_title
"""

import logging
import re

from ....config import settings
from ...wd_bots import Get_Sitelinks_from_qid, Get_Sitelinks_From_wikidata
from ...wiki_api import find_LCN, get_cache_L_C_N, set_cache_L_C_N

logger = logging.getLogger(__name__)


def extract_wikidata_qid(text):
    qid = ""
    foos = re.compile(r"\{\{قيمة ويكي بيانات\/قالب تحقق\s*\|\s*(Q\d+)\s*\}\}").findall(text)
    foos2 = re.compile(r"\{\{قيمة ويكي بيانات\/قالب تحقق\s*\|\s*id\s*\=\s*(Q\d+)\s*\}\}").findall(text)
    match3 = re.search(r"\{\{سباق الدراجات\/صندوق معلومات\s*\|\s*(Q\d+)\s*\}\}", text)
    match4 = re.search(r"\{\{Cycling race\/infobox\s*\|\s*(Q\d+)\s*\}\}", text)

    if foos:
        qid = foos[0]
    elif foos2:
        qid = foos2[0]
    elif match3:
        qid = match3.group(1)
    elif match4:
        qid = match4.group(1)
    return qid


def english_page_link_from_text(link, firstsite_code, second_site_code, text="") -> str:
    tubb = (link, firstsite_code, second_site_code, "en_links")

    logger.debug(">>sssss text: ")
    qid = extract_wikidata_qid(text)

    if not qid.startswith("Q"):
        logger.debug(">> No valid qid found in text.")
        return ""

    logger.debug(f">> get qid from text: {qid} ")
    logger.debug(f">> qid {qid} ")

    data = Get_Sitelinks_from_qid(ids=qid)

    sitelinks = data.get("sitelinks", {})

    logger.debug(f">> Sitelinks {len(sitelinks)=}")

    table = {}
    for x in sitelinks:
        x2 = re.sub(r"wiki$", "", x)
        table[x2] = sitelinks[x]

    result = table.get(second_site_code, "")

    logger.debug(f">> table: result : {result}")

    if not result:
        logger.debug(">> No link found for the specified site code.")
        set_cache_L_C_N(tubb, False)
        return False

    if "#" in result:
        logger.debug(">> Link contains '#', indicating a section link.")
        set_cache_L_C_N(tubb, False)
        return False

    oppsite_tubb = (result, second_site_code, firstsite_code, "en_links")
    set_cache_L_C_N(oppsite_tubb, link)
    set_cache_L_C_N(tubb, result)

    return result


def english_page_link_from_api(link, firstsite_code, second_site_code, text=""):
    """
    This function is used to find the English page link for a given page on a Wikipedia-like site.

    Args:
        link (str): The title of the page to find the English link for.
        firstsite_code (str): The language code of the site that the page is on.
        second_site_code (str): The language code of the site to find the link for.

    Returns:
        str: The title of the English page that corresponds to the given page, or False if no such page exists.
    """
    tubb = (link, firstsite_code, second_site_code, "en_links")

    cac = get_cache_L_C_N(tubb)

    if cac:
        logger.debug(f'>> _cache LCN tubb: "{link}": = {second_site_code}:{cac}')
        return cac

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
            # if second_site_code in sasa[link1]['langlinks']:
            # result = sasa[link1]['langlinks'][second_site_code]

            if ar_to_match and ar_to_match != link1:
                logger.info(f">> ar_to_match:({ar_to_match}) != ar:({link1}).")
                return False

    if text and results == "":
        match = re.search(r"\[\[en:(Category\:.+?)\]\]", text)
        if match:
            logger.info(f"FindEngInArwiki: {match.group(1)}.")
            results = match.group(1)

    Sitelinks2 = {}

    if results:
        tavr = Get_Sitelinks_From_wikidata("enwiki", results)
        if tavr and "sitelinks" in tavr:
            Sitelinks2 = tavr["sitelinks"]
    else:
        tavr = Get_Sitelinks_From_wikidata(firstsite_code + "wiki", link)

        if tavr and "sitelinks" in tavr:
            Sitelinks2 = tavr["sitelinks"]
            logger.info("sitelinks 2020.")

    for x in Sitelinks2:
        x2 = re.sub(r"wiki$", "", x)

        if firstsite_code == x2:
            link1_other = Sitelinks2[firstsite_code]
            if link1 != link1_other:
                logger.info(f"link1 ({link1}) != link1_other ({link1_other}).")
                set_cache_L_C_N(tubb, False)
                return False

        oppsite_tubb = (results, second_site_code, firstsite_code, "en_links")
        set_cache_L_C_N(oppsite_tubb, link)
        set_cache_L_C_N(tubb, results)
        logger.info(f" ({results}).")
        return results

    set_cache_L_C_N(tubb, False)

    return False


def english_page_link(link, firstsite_code, second_site_code, text=""):
    """
    This function is used to find the English page link for a given page on a Wikipedia-like site.

    Args:
        link (str): The title of the page to find the English link for.
        firstsite_code (str): The language code of the site that the page is on.
        second_site_code (str): The language code of the site to find the link for.
        text (str, optional): The text of the page. Defaults to "".

    Returns:
        str: The title of the English page that corresponds to the given page, or False if no such page exists.
    """
    if text:
        results = english_page_link_from_text(link, firstsite_code, second_site_code, text)
        if results:
            return results

    results = english_page_link_from_api(link, firstsite_code, second_site_code, text)
    return results


def get_en_link_from_ar_text(title, site, sitetarget):
    enpage = Get_Sitelinks_From_wikidata(site, title)

    if not enpage:
        return ""

    EngInterwiki = ""

    if sitetarget:
        sitetarget2 = sitetarget
        if not sitetarget.endswith("wiki"):
            sitetarget2 += "wiki"

        sitelinks = enpage.get("sitelinks", {})
        EngInterwiki = sitelinks.get(sitetarget) or sitelinks.get(sitetarget2) or ""

    if EngInterwiki:
        logger.debug(f"<<lightblue>> {EngInterwiki}")

    return EngInterwiki


def get_english_page_title(englishlink, pagetitle, text_new, ar_page_langlinks):
    en = ""

    if englishlink:
        en = englishlink

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
        en = english_page_link(pagetitle, en_site, en_site, text=text_new)

    if (not en or en == "") and settings.category.work_fr:
        fr_page_title = False
        logger.info("<<lightred>>c18/scat/cat.py no en")
        logger.info(ar_page_langlinks)
        fr2 = ar_page_langlinks.get(fr_site, "")
        if fr2:
            fr_page_title = fr2
        else:
            fr_page_title = english_page_link(pagetitle, en_site, fr_site, text=text_new)

        if not fr_page_title:
            logger.info("<<lightred>> no fr_page_title")
            return "", ""
        en = fr_page_title
        new_site = fr_site
        logger.info("<<lightred>> find cat from frwiki.....")

    pageblacklist = ["Sandbox"]

    if en:
        for item in pageblacklist:
            if en.find(item.lower()) != -1:
                logger.info(f"<<lightred>> en {en} in blacklist")
                return "", ""

    return en, new_site
