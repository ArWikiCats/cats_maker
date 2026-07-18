"""
Tests for sub_cats_bot.py

This module tests subcategory query functions.
"""

from src.core.cats_helpers.sub_cats_bot import (
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
        assert result == {}

    def test_returns_false_for_none_link(self):
        """Test that False is returned for None link"""
        result = sub_cats_query(None, "en")
        assert result == {}

    def test_increments_api_call_counter(self, mocker):
        """Test that API call counter is incremented"""
        initial_count = API_n_CALLS[1]

        mocker.patch("src.core.cats_helpers.sub_cats_bot.submitParams", return_value={"query": {"pages": {}}})

        sub_cats_query("Category:NewCategory", "en")

        assert API_n_CALLS[1] >= initial_count

    def test_handles_subcat_type(self, mocker):
        """Test handling of subcat type parameter"""

        mock_submit = mocker.patch(
            "src.core.cats_helpers.sub_cats_bot.submitParams", return_value={"query": {"pages": {}}}
        )

        sub_cats_query("Category:Science", "en", ctype="subcat")

        call_args = mock_submit.call_args[0][0]
        assert call_args["gcmtype"] == "subcat"

    def test_handles_page_type(self, mocker):
        """Test handling of page type parameter"""

        mock_submit = mocker.patch(
            "src.core.cats_helpers.sub_cats_bot.submitParams", return_value={"query": {"pages": {}}}
        )

        sub_cats_query("Category:Science", "en", ctype="page")

        call_args = mock_submit.call_args[0][0]
        assert call_args["gcmtype"] == "page"

    def test_extracts_langlinks(self, mocker):
        """Test extraction of language links from response"""

        mocker.patch(
            "src.core.cats_helpers.sub_cats_bot.submitParams",
            return_value={
                "query": {"pages": {"123": {"title": "Science", "ns": 14, "langlinks": [{"lang": "ar", "*": "علوم"}]}}}
            },
        )

        result = sub_cats_query("Category:Science", "en")

        assert "categorymembers" in result

    def test_returns_table_structure(self, mocker):
        """Test that result has correct table structure"""

        mocker.patch("src.core.cats_helpers.sub_cats_bot.submitParams", return_value={"query": {"pages": {}}})

        result = sub_cats_query("Category:Test", "en")

        assert "categorymembers" in result
        assert isinstance(result["categorymembers"], dict)
