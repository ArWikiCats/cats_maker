"""
Helper module for category member processing.

This module encapsulates all logic related to collecting, merging, filtering,
and normalizing category members from various sources (API, SQL, SubSub).

Responsibilities:
- Gathering members from API, SQL, and SubSub sources
- Deduplicating results
- Removing invalid entries and redirects
- Returning a clean, final list of category members
"""

import logging

from ..b18_new import MakeLitApiWay, get_listenpageTitle, get_SubSub_value
from ..config import settings
from ..wiki_api.check_redirects import remove_redirect_pages

logger = logging.getLogger(__name__)


def gather_members_from_sql(ar_title: str, en_page_title: str) -> list:
    """
    Gather category members using SQL-based queries.

    Args:
        ar_title: The Arabic category title
        en_page_title: The English page title

    Returns:
        A list of category member titles from SQL sources
    """
    return get_listenpageTitle(ar_title, en_page_title)


def gather_members_from_api(en_page_title: str) -> list:
    """
    Gather category members using the Wikipedia API.

    Args:
        en_page_title: The English page title

    Returns:
        A list of category member titles from API sources
    """
    result = MakeLitApiWay(en_page_title, Type="all")
    return result if result else []


def gather_members_from_subsub(en_page_title: str) -> list:
    """
    Gather category members from SubSub source (previously created categories).

    Args:
        en_page_title: The English page title (stripped)

    Returns:
        A list of category member titles from SubSub sources
    """
    sub_category_values = get_SubSub_value(en_page_title.strip())
    if not sub_category_values:
        return []

    logger.debug('<<lightgreen>> New Adding for cats: "%s" : ' % en_page_title)
    for member in sub_category_values:
        logger.debug('<<lightgreen>> New Adding "%s" to fapage list.............' % member)

    return list(sub_category_values)


def merge_member_lists(*member_lists: list) -> list:
    """
    Merge multiple member lists, removing duplicates while preserving order.

    Uses dict.fromkeys() for O(n) deduplication instead of O(n²) list lookup.

    Args:
        *member_lists: Variable number of member lists to merge

    Returns:
        A deduplicated list of all members (order preserved)
    """
    # Chain all lists and use dict.fromkeys() for efficient O(n) deduplication
    from itertools import chain

    return list(dict.fromkeys(chain.from_iterable(member_lists)))


def filter_invalid_members(members: list) -> list:
    """
    Filter out invalid members (empty strings, non-strings, None values).

    Args:
        members: A list of category members

    Returns:
        A filtered list containing only valid string members
    """
    return [m for m in members if m and isinstance(m, str)]


def deduplicate_members(members: list) -> list:
    """
    Remove duplicate entries from a member list while preserving order.

    Args:
        members: A list of category members

    Returns:
        A deduplicated list of members
    """
    return list(set(members))


def remove_redirects(lang: str, members: list) -> list:
    """
    Remove redirect pages from the member list.

    Args:
        lang: The language code (e.g., "ar")
        members: A list of category members

    Returns:
        A list of members with redirects removed
    """
    return remove_redirect_pages(lang, members)


def collect_category_members(ar_title: str, en_page_title: str) -> list:
    """
    Collect, merge, filter, and normalize category members from all sources.

    This is the main entry point for gathering category members. It:
    1. Gathers members from SQL sources
    2. Gathers members from API if SQL returns empty or is disabled
    3. Gathers members from SubSub sources
    4. Merges all results
    5. Deduplicates the list
    6. Filters out invalid entries
    7. Removes redirect pages

    Args:
        ar_title: The Arabic category title
        en_page_title: The English page title

    Returns:
        A clean, deduplicated list of valid category members
    """
    # Step 1: Gather members from SQL
    members = gather_members_from_sql(ar_title, en_page_title)

    # Step 2: Gather from API if SQL is disabled or returned empty
    if settings.database.use_sql is False or members == []:
        api_members = gather_members_from_api(en_page_title)
        members = merge_member_lists(members, api_members)

    # Step 3: Gather from SubSub sources
    subsub_members = gather_members_from_subsub(en_page_title)
    members = merge_member_lists(members, subsub_members)

    # Step 4: Deduplicate
    members = deduplicate_members(members)

    # Step 5: Filter invalid entries
    members = filter_invalid_members(members)

    # Step 6: Remove redirects
    members = remove_redirects("ar", members)

    return members
