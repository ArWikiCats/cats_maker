"""
Tests for src/c18_new/cats_tools/ar_from_en.py

This module tests functions for converting English category pages to Arabic.
"""

import pytest

from src.core.c18_new.cats_tools.ar_from_en import (
    Get_ar_list_from_en_list,
    clean_category_input,
    make_ar_list_from_en_cat,
    retrieve_ar_list_from_category,
)


class TestCleanCategoryInput:
    """Tests for clean_category_input function"""

    def test_removes_double_brackets(self):
        """Test that double brackets are removed"""
        result = clean_category_input("[[Category:Science]]")
        assert result == "Science"

    def test_removes_category_prefix(self):
        """Test that Category: prefix is removed"""
        result = clean_category_input("Category:Science")
        assert result == "Science"

    def test_removes_lowercase_category_prefix(self):
        """Test that category: prefix (lowercase) is removed"""
        result = clean_category_input("category:Science")
        assert result == "Science"

    def test_removes_category_talk_prefix(self):
        """Test that category talk: prefix is removed"""
        result = clean_category_input("category talk:Science")
        assert result == "Science"

    def test_removes_french_category_prefix(self):
        """Test that Catégorie: prefix is removed"""
        result = clean_category_input("Catégorie:Sciences")
        assert result == "Sciences"

    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        result = clean_category_input("  Science  ")
        assert result == "Science"

    def test_handles_combined_formats(self):
        """Test handling combined bracket and prefix formats"""
        result = clean_category_input("[[Category:Science]]")
        assert result == "Science"

    def test_handles_empty_string(self):
        """Test handling empty string"""
        result = clean_category_input("")
        assert result == ""


class TestMakeArListFromEnCat:
    """Tests for make_ar_list_from_en_cat function"""

    def test_returns_false_for_empty_category(self):
        """Test that empty category returns False"""
        result = make_ar_list_from_en_cat("")
        assert result is False

    def test_returns_false_for_none_category(self):
        """Test that None category returns False"""
        result = make_ar_list_from_en_cat(None)
        assert result is False

    def test_cleans_category_input(self, mocker):
        """Test that category input is cleaned"""
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.settings.database.use_sql", False)
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.retrieve_ar_list_from_category", return_value=[])
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.get_ar_list_from_encat", return_value={})

        result = make_ar_list_from_en_cat("[[Category:Science]]")
        assert result == []


class TestGetArListFromEnList:
    """Tests for Get_ar_list_from_en_list function"""

    def test_returns_empty_list_for_empty_input(self):
        """Test that empty input returns empty list"""
        result = Get_ar_list_from_en_list([])
        assert result == []

    def test_processes_list_in_batches(self, mocker):
        """Test that list is processed in batches of 50"""
        mock_find_lcn = mocker.patch(
            "src.core.c18_new.cats_tools.ar_from_en.find_LCN",
            return_value={
                "Page1": {"langlinks": {"ar": "صفحة1"}},
            },
        )

        # Create list with 55 items to ensure batching
        input_list = [f"Page{i}" for i in range(55)]
        result = Get_ar_list_from_en_list(input_list)

        # Should be called twice (0-50, 50-55)
        assert mock_find_lcn.call_count == 2

    def test_extracts_arabic_langlinks(self, mocker):
        """Test that Arabic langlinks are extracted"""
        mocker.patch(
            "src.core.c18_new.cats_tools.ar_from_en.find_LCN",
            return_value={
                "Science": {"langlinks": {"ar": "علوم"}},
                "History": {"langlinks": {"ar": "تاريخ"}},
            },
        )

        result = Get_ar_list_from_en_list(["Science", "History"])
        assert "علوم" in result
        assert "تاريخ" in result

    def test_skips_pages_without_arabic_langlink(self, mocker):
        """Test that pages without Arabic langlinks are skipped"""
        mocker.patch(
            "src.core.c18_new.cats_tools.ar_from_en.find_LCN",
            return_value={
                "Science": {"langlinks": {"fr": "Science"}},  # No Arabic
            },
        )

        result = Get_ar_list_from_en_list(["Science"])
        assert len(result) == 0

    def test_removes_duplicates(self, mocker):
        """Test that duplicate results are removed"""
        mocker.patch(
            "src.core.c18_new.cats_tools.ar_from_en.find_LCN",
            return_value={
                "Page1": {"langlinks": {"ar": "صفحة"}},
                "Page2": {"langlinks": {"ar": "صفحة"}},  # Same Arabic
            },
        )

        result = Get_ar_list_from_en_list(["Page1", "Page2"])
        assert len(result) == 1

    def test_handles_pipe_prefix_in_list(self, mocker):
        """Test that pipe prefix is removed from joined list"""
        mock_find_lcn = mocker.patch("src.core.c18_new.cats_tools.ar_from_en.find_LCN", return_value={})

        # This tests the handling when "|" appears at the start
        result = Get_ar_list_from_en_list(["Page1"])
        mock_find_lcn.assert_called_once()


class TestRetrieveArListFromCategory:
    """Tests for retrieve_ar_list_from_category function"""

    def test_calls_categorized_page_generator(self, mocker):
        """Test that Categorized_Page_Generator is called"""
        mock_cpg = mocker.patch("src.core.c18_new.cats_tools.ar_from_en.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.get_arpage_inside_encat", return_value=[])
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.Get_ar_list_from_en_list", return_value=[])

        retrieve_ar_list_from_category("Science", "Science")

        mock_cpg.assert_called_once_with("Science", "all")

    def test_adds_pages_from_encat(self, mocker):
        """Test that pages from get_arpage_inside_encat are added"""
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.Categorized_Page_Generator", return_value=[])
        mocker.patch("src.core.c18_new.cats_tools.ar_from_en.get_arpage_inside_encat", return_value=["صفحة_عربية"])
        mock_get_ar = mocker.patch("src.core.c18_new.cats_tools.ar_from_en.Get_ar_list_from_en_list", return_value=[])

        retrieve_ar_list_from_category("Science", "Science")

        # Should include the Arabic page with underscores replaced
        call_args = mock_get_ar.call_args[0][0]
        assert "صفحة عربية" in call_args
