"""
Unit tests for src/cats_maker/core/new_c18/io/en_lists.py module.
"""

from src.cats_maker.core.new_c18.new_config import C18Config
from src.cats_maker.core.new_c18.infrastructure.sql.en_lists import (
    EnCategorySQL,
)


class FakeDB:
    def __init__(self, rows=None, should_fail=False):
        self.dbname = "en"
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


class TestFetchEnCategoryLanglinks:
    def test_returns_rows(self):
        fake_db = FakeDB(rows=[{"ll_title": "علوم"}])
        service = EnCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.fetch_arabic_titles_from_en_category("Science")
        assert len(result) == 1

    def test_strips_category_prefix(self):
        fake_db = FakeDB(rows=[])
        service = EnCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        service.fetch_arabic_titles_from_en_category("Category:Science")
        assert fake_db.last_params == ("Science",)

    def test_returns_empty_on_error(self):
        fake_db = FakeDB(should_fail=True)

        service = EnCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.fetch_arabic_titles_from_en_category("test")
        assert result == []
