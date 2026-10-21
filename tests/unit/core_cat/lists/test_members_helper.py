"""
Tests for members_helper.py

This module tests the helper functions for category member processing:
- gather_members_from_api() - Gather members from API
- merge_member_lists() - Merge multiple member lists
- filter_invalid_members() - Filter out invalid members
- deduplicate_members() - Remove duplicates from member list
- collect_category_members() - Main entry point for member collection
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.cats_maker.core_cat.lists.members_helper import (
    collect_category_members,
    deduplicate_members,
    filter_invalid_members,
    gather_members_from_api,
    merge_member_lists,
)


@pytest.fixture
def mock_gather_api(mocker):
    """Fixture to mock gather_members_from_api."""
    return mocker.patch("src.cats_maker.core_cat.lists.members_helper.gather_members_from_api")


@dataclass
class CollectMembersDeps:
    """Dataclass holding mocked dependencies for collect_category_members tests."""

    gather_sql: MagicMock
    gather_api: MagicMock
    remove_redirects: MagicMock
    settings: MagicMock


@pytest.fixture
def collect_members_deps(mocker) -> CollectMembersDeps:
    """Fixture providing a complete set of mocked dependencies for collect_category_members."""
    return CollectMembersDeps(
        gather_sql=mocker.patch(
            "src.cats_maker.core_cat.lists.members_helper.gather_members_from_sql", return_value=[]
        ),
        gather_api=mocker.patch(
            "src.cats_maker.core_cat.lists.members_helper.gather_members_from_api", return_value=[]
        ),
        remove_redirects=mocker.patch(
            "src.cats_maker.core_cat.lists.members_helper.remove_redirect_pages",
            side_effect=lambda lang, members: members,
        ),
        settings=mocker.patch("src.cats_maker.core_cat.lists.members_helper.main_settings"),
    )


class TestGatherMembersFromApi:
    """Tests for gather_members_from_api function."""

    def test_calls_make_lit_api_way(self, mocker):
        """Test that gather_members_from_api calls CategoryResolver.make_lit_api_way."""
        mock_api = mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.make_lit_api_way",
            return_value=["Article1", "Article2"],
        )

        result = gather_members_from_api("Category:Science")

        mock_api.assert_called_once_with("Category:Science", item_type="all")
        assert result == ["Article1", "Article2"]

    def test_returns_empty_list_when_api_returns_none(self, mocker):
        """Test that gather_members_from_api returns empty list when API returns None."""
        mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.make_lit_api_way",
            return_value=None,
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.members_helper.CategoryMembersClient.retrieve_category_members_with_langlinks",
            return_value=None,
        )

        result = gather_members_from_api("Category:Science")

        assert result == []

    def test_returns_empty_list_when_api_returns_false(self, mocker):
        """Test that gather_members_from_api returns empty list when API returns False."""
        mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.make_lit_api_way",
            return_value=False,
        )
        mocker.patch(
            "src.cats_maker.core_cat.lists.members_helper.CategoryMembersClient.retrieve_category_members_with_langlinks",
            return_value=False,
        )

        result = gather_members_from_api("Category:Science")

        assert result == []


class TestMergeMemberLists:
    """Tests for merge_member_lists function."""

    def test_merges_two_lists(self):
        """Test that merge_member_lists merges two lists."""
        result = merge_member_lists(["A", "B"], ["C", "D"])

        assert set(result) == {"A", "B", "C", "D"}

    def test_removes_duplicates(self):
        """Test that merge_member_lists removes duplicates."""
        result = merge_member_lists(["A", "B"], ["B", "C"])

        assert len(result) == 3
        assert set(result) == {"A", "B", "C"}

    def test_handles_empty_lists(self):
        """Test that merge_member_lists handles empty lists."""
        result = merge_member_lists([], [])

        assert result == []

    def test_merges_multiple_lists(self):
        """Test that merge_member_lists merges multiple lists."""
        result = merge_member_lists(["A"], ["B"], ["C"])

        assert set(result) == {"A", "B", "C"}


class TestFilterInvalidMembers:
    """Tests for filter_invalid_members function."""

    def test_filters_empty_strings(self):
        """Test that filter_invalid_members filters empty strings."""
        result = filter_invalid_members(["A", "", "B"])

        assert result == ["A", "B"]

    def test_filters_none_values(self):
        """Test that filter_invalid_members filters None values."""
        result = filter_invalid_members(["A", None, "B"])

        assert result == ["A", "B"]

    def test_filters_non_strings(self):
        """Test that filter_invalid_members filters non-string values."""
        result = filter_invalid_members(["A", 123, "B", [], {}])

        assert result == ["A", "B"]

    def test_returns_empty_list_for_all_invalid(self):
        """Test that filter_invalid_members returns empty list when all values are invalid."""
        result = filter_invalid_members(["", None, 123])

        assert result == []


class TestDeduplicateMembers:
    """Tests for deduplicate_members function."""

    def test_removes_duplicates(self):
        """Test that deduplicate_members removes duplicate entries."""
        result = deduplicate_members(["A", "A", "B", "B"])

        assert set(result) == {"A", "B"}
        assert len(result) == 2

    def test_handles_empty_list(self):
        """Test that deduplicate_members handles empty lists."""
        result = deduplicate_members([])

        assert result == []

    def test_preserves_unique_items(self):
        """Test that deduplicate_members preserves unique items."""
        result = deduplicate_members(["A", "B", "C"])

        assert set(result) == {"A", "B", "C"}


class TestCollectCategoryMembers:
    """Tests for collect_category_members function."""

    def test_collects_from_all_sources(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members collects from all available sources."""
        collect_members_deps.gather_sql.return_value = ["SqlArticle"]
        collect_members_deps.gather_api.return_value = ["ApiArticle"]

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert "SqlArticle" in result

    def test_skips_api_when_sql_has_results(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members skips API when SQL has results and SQL is enabled."""
        collect_members_deps.gather_sql.return_value = ["SqlArticle1", "SqlArticle2"]
        collect_members_deps.gather_api.return_value = ["ApiArticle"]
        collect_members_deps.settings.analytics_database.use_sql = True

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        collect_members_deps.gather_sql.assert_called_once()
        collect_members_deps.gather_api.assert_not_called()
        assert "SqlArticle1" in result
        assert "SqlArticle2" in result

    def test_uses_api_when_sql_disabled(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members uses API when SQL is disabled."""
        collect_members_deps.gather_sql.return_value = ["SqlArticle"]
        collect_members_deps.gather_api.return_value = ["ApiArticle"]
        collect_members_deps.settings.analytics_database.use_sql = False

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        collect_members_deps.gather_api.assert_called_once()
        assert "ApiArticle" in result

    def test_returns_empty_list_when_no_members(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members returns empty list when no members are found."""
        collect_members_deps.gather_sql.return_value = []
        collect_members_deps.gather_api.return_value = []
        collect_members_deps.remove_redirects.return_value = []
        collect_members_deps.settings.analytics_database.use_sql = False

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == []

    def test_removes_invalid_entries(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members removes invalid entries from the result."""
        collect_members_deps.gather_sql.return_value = ["Valid", "", None, 123]
        collect_members_deps.gather_api.return_value = []
        collect_members_deps.settings.analytics_database.use_sql = True

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == ["Valid"]

    def test_removes_duplicates(self, collect_members_deps: CollectMembersDeps):
        """Test that collect_category_members removes duplicate entries from the result."""
        collect_members_deps.gather_sql.return_value = ["Article", "Article"]
        collect_members_deps.gather_api.return_value = []
        collect_members_deps.settings.analytics_database.use_sql = True

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == ["Article"]
