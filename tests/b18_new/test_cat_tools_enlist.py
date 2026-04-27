"""
Tests for src/core/b18_new/cat_tools_enlist.py

This module tests category page listing functions.
"""

import pytest

from src.core.b18_new.cat_tools_enlist import (
    extract_fan_page_titles,
    get_listenpageTitle,
)


class TestExtractFanPageTitles:
    """Tests for extract_fan_page_titles function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.settings.database.use_sql", False)

        result = extract_fan_page_titles("Category:Science")

        assert isinstance(result, list)

    def test_returns_empty_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.settings.database.use_sql", False)

        result = extract_fan_page_titles("Category:Science")

        assert result == []

    def test_calls_get_exclusive_when_sql_enabled(self, mocker):
        """Test that get_exclusive_category_titles is called when SQL enabled"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.settings.database.use_sql", True)
        mock_comparator = mocker.patch("src.core.b18_new.cat_tools_enlist.CategoryComparator")
        mock_comparator.return_value.get_exclusive_category_titles.return_value = ["Page1", "Page2"]

        result = extract_fan_page_titles("Category:Science")

        mock_comparator.return_value.get_exclusive_category_titles.assert_called_once()
        assert len(result) == 2

    def test_strips_category_prefix(self, mocker):
        """Test that Category: prefix is stripped"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.settings.database.use_sql", True)
        mock_comparator = mocker.patch("src.core.b18_new.cat_tools_enlist.CategoryComparator")
        mock_get_exclusive = mock_comparator.return_value.get_exclusive_category_titles
        mock_get_exclusive.return_value = []

        extract_fan_page_titles("Category:Science")

        call_args = mock_get_exclusive.call_args[0]
        assert "Category:" not in call_args[0]


class TestGetListenpageTitle:
    """Tests for get_listenpageTitle function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=False)
        mocker.patch("src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=[])

        result = get_listenpageTitle("تصنيف:علوم", "Category:Science")

        assert isinstance(result, list)

    def test_strips_whitespace_from_title(self, mocker):
        """Test that whitespace is stripped from title"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=False)
        mocker.patch("src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=[])

        result = get_listenpageTitle("تصنيف:علوم", "  Category:Science  ")

        # Should work without error
        assert isinstance(result, list)

    def test_uses_make_ar_list_newcat2_when_valid(self, mocker):
        """Test that make_ar_list_newcat2 is called when validation passes"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=True)
        mock_make_ar = mocker.patch(
            "src.core.b18_new.cat_tools_enlist.make_ar_list_newcat2", return_value=["صفحة1", "صفحة2"]
        )
        mocker.patch("src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=[])

        result = get_listenpageTitle("تصنيف:علوم", "Category:Science")

        mock_make_ar.assert_called_once()
        assert "صفحة1" in result

    def test_falls_back_to_extract_fan_page_titles(self, mocker):
        """Test fallback to extract_fan_page_titles"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=False)
        mock_extract = mocker.patch(
            "src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=["Page1", "Page2"]
        )

        result = get_listenpageTitle("تصنيف:علوم", "Category:Science")

        mock_extract.assert_called_once()
        assert "Page1" in result

    def test_removes_duplicates(self, mocker):
        """Test that duplicates are removed"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=False)
        mocker.patch(
            "src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=["Page1", "Page1", "Page2"]
        )

        result = get_listenpageTitle("تصنيف:علوم", "Category:Science")

        assert len(result) == len(set(result))

    def test_filters_empty_strings(self, mocker):
        """Test that empty strings are filtered"""
        mocker.patch("src.core.b18_new.cat_tools_enlist.validate_categories_for_new_cat", return_value=False)
        mocker.patch(
            "src.core.b18_new.cat_tools_enlist.extract_fan_page_titles", return_value=["Page1", "", "Page2", None]
        )

        result = get_listenpageTitle("تصنيف:علوم", "Category:Science")

        assert "" not in result
        assert None not in result
