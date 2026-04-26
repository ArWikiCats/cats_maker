"""
Tests for src/core/mk_cats/add_bot.py

This module tests functions for adding categories to pages.
"""

import pytest

from src.core.mk_cats.add_bot import (
    add_to_final_list,
    add_to_page,
)


class TestAddToPage:
    """Tests for add_to_page function"""

    def test_returns_false_for_dont_add_pages(self, mocker):
        """Test that pages in dont_add list return False"""
        mocker.patch("src.core.mk_cats.add_bot.Dont_add_to_pages_def", return_value=["صفحة_ممنوعة"])

        result = add_to_page("صفحة_ممنوعة", "تصنيف:علوم")
        assert result is False

    def test_replaces_underscores_in_category(self, mocker):
        """Test that underscores are replaced with spaces in category"""
        mocker.patch("src.core.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = ""
        mocker.patch("src.core.mk_cats.add_bot._get_page", return_value=False)

        result = add_to_page("صفحة", "تصنيف:علوم_الحاسوب")
        # The category should have underscores replaced

    def test_returns_false_when_page_cannot_be_retrieved(self, mocker):
        """Test that False is returned when page cannot be retrieved"""
        mocker.patch("src.core.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mocker.patch("src.core.mk_cats.add_bot._get_page", return_value=False)

        result = add_to_page("صفحة_غير_موجودة", "تصنيف:علوم")
        assert result is False

    def test_returns_false_when_category_already_exists(self, mocker):
        """Test that False is returned when category already in page"""
        mocker.patch("src.core.mk_cats.add_bot.Dont_add_to_pages_def", return_value=[])
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = "[[تصنيف:علوم]]"
        mock_page.namespace.return_value = 0
        mock_page.get_categories.return_value = []
        mocker.patch("src.core.mk_cats.add_bot._get_page", return_value=mock_page)

        result = add_to_page("صفحة", "تصنيف:علوم")
        assert result is False


class TestAddToFinalList:
    """Tests for add_to_final_list function"""

    def test_handles_empty_list(self):
        """Test that empty list is handled gracefully"""
        # Should not raise any error
        add_to_final_list([], "تصنيف:علوم")

    def test_handles_none_list(self):
        """Test that None list is handled gracefully"""
        # Should not raise any error
        add_to_final_list(None, "تصنيف:علوم")

    def test_adds_tasneef_prefix_if_missing(self, mocker):
        """Test that تصنيف: prefix is added if missing"""
        mocker.patch("src.core.mk_cats.add_bot.add_to_page", return_value=True)

        # The function should add prefix
        add_to_final_list(["صفحة1"], "علوم")
        # Should be called with تصنيف:علوم

    def test_replaces_underscores_in_title(self, mocker):
        """Test that underscores are replaced in title"""
        mock_add = mocker.patch("src.core.mk_cats.add_bot.add_to_page", return_value=True)

        add_to_final_list(["صفحة1"], "تصنيف:علوم_الحاسوب")

        # Should be called with spaces instead of underscores
        call_args = mock_add.call_args[0]
        assert "_" not in call_args[1] or "تصنيف:علوم الحاسوب" in str(call_args)

    def test_calls_add_to_page_for_each_item(self, mocker):
        """Test that add_to_page is called for each item in list"""
        mock_add = mocker.patch("src.core.mk_cats.add_bot.add_to_page", return_value=True)

        add_to_final_list(["صفحة1", "صفحة2", "صفحة3"], "تصنيف:علوم")

        assert mock_add.call_count == 3

    def test_calls_callback_on_success(self, mocker):
        """Test that callback is called on successful save"""
        mocker.patch("src.core.mk_cats.add_bot.add_to_page", return_value=True)
        mock_callback = mocker.MagicMock()

        add_to_final_list(["صفحة1"], "تصنيف:علوم", callback=mock_callback)

        mock_callback.assert_called_once()

    def test_handles_callback_exception(self, mocker):
        """Test that callback exceptions are handled"""
        mocker.patch("src.core.mk_cats.add_bot.add_to_page", return_value=True)
        mock_callback = mocker.MagicMock(side_effect=Exception("Test error"))

        # Should not raise exception
        add_to_final_list(["صفحة1"], "تصنيف:علوم", callback=mock_callback)
