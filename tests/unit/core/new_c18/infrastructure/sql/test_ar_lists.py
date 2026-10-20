"""
Unit tests for src/cats_maker/core/new_c18/infrastructure/sql/ar_lists.py module.
"""

from types import SimpleNamespace

import pytest

from src.cats_maker.core.new_c18.infrastructure.sql.ar_lists import (
    ArCategorySQL,
)


class FakeDB:
    """Fake replica client: records the last query and returns canned rows."""

    def __init__(self, rows=None, should_fail=False):
        self.dbname = "ar"
        self.rows = rows or []
        self.should_fail = should_fail
        self.last_query: str = ""
        self.last_params = {}
        self.calls = 0
        self.loaded = {}

    def select(self, query, params=None):
        self.calls += 1
        self.last_query = query
        self.last_params = params
        if self.should_fail:
            raise RuntimeError("Database error")
        return self.rows

    def load(self, dbname, wrapper=None):
        """Mimic ReplicaClient.load; return (and remember) a separate fake."""
        other = FakeDB(rows=self.rows, should_fail=self.should_fail)
        other.dbname = dbname
        self.loaded[dbname] = other
        return other


class FakeWrapper:
    def __init__(self, can_use=True, ns_filter="0, 10, 14"):
        self._can_use = can_use
        self.config = SimpleNamespace(sql_ns_filter=ns_filter)

    def can_use_sql(self):
        return self._can_use


class FakeNamespaceHandler:
    """Prefixes titles by namespace id, like the real handler would."""

    PREFIXES = {"0": "", "10": "قالب:", "14": "تصنيف:"}

    def __init__(self):
        self.calls = []

    def get_full_title(self, title, ns):
        self.calls.append((title, ns))
        return f"{self.PREFIXES.get(ns, '')}{title}"


def make_sql(
    rows=None,
    *,
    can_use=True,
    should_fail=False,
) -> tuple[ArCategorySQL, FakeDB, FakeNamespaceHandler]:
    db = FakeDB(rows=rows, should_fail=should_fail)
    handler = FakeNamespaceHandler()
    wrapper = FakeWrapper(can_use=can_use)

    client = ArCategorySQL(
        client=db,  # pyright: ignore[reportArgumentType]
        wrapper=wrapper,  # pyright: ignore[reportArgumentType]
        ar_ns_handler=handler,  # pyright: ignore[reportArgumentType]
    )
    return client, db, handler


class TestInit:
    def test_uses_injected_dependencies(self):
        sql, db, handler = make_sql()
        assert sql.client is db
        assert sql.ar_ns_handler is handler
        assert sql.can_use_sql is True

    def test_can_use_sql_false_is_propagated(self):
        sql, _, _ = make_sql(can_use=False)
        assert sql.can_use_sql is False


class TestRemoveCategoryPrefix:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("تصنيف:علوم", "علوم"),
            ("تصنيف:علوم_الحاسوب", "علوم_الحاسوب"),
            ("علوم", "علوم"),
            ("تصنيف:", ""),
            ("", ""),
        ],
    )
    def test_remove_prefix(self, title, expected):
        sql, _, _ = make_sql()
        assert sql.remove_category_prefix(title) == expected

    def test_only_leading_prefix_is_removed(self):
        sql, _, _ = make_sql()
        assert sql.remove_category_prefix("تصنيف:تصنيف:علوم") == "تصنيف:علوم"


