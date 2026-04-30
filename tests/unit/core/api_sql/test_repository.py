"""Unit tests for src/core/api_sql/repository.py module."""

import pytest

from src.core.api_sql.repository import CategoryRepository


class TestFetchArabicTitlesWithEnglishLinks:
    """Tests for CategoryRepository.fetch_arabic_titles_with_english_links."""

    def test_returns_prefixed_titles(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[
                {"page_title": "علوم", "page_namespace": 14},
                {"page_title": "فيزياء", "page_namespace": 0},
            ],
        )
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Science")
        assert result == ["تصنيف:علوم", "فيزياء"]

    def test_replaces_spaces_with_underscores(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[
                {"page_title": "علوم الحاسوب", "page_namespace": 14},
            ],
        )
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Computer_science")
        assert result == ["تصنيف:علوم_الحاسوب"]

    def test_returns_empty_list_on_error(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            side_effect=Exception("db down"),
        )
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Science")
        assert result == []

    def test_returns_empty_list_for_no_results(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[],
        )
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Nonexistent")
        assert result == []

    def test_passes_correct_params(self, mocker):
        mock_exec = mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[],
        )
        CategoryRepository.fetch_arabic_titles_with_english_links("TestCategory")
        mock_exec.assert_called_once_with(
            wiki="ar",
            query=mocker.ANY,
            params=("TestCategory",),
        )


class TestFetchEnglishTitlesWithArabicLinks:
    """Tests for CategoryRepository.fetch_english_titles_with_arabic_links."""

    def test_returns_sorted_titles(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[
                {"ll_title": "Zebra"},
                {"ll_title": "Apple"},
                {"ll_title": "Mango"},
            ],
        )
        result = CategoryRepository.fetch_english_titles_with_arabic_links("حيوانات")
        assert result == ["Apple", "Mango", "Zebra"]

    def test_returns_empty_list_on_error(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            side_effect=Exception("timeout"),
        )
        result = CategoryRepository.fetch_english_titles_with_arabic_links("Test")
        assert result == []

    def test_returns_empty_list_for_no_results(self, mocker):
        mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[],
        )
        result = CategoryRepository.fetch_english_titles_with_arabic_links("Empty")
        assert result == []

    def test_passes_correct_params(self, mocker):
        mock_exec = mocker.patch(
            "src.core.api_sql.repository.db_manager.execute_query",
            return_value=[],
        )
        CategoryRepository.fetch_english_titles_with_arabic_links("MyCat")
        mock_exec.assert_called_once_with(
            wiki="enwiki",
            query=mocker.ANY,
            params=("MyCat",),
        )
