"""
Tests for src/mk_cats/add_bot.py

This module tests functions for adding categories to pages.
"""

import pytest

from src.mk_cats.add_bot import (
    add_to_page,
)


class TestAddToPage:
    """Tests for add_to_page function"""

    def test_returns_false_for_dont_add_pages(self, mocker):
        """Test that pages in dont_add list return False"""
        mocker.patch("src.mk_cats.add_bot.Dont_add_to_pages_def", return_value=["صفحة_ممنوعة"])

        result = add_to_page("صفحة_ممنوعة", "تصنيف:علوم")
        assert result is False

    def test_replaces_underscores_in_category(self, mocker):
        """Test that underscores are replaced with spaces in category"""
        mocker.patch("src.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = ""
        mocker.patch("src.mk_cats.add_bot._get_page", return_value=False)

        result = add_to_page("صفحة", "تصنيف:علوم_الحاسوب")
        # The category should have underscores replaced

    def test_returns_false_when_page_cannot_be_retrieved(self, mocker):
        """Test that False is returned when page cannot be retrieved"""
        mocker.patch("src.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mocker.patch("src.mk_cats.add_bot._get_page", return_value=False)

        result = add_to_page("صفحة_غير_موجودة", "تصنيف:علوم")
        assert result is False

    def test_returns_false_when_category_already_exists(self, mocker):
        """Test that False is returned when category already in page"""
        mocker.patch("src.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = "[[تصنيف:علوم]]"
        mock_page.namespace.return_value = 0
        mock_page.get_categories.return_value = []
        mocker.patch("src.mk_cats.add_bot._get_page", return_value=mock_page)

        result = add_to_page("صفحة", "تصنيف:علوم")
        assert result is False
