"""
NOTE: ar_make_lab, create_categories_from_list, process_catagories
    is used by external scripts and should not be changed.

from cats_maker_new import (
    process_catagories,
    create_categories_from_list,
    ar_make_lab,
)
"""

from pathlib import Path

from .core.mk_cats import (
    ar_make_lab,
    create_categories_from_list,
    process_catagories,
)
from .logging_config import setup_logging

name = Path(__file__).parent.name
setup_logging(level="DEBUG", name=name)

__all__ = [
    "ar_make_lab",
    "process_catagories",
    "create_categories_from_list",
]
