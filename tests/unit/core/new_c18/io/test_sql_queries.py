"""
Unit tests for src/core/new_c18/io/sql_queries.py module.
"""

from unittest.mock import patch

from src.core.new_c18.io.sql_queries import (
    fetch_ar_category_members,
    fetch_dont_add_pages,
    fetch_en_category_langlinks,
)


class TestFetchArCategoryMembers:
    @patch("src.core.new_c18.io.sql_queries.db_manager")
    def test_returns_rows(self, mock_db):
        mock_db.execute_query.return_value = [{"page_title": "Test", "page_namespace": 0}]
        result = fetch_ar_category_members("تصنيف:علوم")
        assert len(result) == 1
        mock_db.execute_query.assert_called_once()

    @patch("src.core.new_c18.io.sql_queries.db_manager")
    def test_strips_prefix_and_spaces(self, mock_db):
        mock_db.execute_query.return_value = []
        fetch_ar_category_members("تصنيف:علوم الطبيعة")
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"] == ("علوم_الطبيعة",)

    @patch("src.core.new_c18.io.sql_queries.db_manager")
    def test_returns_empty_on_error(self, mock_db):
        mock_db.execute_query.side_effect = Exception("db error")
        result = fetch_ar_category_members("test")
        assert result == []


class TestFetchEnCategoryLanglinks:
    @patch("src.core.new_c18.io.sql_queries.db_manager")
    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_returns_rows(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.execute_query.return_value = [{"ll_title": "علوم"}]
        result = fetch_en_category_langlinks("Science")
        assert len(result) == 1

    @patch("src.core.new_c18.io.sql_queries.db_manager")
    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_strips_category_prefix(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.execute_query.return_value = []
        fetch_en_category_langlinks("Category:Science")
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"] == ("Science",)

    @patch("src.core.new_c18.io.sql_queries.db_manager")
    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_returns_empty_on_error(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.execute_query.side_effect = Exception("db error")
        result = fetch_en_category_langlinks("test")
        assert result == []


class TestFetchDontAddPages:
    @patch("src.core.new_c18.io.sql_queries.add_namespace_prefix")
    @patch("src.core.new_c18.io.sql_queries.db_manager")
    def test_returns_prefixed_titles(self, mock_db, mock_prefix):
        mock_db.execute_query.return_value = [{"page_title": "Test", "page_namespace": 0}]
        mock_prefix.return_value = "مقالة:Test"
        result = fetch_dont_add_pages()
        assert result == ["مقالة:Test"]

    @patch("src.core.new_c18.io.sql_queries.db_manager")
    def test_returns_empty_on_error(self, mock_db):
        mock_db.execute_query.side_effect = Exception("db error")
        result = fetch_dont_add_pages()
        assert result == []
