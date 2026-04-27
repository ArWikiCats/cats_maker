"""
Tests for sub_cats_bot.py

This module tests subcategory query functions.
"""

import pytest

from src.core.wiki_api.sub_cats_bot import (
    API_n_CALLS,
    sub_cats_query,
)


class TestAPInCalls:
    """Tests for API_n_CALLS counter"""

    def test_is_dict(self):
        """Test that API_n_CALLS is a dictionary"""
        assert isinstance(API_n_CALLS, dict)

    def test_has_key_1(self):
        """Test that API_n_CALLS has key 1"""
        assert 1 in API_n_CALLS

    def test_value_is_integer(self):
        """Test that API_n_CALLS[1] is an integer"""
        assert isinstance(API_n_CALLS[1], int)


class TestSubCatsQuery:
    """Tests for sub_cats_query function"""

    def test_returns_false_for_empty_link(self):
        """Test that False is returned for empty link"""
        result = sub_cats_query("", "en")
        assert result is False

    def test_returns_false_for_none_link(self):
        """Test that False is returned for None link"""
        result = sub_cats_query(None, "en")
        assert result is False

    def test_returns_cached_value(self, mocker):
        """Test that cached values are returned"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value={"categorymembers": {"Page1": {}}})

        result = sub_cats_query("Category:Test", "en")
        assert "categorymembers" in result

    def test_calls_submit_api_for_uncached(self, mocker):
        """Test that submitAPI is called for uncached queries"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mock_submit = mocker.patch("src.core.wiki_api.sub_cats_bot.submitAPI", return_value={"query": {"pages": {}}})
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        sub_cats_query("Category:Science", "en")

        mock_submit.assert_called_once()

    def test_increments_api_call_counter(self, mocker):
        """Test that API call counter is incremented"""
        initial_count = API_n_CALLS[1]
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.wiki_api.sub_cats_bot.submitAPI", return_value={"query": {"pages": {}}})
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        sub_cats_query("Category:NewCategory", "en")

        assert API_n_CALLS[1] >= initial_count

    def test_handles_subcat_type(self, mocker):
        """Test handling of subcat type parameter"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mock_submit = mocker.patch("src.core.wiki_api.sub_cats_bot.submitAPI", return_value={"query": {"pages": {}}})
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        sub_cats_query("Category:Science", "en", ctype="subcat")

        call_args = mock_submit.call_args[0][0]
        assert call_args["gcmtype"] == "subcat"

    def test_handles_page_type(self, mocker):
        """Test handling of page type parameter"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mock_submit = mocker.patch("src.core.wiki_api.sub_cats_bot.submitAPI", return_value={"query": {"pages": {}}})
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        sub_cats_query("Category:Science", "en", ctype="page")

        call_args = mock_submit.call_args[0][0]
        assert call_args["gcmtype"] == "page"

    def test_extracts_langlinks(self, mocker):
        """Test extraction of language links from response"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mocker.patch(
            "src.core.wiki_api.sub_cats_bot.submitAPI",
            return_value={
                "query": {"pages": {"123": {"title": "Science", "ns": 14, "langlinks": [{"lang": "ar", "*": "علوم"}]}}}
            },
        )
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        result = sub_cats_query("Category:Science", "en")

        assert "categorymembers" in result

    def test_returns_table_structure(self, mocker):
        """Test that result has correct table structure"""
        mocker.patch("src.core.wiki_api.sub_cats_bot.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.wiki_api.sub_cats_bot.submitAPI", return_value={"query": {"pages": {}}})
        mocker.patch("src.core.wiki_api.sub_cats_bot.set_cache_L_C_N")

        result = sub_cats_query("Category:Test", "en")

        assert "categorymembers" in result
        assert isinstance(result["categorymembers"], dict)
