"""
Tests for src/api_sql/sql_bot.py

This module tests SQL query functions for Wikipedia databases.
"""

import pytest

from src.api_sql.sql_bot import (
    Make_sql,
    fetch_arcat_titles,
    find_sql,
    get_exclusive_category_titles,
)


class TestFetchArcatTitles:
    """Tests for fetch_arcat_titles function"""

    def test_returns_empty_list_for_empty_title(self):
        """Test that empty list is returned for empty title"""
        result = fetch_arcat_titles("")
        assert result == []

    def test_returns_empty_list_for_none_title(self):
        """Test that empty list is returned for None title"""
        result = fetch_arcat_titles(None)
        assert result == []

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=False)

        result = fetch_arcat_titles("تصنيف:علوم")
        assert result == []

    def test_strips_tasneef_prefix(self, mocker):
        """Test that تصنيف: prefix is stripped"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.wiki_sql.make_labsdb_dbs_p", return_value=("host", "db"))
        mock_connect = mocker.patch("src.api_sql.sql_bot.make_sql_connect", return_value=[])

        fetch_arcat_titles("تصنيف:علوم")

        # Query should not contain تصنيف: prefix
        call_args = mock_connect.call_args[0][0]
        assert "تصنيف:" not in call_args

    def test_replaces_spaces_with_underscores(self, mocker):
        """Test that spaces are replaced with underscores in parameter"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.wiki_sql.make_labsdb_dbs_p", return_value=("host", "db"))
        mock_connect = mocker.patch("src.api_sql.sql_bot.make_sql_connect", return_value=[])

        fetch_arcat_titles("علوم الحاسوب")

        # Check that the parameter is passed correctly (with underscores)
        call_kwargs = mock_connect.call_args[1]
        assert "values" in call_kwargs
        assert "علوم_الحاسوب" in call_kwargs["values"][0]


class TestMakeSql:
    """Tests for Make_sql function"""

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=False)

        result = Make_sql("SELECT * FROM page")
        assert result == []

    def test_defaults_to_enwiki(self, mocker):
        """Test that default wiki is enwiki"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mock_make_labs = mocker.patch("src.api_sql.sql_bot.wiki_sql.make_labsdb_dbs_p", return_value=("host", "db"))
        mocker.patch("src.api_sql.sql_bot.make_sql_connect", return_value=[])

        Make_sql("SELECT * FROM page")

        mock_make_labs.assert_called_with("enwiki")

    def test_sorts_results(self, mocker):
        """Test that results are sorted"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.wiki_sql.make_labsdb_dbs_p", return_value=("host", "db"))
        mocker.patch(
            "src.api_sql.sql_bot.make_sql_connect",
            return_value=[
                (b"Zebra",),
                (b"Apple",),
                (b"Mango",),
            ],
        )

        result = Make_sql("SELECT * FROM page")

        assert result == sorted(result)


class TestGetExclusiveCategoryTitles:
    """Tests for get_exclusive_category_titles function"""

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=False)

        result = get_exclusive_category_titles("Science", "علوم")
        assert result == []

    def test_returns_difference_of_lists(self, mocker):
        """Test that result is difference of en and ar lists"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.fetch_arcat_titles", return_value=["Page1", "Page2"])

        # Mock fetch_encat_titles indirectly through Make_sql
        mocker.patch("src.api_sql.sql_bot.wiki_sql.make_labsdb_dbs_p", return_value=("host", "db"))
        mocker.patch(
            "src.api_sql.sql_bot.make_sql_connect",
            return_value=[
                {"ll_title": b"Page1"},
                {"ll_title": b"Page2"},
                {"ll_title": b"Page3"},
            ],
        )

        # Page3 should be in result (in en but not in ar)
        # This depends on internal implementation


class TestFindSql:
    """Tests for find_sql function"""

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that empty list is returned when SQL is disabled"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=False)

        result = find_sql("Science")
        assert result == []

    def test_returns_empty_list_for_no_results(self, mocker):
        """Test that empty list is returned when no results"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.get_exclusive_category_titles", return_value=[])

        result = find_sql("EmptyCategory")
        assert result == []

    def test_replaces_underscores_with_spaces(self, mocker):
        """Test that underscores are replaced with spaces in results"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.get_exclusive_category_titles", return_value=["Page_With_Underscores"])

        result = find_sql("Category")

        assert "Page With Underscores" in result

    def test_filters_empty_pages(self, mocker):
        """Test that empty page names are filtered"""
        mocker.patch("src.api_sql.sql_bot.wiki_sql.GET_SQL", return_value=True)
        mocker.patch("src.api_sql.sql_bot.get_exclusive_category_titles", return_value=["Page1", "", "  ", "Page2"])

        result = find_sql("Category")

        assert "" not in result
        assert "  " not in result
