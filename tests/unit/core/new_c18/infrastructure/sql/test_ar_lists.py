"""
Unit tests for src/cats_maker/core/new_c18/io/ar_lists.py module.
"""

from src.cats_maker.core.new_c18.infrastructure.sql.ar_lists import (
    ArCategorySQL,
)


class FakeDB:
    def __init__(self, rows=None, should_fail=False):
        self.dbname = "ar"
        self.rows = rows or []
        self.should_fail = should_fail
        self.last_query = None
        self.last_params = None

    def select(self, query, params=None):
        self.last_query = query
        self.last_params = params
        if self.should_fail:
            raise RuntimeError("Database error")
        return self.rows


class TestFetchArCategoryMembers: ...


class TestFetchDontAddPages: ...
