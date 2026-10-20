"""
Unit tests for src/cats_maker/core/new_c18/io/ar_lists.py module.
"""

from src.cats_maker.core.new_c18.new_config import C18Config
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


class TestFetchArCategoryMembers:
    def test_fetch_ar_category_members_success(self):
        fake_db = FakeDB(rows=[{"page_title": "Test_Page", "page_namespace": 0}])

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )

        result = service.sql_retrieve_category_members_list("تصنيف:Test")

        assert result == [{"page_title": "Test_Page", "page_namespace": 0}]
        assert fake_db.last_params == ("Test",)

    def test_fetch_ar_category_members_unavailable_sql(self):
        service = ArCategorySQL(
            config=C18Config(use_sql=True),
        )
        assert service.sql_retrieve_category_members_list("Test") == []

    def test_returns_rows(self):
        fake_db = FakeDB(rows=[{"page_title": "Test", "page_namespace": 0}])

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.sql_retrieve_category_members_list("تصنيف:علوم")
        assert len(result) == 1
        assert fake_db.last_params == ("علوم",)

    def test_strips_prefix_and_spaces(self):
        fake_db = FakeDB(rows=[])

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        service.sql_retrieve_category_members_list("تصنيف:علوم الطبيعة")
        assert fake_db.last_params == ("علوم_الطبيعة",)

    def test_returns_empty_on_error(self):
        fake_db = FakeDB(should_fail=True)

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.sql_retrieve_category_members_list("test")
        assert result == []


class TestFetchDontAddPages:
    def test_returns_prefixed_titles(self):
        fake_db = FakeDB(rows=[{"page_title": "Test", "page_namespace": 10}])

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.fetch_dont_add_pages()
        assert result == ["قالب:Test"]

    def test_returns_empty_on_error(self):
        fake_db = FakeDB(should_fail=True)

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )
        result = service.fetch_dont_add_pages()
        assert result == []

    def test_fetch_dont_add_pages_success(self):
        fake_db = FakeDB(rows=[{"page_title": "Page1", "page_namespace": 10}])

        service = ArCategorySQL(
            client=fake_db,  # pyright: ignore[reportArgumentType]
            config=C18Config(use_sql=True),
        )

        result = service.fetch_dont_add_pages()

        assert result == ["قالب:Page1"]
