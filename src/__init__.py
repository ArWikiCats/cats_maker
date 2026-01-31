
from pathlib import Path

from .logging_config import setup_logging
from .mk_cats import (
    ToMakeNewCat2222,
    ar_make_lab,
    create_categories_from_list,
    make_category,
    no_work,
    process_catagories,
)

name = Path(__file__).parent.name
setup_logging(level="DEBUG", name=name)

__all__ = [
    "no_work",
    "ToMakeNewCat2222",
    "process_catagories",
    "create_categories_from_list",
    "make_category",
    "ar_make_lab",
]
