"""
NOTE: ar_make_lab, create_categories_from_list, process_catagories
    is used by external scripts and should not be changed.

from cats_maker import (
    process_catagories,
    create_categories_from_list,
    ar_make_lab,
)
"""

import os
from pathlib import Path

_arwikicats_path = os.getenv("ARWIKICATS_PATH")
if _arwikicats_path:
    _arwikicats_path = Path(_arwikicats_path)
    if _arwikicats_path.exists():
        sys.path.insert(0, str(_arwikicats_path.parent))

from .mk_cats import (  # noqa: E402
    ar_make_lab,
    create_categories_from_list,
    process_catagories,
)

__all__ = [
    "ar_make_lab",
    "create_categories_from_list",
    "process_catagories",
]
