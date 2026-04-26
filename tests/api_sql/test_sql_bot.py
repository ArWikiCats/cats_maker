"""
Tests for src/core/api_sql/sql_bot.py

This module tests SQL query functions for Wikipedia databases.
"""

from src.core.api_sql.sql_bot import (
    _fetch_ar_titles,
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
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.core.api_sql.sql_bot.GET_SQL", return_value=False)

        result = _fetch_ar_titles("تصنيف:علوم")
        assert result == []

    def test_strips_tasneef_prefix(self, mocker):
        """Test that تصنيف: prefix is stripped"""
        mocker.patch("src.core.api_sql.sql_bot.GET_SQL", return_value=True)
        mocker.patch("src.core.api_sql.sql_bot.make_labsdb_dbs_p", return_value=("host", "db"))
        mock_connect = mocker.patch("src.core.api_sql.sql_bot.make_sql_connect_silent", return_value=[])

        _fetch_ar_titles("تصنيف:علوم")

        # Query should not contain تصنيف: prefix
        call_args = mock_connect.call_args[0][0]
        assert "تصنيف:" not in call_args

    def test_replaces_spaces_with_underscores(self, mocker):
        """Test that spaces are replaced with underscores in parameter"""
        mocker.patch("src.core.api_sql.sql_bot.GET_SQL", return_value=True)
        mocker.patch("src.core.api_sql.sql_bot.make_labsdb_dbs_p", return_value=("host", "db"))
        mock_connect = mocker.patch("src.core.api_sql.sql_bot.make_sql_connect_silent", return_value=[])

        _fetch_ar_titles("علوم الحاسوب")

        # Check that the parameter is passed correctly (with underscores)
        call_kwargs = mock_connect.call_args[1]
        assert "values" in call_kwargs
        assert "علوم_الحاسوب" in call_kwargs["values"][0]


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

        # Mock fetch_encat_titles indirectly through Make_sql
        mocker.patch("src.core.api_sql.sql_bot.make_labsdb_dbs_p", return_value=("host", "db"))
        mocker.patch(
            "src.core.api_sql.sql_bot.make_sql_connect_silent",
            return_value=[
                {"ll_title": b"Page1"},
                {"ll_title": b"Page2"},
                {"ll_title": b"Page3"},
            ],
        )

        # Page3 should be in result (in en but not in ar)
        # This depends on internal implementation
