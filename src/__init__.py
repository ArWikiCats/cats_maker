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

from .logging_config import setup_logging

use_colorlog = False
# Optional ArWikiCats integration - configure via environment variable
_arwikicats_path = os.getenv("ARWIKICATS_PATH")
if _arwikicats_path:
    use_colorlog = True
    _arwikicats_path = Path(_arwikicats_path)
    if _arwikicats_path.exists():
        sys.path.insert(0, str(_arwikicats_path.parent))

from .mk_cats import (  # noqa: E402
    ar_make_lab,
    create_categories_from_list,
    process_catagories,
)

name = Path(__file__).parent.name

setup_logging(level="DEBUG", name=name, use_colorlog=use_colorlog)

__all__ = [
    "ar_make_lab",
    "create_categories_from_list",
    "process_catagories",
]
