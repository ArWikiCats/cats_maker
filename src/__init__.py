try:
    from .logging_config import setup_logging
    from .mk_cats import (
        ToMakeNewCat2222,
        ar_make_lab,
        create_categories_from_list,
        make_category,
        no_work,
        process_catagories,
    )

    setup_logging(level="DEBUG", name="src")

except ImportError:
    # Skip imports when running as a standalone package (e.g., during testing)
    print("ImportError in cats_maker_new/src/__init__.py")
    pass

__all__ = [
    "no_work",
    "ToMakeNewCat2222",
    "process_catagories",
    "create_categories_from_list",
    "make_category",
    "ar_make_lab",
]
