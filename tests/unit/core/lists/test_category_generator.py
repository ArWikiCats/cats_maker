"""
Unit tests for src/cats_maker/core/new_c18/core/category_generator.py module.
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.core.lists.category_generator import (
    fetch_category_members,
)


@pytest.fixture
def mock_load_api(mocker):
    """Fixture to mock AllAPIS.load."""
    return mocker.patch("src.cats_maker.core.lists.category_generator.AllAPIS.load")


class TestFetchCategoryMembers:
    """Tests for fetch_category_members function."""

    def test_returns_titles(self, mock_load_api):
        """Test that fetch_category_members returns page titles based on namespace."""
        mock_api = MagicMock()
        mock_api.catdepth.return_value = {
            "Page1": {"ns": 0},
            "Page2": {"ns": 0},
        }
        mock_load_api.return_value = mock_api
        result = fetch_category_members("Category:Test", wiki="en", namespaces=[0])
        assert "Page1" in result
        assert "Page2" in result

    def test_filters_by_namespace(self, mock_load_api):
        """Test that fetch_category_members filters out items not in the requested namespace."""
        mock_api = MagicMock()
        mock_api.catdepth.return_value = {
            "Page1": {"ns": 0},
            "Cat1": {"ns": 14},
        }
        mock_load_api.return_value = mock_api
        result = fetch_category_members("Category:Test", wiki="en", namespaces=[0])
        assert "Page1" in result
        assert "Cat1" not in result
