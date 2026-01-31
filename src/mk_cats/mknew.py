"""
python3 core8/pwb.py mk_cats/mknew
"""

import logging
import sys
from pathlib import Path

from ..b18_new import (
    add_SubSub,
    get_ar_list_from_en,
    get_SubSub_keys,
    make_ar_list_newcat2,
    validate_categories_for_new_cat,
)
from ..config import settings
from ..new_api.pagenew import load_main_api
from ..wd_bots import to_wd
from ..wd_bots.wd_api_bot import Get_Sitelinks_From_wikidata
from ..wiki_api import find_Page_Cat_without_hidden
from .add_bot import add_to_final_list
from .create_category_page import new_category
from .members_helper import collect_category_members
from .utils import filter_en
from .utils.check_en import check_en_temps

arwikicats_path = Path("D:/categories_bot/make2_new/ArWikiCats")
if arwikicats_path.exists():
    sys.path.insert(0, str(arwikicats_path.parent))

try:
    from ArWikiCats import resolve_arabic_category_label  # type: ignore
except ImportError:
    resolve_arabic_category_label = None


def set_project_log_level(name, level: int) -> None:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    for handler in logger.handlers:
        handler.setLevel(level)


set_project_log_level("ArWikiCats", logging.ERROR)

DONE_D = []
NewCat_Done = {}
Already_Created = []

# TODO: move it to the settings file!
wiki_site_ar = {"family": "wikipedia", "code": "ar"}
wiki_site_en = {"family": "wikipedia", "code": "en"}

logger = logging.getLogger(__name__)


def ar_make_lab(title, **Kwargs):
    okay = filter_en.filter_cat(title)

    if not okay:
        logger.debug(f"<<lightred>> {title} is not okay.")
        return ""

    if resolve_arabic_category_label:
        label = resolve_arabic_category_label(title)
        # logger.warning(f'<<lightgreen>> Resolved label for "{title}": "{label}"')
        return label

    logger.debug("<<lightred>> ArWikiCats.resolve_arabic_category_label not available.")
    return ""


def scan_ar_title(title):
    if title in Already_Created:
        logger.debug(f'<<lightpurple>> title "{title}". in Already_Created')
        return False

    cat3 = str(title)
    if cat3 in NewCat_Done.keys():
        NewCat_Done[cat3] += 1
        if settings.category.we_try and cat3 in get_SubSub_keys():
            logger.debug(f'<<lightred>>2070:<<lightpurple>>new trying with cat: "{title}"')
            NewCat_Done[cat3] += 1
            return True
        else:
            logger.debug(f'<<lightblue>> We tried {NewCat_Done[cat3]} times to/created title:<<lightred>>"{cat3}".')
            return False
    else:
        if cat3 in NewCat_Done.keys():
            logger.debug(f'<<lightred>>2070:<<lightpurple>>new trying with cat: "{title}"')
            NewCat_Done[cat3] += 1
        else:
            NewCat_Done[cat3] = 1
    return True


def check_if_artitle_exists(test_title):
    if not test_title.startswith("تصنيف:"):
        test_title = f"تصنيف:{test_title}"
    # ---
    api = load_main_api(wiki_site_ar["code"])
    page = api.MainPage(test_title)
    # ---
    if page.exists():
        logger.debug(f"<<lightred>>* category:{test_title} already exists in arwiki.")
        return False
    # ---
    return True


def _normalize_en_page_title(en_page_title: str) -> str:
    """Clean and normalize an English page title."""
    title = en_page_title.replace("[[", "").replace("]]", "").strip()
    return title.replace("_", " ")


def _get_site_identifiers():
    """Get the Arabic and English site identifiers based on wiki family."""
    ar_site_wiki = "arwiki"
    en_site_lang = wiki_site_en["code"]  # "en"

    if wiki_site_en["family"] != "wikipedia" and wiki_site_en["code"] != "commons":
        ar_site_wiki = f"ar{wiki_site_ar['family']}"
        en_site_lang = wiki_site_en["code"] + wiki_site_en["family"]

    return ar_site_wiki, en_site_lang


