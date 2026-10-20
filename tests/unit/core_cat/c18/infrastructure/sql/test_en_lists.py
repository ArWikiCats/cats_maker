"""
Unit tests for src/cats_maker/core_cat/infrastructure/sql/en_lists.py module.
"""

from types import SimpleNamespace

import pytest

from src.cats_maker.core_cat.c18.infrastructure.sql.en_lists import (
    EnCategorySQL,
)


class FakeDB:
    """Fake replica client: records the last query and returns canned rows."""

    def __init__(self, rows=None, should_fail=False):
        self.dbname = "en"
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


def make_sql(
    rows=None,
    *,
    can_use=True,
    should_fail=False,
    ns_filter="0, 10, 14",
    en_false_templates: list[str] | None = None,
) -> tuple[EnCategorySQL, FakeDB]:
    db = FakeDB(rows=rows, should_fail=should_fail)
    wrapper = FakeWrapper(can_use=can_use, ns_filter=ns_filter)

    en_false_templates = en_false_templates if en_false_templates is not None else ["Some template", "Other_template"]

    client = EnCategorySQL(
        client=db,  # pyright: ignore[reportArgumentType]
        wrapper=wrapper,  # pyright: ignore[reportArgumentType]
        en_false_templates=en_false_templates,
    )
    return client, db


class TestInit:
    def test_uses_injected_dependencies(self):
        sql, db = make_sql(ns_filter="0, 14")
        assert sql.client is db
        assert sql.can_use_sql is True
        assert sql.sql_ns_filter == "0, 14"

    def test_can_use_sql_false_is_propagated(self):
        sql, _ = make_sql(can_use=False)
        assert sql.can_use_sql is False

    def test_explicit_config_overrides_wrapper_config(self):
        config = SimpleNamespace(sql_ns_filter="14")
        sql = EnCategorySQL(client=FakeDB(), wrapper=FakeWrapper(), config=config)
        assert sql.config is config
        assert sql.sql_ns_filter == "14"


class TestRemoveCategoryPrefix:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Category:Foo", "Foo"),
            ("category:Foo", "Foo"),
            ("[[Category:Foo]]", "Foo"),
            ("Category talk:Foo", "Foo"),
            ("category talk:Foo", "Foo"),
            ("  Category:Foo  ", "Foo"),
            ("Foo", "Foo"),
            ("Category:", ""),
            ("", ""),
        ],
    )
    def test_remove_prefix(self, title, expected):
        sql, _ = make_sql()
        assert sql.remove_category_prefix(title) == expected


class TestGetFalseTemplateParams:
    def test_spaces_replaced_with_underscores(self):
        sql, _ = make_sql()
        params, placeholders = sql.get_false_template_params()
        assert params == ["Some_template", "Other_template"]
        assert placeholders == "%s, %s"

    def test_empty_templates_gives_empty_string_placeholder(self, monkeypatch):
        sql, _ = make_sql(en_false_templates=[])
        params, placeholders = sql.get_false_template_params()
        assert params == []
        assert placeholders == "''"

    def test_returns_new_list_each_call(self):
        sql, _ = make_sql()
        first, _ = sql.get_false_template_params()
        first.append("mutated")
        second, _ = sql.get_false_template_params()
        assert "mutated" not in second


class TestFetchArabicTitlesFromEnCategory:
    def test_returns_empty_when_sql_disabled(self):
        sql, db = make_sql(can_use=False)
        assert sql.fetch_arabic_titles_from_en_category("Category:Foo") == []
        assert db.calls == 0

    @pytest.mark.parametrize("title", ["", "Category:", "[[Category:]]", "   "])
    def test_invalid_category_returns_empty_without_query(self, title):
        sql, db = make_sql()
        assert sql.remove_category_prefix(title) == ""
        assert sql.fetch_arabic_titles_from_en_category(title) == []
        assert db.calls == 0, f"{title=} should not trigger a query"

    def test_normalizes_title_and_passes_param(self):
        sql, db = make_sql(rows=[])
        sql.fetch_arabic_titles_from_en_category("Category:Foo bar baz")
        assert db.last_params == ["Foo_bar_baz"]

    def test_query_contains_namespace_filter_and_ar_lang(self):
        sql, db = make_sql(rows=[], ns_filter="0, 14")
        sql.fetch_arabic_titles_from_en_category("Category:Foo")
        assert "p1.page_namespace IN (0, 14)" in db.last_query
        assert "ll_lang = 'ar'" in db.last_query
        assert "lt.lt_namespace = 14" in db.last_query
        assert "%s" in db.last_query

    def test_underscores_replaced_in_results(self):
        rows = [{"ll_title": "مقالة_أولى"}, {"ll_title": "مقالة_ثانية"}]
        sql, _ = make_sql(rows=rows)
        assert sql.fetch_arabic_titles_from_en_category("Category:Foo") == [
            "مقالة أولى",
            "مقالة ثانية",
        ]

    def test_empty_and_missing_titles_are_skipped(self):
        rows = [{"ll_title": "أ"}, {"ll_title": ""}, {"ll_title": None}, {}]
        sql, _ = make_sql(rows=rows)
        assert sql.fetch_arabic_titles_from_en_category("Category:Foo") == ["أ"]

    def test_duplicates_removed_preserving_order(self):
        rows = [{"ll_title": "ب"}, {"ll_title": "أ"}, {"ll_title": "ب"}, {"ll_title": "ج"}]
        sql, _ = make_sql(rows=rows)
        assert sql.fetch_arabic_titles_from_en_category("Category:Foo") == ["ب", "أ", "ج"]

    def test_no_rows_returns_empty_list(self):
        sql, _ = make_sql(rows=[])
        assert sql.fetch_arabic_titles_from_en_category("Category:Foo") == []

    def test_same_site_code_does_not_load_new_client(self):
        sql, db = make_sql(rows=[{"ll_title": "أ"}])
        sql.fetch_arabic_titles_from_en_category("Category:Foo", site_code="en")
        assert db.loaded == {}
        assert db.calls == 1

    def test_other_site_code_loads_separate_client(self):
        sql, db = make_sql(rows=[{"ll_title": "أ"}])
        result = sql.fetch_arabic_titles_from_en_category("Category:Foo", site_code="fr")
        assert result == ["أ"]
        assert "frwiki" in db.loaded
        # The original client must not be used for the query
        assert db.calls == 0
        assert db.loaded["frwiki"].calls == 1
        assert db.loaded["frwiki"].last_params == ["Foo"]

    def test_database_error_propagates(self):
        sql, _ = make_sql(should_fail=True)
        with pytest.raises(RuntimeError, match="Database error"):
            sql.fetch_arabic_titles_from_en_category("Category:Foo")


