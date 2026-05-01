"""
Tests for check_redirects.py

This module tests Wikipedia API helper functions.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.wiki_api.check_redirects import NEW_API, load_non_redirects, remove_redirect_pages


class TestNewAPI:
    """Tests for NEW_API class"""

    def test_init_sets_login_bot(self):
        """Test that NEW_API init sets login_bot"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)
        assert api.login_bot == mock_login_bot

    def test_chunk_titles_list(self):
        """Test chunk_titles with a list"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        result = api.chunk_titles(["Page1", "Page2", "Page3", "Page4", "Page5"], chunk_size=2)
        assert result == [["Page1", "Page2"], ["Page3", "Page4"], ["Page5"]]

    def test_chunk_titles_dict_keys(self):
        """Test chunk_titles with a dict keys"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        result = api.chunk_titles({"Page1": 1, "Page2": 2, "Page3": 3}, chunk_size=2)
        assert result == [["Page1", "Page2"], ["Page3"]]

    def test_chunk_titles_keys_view(self):
        """Test chunk_titles with KeysView"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        d = {"Page1": 1, "Page2": 2, "Page3": 3}
        result = api.chunk_titles(d.keys(), chunk_size=2)
        assert result == [["Page1", "Page2"], ["Page3"]]

    def test_merge_all_jsons_deep_dicts(self):
        """Test merge_all_jsons_deep with dicts"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        all_jsons = {"a": {"b": 1}}
        json1 = {"a": {"c": 2}}
        result = api.merge_all_jsons_deep(all_jsons, json1)
        assert result == {"a": {"b": 1, "c": 2}}

    def test_merge_all_jsons_deep_lists(self):
        """Test merge_all_jsons_deep with lists"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        all_jsons = {"a": [1, 2]}
        json1 = {"a": [3, 4]}
        result = api.merge_all_jsons_deep(all_jsons, json1)
        assert result == {"a": [1, 2, 3, 4]}

    def test_merge_all_jsons_deep_non_dict(self):
        """Test merge_all_jsons_deep handles non-dict input"""
        mock_login_bot = MagicMock()
        api = NEW_API(mock_login_bot)

        result = api.merge_all_jsons_deep("not a dict", {"a": 1})
        assert result == {"a": 1}

    def test_find_pages_exists_or_not_normal_pages(self, mocker):
        """Test Find_pages_exists_or_not with normal pages"""
        mock_login_bot = MagicMock()
        mock_login_bot.client_request.return_value = {
            "query": {
                "pages": [
                    {"title": "Page1", "missing": None},
                    {"title": "Page2"},
                ]
            }
        }

        api = NEW_API(mock_login_bot)
        result = api.Find_pages_exists_or_not(["Page1", "Page2"])

        assert result["Page1"] is False
        assert result["Page2"] is True

    def test_find_pages_exists_or_not_with_redirects(self, mocker):
        """Test Find_pages_exists_or_not with redirects"""
        mock_login_bot = MagicMock()
        mock_login_bot.client_request.return_value = {
            "query": {
                "pages": [
                    {"title": "Page1", "redirect": None},
                    {"title": "Page2"},
                ]
            }
        }

        api = NEW_API(mock_login_bot)
        result = api.Find_pages_exists_or_not(["Page1", "Page2"], get_redirect=True)

        assert result["Page1"] == "redirect"
        assert result["Page2"] is True

    def test_find_pages_exists_or_not_with_normalization(self, mocker):
        """Test Find_pages_exists_or_not with normalized titles"""
        mock_login_bot = MagicMock()
        mock_login_bot.client_request.return_value = {
            "query": {
                "normalized": [{"from": "Page_One", "to": "Page One"}],
                "pages": [{"title": "Page One"}],
            }
        }

        api = NEW_API(mock_login_bot)
        result = api.Find_pages_exists_or_not(["Page_One"])

        assert result["Page_One"] is True

    def test_find_pages_exists_or_not_empty_response(self, mocker):
        """Test Find_pages_exists_or_not handles empty response"""
        mock_login_bot = MagicMock()
        mock_login_bot.client_request.return_value = {}

        api = NEW_API(mock_login_bot)
        result = api.Find_pages_exists_or_not(["Page1"])

        assert result == {}

    def test_find_pages_exists_or_not_skips_empty_titles(self, mocker):
        """Test Find_pages_exists_or_not skips pages with empty titles"""
        mock_login_bot = MagicMock()
        mock_login_bot.client_request.return_value = {
            "query": {
                "pages": [
                    {"title": ""},
                    {"title": "Page1"},
                ]
            }
        }

        api = NEW_API(mock_login_bot)
        result = api.Find_pages_exists_or_not(["Page1"])

        assert "Page1" in result
        assert "" not in result


class TestLoadNonRedirects:
    """Tests for load_non_redirects function"""

    def test_empty_page_titles(self):
        """Test that empty input returns empty dict"""
        result = load_non_redirects("en", [])
        assert result == {}


class TestRemoveRedirectPages:
    """Tests for remove_redirect_pages function"""

    def test_returns_non_redirect_pages(self, mocker):
        """Test that remove_redirect_pages returns only non-redirect pages"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Science": True,
                "Mathematics": True,
                "redirect": False,
            },
        )

        result = remove_redirect_pages("en", ["Science", "Mathematics", "Physics"])

        assert result == ["Science", "Mathematics"]

    def test_logs_zero_removals(self, mocker):
        """Test that remove_redirect_pages logs correctly when no redirects are removed"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": True,
                "Page2": True,
            },
        )
        result = remove_redirect_pages("en", ["Page1", "Page2"])
        assert result == ["Page1", "Page2"]

    def test_handles_empty_input(self, mocker):
        """Test that remove_redirect_pages handles empty input list"""
        result = remove_redirect_pages("en", [])

        assert result == []

    def test_handles_all_redirects(self, mocker):
        """Test that remove_redirect_pages handles case where all pages are redirects"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": False,
                "Page2": False,
                "Page3": False,
                "redirect": True,
            },
        )
        result = remove_redirect_pages("en", ["Page1", "Page2", "Page3"])

        assert result == ["redirect"]

    def test_preserves_order(self, mocker):
        """Test that remove_redirect_pages preserves the order of non-redirect pages"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": True,
                "Page2": False,
                "Page3": True,
                "Page4": True,
                "redirect": False,
            },
        )

        result = remove_redirect_pages("en", ["Page1", "Page2", "Page3", "Page4"])

        assert result == ["Page1", "Page3", "Page4"]

    def test_works_with_different_languages(self, mocker):
        """Test that remove_redirect_pages works with different language codes"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "صفحة": True,
            },
        )
        result = remove_redirect_pages("ar", ["صفحة"])

        assert result == ["صفحة"]