def _check_wikidata_sitelink(en_site_lang: str, en_page_title: str, ar_site_wiki: str):
    """
    Check if an Arabic sitelink exists in Wikidata.

    Returns:
        tuple: (has_ar_sitelink, ar_info_dict)
    """
    ar_info = Get_Sitelinks_From_wikidata(en_site_lang, en_page_title) or {}

    if ar_info and ("sitelinks" in ar_info) and (ar_site_wiki in ar_info["sitelinks"]):
        ar_page = ar_info["sitelinks"][ar_site_wiki]
        logger.debug(f'found "{ar_site_wiki}" link "{ar_page}" for en cat. ')
        return True, ar_info

    logger.debug(f'No "{ar_site_wiki}" link for en cat "{en_page_title}"')
    return False, ar_info


def _extract_parent_categories(en_page_title: str):
    """
    Extract parent categories for the English page.

    Returns:
        tuple: (en_cats_of_new_cat, cats_of_new_cat)
            - en_cats_of_new_cat: English categories without Arabic equivalents
            - cats_of_new_cat: Arabic category titles
    """
    cates = find_Page_Cat_without_hidden(
        en_page_title,
        prop="langlinks",
        site_code=wiki_site_en["code"],
        family=wiki_site_en["family"],
    )

    en_cats_of_new_cat = []
    cats_of_new_cat = []

    if not cates:
        return en_cats_of_new_cat, cats_of_new_cat

    for cato in cates:
        if "ar" in cates[cato]:
            cats_of_new_cat.append(cates[cato]["ar"])
        else:
            en_cats_of_new_cat.append(cato)

    if en_cats_of_new_cat:
        logger.debug(f"en_cats_of_new_cat : {','.join(en_cats_of_new_cat)}")
    if cats_of_new_cat:
        logger.debug(f"cats_of_new_cat : {','.join(cats_of_new_cat)}")

    return en_cats_of_new_cat, cats_of_new_cat


def _log_members_info(members: list) -> None:
    """Log information about collected members."""
    formatted_member_list = ""
    if members and len(members) < 30:
        formatted_member_list = ",".join(members)
    logger.debug(f"Add to {len(members)} pages: {formatted_member_list}")


def _finalize_category_creation(
    created_category, ar_title: str, en_page_title: str, qid: str, members: list, en_cats_of_new_cat: list, callback
) -> list:
    """
    Finalize category creation: add members, update SubSub, and log to Wikidata.

    Returns:
        list: English categories of the new category
    """
    add_to_final_list(members, ar_title, callback=callback)
    add_SubSub(en_cats_of_new_cat, created_category)

    if validate_categories_for_new_cat(ar_title, en_page_title, wiki="en"):
        listen = make_ar_list_newcat2(ar_title, en_page_title, us_sql=True) or []
        if listen:
            add_to_final_list(listen, ar_title, callback=callback)

    to_wd.Log_to_wikidata(ar_title, en_page_title, qid)

    return en_cats_of_new_cat


