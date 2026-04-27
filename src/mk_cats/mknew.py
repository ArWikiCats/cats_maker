"""
python3 core8/pwb.py mk_cats/mknew
"""

import logging

from ..config import settings
from ..core.new_api import load_main_api
from ..core.new_c18 import CategoryResolver, validate_categories_for_new_cat
from ..core.wd_bots import Get_Sitelinks_From_wikidata, add_labels, log_to_wikidata, log_to_wikidata_qid
from ..core.wiki_api import find_Page_Cat_without_hidden
from .add_bot import add_to_page
from .create_category_page import new_category
from .members_helper import collect_category_members
from .utils import check_en_temps, filter_category

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

# Category processing state - encapsulated in module-level variables
# These are cleared between runs to prevent state leakage
_done_d: list = []
_new_cat_done: dict = {}
_already_created: list = []

# TODO: move it to the settings file!
WIKI_SITE_AR = {"family": "wikipedia", "code": "ar"}
WIKI_SITE_EN = {"family": "wikipedia", "code": "en"}

_resolver = CategoryResolver()

logger = logging.getLogger(__name__)

bad_words = [
    "ذكور",
]


def add_to_final_list(final_list, title, callback=None):
    title = title.replace("_", " ")

    if not title.startswith("تصنيف:"):
        title = f"تصنيف:{title}"

    if not final_list:
        return

    for n, page in enumerate(final_list, start=1):
        logger.info(f"<<yellow>> cat:{title} page:{page} n:{n}/{len(final_list)}")
        save = add_to_page(page, title)
        if save and callback:
            try:
                callback(title)
            except Exception as e:
                logger.info(f"<<lightred>> Error in callback: {e}")


def clear_processing_state():
    """Clear all processing state. Call between runs to prevent state leakage."""
    _done_d.clear()
    _new_cat_done.clear()
    _already_created.clear()


def get_processing_state():
    """Get current processing state for testing/debugging."""
    return {
        "done_d": list(_done_d),
        "new_cat_done": dict(_new_cat_done),
        "already_created": list(_already_created),
    }


def ar_make_lab(title, **Kwargs) -> str:
    okay = filter_category(title)

    if not okay:
        logger.debug(f"<<lightred>> {title} is not okay.")
        return ""

    if not resolve_arabic_category_label:
        logger.debug("<<lightred>> ArWikiCats.resolve_arabic_category_label not available.")
        return ""

    label = resolve_arabic_category_label(title)
    # logger.warning(f'<<lightgreen>> Resolved label for "{title}": "{label}"')

    if not label:
        logger.debug(f'<<lightred>> No label found for "{title}".')
        return ""

    for word in bad_words:
        if word in label:
            logger.error(f'<<lightred>> label "{label}" has "{word}".')
            return ""

    return label


def scan_ar_title(title):
    if title in _already_created:
        logger.debug(f'<<lightpurple>> title "{title}". in _already_created')
        return False

    cat3 = str(title)
    if cat3 in _new_cat_done.keys():
        _new_cat_done[cat3] += 1
        logger.debug(f'<<lightblue>> We tried {_new_cat_done[cat3]} times to/created title:<<lightred>>"{cat3}".')
        return False
    else:
        if cat3 in _new_cat_done.keys():
            logger.debug(f'<<lightred>>2070:<<lightpurple>>new trying with cat: "{title}"')
            _new_cat_done[cat3] += 1
        else:
            _new_cat_done[cat3] = 1
    return True


def check_if_artitle_exists(test_title):
    if not test_title.startswith("تصنيف:"):
        test_title = f"تصنيف:{test_title}"

    api = load_main_api(WIKI_SITE_AR["code"])
    page = api.MainPage(test_title)

    if page.exists():
        logger.debug(f"<<lightred>>* category:{test_title} already exists in arwiki.")
        return False

    return True


def _normalize_en_page_title(en_page_title: str) -> str:
    """Clean and normalize an English page title."""
    title = en_page_title.replace("[[", "").replace("]]", "").strip()
    return title.replace("_", " ")


def _get_site_identifiers():
    """Get the Arabic and English site identifiers based on wiki family."""
    ar_site_wiki = "arwiki"
    en_site_lang = WIKI_SITE_EN["code"]  # "en"

    if WIKI_SITE_EN["family"] != "wikipedia" and WIKI_SITE_EN["code"] != "commons":
        ar_site_wiki = f"ar{WIKI_SITE_AR['family']}"
        en_site_lang = WIKI_SITE_EN["code"] + WIKI_SITE_EN["family"]

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
        site_code=WIKI_SITE_EN["code"],
        family=WIKI_SITE_EN["family"],
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
    ar_title: str,
    en_page_title: str,
    qid: str,
    members: list,
    en_cats_of_new_cat: list,
    callback,
) -> list:
    """
    Finalize category creation: add members, and log to Wikidata.

    Returns:
        list: English categories of the new category
    """
    add_to_final_list(members, ar_title, callback=callback)

    if validate_categories_for_new_cat(ar_title, en_page_title, wiki="en"):
        listen = _resolver.resolve_members(en_page_title, ar_title, wiki="en") or []
        if listen:
            add_to_final_list(listen, ar_title, callback=callback)

    if qid:
        log_to_wikidata_qid(ar_title, qid)
    else:
        log_to_wikidata(ar_title, en_page_title)

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
    _already_created.append(en_page_title)

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
    created_category = new_category(en_page_title, ar_title, cats_of_new_cat, qid, family=WIKI_SITE_AR["family"])

    if not created_category.success:
        add_labels(qid, ar_title, "ar")
        return en_cats_of_new_cat

    # Finalize: add members, log to Wikidata
    return _finalize_category_creation(
        ar_title,
        en_page_title,
        qid,
        members,
        en_cats_of_new_cat,
        callback,
    )


def process_catagories(cat, arlab, num, lenth, callback=None) -> None:
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

            en_list = _resolver.list_en_pages_with_ar_links(title, wiki="en")

            if not en_list:
                continue

            enriched_article_list = make_ar(title, labe, callback=callback)

            enriched_titles.extend(enriched_article_list)

        ma_table = list(set(enriched_titles))

    logger.debug("<<lightred>> tago done........... ")


def one_cat(en_title, num, lenth, sugust="", callback=None):
    logger.debug("_________________________________________________________")

    logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}")

    if not en_title.strip():
        logger.warning("<<lightred>> en_title is empty. return")
        return False

    if en_title in _done_d:
        logger.warning(f'en_title:"{en_title}" in _done_d ')
        return False

    _done_d.append(en_title)
    labb = ar_make_lab(en_title)

    logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}, {labb=}")

    labb = labb or sugust

    if not labb:
        logger.warning("<<lightred>> labb is empty.")
        return False

    if not check_en_temps(en_title):
        logger.warning("<<lightred>> check_en_temps failed.")
        return False

    en_list = _resolver.list_en_pages_with_ar_links(en_title, wiki="en")

    if not en_list:
        logger.warning("<<lightred>> en_list is empty. return")
        return False

    return process_catagories(en_title, labb, num, lenth, callback=callback)


def create_categories_from_list(liste, callback=None) -> None:
    # clear_processing_state()
    lenth = len(liste)

    for num, en_title in enumerate(liste, 1):
        one_cat(en_title, num, lenth, callback=callback)


__all__ = [
    "create_categories_from_list",
    "process_catagories",
    "ar_make_lab",
]