class TestFetchArCategoryMembers:
    """Tests for ArCategorySQL.sql_retrieve_category_members_list."""

    def test_returns_empty_when_sql_disabled(self):
        sql, db, _ = make_sql(can_use=False)
        assert sql.sql_retrieve_category_members_list("تصنيف:علوم") == []
        assert db.calls == 0

    def test_strips_prefix_and_replaces_spaces_in_param(self):
        sql, db, _ = make_sql(rows=[])
        sql.sql_retrieve_category_members_list("تصنيف:علوم الحاسوب")
        assert db.last_params == ["علوم_الحاسوب"]

    def test_param_without_prefix(self):
        sql, db, _ = make_sql(rows=[])
        sql.sql_retrieve_category_members_list("علوم الحاسوب")
        assert db.last_params == ["علوم_الحاسوب"]

    def test_query_filters_on_category_namespace(self):
        sql, db, _ = make_sql(rows=[])
        sql.sql_retrieve_category_members_list("تصنيف:علوم")
        assert "lt_namespace = 14" in db.last_query
        assert "lt_title = %s" in db.last_query
        assert db.last_query.count("%s") == len(db.last_params)

    def test_empty_result(self):
        sql, _, _ = make_sql(rows=[])
        assert sql.sql_retrieve_category_members_list("تصنيف:علوم") == []

    def test_titles_get_namespace_prefix(self):
        rows = [
            {"page_title": "فيزياء", "page_namespace": 0},
            {"page_title": "قالب_معلومات", "page_namespace": 10},
            {"page_title": "تصنيف_فرعي", "page_namespace": 14},
        ]
        sql, _, _ = make_sql(rows=rows)
        assert sql.sql_retrieve_category_members_list("تصنيف:علوم") == [
            "فيزياء",
            "قالب:قالب معلومات",
            "تصنيف:تصنيف فرعي",
        ]

    def test_namespace_is_passed_to_handler_as_string(self):
        rows = [{"page_title": "فيزياء_نظرية", "page_namespace": 0}]
        sql, _, handler = make_sql(rows=rows)
        sql.sql_retrieve_category_members_list("تصنيف:علوم")
        assert handler.calls == [("فيزياء نظرية", "0")]

    def test_result_order_is_preserved(self):
        rows = [
            {"page_title": "ج", "page_namespace": 0},
            {"page_title": "أ", "page_namespace": 0},
            {"page_title": "ب", "page_namespace": 0},
        ]
        sql, _, _ = make_sql(rows=rows)
        assert sql.sql_retrieve_category_members_list("تصنيف:علوم") == ["ج", "أ", "ب"]

    def test_database_error_propagates(self):
        sql, _, _ = make_sql(should_fail=True)
        with pytest.raises(RuntimeError, match="Database error"):
            sql.sql_retrieve_category_members_list("تصنيف:علوم")


class TestFetchDontAddPages:
    def test_returns_empty_when_sql_disabled(self):
        sql, db, _ = make_sql(can_use=False)
        assert sql.fetch_dont_add_pages() == []
        assert db.calls == 0

    def test_query_targets_template_and_namespaces(self):
        sql, db, _ = make_sql(rows=[])
        sql.fetch_dont_add_pages()
        assert "لا_للتصنيف_المعادل" in db.last_query
        assert "page_namespace IN (0, 10)" in db.last_query
        assert "lt_namespace = 10" in db.last_query

    def test_query_has_no_params(self):
        sql, db, _ = make_sql(rows=[])
        sql.fetch_dont_add_pages()
        assert not db.last_params

    def test_empty_result(self):
        sql, _, _ = make_sql(rows=[])
        assert sql.fetch_dont_add_pages() == []

    def test_titles_get_namespace_prefix(self):
        rows = [
            {"page_title": "مقالة_مستثناة", "page_namespace": 0},
            {"page_title": "قالب_مستثنى", "page_namespace": 10},
        ]
        sql, _, _ = make_sql(rows=rows)
        assert sql.fetch_dont_add_pages() == [
            "مقالة مستثناة",
            "قالب:قالب مستثنى",
        ]

    def test_namespace_is_passed_to_handler_as_string(self):
        rows = [{"page_title": "مقالة", "page_namespace": 10}]
        sql, _, handler = make_sql(rows=rows)
        sql.fetch_dont_add_pages()
        assert handler.calls == [("مقالة", "10")]

    def test_database_error_propagates(self):
        sql, _, _ = make_sql(should_fail=True)
        with pytest.raises(RuntimeError, match="Database error"):
            sql.fetch_dont_add_pages()
