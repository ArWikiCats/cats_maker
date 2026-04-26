"""
Tests for src/mk_cats/create_category_page.py

This module tests category page creation functionality.
"""

import pytest

from src.core.mk_cats.create_category_page import (
    add_text_to_cat,
    make_category,
    new_category,
)
from src.core.utils.skip_cats import skip_encats


class TestMakeCategory:
    """Tests for make_category function"""

    def test_returns_false_for_skip_encats(self, mocker):
        """Test that make_category returns failed result for categories in skip_encats"""
        # Mock the create_Page to not actually create pages
        mocker.patch("src.core.mk_cats.create_category_page.create_Page", return_value=False)

        # Use a category that's in skip_encats
        if skip_encats:
            result = make_category([], skip_encats[0], "تصنيف:اختبار", "Q123")
            assert result.success is False
            assert result.error_message == "Category in skip list"

    def test_returns_false_for_non_arabic_category_title(self, mocker):
        """Test that make_category returns failed result for titles not starting with تصنيف:"""
        mocker.patch("src.core.mk_cats.create_category_page.create_Page", return_value=False)

        result = make_category([], "Category:Test", "Test Category", "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title prefix"

    def test_returns_false_for_title_without_tasneef_prefix(self, mocker):
        """Test that title must start with تصنيف:"""
        mocker.patch("src.core.mk_cats.create_category_page.create_Page", return_value=False)

        result = make_category([], "Category:Science", "علوم", "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title prefix"


class TestNewCategory:
    """Tests for new_category function"""

    def test_returns_false_for_empty_title(self, mocker):
        """Test that new_category returns failed result for empty title"""
        result = new_category("Category:Test", "", [], "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title"

    def test_returns_false_when_make_category_fails(self, mocker):
        """Test that new_category returns failed result when make_category fails"""
        from src.core.mk_cats.create_category_page import CategoryResult

        mocker.patch(
            "src.core.mk_cats.create_category_page.make_category",
            return_value=CategoryResult(False, None, "Test error"),
        )

        result = new_category("Category:Science", "تصنيف:علوم", ["تصنيف:علوم طبيعية"], "Q123")
        assert result.success is False

    def test_returns_true_when_make_category_succeeds(self, mocker):
        """Test that new_category returns successful result when make_category succeeds"""
        from src.core.mk_cats.create_category_page import CategoryResult

        mocker.patch(
            "src.core.mk_cats.create_category_page.make_category", return_value=CategoryResult(True, "تصنيف:علوم", None)
        )

        result = new_category("Category:Science", "تصنيف:علوم", ["تصنيف:علوم طبيعية"], "Q123")
        assert result.success is True
        assert result.page_title == "تصنيف:علوم"


class TestAddTextToCat:
    """Tests for add_text_to_cat function"""

    def test_returns_text_for_non_wikipedia_family(self, mocker):
        """Test that add_text_to_cat returns unchanged text for non-wikipedia family"""
        text = "Test text"
        result = add_text_to_cat(text, [], "Category:Test", "تصنيف:اختبار", "Q123", family="wikisource")
        assert result == text

    def test_handles_empty_categories(self, mocker):
        """Test that add_text_to_cat handles empty categories list"""
        mocker.patch("src.core.mk_cats.create_category_page.page_put", return_value=False)
        mocker.patch("src.core.mk_cats.create_category_page.categorytext.fetch_commons_category", return_value="")
        mocker.patch(
            "src.core.mk_cats.create_category_page.categorytext.generate_portal_content", return_value=("", [])
        )
        mocker.patch("src.core.mk_cats.create_category_page.categorytext.main_make_temp_no_title", return_value="")

        text = "Test text"
        result = add_text_to_cat(text, [], "Category:Test", "تصنيف:اختبار", "Q123", family="wikipedia")
        assert result is not None

    def test_filters_none_and_false_categories(self, mocker):
        """Test that add_text_to_cat filters out None and False categories"""
        mocker.patch("src.core.mk_cats.create_category_page.page_put", return_value=False)
        mocker.patch("src.core.mk_cats.create_category_page.categorytext.fetch_commons_category", return_value="")
        mocker.patch(
            "src.core.mk_cats.create_category_page.categorytext.generate_portal_content", return_value=("", [])
        )
        mocker.patch("src.core.mk_cats.create_category_page.categorytext.main_make_temp_no_title", return_value="")

        text = "Test text"
        categories = [None, False, "تصنيف:صالح", None]
        result = add_text_to_cat(text, categories, "Category:Test", "تصنيف:اختبار", "Q123", family="wikipedia")
        # The function should handle the mixed list without errors
        assert result is not None
