"""
Tests for src/mk_cats/members_helper.py

This module tests the helper functions for category member processing:
- gather_members_from_sql() - Gather members from SQL sources
- gather_members_from_api() - Gather members from API
X- merge_member_lists() - Merge multiple member lists
- filter_invalid_members() - Filter out invalid members
- deduplicate_members() - Remove duplicates from member list
- remove_redirects() - Remove redirect pages
- collect_category_members() - Main entry point for member collection
"""

from unittest.mock import MagicMock

import pytest

from src.mk_cats.members_helper import gather_members_from_api, gather_members_from_sql


class TestGatherMembersFromSql:
    """Tests for gather_members_from_sql function."""

    def test_calls_get_listenpageTitle(self, mocker):
        """Test that gather_members_from_sql calls get_listenpageTitle."""
        mock_get_listen = mocker.patch(
            "src.mk_cats.members_helper.get_listenpageTitle", return_value=["Article1", "Article2"]
        )

        result = gather_members_from_sql("تصنيف:علوم", "Category:Science")

        mock_get_listen.assert_called_once_with("تصنيف:علوم", "Category:Science")
        assert result == ["Article1", "Article2"]

    def test_returns_empty_list_when_no_members(self, mocker):
        """Test that gather_members_from_sql returns empty list when no members found."""
        mocker.patch("src.mk_cats.members_helper.get_listenpageTitle", return_value=[])

        result = gather_members_from_sql("تصنيف:علوم", "Category:Science")

        assert result == []


class TestGatherMembersFromApi:
    """Tests for gather_members_from_api function."""

    def test_calls_makelitapiway(self, mocker):
        """Test that gather_members_from_api calls MakeLitApiWay."""
        mock_api = mocker.patch("src.mk_cats.members_helper.MakeLitApiWay", return_value=["Article1", "Article2"])

        result = gather_members_from_api("Category:Science")

        mock_api.assert_called_once_with("Category:Science", Type="all")
        assert result == ["Article1", "Article2"]

    def test_returns_empty_list_when_api_returns_none(self, mocker):
        """Test that gather_members_from_api returns empty list when API returns None."""
        mocker.patch("src.mk_cats.members_helper.MakeLitApiWay", return_value=None)
        mocker.patch("src.mk_cats.members_helper.sub_cats_query", return_value=None)

        result = gather_members_from_api("Category:Science")

        assert result == []

    def test_returns_empty_list_when_api_returns_false(self, mocker):
        """Test that gather_members_from_api returns empty list when API returns False."""
        mocker.patch("src.mk_cats.members_helper.MakeLitApiWay", return_value=False)
        mocker.patch("src.mk_cats.members_helper.sub_cats_query", return_value=False)

        result = gather_members_from_api("Category:Science")

        assert result == []


class TestMergeMemberLists:
    """Tests for merge_member_lists function."""

    def test_merges_two_lists(self):
        """Test that merge_member_lists merges two lists."""
        from src.mk_cats.members_helper import merge_member_lists

        result = merge_member_lists(["A", "B"], ["C", "D"])

        assert set(result) == {"A", "B", "C", "D"}

    def test_removes_duplicates(self):
        """Test that merge_member_lists removes duplicates."""
        from src.mk_cats.members_helper import merge_member_lists

        result = merge_member_lists(["A", "B"], ["B", "C"])

        assert len(result) == 3
        assert set(result) == {"A", "B", "C"}

    def test_handles_empty_lists(self):
        """Test that merge_member_lists handles empty lists."""
        from src.mk_cats.members_helper import merge_member_lists

        result = merge_member_lists([], [])

        assert result == []

    def test_merges_multiple_lists(self):
        """Test that merge_member_lists merges multiple lists."""
        from src.mk_cats.members_helper import merge_member_lists

        result = merge_member_lists(["A"], ["B"], ["C"])

        assert set(result) == {"A", "B", "C"}


class TestFilterInvalidMembers:
    """Tests for filter_invalid_members function."""

    def test_filters_empty_strings(self):
        """Test that filter_invalid_members filters empty strings."""
        from src.mk_cats.members_helper import filter_invalid_members

        result = filter_invalid_members(["A", "", "B"])

        assert result == ["A", "B"]

    def test_filters_none_values(self):
        """Test that filter_invalid_members filters None values."""
        from src.mk_cats.members_helper import filter_invalid_members

        result = filter_invalid_members(["A", None, "B"])

        assert result == ["A", "B"]

    def test_filters_non_strings(self):
        """Test that filter_invalid_members filters non-string values."""
        from src.mk_cats.members_helper import filter_invalid_members

        result = filter_invalid_members(["A", 123, "B", [], {}])

        assert result == ["A", "B"]

    def test_returns_empty_list_for_all_invalid(self):
        """Test that filter_invalid_members returns empty list when all invalid."""
        from src.mk_cats.members_helper import filter_invalid_members

        result = filter_invalid_members(["", None, 123])

        assert result == []


