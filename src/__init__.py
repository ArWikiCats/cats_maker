""" """

from pathlib import Path

from .logger_config import setup_logging

use_colorlog = False

from .cats_maker import (  # noqa: E402
    ar_make_lab,
    create_categories_from_list,
    process_categories,
)

process_catagories = process_categories

name = Path(__file__).parent.name

setup_logging(level="DEBUG", name=name, use_colorlog=use_colorlog)

__all__ = [
    "ar_make_lab",
    "create_categories_from_list",
    "process_catagories",
]
