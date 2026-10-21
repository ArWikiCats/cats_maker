"""
NOTE: ar_make_lab, create_categories_from_list, process_categories
    is used by external scripts and should not be changed.

from cats_maker import (
    process_categories,
    create_categories_from_list,
    ar_make_lab,
)
"""

import logging

from .mk_cats import (
    ar_make_lab,
    create_categories_from_list,
    process_categories,
)

try:
    from ArWikiCats import resolve_arabic_category_label  # type: ignore  # noqa: F401
except ImportError:
    logging.warning("ArWikiCats not available.")
    msg = """
    Please install ArWikiCats from https://github.com/ArWikiCats/ArWikiCats
        - `pip install git+https://github.com/ArWikiCats/ArWikiCats.git -U`
        or clone ArWikiCats into your workspace and inside `ArWikiCats` folder run:
        - `pip install -e .`
    """
    logging.error(msg)


__all__ = [
    "ar_make_lab",
    "create_categories_from_list",
    "process_categories",
]
