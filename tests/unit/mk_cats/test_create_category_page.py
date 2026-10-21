"""
Tests for create_category_page.py

This module tests category page creation functionality.
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats.create_category_page import (
    CategoryResult,
    add_text_to_cat,
    make_category,
    new_category,
)


@pytest.fixture
def mock_create_page(mocker):
    """Fixture to mock create_page function with default return value False."""
    return mocker.patch("src.cats_maker.mk_cats.create_category_page.create_page", return_value=False)


@pytest.fixture
def mock_make_category(mocker):
    """Fixture to mock make_category function."""
    return mocker.patch("src.cats_maker.mk_cats.create_category_page.make_category")


@dataclass
class MockCategoryDependencies:
    """Dataclass holding mocked dependencies for add_text_to_cat tests."""

    page_put: MagicMock
    fetch_commons_category: MagicMock
    generate_portal_content: MagicMock
    main_make_temp_no_title: MagicMock


@pytest.fixture
def mock_category_deps(mocker) -> MockCategoryDependencies:
    """Fixture providing mocked dependencies for add_text_to_cat."""
    return MockCategoryDependencies(
        page_put=mocker.patch("src.cats_maker.mk_cats.create_category_page.page_put", return_value=False),
        fetch_commons_category=mocker.patch(
            "src.cats_maker.mk_cats.create_category_page.fetch_commons_category", return_value=""
        ),
        generate_portal_content=mocker.patch(
            "src.cats_maker.mk_cats.create_category_page.generate_portal_content", return_value=[]
        ),
        main_make_temp_no_title=mocker.patch(
            "src.cats_maker.mk_cats.create_category_page.main_make_temp_no_title", return_value=""
        ),
    )


class TestMakeCategory:
    """Tests for make_category function."""

    def test_returns_false_for_non_arabic_category_title(self, mock_create_page):
        """Test that make_category returns failed result for titles not starting with تصنيف:"""
        result = make_category([], "Category:Test", "Test Category", "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title prefix"

    def test_returns_false_for_title_without_tasneef_prefix(self, mock_create_page):
        """Test that title must start with تصنيف:"""
        result = make_category([], "Category:Science", "علوم", "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title prefix"


class TestNewCategory:
    """Tests for new_category function."""

    def test_returns_false_for_empty_title(self):
        """Test that new_category returns failed result for empty title."""
        result = new_category("Category:Test", "", [], "Q123")
        assert result.success is False
        assert result.error_message == "Invalid title"

    def test_returns_false_when_make_category_fails(self, mock_make_category):
        """Test that new_category returns failed result when make_category fails."""
        mock_make_category.return_value = CategoryResult(False, None, "Test error")

        result = new_category("Category:Science", "تصنيف:علوم", ["تصنيف:علوم طبيعية"], "Q123")
        assert result.success is False

    def test_returns_true_when_make_category_succeeds(self, mock_make_category):
        """Test that new_category returns successful result when make_category succeeds."""
        mock_make_category.return_value = CategoryResult(True, "تصنيف:علوم", None)

        result = new_category("Category:Science", "تصنيف:علوم", ["تصنيف:علوم طبيعية"], "Q123")
        assert result.success is True
        assert result.page_title == "تصنيف:علوم"


class TestAddTextToCat:
    """Tests for add_text_to_cat function."""

    def test_returns_text_for_non_wikipedia_family(self):
        """Test that add_text_to_cat returns unchanged text for non-wikipedia family."""
        text = "Test text"
        result = add_text_to_cat(text, [], "Category:Test", "تصنيف:اختبار", "Q123", family="wikisource")
        assert result == text

    def test_handles_empty_categories(self, mock_category_deps: MockCategoryDependencies):
        """Test that add_text_to_cat handles empty categories list."""
        text = "Test text"
        result = add_text_to_cat(text, [], "Category:Test", "تصنيف:اختبار", "Q123", family="wikipedia")
        assert result is not None

    def test_filters_none_and_false_categories(self, mock_category_deps: MockCategoryDependencies):
        """Test that add_text_to_cat filters out None and False categories."""
        text = "Test text"
        categories = [None, False, "تصنيف:صالح", None]
        result = add_text_to_cat(text, categories, "Category:Test", "تصنيف:اختبار", "Q123", family="wikipedia")
        # The function should handle the mixed list without errors
        assert result is not None
