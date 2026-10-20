# config.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class C18Config:
    """
    Central configuration
    """

    # --- Matching / lookup ---
    include_source_title: bool = False
    """Include category title in CatProcessor.process_titles"""

    # --- Create new categories ---
    create_en_cats: bool = True
    """If True, automatic create missing categories in arwiki."""

    use_cache: bool = True
    """Use cache in many files like: TemplateClient/LangLinksClient."""

    dev_mode: bool = False
    """If True, don't save anything to the wiki."""

    # --- Save changes ---
    auto_save: bool = True
    """If True, automatically (Save changes/Create pages) to the wiki."""

    sql_ns_filter: str = "0, 10, 14"
    """Namespace filter for SQL queries."""

    use_sql: bool = True
    """If True, use SQL queries to get categories, if False use API."""

    def with_updates(self, **kwargs) -> C18Config:
        """Return a new config with the given fields replaced."""
        from dataclasses import replace

        return replace(self, **kwargs)


__all__ = [
    "C18Config",
]
