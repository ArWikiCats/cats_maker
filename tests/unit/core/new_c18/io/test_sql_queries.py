"""
Unit tests for src/core/new_c18/io/sql_queries.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.new_c18.io.sql_queries import (
    fetch_ar_category_members,
    fetch_dont_add_pages,
    fetch_en_category_langlinks,
)


@pytest.fixture
def mock_db(monkeypatch):
    """Mock database connections."""
    mock_instance = MagicMock()
    mock_class = MagicMock(return_value=mock_instance)
    monkeypatch.setattr("src.core.new_c18.io.sql_queries.WikiReplicaDB", mock_class)
    return mock_instance


class TestFetchArCategoryMembers:

    def test_returns_rows(self, mock_db):
        mock_db.select_safe.return_value = [{"page_title": "Test", "page_namespace": 0}]
        result = fetch_ar_category_members("تصنيف:علوم")
        assert len(result) == 1
        mock_db.select_safe.assert_called_once()

    def test_strips_prefix_and_spaces(self, mock_db):
        mock_db.select_safe.return_value = []
        fetch_ar_category_members("تصنيف:علوم الطبيعة")
        call_args = mock_db.select_safe.call_args
        assert call_args[1]["params"] == ("علوم_الطبيعة",)

    def test_returns_empty_on_error(self, mock_db):
        mock_db.select_safe.side_effect = Exception("db error")
        result = fetch_ar_category_members("test")
        assert result == []


class TestFetchEnCategoryLanglinks:

    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_returns_rows(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.select_safe.return_value = [{"ll_title": "علوم"}]
        result = fetch_en_category_langlinks("Science")
        assert len(result) == 1

    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_strips_category_prefix(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.select_safe.return_value = []
        fetch_en_category_langlinks("Category:Science")
        call_args = mock_db.select_safe.call_args
        assert call_args[1]["params"] == ("Science",)

    @patch("src.core.new_c18.io.sql_queries.main_settings")
    def test_returns_empty_on_error(self, mock_settings, mock_db):
        mock_settings.query.ns_no_10 = False
        mock_settings.query.ns_only_14 = False
        mock_db.select_safe.side_effect = Exception("db error")
        result = fetch_en_category_langlinks("test")
        assert result == []


class TestFetchDontAddPages:

    @patch("src.core.new_c18.io.sql_queries.add_namespace_prefix")
    def test_returns_prefixed_titles(self, mock_prefix, mock_db):
        mock_db.select_safe.return_value = [{"page_title": "Test", "page_namespace": 0}]
        mock_prefix.return_value = "مقالة:Test"
        result = fetch_dont_add_pages()
        assert result == ["مقالة:Test"]

    def test_returns_empty_on_error(self, mock_db):
        mock_db.select_safe.side_effect = Exception("db error")
        result = fetch_dont_add_pages()
        assert result == []
