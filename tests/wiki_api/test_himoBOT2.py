"""
Tests for himoBOT2.py

This module tests Wikipedia API helper functions.
"""

import pytest

from src.core.wiki_api.himoBOT2 import (
    get_page_info_from_wikipedia,
)


class TestGetPageInfoFromWikipediaNew:
    """Tests for get_page_info_from_wikipedia function"""

    def test_returns_dict_for_valid_page(self, mocker):
        """Test that function returns dict for valid page"""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test Page",
                        "langlinks": [{"lang": "en", "*": "Test Page"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test Page")
        assert isinstance(result, dict)

    def test_returns_empty_dict_on_no_response(self, mocker):
        """Test that function returns empty dict when API fails"""
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=None)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Nonexistent")
        assert result == {}

    def test_handles_missing_page(self, mocker):
        """Test that function handles missing pages correctly"""
        mock_response = {
            "query": {
                "pages": {
                    "-1": {
                        "ns": 0,
                        "title": "Missing Page",
                        "missing": "",
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Missing Page")
        assert isinstance(result, dict)
        if result:
            assert result.get("exists") is False

    def test_strips_wiki_suffix_from_sitecode(self, mocker):
        """Test that function strips 'wiki' suffix from sitecode"""
        mock_response = {"query": {"pages": {"123": {"pageid": 123, "ns": 0, "title": "Test"}}}}
        mock_submit = mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        get_page_info_from_wikipedia("arwiki", "Test")
        # The function should call submitAPI with 'ar' not 'arwiki'
        call_args = mock_submit.call_args
        assert call_args[0][1] == "ar"  # sitecode should be 'ar'
