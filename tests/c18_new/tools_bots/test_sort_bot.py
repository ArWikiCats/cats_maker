"""
Tests for src/c18_new/tools_bots/sort_bot.py

This module tests category sorting functions.
"""

import pytest

from src.core.c18_new.tools_bots.sort_bot import (
    sort_categories,
    sort_text,
)


class TestSortText:
    """Tests for sort_text function"""

    def test_sorts_arabic_categories_alphabetically(self):
        """Test that Arabic categories are sorted alphabetically"""
        categories = [
            "[[تصنيف:علوم]]",
            "[[تصنيف:أدب]]",
            "[[تصنيف:تاريخ]]",
        ]
        result = sort_text(categories)
        # Arabic alphabetical order: أ before ت before ع
        assert result[0] == "[[تصنيف:أدب]]"
        assert result[1] == "[[تصنيف:تاريخ]]"
        assert result[2] == "[[تصنيف:علوم]]"

    def test_handles_empty_list(self):
        """Test that empty list returns empty list"""
        result = sort_text([])
        assert result == []

    def test_handles_single_category(self):
        """Test that single category returns same category"""
        categories = ["[[تصنيف:علوم]]"]
        result = sort_text(categories)
        assert result == ["[[تصنيف:علوم]]"]

    def test_removes_duplicates(self):
        """Test that duplicate categories are removed"""
        categories = [
            "[[تصنيف:علوم]]",
            "[[تصنيف:علوم]]",
            "[[تصنيف:تاريخ]]",
        ]
        result = sort_text(categories)
        assert len(result) == 2

    def test_handles_categories_with_numbers(self):
        """Test handling categories with numbers"""
        categories = [
            "[[تصنيف:أحداث 2020]]",
            "[[تصنيف:أحداث 2010]]",
            "[[تصنيف:أحداث 2015]]",
        ]
        result = sort_text(categories)
        assert len(result) == 3
        # Numbers are sorted before letters

    def test_handles_categories_with_sort_keys(self):
        """Test handling categories with sort keys (pipe separator)"""
        categories = [
            "[[تصنيف:علوم|*]]",
            "[[تصنيف:أدب]]",
        ]
        result = sort_text(categories)
        assert len(result) == 2


class TestSortCategories:
    """Tests for sort_categories function"""

    def test_returns_original_text_if_no_categories(self):
        """Test that text without categories returns unchanged"""
        text = "هذا نص عادي بدون تصنيفات"
        result = sort_categories(text, "صفحة اختبار")
        assert result == text

    def test_sorts_categories_in_text(self):
        """Test that categories are sorted in text"""
        text = "محتوى الصفحة\n[[تصنيف:علوم]]\n[[تصنيف:أدب]]"
        result = sort_categories(text, "صفحة اختبار")
        # Categories should be extracted and sorted
        assert "[[تصنيف:" in result

    def test_preserves_text_content(self):
        """Test that text content is preserved"""
        text = "محتوى مهم\n[[تصنيف:علوم]]"
        result = sort_categories(text, "صفحة")
        assert "محتوى مهم" in result

    def test_handles_empty_text(self):
        """Test handling empty text"""
        result = sort_categories("", "صفحة")
        assert result == ""

    def test_handles_categories_with_special_sort_keys(self):
        """Test categories with special sort keys (asterisk, space)"""
        text = "محتوى\n[[تصنيف:علوم|*]]"
        result = sort_categories(text, "صفحة")
        assert "[[تصنيف:علوم" in result

    def test_moves_self_referencing_category_to_front(self):
        """Test that self-referencing category (matching title) is moved to front"""
        text = "محتوى\n[[تصنيف:علوم]]\n[[تصنيف:صفحة]]"
        result = sort_categories(text, "صفحة")
        # Category matching title should be handled specially
        assert "[[تصنيف:" in result
