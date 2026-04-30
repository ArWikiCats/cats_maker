"""
Tests for service.py

This module tests namespace handling and SQL query functions for MediaWiki.
"""

from src.core.api_sql.service import CategoryComparator


class TestCategoryComparator:
    """Tests for CategoryComparator class"""

    def test_normalize_category_title(self):
        """Test normalize_category_title method"""
        comparator = CategoryComparator()
        assert comparator.normalize_category_title("تصنيف:علوم", r"تصنيف:") == "علوم"
        assert comparator.normalize_category_title("علوم الحاسوب", r"تصنيف:") == "علوم_الحاسوب"
        assert comparator.normalize_category_title("Category:Science", r"category:") == "Science"

    def test_normalize_category_title_empty_returns_empty(self):
        """Test that empty title returns empty string unchanged"""
        assert CategoryComparator.normalize_category_title("", r"prefix:") == ""

    def test_normalize_category_title_none_returns_none(self):
        """Test that None title returns None unchanged"""
        assert CategoryComparator.normalize_category_title(None, r"prefix:") is None

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

    def test_get_exclusive_returns_empty_when_en_title_becomes_empty(self, mocker):
        """Test that empty list is returned when English title normalizes to empty"""
        mocker.patch("src.core.api_sql.service.ConfigLoader.is_production", return_value=True)
        comparator = CategoryComparator()
        # An input that is entirely the prefix pattern will normalize to empty
        result = comparator.get_exclusive_category_titles("[[en:]]", "علوم")
        assert result == []

    def test_get_exclusive_skips_ar_fetch_when_ar_title_empty(self, mocker):
        """Test that Arabic repo is not called when ar_category normalizes to empty.

        Note: This currently hits an UnboundLocalError bug in service.py:67
        where ar_titles is referenced but never assigned when ar_title_clean
        is empty. When the bug is fixed, this test should be updated.
        """
        mocker.patch("src.core.api_sql.service.ConfigLoader.is_production", return_value=True)
        mock_ar = mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_arabic_titles_with_english_links",
            return_value=[],
        )
        mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_english_titles_with_arabic_links",
            return_value=["Page1"],
        )

        comparator = CategoryComparator()
        # Arabic category that is entirely the prefix will normalize to empty
        # This triggers UnboundLocalError because ar_titles is never assigned
        import pytest

        with pytest.raises(UnboundLocalError):
            comparator.get_exclusive_category_titles("Science", "تصنيف:")

        mock_ar.assert_not_called()

    def test_get_exclusive_returns_all_when_no_ar_titles(self, mocker):
        """Test that all EN titles are returned when AR set is empty"""
        mocker.patch("src.core.api_sql.service.ConfigLoader.is_production", return_value=True)
        mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_arabic_titles_with_english_links",
            return_value=[],
        )
        mocker.patch(
            "src.core.api_sql.repository.CategoryRepository.fetch_english_titles_with_arabic_links",
            return_value=["A", "B"],
        )

        comparator = CategoryComparator()
        result = comparator.get_exclusive_category_titles("Science", "علوم")
        assert result == ["A", "B"]
