"""
Unit tests for src/core/client_wiki/categories/category_db.py module.
"""

from unittest.mock import MagicMock

import pytest

from src.core.client_wiki.categories.category_db import CategoryDepth


@pytest.fixture
def mock_login_bot():
    return MagicMock()


@pytest.fixture
def bot(mock_login_bot):
    return CategoryDepth(mock_login_bot, title="Category:Test")


class TestCategoryDepthInit:
    def test_default_attributes(self, bot):
        assert bot.title == "Category:Test"
        assert bot.len_pages == 0
        assert bot.revids == {}
        assert bot.timestamps == {}
        assert bot.result_table == {}
        assert bot.gcmlimit == 1000
        assert bot.depth == 0
        assert bot.ns == "all"

    def test_kwargs_set_attributes(self, mock_login_bot):
        bot = CategoryDepth(mock_login_bot, title="Test", depth=3, ns="0")
        assert bot.depth == 3
        assert bot.ns == "0"


class TestParseParams:
    def test_sets_depth(self, bot):
        bot._parse_params(depth=5)
        assert bot.depth == 5

    def test_invalid_depth_prints_warning(self, bot, capsys):
        bot._parse_params(depth="invalid")
        # The try/except catches ValueError and prints, but later line overwrites
        captured = capsys.readouterr()
        assert "self.depth != int" in captured.out

    def test_sets_gcmlimit(self, bot):
        bot._parse_params(gcmlimit=500)
        assert bot.gcmlimit == 500

    def test_sets_only_titles(self, bot):
        bot._parse_params(only_titles=True)
        assert bot.only_titles is True

    def test_sets_with_lang(self, bot):
        bot._parse_params(with_lang="ar")
        assert bot.with_lang == "ar"

    def test_sets_without_lang(self, bot):
        bot._parse_params(without_lang="en")
        assert bot.without_lang == "en"

    def test_empty_kwargs_early_return(self, bot):
        bot.depth = 99
        bot._parse_params()
        assert bot.depth == 99


class TestDetermineGcmtype:
    def test_removes_gcmsort_when_no_gcm_sort(self, bot):
        bot.no_gcm_sort = True
        params = {"gcmsort": "timestamp", "gcmdir": "newer", "other": "val"}
        result = bot._determine_gcmtype(params)
        assert "gcmsort" not in result
        assert "gcmdir" not in result
        assert result["other"] == "val"

    def test_keeps_gcmsort_when_gcm_sort_enabled(self, bot):
        bot.no_gcm_sort = False
        params = {"gcmsort": "timestamp", "gcmdir": "newer"}
        result = bot._determine_gcmtype(params)
        assert "gcmsort" in result


class TestBuildPropList:
    def test_default_includes_revisions(self, bot):
        result = bot._build_prop_list()
        assert "revisions" in result

    def test_no_props_returns_empty(self, bot):
        bot.no_props = True
        result = bot._build_prop_list()
        assert result == []

    def test_no_gcm_sort_excludes_revisions(self, bot):
        bot.no_gcm_sort = True
        result = bot._build_prop_list()
        assert "revisions" not in result

    def test_template_whitelist_adds_templates(self, bot):
        bot.template_whitelist = ["Template:A"]
        result = bot._build_prop_list()
        assert "templates" in result

    def test_with_lang_adds_langlinks(self, bot):
        bot.with_lang = "ar"
        result = bot._build_prop_list()
        assert "langlinks" in result

    def test_without_lang_adds_langlinks(self, bot):
        bot.without_lang = "en"
        result = bot._build_prop_list()
        assert "langlinks" in result


class TestExtractTimestampRevid:
    def test_extracts_data(self, bot):
        caca = {"revisions": [{"timestamp": "2024-01-01T00:00:00Z", "revid": 123}]}
        ts, revid = bot._extract_timestamp_revid(caca)
        assert ts == "2024-01-01T00:00:00Z"
        assert revid == 123

    def test_missing_revisions(self, bot):
        caca = {}
        ts, revid = bot._extract_timestamp_revid(caca)
        assert ts == ""
        assert revid == ""


class TestFilterByNamespace:
    def test_ns_14_filters_non_subcats(self, bot):
        bot.ns = "14"
        assert bot._filter_by_namespace("0") is False
        assert bot._filter_by_namespace("14") is True

    def test_ns_0_filters_non_articles(self, bot):
        bot.ns = "0"
        assert bot._filter_by_namespace("14") is False
        assert bot._filter_by_namespace("0") is True

    def test_ns_all_passes_all(self, bot):
        bot.ns = "all"
        assert bot._filter_by_namespace("0") is True
        assert bot._filter_by_namespace("14") is True

    def test_nslist_14_filters(self, bot):
        bot.nslist = [14]
        assert bot._filter_by_namespace("0") is False
        assert bot._filter_by_namespace("14") is True


class TestMergeTemplates:
    def test_merges_new_templates(self, bot):
        tablese = {}
        caca = {"templates": [{"title": "قالب:A"}, {"title": "قالب:B"}]}
        bot._merge_templates(tablese, caca)
        assert set(tablese["templates"]) == {"قالب:A", "قالب:B"}

    def test_extends_existing_templates(self, bot):
        tablese = {"templates": ["قالب:A"]}
        caca = {"templates": [{"title": "قالب:B"}]}
        bot._merge_templates(tablese, caca)
        assert set(tablese["templates"]) == {"قالب:A", "قالب:B"}

    def test_deduplicates(self, bot):
        tablese = {"templates": ["قالب:A"]}
        caca = {"templates": [{"title": "قالب:A"}]}
        bot._merge_templates(tablese, caca)
        assert tablese["templates"].count("قالب:A") == 1

    def test_no_templates(self, bot):
        tablese = {}
        caca = {"templates": []}
        bot._merge_templates(tablese, caca)
        assert "templates" not in tablese


