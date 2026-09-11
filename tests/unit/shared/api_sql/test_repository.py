"""Unit tests for src/core/api_sql/repository.py module."""

import pytest

from src.shared.api_sql.repository import CategoryRepository


@pytest.fixture
def mock_db(mocker):
    """Mock WikiReplicaDB class and return its instance mock."""
    mock_instance = mocker.MagicMock()
    mocker.patch(
        "src.shared.api_sql.repository.WikiReplicaDB",
        return_value=mock_instance,
    )
    return mock_instance


class TestFetchArabicTitlesWithEnglishLinks:
    """Tests for CategoryRepository.fetch_arabic_titles_with_english_links."""

    def test_returns_prefixed_titles(self, mock_db):
        mock_db.select_safe.return_value = [
            {"page_title": "علوم", "page_namespace": 14},
            {"page_title": "فيزياء", "page_namespace": 0},
        ]
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Science")
        assert result == ["تصنيف:علوم", "فيزياء"]

    def test_replaces_spaces_with_underscores(self, mock_db):
        mock_db.select_safe.return_value = [
            {"page_title": "علوم الحاسوب", "page_namespace": 14},
        ]
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Computer_science")
        assert result == ["تصنيف:علوم_الحاسوب"]

    def test_returns_empty_list_on_error(self, mock_db):
        mock_db.select_safe.side_effect = Exception("db down")
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Science")
        assert result == []

    def test_returns_empty_list_for_no_results(self, mock_db):
        mock_db.select_safe.return_value = []
        result = CategoryRepository.fetch_arabic_titles_with_english_links("Nonexistent")
        assert result == []

    def test_passes_correct_params(self, mock_db, mocker):
        mock_db.select_safe.return_value = []
        CategoryRepository.fetch_arabic_titles_with_english_links("TestCategory")
        mock_db.select_safe.assert_called_once_with(
            query=mocker.ANY,
            params=("TestCategory",),
        )


class TestFetchEnglishTitlesWithArabicLinks:
    """Tests for CategoryRepository.fetch_english_titles_with_arabic_links."""

    def test_returns_sorted_titles(self, mock_db):
        mock_db.select_safe.return_value = [
            {"ll_title": "Zebra"},
            {"ll_title": "Apple"},
            {"ll_title": "Mango"},
        ]
        result = CategoryRepository.fetch_english_titles_with_arabic_links("حيوانات")
        assert result == ["Apple", "Mango", "Zebra"]

    def test_returns_empty_list_on_error(self, mock_db):
        mock_db.select_safe.side_effect = Exception("timeout")
        result = CategoryRepository.fetch_english_titles_with_arabic_links("Test")
        assert result == []

    def test_returns_empty_list_for_no_results(self, mock_db):
        mock_db.select_safe.return_value = []
        result = CategoryRepository.fetch_english_titles_with_arabic_links("Empty")
        assert result == []

    def test_passes_correct_params(self, mock_db, mocker):
        mock_db.select_safe.return_value = []
        CategoryRepository.fetch_english_titles_with_arabic_links("MyCat")
        mock_db.select_safe.assert_called_once_with(
            query=mocker.ANY,
            params=("MyCat",),
        )
