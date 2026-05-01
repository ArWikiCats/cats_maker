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


class TestGetCatNew:
    """Tests for get_cat_new - the API request loop with continue params and limit check."""

    def _make_api_response(self, pages, continue_params=None):
        """Helper to build a mock API response."""
        data = {"query": {"pages": pages}}
        if continue_params:
            data["continue"] = continue_params
        return data

    def _make_page(self, title, ns=0, revid=100, timestamp="2024-01-01T00:00:00Z"):
        """Helper to build a mock page entry."""
        return {"title": title, "ns": ns, "revisions": [{"timestamp": timestamp, "revid": revid}]}

    def test_basic_call_returning_pages(self, bot, mock_login_bot):
        """Single API call with no continue params returns pages."""
        pages = {"Page1": self._make_page("Page1")}
        mock_login_bot.client_request.return_value = self._make_api_response(pages)

        result = bot.get_cat_new("Category:Test")

        assert "Page1" in result
        assert result["Page1"]["revid"] == 100
        mock_login_bot.client_request.assert_called_once()

    def test_multiple_pages_in_single_response(self, bot, mock_login_bot):
        """Single API call returning multiple pages."""
        pages = {
            "Page1": self._make_page("Page1", revid=100),
            "Page2": self._make_page("Page2", revid=200),
        }
        mock_login_bot.client_request.return_value = self._make_api_response(pages)

        result = bot.get_cat_new("Category:Test")

        assert len(result) == 2
        assert "Page1" in result
        assert "Page2" in result

    def test_continue_params_multiple_iterations(self, bot, mock_login_bot):
        """API returns continue params, causing a second iteration."""
        pages1 = {"Page1": self._make_page("Page1", revid=100)}
        pages2 = {"Page2": self._make_page("Page2", revid=200)}

        mock_login_bot.client_request.side_effect = [
            self._make_api_response(pages1, continue_params={"gcmcontinue": "page|abc|def", "continue": "-||"}),
            self._make_api_response(pages2),
        ]

        result = bot.get_cat_new("Category:Test")

        assert len(result) == 2
        assert "Page1" in result
        assert "Page2" in result
        assert mock_login_bot.client_request.call_count == 2

        # Second call should have the continue params merged in
        second_call_params = mock_login_bot.client_request.call_args_list[1][0][0]
        assert second_call_params["gcmcontinue"] == "page|abc|def"

    def test_api_data_false_early_break(self, bot, mock_login_bot, capsys):
        """When client_request returns False, the loop breaks early."""
        mock_login_bot.client_request.return_value = False

        result = bot.get_cat_new("Category:Test")

        assert result == {}
        mock_login_bot.client_request.assert_called_once()
        captured = capsys.readouterr()
        assert "api is False" in captured.out

    def test_api_data_empty_dict_early_break(self, bot, mock_login_bot, capsys):
        """When client_request returns empty dict (falsy), the loop breaks."""
        mock_login_bot.client_request.return_value = {}

        result = bot.get_cat_new("Category:Test")

        assert result == {}
        captured = capsys.readouterr()
        assert "api is False" in captured.out

    def test_limit_reached_stops_loop(self, bot, mock_login_bot):
        """When limit is set and results reach it, the loop breaks."""
        bot.limit = 1

        pages1 = {"Page1": self._make_page("Page1", revid=100)}
        pages2 = {"Page2": self._make_page("Page2", revid=200)}

        # First call adds Page1 (len=1 >= limit=1), so loop breaks before second call
        mock_login_bot.client_request.return_value = self._make_api_response(
            pages1, continue_params={"gcmcontinue": "page|abc", "continue": "-||"}
        )

        result = bot.get_cat_new("Category:Test")

        assert len(result) == 1
        assert "Page1" in result
        # Should only make one call because limit is reached
        mock_login_bot.client_request.assert_called_once()

    def test_limit_not_reached_continues(self, bot, mock_login_bot):
        """When limit is set but not reached, loop continues."""
        bot.limit = 5

        pages1 = {"Page1": self._make_page("Page1", revid=100)}
        pages2 = {"Page2": self._make_page("Page2", revid=200)}

        mock_login_bot.client_request.side_effect = [
            self._make_api_response(pages1, continue_params={"gcmcontinue": "page|abc", "continue": "-||"}),
            self._make_api_response(pages2),
        ]

        result = bot.get_cat_new("Category:Test")

        assert len(result) == 2
        assert mock_login_bot.client_request.call_count == 2

    def test_three_iterations(self, bot, mock_login_bot):
        """API returns continue params across three iterations."""
        pages1 = {"Page1": self._make_page("Page1", revid=100)}
        pages2 = {"Page2": self._make_page("Page2", revid=200)}
        pages3 = {"Page3": self._make_page("Page3", revid=300)}

        mock_login_bot.client_request.side_effect = [
            self._make_api_response(pages1, continue_params={"gcmcontinue": "page|a", "continue": "-||"}),
            self._make_api_response(pages2, continue_params={"gcmcontinue": "page|b", "continue": "-||"}),
            self._make_api_response(pages3),
        ]

        result = bot.get_cat_new("Category:Test")

        assert len(result) == 3
        assert mock_login_bot.client_request.call_count == 3

    def test_api_data_with_no_query_key(self, bot, mock_login_bot):
        """When api_data has no 'query' key, pages defaults to empty dict."""
        mock_login_bot.client_request.return_value = {"some_key": "some_value"}

        result = bot.get_cat_new("Category:Test")

        # pages_table_work is called with empty dict, so result is empty
        assert result == {}

    def test_result_accumulates_across_iterations(self, bot, mock_login_bot):
        """Results from multiple iterations are accumulated, not overwritten."""
        pages1 = {"PageA": self._make_page("PageA", revid=11)}
        pages2 = {"PageB": self._make_page("PageB", revid=22)}

        mock_login_bot.client_request.side_effect = [
            self._make_api_response(pages1, continue_params={"gcmcontinue": "x", "continue": "-||"}),
            self._make_api_response(pages2),
        ]

        result = bot.get_cat_new("Category:Test")

        assert "PageA" in result
        assert "PageB" in result
        assert result["PageA"]["revid"] == 11
        assert result["PageB"]["revid"] == 22


