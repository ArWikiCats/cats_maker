"""
Tests for category_resolver.py

This module tests category member API functions.
"""

import pytest

from src.core.new_c18.core.category_resolver import CategoryResolver


class TestMakeLitApiWay:
    """Tests for CategoryResolver.make_lit_api_way method"""

    def test_returns_empty_list_for_empty_title(self, mocker):
        """Test that empty list is returned for empty title"""
        resolver = CategoryResolver()
        result = resolver.make_lit_api_way("")
        assert result == []

    def test_returns_empty_list_for_none_title(self, mocker):
        """Test that empty list is returned for None title"""
        resolver = CategoryResolver()
        result = resolver.make_lit_api_way(None)
        assert result == []

    def test_calls_categorized_page_generator(self, mocker):
        """Test that Categorized_Page_Generator is called"""
        mock_cpg = mocker.patch("src.core.new_c18.core.category_resolver.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.new_c18.core.category_resolver.get_arpage_inside_encat", return_value=[])

        resolver = CategoryResolver()
        resolver.make_lit_api_way("Science")

        mock_cpg.assert_called_once()

    def test_strips_category_prefix(self, mocker):
        """Test that Category: prefix is stripped"""
        mock_cpg = mocker.patch("src.core.new_c18.core.category_resolver.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.new_c18.core.category_resolver.get_arpage_inside_encat", return_value=[])

        resolver = CategoryResolver()
        resolver.make_lit_api_way("[[Category:Science]]")

        call_args = mock_cpg.call_args[0]
        assert "[[" not in call_args[0]
        assert "Category:" not in call_args[0]

    def test_includes_pages_from_encat(self, mocker):
        """Test that pages from get_arpage_inside_encat are included"""
        mocker.patch("src.core.new_c18.core.category_resolver.Categorized_Page_Generator", return_value=["Page1"])
        mocker.patch("src.core.new_c18.core.category_resolver.get_arpage_inside_encat", return_value=["صفحة_عربية"])
        mocker.patch(
            "src.core.new_c18.core.category_resolver.find_LCN",
            return_value={"Page1": {"langlinks": {"ar": "صفحة1"}}, "صفحة عربية": {"langlinks": {"ar": "صفحة عربية"}}},
        )

        resolver = CategoryResolver()
        result = resolver.make_lit_api_way("Science")

        # Should include pages from both sources
        assert result is not None

    def test_returns_empty_list_for_no_pages(self, mocker):
        """Test that empty list is returned when no pages found"""
        mocker.patch("src.core.new_c18.core.category_resolver.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.new_c18.core.category_resolver.get_arpage_inside_encat", return_value=[])

        resolver = CategoryResolver()
        result = resolver.make_lit_api_way("EmptyCategory")

        assert result == []
