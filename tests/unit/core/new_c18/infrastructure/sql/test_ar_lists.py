"""
Unit tests for src/cats_maker/core/new_c18/io/ar_lists.py module.
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.core.new_c18.infrastructure.sql.ar_lists import (
    ArCategorySQL,
)


class FakeDB:
    def __init__(self, rows=None, should_fail=False):
        self.rows = rows or []
        self.should_fail = should_fail
        self.last_query = None
        self.last_params = None

    def select_safe(self, query, params=None):
        self.last_query = query
        self.last_params = params
        if self.should_fail:
            raise RuntimeError("Database error")
        return self.rows


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock main settings."""
    mock_obj = MagicMock()
    mock_obj.query.ns_no_10 = False
    mock_obj.query.ns_only_14 = False
    return mock_obj


class TestFetchArCategoryMembers:
    def test_fetch_ar_category_members_success(self):
        fake_db = FakeDB(rows=[{"page_title": "Test_Page", "page_namespace": 0}])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )

        result = service.sql_retrieve_category_members_list("تصنيف:Test")

        assert result == [{"page_title": "Test_Page", "page_namespace": 0}]
        assert fake_db.last_params == ("Test",)

    def test_fetch_ar_category_members_unavailable_sql(self):
        service = ArCategorySQL(
            can_use_sql_fn=lambda: False,
        )
        assert service.sql_retrieve_category_members_list("Test") == []

    def test_returns_rows(self):
        fake_db = FakeDB(rows=[{"page_title": "Test", "page_namespace": 0}])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )
        result = service.sql_retrieve_category_members_list("تصنيف:علوم")
        assert len(result) == 1
        assert fake_db.last_params == ("علوم",)

    def test_strips_prefix_and_spaces(self):
        fake_db = FakeDB(rows=[])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )
        service.sql_retrieve_category_members_list("تصنيف:علوم الطبيعة")
        assert fake_db.last_params == ("علوم_الطبيعة",)

    def test_returns_empty_on_error(self):
        fake_db = FakeDB(should_fail=True)
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )
        result = service.sql_retrieve_category_members_list("test")
        assert result == []


class TestFetchEnCategoryLanglinks:
    def test_returns_rows(self, mock_settings: MagicMock):
        fake_db = FakeDB(rows=[{"ll_title": "علوم"}])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
            settings=mock_settings,
        )
        result = service.fetch_arabic_titles_from_en_category("Science")
        assert len(result) == 1

    def test_strips_category_prefix(self, mock_settings: MagicMock):
        fake_db = FakeDB(rows=[])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
            settings=mock_settings,
        )
        service.fetch_arabic_titles_from_en_category("Category:Science")
        assert fake_db.last_params == ("Science",)

    def test_returns_empty_on_error(self, mock_settings: MagicMock):
        fake_db = FakeDB(should_fail=True)
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
            settings=mock_settings,
        )
        result = service.fetch_arabic_titles_from_en_category("test")
        assert result == []


class TestFetchDontAddPages:
    def test_returns_prefixed_titles(self):
        fake_db = FakeDB(rows=[{"page_title": "Test", "page_namespace": 10}])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )
        result = service.fetch_dont_add_pages()
        assert result == ["قالب:Test"]

    def test_returns_empty_on_error(self):
        fake_db = FakeDB(should_fail=True)
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )
        result = service.fetch_dont_add_pages()
        assert result == []

    def test_fetch_dont_add_pages_success(self):
        fake_db = FakeDB(rows=[{"page_title": "Page1", "page_namespace": 10}])
        service = ArCategorySQL(
            db_factory=lambda _: fake_db,
            can_use_sql_fn=lambda: True,
        )

        result = service.fetch_dont_add_pages()

        assert result == ["قالب:Page1"]
