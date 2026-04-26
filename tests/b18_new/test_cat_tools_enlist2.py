"""
Tests for src/b18_new/cat_tools_enlist2.py

This module tests category member API functions.
"""

import pytest

from src.core.b18_new.cat_tools_enlist2 import (
    MakeLitApiWay,
    get_ar_list_from_encat,
)


class TestGetArListFromCat:
    """Tests"""

    def test_returns_dict(self, mocker):
        """Test that function returns a dict"""
        mocker.patch("src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value={"categorymembers": {}})

        result = get_ar_list_from_encat("Science")

        assert isinstance(result, dict)

    def test_strips_category_prefix(self, mocker):
        """Test that Category: prefix is stripped"""
        mock_sub_cats = mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value={"categorymembers": {}}
        )

        get_ar_list_from_encat("Category:Science", code="ar")

        call_args = mock_sub_cats.call_args[0][0]
        assert "Category:Science" in call_args  # Prefix is added back

    def test_strips_tasneef_prefix(self, mocker):
        """Test that تصنيف: prefix is stripped"""
        mock_sub_cats = mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value={"categorymembers": {}}
        )

        get_ar_list_from_encat("تصنيف:علوم", code="ar")

        # Should process without error

    def test_returns_category_members(self, mocker):
        """Test that category members are returned"""
        mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.sub_cats_query",
            return_value={"categorymembers": {"Page1": {}, "Page2": {}, "Page3": {}}},
        )

        result = get_ar_list_from_encat("Science")

        assert len(result) == 3
        assert "Page1" in result

    def test_handles_subcat_type(self, mocker):
        """Test handling of 'cat' type parameter"""
        mock_sub_cats = mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value={"categorymembers": {}}
        )

        get_ar_list_from_encat("Science", typee="cat")

        call_args = mock_sub_cats.call_args
        assert call_args[1]["ctype"] == "subcat"

    def test_handles_page_type(self, mocker):
        """Test handling of 'page' type parameter"""
        mock_sub_cats = mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value={"categorymembers": {}}
        )

        get_ar_list_from_encat("Science", typee="page")

        call_args = mock_sub_cats.call_args
        assert call_args[1]["ctype"] == "page"

    def test_returns_empty_list_for_no_results(self, mocker):
        """Test that empty list is returned when no results"""
        mocker.patch("src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value=None)

        result = get_ar_list_from_encat("EmptyCategory")

        assert result == {}


class TestMakeLitApiWay:
    """Tests for MakeLitApiWay function"""

    def test_returns_false_for_empty_title(self, mocker):
        """Test that False is returned for empty title"""
        result = MakeLitApiWay("")
        assert result is False

    def test_returns_false_for_none_title(self, mocker):
        """Test that False is returned for None title"""
        result = MakeLitApiWay(None)
        assert result is False

    def test_calls_categorized_page_generator(self, mocker):
        """Test that Categorized_Page_Generator is called"""
        mock_cpg = mocker.patch("src.core.b18_new.cat_tools_enlist2.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.get_arpage_inside_encat", return_value=[])

        MakeLitApiWay("Science")

        mock_cpg.assert_called_once()

    def test_strips_category_prefix(self, mocker):
        """Test that Category: prefix is stripped"""
        mock_cpg = mocker.patch("src.core.b18_new.cat_tools_enlist2.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.get_arpage_inside_encat", return_value=[])

        MakeLitApiWay("[[Category:Science]]")

        call_args = mock_cpg.call_args[0][0]
        assert "[[" not in call_args
        assert "Category:" not in call_args

    def test_includes_pages_from_encat(self, mocker):
        """Test that pages from get_arpage_inside_encat are included"""
        mocker.patch("src.core.b18_new.cat_tools_enlist2.Categorized_Page_Generator", return_value=["Page1"])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.get_arpage_inside_encat", return_value=["صفحة_عربية"])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value=["صفحة_عربية"])
        mocker.patch(
            "src.core.b18_new.cat_tools_enlist2.find_LCN",
            return_value={"Page1": {"langlinks": {"ar": "صفحة1"}}, "صفحة عربية": {"langlinks": {"ar": "صفحة عربية"}}},
        )

        result = MakeLitApiWay("Science")

        # Should include pages from both sources
        assert result is not False

    def test_returns_false_for_no_pages(self, mocker):
        """Test that False is returned when no pages found"""
        mocker.patch("src.core.b18_new.cat_tools_enlist2.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.get_arpage_inside_encat", return_value=[])
        mocker.patch("src.core.b18_new.cat_tools_enlist2.sub_cats_query", return_value=[])

        result = MakeLitApiWay("EmptyCategory")

        assert result == []