class TestMergeLanglinks:
    def test_merges_langlinks(self, bot):
        tablese = {}
        caca = {"langlinks": [{"lang": "en", "title": "Science"}]}
        bot._merge_langlinks(tablese, caca)
        assert tablese["langlinks"] == {"en": "Science"}

    def test_uses_star_key(self, bot):
        tablese = {}
        caca = {"langlinks": [{"lang": "fr", "*": "Science"}]}
        bot._merge_langlinks(tablese, caca)
        assert tablese["langlinks"] == {"fr": "Science"}

    def test_no_langlinks(self, bot):
        tablese = {}
        caca = {"langlinks": []}
        bot._merge_langlinks(tablese, caca)
        assert "langlinks" not in tablese


class TestMergeCategories:
    def test_merges_categories(self, bot):
        tablese = {}
        caca = {"categories": [{"title": "تصنيف:A"}]}
        bot._merge_categories(tablese, caca)
        assert tablese["categories"] == ["تصنيف:A"]

    def test_extends_existing(self, bot):
        tablese = {"categories": ["تصنيف:A"]}
        caca = {"categories": [{"title": "تصنيف:B"}]}
        bot._merge_categories(tablese, caca)
        assert tablese["categories"] == ["تصنيف:A", "تصنيف:B"]


class TestPagesTableWork:
    def test_processes_pages(self, bot):
        table = {}
        pages = {
            "Page1": {
                "title": "Page1",
                "ns": 0,
                "revisions": [{"timestamp": "2024-01-01T00:00:00Z", "revid": 100}],
            }
        }
        result = bot.pages_table_work(table, pages)
        assert "Page1" in result
        assert bot.len_pages == 1

    def test_skips_filtered_namespace(self, bot):
        bot.ns = "14"
        table = {}
        pages = {
            "Page1": {
                "title": "Page1",
                "ns": 0,
                "revisions": [{"timestamp": "2024-01-01T00:00:00Z", "revid": 100}],
            }
        }
        result = bot.pages_table_work(table, pages)
        assert "Page1" not in result


class TestAddToResultTable:
    def test_basic_add(self, bot):
        bot.add_to_result_table("Page1", {"ns": 0})
        assert "Page1" in bot.result_table

    def test_without_lang_filter(self, bot):
        bot.without_lang = "en"
        bot.add_to_result_table("Page1", {"langlinks": {"en": "Page1"}})
        assert "Page1" not in bot.result_table

    def test_with_lang_filter_no_match(self, bot):
        bot.with_lang = "ar"
        bot.add_to_result_table("Page1", {"langlinks": {"en": "Page1"}})
        assert "Page1" not in bot.result_table

    def test_with_lang_filter_match(self, bot):
        bot.with_lang = "ar"
        bot.add_to_result_table("Page1", {"langlinks": {"ar": "صفحة1"}})
        assert "Page1" in bot.result_table

    def test_onlyns_filter(self, bot):
        bot.onlyns = 14
        bot.add_to_result_table("Page1", {"ns": 0})
        assert "Page1" not in bot.result_table

    def test_only_titles_mode(self, bot):
        bot.only_titles = True
        bot.add_to_result_table("Page1", {"ns": 0})
        assert "Page1" in bot.result_table
        assert bot.result_table["Page1"] == {}

    def test_merges_existing_entry(self, bot):
        bot.result_table["Page1"] = {"existing": True}
        bot.add_to_result_table("Page1", {"new": True})
        assert bot.result_table["Page1"]["existing"] is True
        assert bot.result_table["Page1"]["new"] is True


class TestGetRevids:
    def test_returns_revids(self, bot):
        bot.revids = {"Page1": 123}
        assert bot.get_revids() == {"Page1": 123}


class TestGetLenPages:
    def test_returns_len_pages(self, bot):
        bot.len_pages = 42
        assert bot.get_len_pages() == 42


class TestParamsWork:
    def test_adds_prop_string(self, bot):
        bot.props = ["categories"]
        bot.no_gcm_sort = False
        params = {"gcmsort": "timestamp", "gcmdir": "newer"}
        result = bot.params_work(params)
        assert "prop" in result

    def test_gcmtype_for_ns_0(self, bot):
        bot.ns = "0"
        bot.no_gcm_sort = True
        params = {"gcmsort": "timestamp", "gcmdir": "newer"}
        result = bot.params_work(params)
        assert result["gcmtype"] == "page"

    def test_gcmtype_for_ns_14(self, bot):
        bot.ns = "14"
        bot.no_gcm_sort = True
        params = {"gcmsort": "timestamp", "gcmdir": "newer"}
        result = bot.params_work(params)
        # ns="14" doesn't match ns in [14] (int), so falls through to nslist check
        # nslist=[] and depth=0, so gcmtype="page"
        assert result["gcmtype"] == "page"

    def test_gcmtype_for_nslist_14(self, bot):
        bot.nslist = [14]
        bot.no_gcm_sort = True
        params = {"gcmsort": "timestamp", "gcmdir": "newer"}
        result = bot.params_work(params)
        assert result["gcmtype"] == "subcat"