class TestDeduplicateMembers:
    """Tests for deduplicate_members function."""

    def test_removes_duplicates(self):
        """Test that deduplicate_members removes duplicates."""
        from src.mk_cats.members_helper import deduplicate_members

        result = deduplicate_members(["A", "A", "B", "B"])

        assert set(result) == {"A", "B"}
        assert len(result) == 2

    def test_handles_empty_list(self):
        """Test that deduplicate_members handles empty list."""
        from src.mk_cats.members_helper import deduplicate_members

        result = deduplicate_members([])

        assert result == []

    def test_preserves_unique_items(self):
        """Test that deduplicate_members preserves unique items."""
        from src.mk_cats.members_helper import deduplicate_members

        result = deduplicate_members(["A", "B", "C"])

        assert set(result) == {"A", "B", "C"}


class TestRemoveRedirects:
    """Tests for remove_redirects function."""

    def test_calls_remove_redirect_pages(self, mocker):
        """Test that remove_redirects calls remove_redirect_pages."""
        mock_remove = mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", return_value=["A", "B"])

        from src.mk_cats.members_helper import remove_redirects

        result = remove_redirects("ar", ["A", "B", "C"])

        mock_remove.assert_called_once_with("ar", ["A", "B", "C"])
        assert result == ["A", "B"]


class TestCollectCategoryMembers:
    """Tests for collect_category_members function."""

    def test_collects_from_all_sources(self, mocker):
        """Test that collect_category_members collects from all sources."""
        mocker.patch("src.mk_cats.members_helper.gather_members_from_sql", return_value=["SqlArticle"])
        mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=["ApiArticle"])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", side_effect=lambda lang, members: members)
        mocker.patch("src.mk_cats.members_helper.settings")

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert "SqlArticle" in result

    def test_skips_api_when_sql_has_results(self, mocker):
        """Test that collect_category_members skips API when SQL has results."""
        mock_sql = mocker.patch(
            "src.mk_cats.members_helper.gather_members_from_sql", return_value=["SqlArticle1", "SqlArticle2"]
        )
        mock_api = mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=["ApiArticle"])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", side_effect=lambda lang, members: members)

        # Mock settings to enable SQL
        mock_settings = mocker.patch("src.mk_cats.members_helper.settings")
        mock_settings.database.use_sql = True

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        mock_sql.assert_called_once()
        mock_api.assert_not_called()
        assert "SqlArticle1" in result
        assert "SqlArticle2" in result

    def test_uses_api_when_sql_disabled(self, mocker):
        """Test that collect_category_members uses API when SQL is disabled."""
        mock_sql = mocker.patch("src.mk_cats.members_helper.gather_members_from_sql", return_value=["SqlArticle"])
        mock_api = mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=["ApiArticle"])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", side_effect=lambda lang, members: members)

        # Mock settings to disable SQL
        mock_settings = mocker.patch("src.mk_cats.members_helper.settings")
        mock_settings.database.use_sql = False

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        mock_api.assert_called_once()
        assert "ApiArticle" in result

    def test_returns_empty_list_when_no_members(self, mocker):
        """Test that collect_category_members returns empty list when no members."""
        mocker.patch("src.mk_cats.members_helper.gather_members_from_sql", return_value=[])
        mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=[])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", return_value=[])

        # Mock settings to disable SQL
        mock_settings = mocker.patch("src.mk_cats.members_helper.settings")
        mock_settings.database.use_sql = False

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == []

    def test_removes_invalid_entries(self, mocker):
        """Test that collect_category_members removes invalid entries."""
        mocker.patch("src.mk_cats.members_helper.gather_members_from_sql", return_value=["Valid", "", None, 123])
        mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=[])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", side_effect=lambda lang, members: members)

        # Mock settings to enable SQL
        mock_settings = mocker.patch("src.mk_cats.members_helper.settings")
        mock_settings.database.use_sql = True

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == ["Valid"]

    def test_removes_duplicates(self, mocker):
        """Test that collect_category_members removes duplicates."""
        mocker.patch("src.mk_cats.members_helper.gather_members_from_sql", return_value=["Article", "Article"])
        mocker.patch("src.mk_cats.members_helper.gather_members_from_api", return_value=[])
        mocker.patch("src.mk_cats.members_helper.remove_redirect_pages", side_effect=lambda lang, members: members)

        # Mock settings to enable SQL
        mock_settings = mocker.patch("src.mk_cats.members_helper.settings")
        mock_settings.database.use_sql = True

        from src.mk_cats.members_helper import collect_category_members

        result = collect_category_members("تصنيف:علوم", "Category:Science")

        assert result == ["Article"]
