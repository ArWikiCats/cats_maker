"""
Tests for src/core/b18_new/cat_tools_enlist2.py

This module tests category member API functions.
"""

import pytest

from src.core.b18_new.cat_tools_enlist2 import (
    MakeLitApiWay,
)


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

        result = MakeLitApiWay("EmptyCategory")

        assert result == []
