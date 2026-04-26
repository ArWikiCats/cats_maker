"""
Tests for src/b18_new/sql_cat.py

This module tests SQL-based category functions.
"""

import pytest

from src.core.b18_new.sql_cat import (
    do_sql,
    get_ar_list,
    get_ar_list_from_en,
    make_ar_list_newcat2,
)


class TestGetArList:
    """Tests for get_ar_list function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=False)

        result = get_ar_list("تصنيف:علوم")

        assert isinstance(result, list)

    def test_uses_sql_when_enabled(self, mocker):
        """Test that SQL is used when enabled"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=True)
        mock_sql = mocker.patch("src.core.b18_new.sql_cat.sql_new_title_ns", return_value=["صفحة1", "صفحة2"])

        result = get_ar_list("تصنيف:علوم", us_sql=True)

        mock_sql.assert_called_once()

    def test_replaces_spaces_with_underscores(self, mocker):
        """Test that spaces are replaced with underscores in parameter"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=True)
        mock_sql = mocker.patch("src.core.b18_new.sql_cat.sql_new_title_ns", return_value=[])

        get_ar_list("تصنيف:علوم الحاسوب", us_sql=True)

        # Check that the parameter is passed correctly (with underscores)
        call_kwargs = mock_sql.call_args[1]
        assert "values" in call_kwargs
        assert "علوم_الحاسوب" in call_kwargs["values"][0]


class TestGetArListFromEn:
    """Tests for get_ar_list_from_en function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=False)
        mocker.patch("src.core.b18_new.sql_cat.fetch_ar_titles_based_on_en_category", return_value=[])

        result = get_ar_list_from_en("Science")

        assert isinstance(result, list)

    def test_uses_sql_when_enabled(self, mocker):
        """Test that SQL is used when enabled"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=True)
        mock_sql = mocker.patch(
            "src.core.b18_new.sql_cat.sql_new", return_value=[{"ll_title": "صفحة1"}, {"ll_title": "صفحة2"}]
        )

        result = get_ar_list_from_en("Science", us_sql=True)

        mock_sql.assert_called_once()

    def test_falls_back_to_api_when_sql_disabled(self, mocker):
        """Test fallback to API when SQL is disabled"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=False)
        mock_api = mocker.patch("src.core.b18_new.sql_cat.fetch_ar_titles_based_on_en_category", return_value=["صفحة1"])

        result = get_ar_list_from_en("Science")

        mock_api.assert_called_once()

    def test_replaces_underscores_in_results(self, mocker):
        """Test that underscores are replaced with spaces in results"""
        mocker.patch("src.core.b18_new.sql_cat.GET_SQL", return_value=True)
        mocker.patch("src.core.b18_new.sql_cat.sql_new", return_value=[{"ll_title": "صفحة_اختبار"}])

        result = get_ar_list_from_en("Science", us_sql=True)

        assert "صفحة اختبار" in result


class TestDoSql:
    """Tests for do_sql function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.sql_cat.get_ar_list", return_value=[])
        mocker.patch("src.core.b18_new.sql_cat.get_ar_list_from_en", return_value=[])

        result = do_sql("Science", "علوم")

        assert isinstance(result, list)

    def test_returns_difference_of_lists(self, mocker):
        """Test that result is pages in en but not in ar"""
        mocker.patch("src.core.b18_new.sql_cat.get_ar_list", return_value=["صفحة1", "صفحة2"])
        mocker.patch("src.core.b18_new.sql_cat.get_ar_list_from_en", return_value=["صفحة1", "صفحة2", "صفحة3"])

        result = do_sql("Science", "علوم")

        assert "صفحة3" in result
        assert "صفحة1" not in result
        assert "صفحة2" not in result


class TestMakeArListNewcat2:
    """Tests for make_ar_list_newcat2 function"""

    def test_returns_list(self, mocker):
        """Test that function returns a list"""
        mocker.patch("src.core.b18_new.sql_cat.do_sql", return_value=[])

        result = make_ar_list_newcat2("علوم", "Science")

        assert isinstance(result, list)

    def test_cleans_category_prefix(self, mocker):
        """Test that Category: prefix is cleaned"""
        mock_do_sql = mocker.patch("src.core.b18_new.sql_cat.do_sql", return_value=[])

        make_ar_list_newcat2("تصنيف:علوم", "Category:Science")

        call_args = mock_do_sql.call_args[0]
        assert "Category:" not in call_args[0]
        assert "تصنيف:" not in call_args[1]

    def test_handles_duplicate_category_prefix(self, mocker):
        """Test handling of duplicate Category: prefix"""
        mock_do_sql = mocker.patch("src.core.b18_new.sql_cat.do_sql", return_value=[])

        make_ar_list_newcat2("تصنيف:علوم", "Category:Category:Science")

        call_args = mock_do_sql.call_args[0]
        assert "Category:Category:" not in call_args[0]

    def test_replaces_underscores(self, mocker):
        """Test that underscores are replaced with spaces"""
        mock_do_sql = mocker.patch("src.core.b18_new.sql_cat.do_sql", return_value=[])

        make_ar_list_newcat2("علوم_الحاسوب", "Computer_Science")

        call_args = mock_do_sql.call_args[0]
        assert "_" not in call_args[0]
        assert "_" not in call_args[1]

    def test_passes_wiki_parameter(self, mocker):
        """Test that wiki parameter is passed"""
        mock_do_sql = mocker.patch("src.core.b18_new.sql_cat.do_sql", return_value=[])

        make_ar_list_newcat2("علوم", "Sciences", wiki="fr")

        call_kwargs = mock_do_sql.call_args[1]
        assert call_kwargs["wiki"] == "fr"
