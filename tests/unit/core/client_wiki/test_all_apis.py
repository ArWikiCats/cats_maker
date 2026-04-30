"""
Unit tests for src/core/client_wiki/all_apis.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.all_apis import ALL_APIS


@pytest.fixture
def mock_login_bot():
    return MagicMock()


class TestALLAPIS:
    @patch("src.core.client_wiki.all_apis._login")
    def test_init_sets_attributes(self, mock_login, mock_login_bot):
        mock_login.return_value = mock_login_bot
        api = ALL_APIS("ar", "wikipedia", "user", "pass")
        assert api.lang == "ar"
        assert api.family == "wikipedia"
        assert api.username == "user"
        assert api.password == "pass"
        assert api.login_bot == mock_login_bot

    @patch("src.core.client_wiki.all_apis._login")
    def test_login_called_with_correct_args(self, mock_login, mock_login_bot):
        mock_login.return_value = mock_login_bot
        ALL_APIS("en", "wikisource", "bot", "pw")
        mock_login.assert_called_once_with("en", "wikisource", "bot")

    @patch("src.core.client_wiki.all_apis.super_page")
    @patch("src.core.client_wiki.all_apis._login")
    def test_main_page_returns_main_page(self, mock_login, mock_super_page, mock_login_bot):
        mock_login.return_value = mock_login_bot
        api = ALL_APIS("ar", "wikipedia", "user", "pass")
        result = api.MainPage("TestTitle")
        mock_super_page.MainPage.assert_called_once_with(mock_login_bot, "TestTitle", "ar", family="wikipedia")
        assert result == mock_super_page.MainPage.return_value

    @patch("src.core.client_wiki.all_apis.catdepth_new")
    @patch("src.core.client_wiki.all_apis._login")
    def test_cat_depth_calls_subcatquery(self, mock_login, mock_catdepth, mock_login_bot):
        mock_login.return_value = mock_login_bot
        api = ALL_APIS("ar", "wikipedia", "user", "pass")
        result = api.CatDepth("Category:Test", depth=2)
        mock_catdepth.subcatquery.assert_called_once_with(
            mock_login_bot, "Category:Test", sitecode="ar", family="wikipedia", depth=2
        )
        assert result == mock_catdepth.subcatquery.return_value

    @patch("src.core.client_wiki.all_apis._login")
    def test_login_adds_users(self, mock_login, mock_login_bot):
        mock_login.return_value = mock_login_bot
        ALL_APIS("ar", "wikipedia", "bot", "pw")
        mock_login_bot.add_users.assert_called_once_with(
            {"wikipedia": {"username": "bot", "password": "pw"}},
            lang="ar",
        )
