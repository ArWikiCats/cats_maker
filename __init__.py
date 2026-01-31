# try:
from .src import (
    ToMakeNewCat2222,
    ar_make_lab,
    create_categories_from_list,
    make_category,
    no_work,
    process_catagories,
)
# except ImportError:
#     # Skip imports when running as a standalone package (e.g., during testing)
#     print("ImportError in cats_maker_new/__init__.py")
#     pass

__all__ = [
    "no_work",
    "ToMakeNewCat2222",
    "process_catagories",
    "create_categories_from_list",
    "make_category",
    "ar_make_lab",
]
