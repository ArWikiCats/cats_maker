"""
Tests for sql_bot.py

This module tests SQL query functions for Wikipedia databases.
"""

from src.core.api_sql.service import (
    CategoryComparator,
)


class TestCategoryComparator:
    """Tests for CategoryComparator class"""

    def test_normalize_category_title(self):
        """Test normalize_category_title method"""
        comparator = CategoryComparator()
        assert comparator.normalize_category_title("تصنيف:علوم", r"تصنيف:") == "علوم"
        assert comparator.normalize_category_title("علوم الحاسوب", r"تصنيف:") == "علوم_الحاسوب"
        assert comparator.normalize_category_title("Category:Science", r"category:") == "Science"

    def test_get_exclusive_category_titles_returns_empty_list_when_not_prod(self, mocker):
        """Test that empty list is returned when not in production"""
        mocker.patch("src.core.api_sql.service.ConfigLoader.is_production", return_value=False)
        comparator = CategoryComparator()
        result = comparator.get_exclusive_category_titles("Science", "علوم")
        assert result == []

    def test_get_exclusive_category_titles_returns_difference(self, mocker):
        """Test that result is difference of en and ar lists"""
        mocker.patch("src.core.api_sql.service.ConfigLoader.is_production", return_value=True)
        mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_arabic_titles_with_english_links",
            return_value=["Page1", "Page2"],
        )
        mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_english_titles_with_arabic_links",
            return_value=["Page1", "Page2", "Page3"],
        )

        comparator = CategoryComparator()
        result = comparator.get_exclusive_category_titles("Science", "علوم")

        assert result == ["Page3"]