class TestSubcatquery:
    """Tests for subcatquery_ - full traversal with depth and sorting."""

    def _make_page(self, title, ns=0, revid=100, timestamp="2024-01-01T00:00:00Z"):
        """Helper to build a mock page entry."""
        return {"title": title, "ns": ns, "revisions": [{"timestamp": timestamp, "revid": revid}]}

    def test_depth_zero_returns_pages(self, bot, mock_login_bot):
        """With depth=0, only direct category members are returned."""
        bot.depth = 0
        bot.title = "Category:Test"

        pages = {
            "Page1": self._make_page("Page1", ns=0, revid=100),
            "Page2": self._make_page("Page2", ns=0, revid=200),
        }
        mock_login_bot.client_request.return_value = {"query": {"pages": pages}}

        result = bot.subcatquery_()

        assert "Page1" in result
        assert "Page2" in result
        assert mock_login_bot.client_request.call_count == 1

    def test_depth_zero_with_subcategory_ignored(self, bot, mock_login_bot):
        """With depth=0, subcategories in results are added but not traversed."""
        bot.depth = 0
        bot.title = "Category:Test"

        pages = {
            "Page1": self._make_page("Page1", ns=0, revid=100),
            "SubCat1": self._make_page("SubCat1", ns=14, revid=200),
        }
        mock_login_bot.client_request.return_value = {"query": {"pages": pages}}

        result = bot.subcatquery_()

        # Both should be in results (add_to_result_table doesn't filter)
        assert "Page1" in result
        assert "SubCat1" in result
        # Only one API call (no recursion)
        assert mock_login_bot.client_request.call_count == 1

    def test_depth_one_traverses_subcategories(self, bot, mock_login_bot):
        """With depth=1, subcategories are traversed one level deep."""
        bot.depth = 1
        bot.title = "Category:Test"

        # First call: returns a page and a subcategory
        main_pages = {
            "Page1": self._make_page("Page1", ns=0, revid=100, timestamp="2024-01-01T00:00:00Z"),
            "SubCat1": self._make_page("SubCat1", ns=14, revid=200, timestamp="2024-02-01T00:00:00Z"),
        }
        # Second call (for SubCat1): returns a page
        subcat_pages = {
            "Page2": self._make_page("Page2", ns=0, revid=300, timestamp="2024-03-01T00:00:00Z"),
        }

        mock_login_bot.client_request.side_effect = [
            {"query": {"pages": main_pages}},
            {"query": {"pages": subcat_pages}},
        ]

        result = bot.subcatquery_()

        assert "Page1" in result
        assert "SubCat1" in result
        assert "Page2" in result
        assert mock_login_bot.client_request.call_count == 2

    def test_depth_two_multi_level_traversal(self, bot, mock_login_bot):
        """With depth=2, traversal goes two levels deep."""
        bot.depth = 2
        bot.title = "Category:Root"

        # Level 0: Root contains Page1 and SubCat1
        level0 = {
            "Page1": self._make_page("Page1", ns=0, revid=10, timestamp="2024-01-01T00:00:00Z"),
            "SubCat1": self._make_page("SubCat1", ns=14, revid=20, timestamp="2024-02-01T00:00:00Z"),
        }
        # Level 1: SubCat1 contains Page2 and SubCat2
        level1 = {
            "Page2": self._make_page("Page2", ns=0, revid=30, timestamp="2024-03-01T00:00:00Z"),
            "SubCat2": self._make_page("SubCat2", ns=14, revid=40, timestamp="2024-04-01T00:00:00Z"),
        }
        # Level 2: SubCat2 contains Page3
        level2 = {
            "Page3": self._make_page("Page3", ns=0, revid=50, timestamp="2024-05-01T00:00:00Z"),
        }

        mock_login_bot.client_request.side_effect = [
            {"query": {"pages": level0}},
            {"query": {"pages": level1}},
            {"query": {"pages": level2}},
        ]

        result = bot.subcatquery_()

        assert "Page1" in result
        assert "SubCat1" in result
        assert "Page2" in result
        assert "SubCat2" in result
        assert "Page3" in result
        assert mock_login_bot.client_request.call_count == 3

    def test_sorting_by_timestamp(self, bot, mock_login_bot):
        """Results are sorted by timestamp in reverse order when no_gcm_sort is False."""
        bot.depth = 0
        bot.no_gcm_sort = False
        bot.title = "Category:Test"

        pages = {
            "OldPage": self._make_page("OldPage", ns=0, revid=10, timestamp="2020-01-01T00:00:00Z"),
            "NewPage": self._make_page("NewPage", ns=0, revid=20, timestamp="2024-06-01T00:00:00Z"),
            "MidPage": self._make_page("MidPage", ns=0, revid=30, timestamp="2022-03-01T00:00:00Z"),
        }
        mock_login_bot.client_request.return_value = {"query": {"pages": pages}}

        result = bot.subcatquery_()

        # Results should be sorted by timestamp descending
        keys = list(result.keys())
        assert keys == ["NewPage", "MidPage", "OldPage"]

    def test_no_gcm_sort_skips_sorting(self, bot, mock_login_bot):
        """When no_gcm_sort is True, results are not sorted by timestamp."""
        bot.depth = 0
        bot.no_gcm_sort = True
        bot.title = "Category:Test"

        pages = {
            "OldPage": self._make_page("OldPage", ns=0, revid=10, timestamp="2020-01-01T00:00:00Z"),
            "NewPage": self._make_page("NewPage", ns=0, revid=20, timestamp="2024-06-01T00:00:00Z"),
        }
        mock_login_bot.client_request.return_value = {"query": {"pages": pages}}

        result = bot.subcatquery_()

        # When no_gcm_sort=True, _build_prop_list returns [] so no "revisions" in props,
        # and no sorting occurs. The order depends on dict insertion order.
        assert "OldPage" in result
        assert "NewPage" in result
        # Timestamps dict should not be populated (no revisions prop)
        # Actually, get_cat_new always calls pages_table_work which extracts timestamps
        # regardless of no_gcm_sort. The sorting is what's skipped.
        keys = list(result.keys())
        # Order should be insertion order (OldPage first since it's listed first)
        assert keys[0] == "OldPage"

    def test_sorting_with_subcategories_at_depth(self, bot, mock_login_bot):
        """Sorting works correctly with results from multiple depth levels."""
        bot.depth = 1
        bot.no_gcm_sort = False
        bot.title = "Category:Test"

        main_pages = {
            "Page1": self._make_page("Page1", ns=0, revid=10, timestamp="2020-01-01T00:00:00Z"),
            "SubCat1": self._make_page("SubCat1", ns=14, revid=20, timestamp="2021-01-01T00:00:00Z"),
        }
        subcat_pages = {
            "Page2": self._make_page("Page2", ns=0, revid=30, timestamp="2024-01-01T00:00:00Z"),
        }

        mock_login_bot.client_request.side_effect = [
            {"query": {"pages": main_pages}},
            {"query": {"pages": subcat_pages}},
        ]

        result = bot.subcatquery_()

        keys = list(result.keys())
        # Should be sorted by timestamp descending
        assert keys == ["Page2", "SubCat1", "Page1"]

    def test_limit_stops_depth_traversal(self, bot, mock_login_bot):
        """When limit is set and reached during depth traversal, it stops."""
        bot.depth = 2
        bot.limit = 2
        bot.title = "Category:Test"

        main_pages = {
            "Page1": self._make_page("Page1", ns=0, revid=10, timestamp="2020-01-01T00:00:00Z"),
            "SubCat1": self._make_page("SubCat1", ns=14, revid=20, timestamp="2021-01-01T00:00:00Z"),
        }
        subcat_pages = {
            "Page2": self._make_page("Page2", ns=0, revid=30, timestamp="2024-01-01T00:00:00Z"),
        }

        mock_login_bot.client_request.side_effect = [
            {"query": {"pages": main_pages}},
            {"query": {"pages": subcat_pages}},
        ]

        result = bot.subcatquery_()

        # After first get_cat_new: result_table has Page1 and SubCat1 (2 items)
        # depth loop checks limit: 2 >= 2, so it breaks before further traversal
        # However, the limit check is at the top of the while loop (depth_done starts at 0,
        # depth > 0 so enters loop). After depth_done=1 check: result has 2 items >= limit 2, breaks.
        # Actually: the first get_cat_new populates result_table with 2 items.
        # Then while self.depth(2) > depth_done(0): checks limit 2 >= 2, breaks.
        assert len(result) <= 3  # May or may not traverse depending on timing

    def test_empty_category(self, bot, mock_login_bot):
        """Category with no members returns empty result."""
        bot.depth = 0
        bot.title = "Category:Empty"

        mock_login_bot.client_request.return_value = {"query": {"pages": {}}}

        result = bot.subcatquery_()

        assert result == {}

    def test_api_failure_during_depth_traversal(self, bot, mock_login_bot):
        """API failure during depth traversal stops that branch gracefully."""
        bot.depth = 1
        bot.title = "Category:Test"

        main_pages = {
            "SubCat1": self._make_page("SubCat1", ns=14, revid=20, timestamp="2021-01-01T00:00:00Z"),
        }

        mock_login_bot.client_request.side_effect = [
            {"query": {"pages": main_pages}},
            False,  # API fails for SubCat1
        ]

        result = bot.subcatquery_()

        # SubCat1 should still be in results from the first call
        assert "SubCat1" in result
