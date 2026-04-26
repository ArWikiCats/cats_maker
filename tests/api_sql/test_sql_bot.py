"""
Tests for src/core/api_sql/sql_bot.py

This module tests SQL query functions for Wikipedia databases.
"""

from src.core.api_sql.sql_bot import (
    _fetch_ar_titles,
    _fetch_en_titles,
    get_exclusive_category_titles,
)


class TestFetchArcatTitles:
    """Tests for _fetch_ar_titles function"""

    def test_returns_empty_list_for_empty_title(self):
        """Test that empty list is returned for empty title"""
        result = _fetch_ar_titles("")
        assert result == []

    def test_returns_empty_list_for_none_title(self):
        """Test that empty list is returned for None title"""
        result = _fetch_ar_titles(None)
        assert result == []

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled via sql_new"""
        mocker.patch("src.core.api_sql.sql_bot.sql_new", return_value=[])

        result = _fetch_ar_titles("تصنيف:علوم")
        assert result == []

    def test_strips_tasneef_prefix(self, mocker):
        """Test that تصنيف: prefix is stripped from the values parameter"""
        mock_sql_new = mocker.patch("src.core.api_sql.sql_bot.sql_new", return_value=[])

        _fetch_ar_titles("تصنيف:علوم")

        call_kwargs = mock_sql_new.call_args[1]
        assert "values" in call_kwargs
        assert "تصنيف:" not in call_kwargs["values"][0]
        assert call_kwargs["values"][0] == "علوم"

    def test_replaces_spaces_with_underscores(self, mocker):
        """Test that spaces are replaced with underscores in parameter"""
        mock_sql_new = mocker.patch("src.core.api_sql.sql_bot.sql_new", return_value=[])

        _fetch_ar_titles("علوم الحاسوب")

        call_kwargs = mock_sql_new.call_args[1]
        assert "values" in call_kwargs
        assert "علوم_الحاسوب" in call_kwargs["values"][0]

    def test_uses_add_nstext_to_title_for_namespace_prefix(self, mocker):
        """Test that Arabic namespace prefixes are applied via add_nstext_to_title"""
        mocker.patch(
            "src.core.api_sql.sql_bot.sql_new",
            return_value=[
                {"page_title": "Test Page", "page_namespace": 14},
                {"page_title": "Normal Page", "page_namespace": 0},
            ],
        )

        result = _fetch_ar_titles("تصنيف:علوم")

        assert result == ["تصنيف:Test_Page", "Normal_Page"]


class TestFetchEnTitles:
    """Tests for _fetch_en_titles function"""

    def test_returns_empty_list_for_empty_title(self):
        """Test that empty list is returned for empty title"""
        result = _fetch_en_titles("")
        assert result == []

    def test_routes_through_sql_new(self, mocker):
        """Test that _fetch_en_titles routes through sql_new"""
        mock_sql_new = mocker.patch(
            "src.core.api_sql.sql_bot.sql_new",
            return_value=[
                {"ll_title": "Page1"},
                {"ll_title": "Page2"},
            ],
        )

        result = _fetch_en_titles("Category:Science")

        assert result == ["Page1", "Page2"]
        call_kwargs = mock_sql_new.call_args[1]
        assert call_kwargs["wiki"] == "enwiki"


class TestGetExclusiveCategoryTitles:
    """Tests for get_exclusive_category_titles function"""

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.core.api_sql.sql_bot.GET_SQL", return_value=False)

        result = get_exclusive_category_titles("Science", "علوم")
        assert result == []

    def test_returns_difference_of_lists(self, mocker):
        """Test that result is difference of en and ar lists"""
        mocker.patch("src.core.api_sql.sql_bot.GET_SQL", return_value=True)
        mocker.patch("src.core.api_sql.sql_bot._fetch_ar_titles", return_value=["Page1", "Page2"])
        mocker.patch(
            "src.core.api_sql.sql_bot._fetch_en_titles",
            return_value=["Page1", "Page2", "Page3"],
        )

        result = get_exclusive_category_titles("Science", "علوم")

        assert result == ["Page3"]
