"""
Unit tests for src/core/client_wiki/categories/catdepth_new.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.categories.catdepth_new import args_group, subcatquery, title_process


class TestTitleProcess:
    def test_english_title_without_prefix(self):
        assert title_process("Science", "en") == "Category:Science"

    def test_english_title_with_prefix(self):
        assert title_process("Category:Science", "en") == "Category:Science"

    def test_arabic_title_without_prefix(self):
        assert title_process("علوم", "ar") == "تصنيف:علوم"

    def test_arabic_title_with_prefix(self):
        assert title_process("تصنيف:علوم", "ar") == "تصنيف:علوم"

    def test_unknown_sitecode_returns_unchanged(self):
        assert title_process("Science", "fr") == "Science"

    def test_www_prefix(self):
        assert title_process("Test", "www") == "Category:Test"


class TestArgsGroup:
    def test_basic_args(self):
        result = args_group("Title", {"depth": 2})
        assert result["title"] == "Title"
        assert result["depth"] == 2

    def test_kwargs_override_defaults(self):
        result = args_group("Title", {"depth": 3, "ns": "0"})
        assert result["depth"] == 3
        assert result["ns"] == "0"

    def test_unknown_keys_added(self):
        result = args_group("Title", {"custom_key": "value"})
        assert result["custom_key"] == "value"

    def test_default_none_values(self):
        result = args_group("Title", {})
        assert result["depth"] is None
        assert result["ns"] is None


class TestSubcatquery:
    @patch("src.core.client_wiki.categories.catdepth_new.CategoryDepth")
    @patch("src.core.client_wiki.categories.catdepth_new.title_process", return_value="Category:Test")
    def test_basic_call(self, mock_title, mock_cd_class):
        mock_bot = MagicMock()
        mock_bot.subcatquery_.return_value = {"Page1": {}}
        mock_bot.get_len_pages.return_value = 1
        mock_cd_class.return_value = mock_bot

        login_bot = MagicMock()
        result = subcatquery(login_bot, "Test", sitecode="en", print_s=False)

        mock_cd_class.assert_called_once()
        mock_bot.subcatquery_.assert_called_once()
        assert result == {"Page1": {}}

    @patch("src.core.client_wiki.categories.catdepth_new.CategoryDepth")
    @patch("src.core.client_wiki.categories.catdepth_new.title_process", return_value="Category:Test")
    def test_get_revids(self, mock_title, mock_cd_class):
        mock_bot = MagicMock()
        mock_bot.subcatquery_.return_value = {}
        mock_bot.get_revids.return_value = {"Page1": 123}
        mock_bot.get_len_pages.return_value = 0
        mock_cd_class.return_value = mock_bot

        login_bot = MagicMock()
        result = subcatquery(login_bot, "Test", sitecode="en", print_s=False, get_revids=True)

        assert result == {"Page1": 123}
