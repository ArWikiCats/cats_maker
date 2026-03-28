from pathlib import Path

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
    "process_catagories",
    "create_categories_from_list",
]