def make_ar(en_page_title, ar_title, callback=None):  # -> list:
    """
    Create an Arabic category based on the English category.

    This function:
    1. Validates inputs and performs early exits
    2. Checks Wikidata sitelinks
    3. Collects category members (delegated to members_helper)
    4. Creates the category
    5. Logs and updates Wikidata

    Args:
        en_page_title: The English category page title
        ar_title: The Arabic category title
        callback: Optional callback function for progress updates

    Returns:
        list: English categories that don't have Arabic equivalents
    """
    # Validation: Check empty Arabic title
    if not ar_title.strip():
        logger.debug("<<lightred>> ar_title is empty.")
        return []

    # Validation: Check if we've already processed this Arabic title
    if not scan_ar_title(ar_title):
        logger.debug("<<lightred>> scan_ar_title failed.")
        return []

    # Normalize the English page title
    en_page_title = _normalize_en_page_title(en_page_title)

    # Validation: Check if Arabic category already exists
    if not check_if_artitle_exists(ar_title):
        logger.debug("<<lightred>> artitle already exists.")
        return []

    # Get site identifiers for Wikidata lookup
    ar_site_wiki, en_site_lang = _get_site_identifiers()

    # Check Wikidata sitelinks - early exit if Arabic link exists
    has_ar_sitelink, ar_info = _check_wikidata_sitelink(en_site_lang, en_page_title, ar_site_wiki)
    if has_ar_sitelink:
        return []

    qid = ar_info.get("q", "")

    # Extract parent categories
    en_cats_of_new_cat, cats_of_new_cat = _extract_parent_categories(en_page_title)

    # Mark as already created
    Already_Created.append(en_page_title)

    # Collect category members using the helper module
    members = collect_category_members(ar_title, en_page_title)

    if not members:
        logger.debug(" collect_category_members returned empty list ")
        return []

    # Check minimum members requirement
    if len(members) < settings.category.min_members:
        logger.debug(
            f" Category has {len(members)} members, less than minimum required ({settings.category.min_members}) "
        )
        return []

    _log_members_info(members)

    # Create the category
    created_category = new_category(en_page_title, ar_title, cats_of_new_cat, qid, family=wiki_site_ar["family"])

    if not created_category:
        to_wd.add_label(qid, ar_title)
        return en_cats_of_new_cat

    # Finalize: add members, update SubSub, log to Wikidata
    return _finalize_category_creation(
        created_category, ar_title, en_page_title, qid, members, en_cats_of_new_cat, callback
    )


def process_catagories(cat, arlab, num, lenth, callback=None):
    logger.debug(f"*: <<lightred>> {num}/{lenth} cat: {cat}, arlab: {arlab}")

    ma_table = make_ar(cat, arlab, callback=callback)

    for i in range(0, settings.range_limit):
        if not ma_table:
            break

        logger.debug("===========================")
        logger.debug(f"**: range: {i} of {settings.range_limit}: for {len(ma_table)} cats.")
        logger.debug("===========================")

        enriched_titles = []
        number = 0

        for title in ma_table:
            logger.debug(r"<<lightred>>\/\/\/ +++++++++ \/\/\/")
            logger.debug(f'work:{number} <<lightpurple>>"{title}"')
            number += 1

            labe = ar_make_lab(title)

            logger.debug(f"*<<lightred>> arlab: {labe}")

            if not labe:
                continue

            en_list = get_ar_list_from_en(title, us_sql=True, wiki="en")

            if not en_list:
                continue

            enriched_article_list = make_ar(title, labe, callback=callback)

            enriched_titles.extend(enriched_article_list)

        ma_table = list(set(enriched_titles))

    logger.debug("<<lightred>> tago done........... ")


def one_cat(en_title, num, lenth, sugust="", uselabs=False, callback=None):
    logger.debug("_________________________________________________________")

    logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}")

    if not en_title.strip():
        logger.warning("<<lightred>> en_title is empty. return")
        return False

    if en_title in DONE_D:
        logger.warning(f'en_title:"{en_title}" in DONE_D ')
        return False

    DONE_D.append(en_title)
    labb = ar_make_lab(en_title)

    logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}, {labb=}")

    labb = labb or sugust

    if not labb:
        logger.warning("<<lightred>> labb is empty.")
        return False

    if not check_en_temps(en_title):
        logger.warning("<<lightred>> check_en_temps failed.")
        return False

    en_list = get_ar_list_from_en(en_title, us_sql=True, wiki="en")

    if not en_list:
        logger.warning("<<lightred>> en_list is empty. return")
        return False

    return process_catagories(en_title, labb, num, lenth, callback=callback)


def create_categories_from_list(liste, uselabs=False, callback=None):
    lenth = len(liste)

    for num, en_title in enumerate(liste, 1):
        one_cat(en_title, num, lenth, uselabs=uselabs, callback=callback)


# Legacy name
ToMakeNewCat2222 = create_categories_from_list
no_work = process_catagories
