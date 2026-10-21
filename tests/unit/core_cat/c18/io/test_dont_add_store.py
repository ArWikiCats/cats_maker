"""
Unit tests for src/cats_maker/core_cat/c18/io/dont_add_store.py module.
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.core_cat.c18.io.dont_add_store import DontAddStore


@pytest.fixture
def mock_settings() -> MagicMock:
    """Set default settings for DontAddStore.get_dont_add_pages tests."""

    settings = MagicMock()
    settings.is_production = lambda: True

    settings.category = MagicMock()
    settings.category.no_dontadd = False
    settings.category.test_mode = False
    settings.category.test_add = True

    settings.paths = MagicMock()
    settings.paths.dont_add_to_pages_path = "/nonexistent/path.json"

    return settings


class TestGetDontAddPages:
    """Tests for DontAddStore.get_dont_add_pages function."""

    def test_returns_empty_when_no_dontadd_enabled(self, mock_settings) -> None:
        """Test that empty list is returned when no_dontadd is True."""

        mock_settings.category.no_dontadd = True
        result = DontAddStore(settings=mock_settings).get_dont_add_pages()
        assert result == []

    def test_returns_empty_when_test_mode_enabled(self, mock_settings) -> None:
        """Test that empty list is returned when test_mode is True."""
        mock_settings.category.test_mode = True

        result = DontAddStore(settings=mock_settings).get_dont_add_pages()
        assert result == []

    def test_returns_empty_when_not_production_and_no_test_add(self, mock_settings) -> None:
        """Test that empty list is returned in non-production without test_add."""
        mock_settings.category.test_add = False
        mock_settings.is_production = lambda: False

        result = DontAddStore(settings=mock_settings).get_dont_add_pages()
        assert result == []

    def test_returns_empty_when_filename_none(self, mock_settings) -> None:
        """Test that empty list is returned when _FILENAME_JSON is None."""

        mock_settings.paths.dont_add_to_pages_path = None

        result = DontAddStore(settings=mock_settings).get_dont_add_pages()
        assert result == []

    def test_returns_empty_when_fetch_returns_dict(self, monkeypatch: pytest.MonkeyPatch, mock_settings) -> None:
        """Test that empty list is returned when fetch returns dict instead of list."""
        monkeypatch.setattr(
            "src.cats_maker.core_cat.c18.io.dont_add_store.ArCategorySQL.fetch_dont_add_pages",
            lambda self: {"key": "value"},
        )

        result = DontAddStore(settings=mock_settings).get_dont_add_pages()
        assert result == []
