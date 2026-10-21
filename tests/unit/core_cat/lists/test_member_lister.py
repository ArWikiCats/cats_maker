"""
Tests for member_lister.py

This module tests category page listing functions.
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.core_cat.lists.member_lister import MemberLister


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()

    settings.analytics_database = MagicMock()
    settings.analytics_database.use_sql = False

    return settings


class TestExtractFanPageTitles:
    """Tests for MemberLister.extract_fan_page_titles method"""

    def test_returns_list(self, mock_settings):
        """
        Test that method returns a list"""

        lister = MemberLister(settings=mock_settings)
        result = lister.extract_fan_page_titles("Category:Science")

        assert isinstance(result, list)

    def test_returns_empty_when_sql_disabled(self, mock_settings):
        """
        Test that empty list is returned when SQL is disabled"""

        lister = MemberLister(settings=mock_settings)
        result = lister.extract_fan_page_titles("Category:Science")

        assert result == []

    def test_calls_get_exclusive_when_sql_enabled(self, mocker, mock_settings):
        """
        Test that get_exclusive_category_titles is called when SQL enabled"""
        mock_settings.analytics_database.use_sql = True

        mock_comparator = mocker.patch("src.cats_maker.core_cat.lists.member_lister.CategoryComparator")
        mock_comparator.return_value.get_exclusive_category_titles.return_value = ["Page1", "Page2"]

        lister = MemberLister(settings=mock_settings)
        result = lister.extract_fan_page_titles("Category:Science")

        mock_comparator.return_value.get_exclusive_category_titles.assert_called_once()
        assert len(result) == 2

    def test_strips_category_prefix(self, mocker, mock_settings):
        """
        Test that Category: prefix is stripped"""
        mock_settings.analytics_database.use_sql = True

        mock_comparator = mocker.patch("src.cats_maker.core_cat.lists.member_lister.CategoryComparator")
        mock_get_exclusive = mock_comparator.return_value.get_exclusive_category_titles
        mock_get_exclusive.return_value = []

        lister = MemberLister(settings=mock_settings)
        lister.extract_fan_page_titles("Category:Science")

        call_args = mock_get_exclusive.call_args[0]
        assert "Category:" not in call_args[0]


class TestGetListenPageTitle:
    """Tests for MemberLister.get_listen_page_title method"""

    def test_returns_list(self, mocker):
        """
        Test that method returns a list"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=False),
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.MemberLister.extract_fan_page_titles",
            return_value=[],
        )

        lister = MemberLister()
        result = lister.get_listen_page_title("تصنيف:علوم", "Category:Science")

        assert isinstance(result, list)

    def test_strips_whitespace_from_title(self, mocker):
        """
        Test that whitespace is stripped from title"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=False),
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.MemberLister.extract_fan_page_titles",
            return_value=[],
        )

        lister = MemberLister()
        result = lister.get_listen_page_title("تصنيف:علوم", "  Category:Science  ")

        # Should work without error
        assert isinstance(result, list)

    def test_uses_resolver_when_valid(self, mocker):
        """
        Test that resolver is called when validation passes"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=True),
        )
        mock_resolver = mocker.Mock()
        mock_resolver.resolve_members.return_value = ["صفحة1", "صفحة2"]

        lister = MemberLister(resolver=mock_resolver)
        result = lister.get_listen_page_title("تصنيف:علوم", "Category:Science")

        mock_resolver.resolve_members.assert_called_once()
        assert "صفحة1" in result

    def test_falls_back_to_extract_fan_page_titles(self, mocker):
        """
        Test fallback to extract_fan_page_titles"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=False),
        )
        mock_extract = mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.MemberLister.extract_fan_page_titles",
            return_value=["Page1", "Page2"],
        )

        lister = MemberLister()
        result = lister.get_listen_page_title("تصنيف:علوم", "Category:Science")

        mock_extract.assert_called_once()
        assert "Page1" in result

    def test_removes_duplicates(self, mocker):
        """
        Test that duplicates are removed"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=False),
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.MemberLister.extract_fan_page_titles",
            return_value=["Page1", "Page1", "Page2"],
        )

        lister = MemberLister()
        result = lister.get_listen_page_title("تصنيف:علوم", "Category:Science")

        assert len(result) == len(set(result))

    def test_filters_empty_strings(self, mocker):
        """
        Test that empty strings are filtered"""
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.CategoryValidator.validate_categories_for_new_cat",
            return_value=mocker.Mock(valid=False),
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.member_lister.MemberLister.extract_fan_page_titles",
            return_value=["Page1", "", "Page2", None],
        )

        lister = MemberLister()
        result = lister.get_listen_page_title("تصنيف:علوم", "Category:Science")

        assert "" not in result
        assert None not in result
