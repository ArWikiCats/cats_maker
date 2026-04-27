"""
NOTE: ar_make_lab, create_categories_from_list, process_catagories
    is used by external scripts and should not be changed.

from cats_maker_new import (
    process_catagories,
    create_categories_from_list,
    ar_make_lab,
)
"""

import os
import sys
from pathlib import Path

# Optional ArWikiCats integration - configure via environment variable
arwikicats_path = os.getenv("ARWIKICATS_PATH", "D:/categories_bot/make2_new/ArWikiCats")
if arwikicats_path:
    arwikicats_path = Path(arwikicats_path)
    if arwikicats_path.exists():
        sys.path.insert(0, str(arwikicats_path.parent))


from .logging_config import setup_logging
from .mk_cats import (
    ar_make_lab,
    create_categories_from_list,
    process_catagories,
)

name = Path(__file__).parent.name
setup_logging(level="DEBUG", name=name)

__all__ = [
    "ar_make_lab",
    "create_categories_from_list",
    "process_catagories",
]