class TestGetCategoriesLike:
    def test_returns_empty_when_sql_disabled(self):
        sql, db = make_sql(can_use=False)
        assert sql.get_categories_like("Foo") == []
        assert db.calls == 0

    @pytest.mark.parametrize("pattern", ["", "   ", "\t\n"])
    def test_blank_pattern_returns_empty(self, pattern):
        sql, db = make_sql()
        assert sql.get_categories_like(pattern) == []
        assert db.calls == 0

    def test_params_order_without_offset(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo bar", limit=10)
        assert db.last_params == [
            "%Foo_bar%",
            "%Foo_bar",
            "CS1_%",
            "Some_template",
            "Other_template",
            10,
        ]
        assert "OFFSET" not in db.last_query

    def test_params_order_with_offset(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo", limit=10, offset=20)
        assert db.last_params[-2:] == [10, 20]
        assert "OFFSET %s" in db.last_query

    def test_string_limit_and_offset_are_cast_to_int(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo", limit="5", offset="7")
        assert db.last_params[-2:] == [5, 7]

    def test_default_limit_is_600(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo")
        assert db.last_params[-1] == 600

    def test_zero_offset_omits_offset_clause(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo", offset=0)
        assert "OFFSET" not in db.last_query

    def test_placeholder_count_matches_params(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo", limit=10, offset=3)
        assert db.last_query.count("%s") == len(db.last_params)

    def test_placeholder_count_matches_params_without_offset(self):
        sql, db = make_sql(rows=[])
        sql.get_categories_like("Foo", limit=10)
        assert db.last_query.count("%s") == len(db.last_params)

    def test_query_uses_namespace_filter(self):
        sql, db = make_sql(rows=[], ns_filter="0, 14")
        sql.get_categories_like("Foo")
        assert "p1.page_namespace IN (0, 14)" in db.last_query

    def test_invalid_limit_raises_value_error(self):
        sql, _ = make_sql()
        with pytest.raises(ValueError):
            sql.get_categories_like("Foo", limit="abc")

    def test_results_have_underscores_replaced(self):
        rows = [
            {"category_title": "Category:Foo_bar"},
            {"category_title": "Category:Baz_qux_quux"},
        ]
        sql, _ = make_sql(rows=rows)
        assert sql.get_categories_like("Foo") == [
            "Category:Foo bar",
            "Category:Baz qux quux",
        ]

    def test_empty_result(self):
        sql, _ = make_sql(rows=[])
        assert sql.get_categories_like("Foo") == []

    def test_database_error_propagates(self):
        sql, _ = make_sql(should_fail=True)
        with pytest.raises(RuntimeError, match="Database error"):
            sql.get_categories_like("Foo")


class TestMake24Cat:
    def test_returns_empty_when_sql_disabled(self):
        sql, db = make_sql(can_use=False)
        assert sql.make_24_cat() == []
        assert db.calls == 0

    def test_params_order_and_default_limit(self):
        sql, db = make_sql(rows=[])
        sql.make_24_cat()
        assert db.last_params == ["Some_template", "Other_template", "%Wikipedia%", 500]

    def test_custom_limit(self):
        sql, db = make_sql(rows=[])
        sql.make_24_cat(sql_limit=42)
        assert db.last_params[-1] == 42

    def test_placeholder_count_matches_params(self):
        sql, db = make_sql(rows=[])
        sql.make_24_cat()
        assert db.last_query.count("%s") == len(db.last_params)

    def test_query_targets_recent_new_categories(self):
        sql, db = make_sql(rows=[])
        sql.make_24_cat()
        assert "recentchanges" in db.last_query
        assert "rc_namespace=14" in db.last_query
        assert "mw.new" in db.last_query

    def test_results_have_underscores_replaced(self):
        rows = [{"title": "Category:New_cat"}, {"title": "Category:Another_new_cat"}]
        sql, _ = make_sql(rows=rows)
        assert sql.make_24_cat() == ["Category:New cat", "Category:Another new cat"]

    def test_empty_result(self):
        sql, _ = make_sql(rows=[])
        assert sql.make_24_cat() == []

    def test_database_error_propagates(self):
        sql, _ = make_sql(should_fail=True)
        with pytest.raises(RuntimeError, match="Database error"):
            sql.make_24_cat()
