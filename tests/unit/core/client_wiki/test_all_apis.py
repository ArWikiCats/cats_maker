"""
Unit tests for src/core/client_wiki/all_apis.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.all_apis import AllAPIS


@pytest.fixture
def mock_login_bot():
    return MagicMock()


class TestALLAPIS:
    @patch("src.core.client_wiki.all_apis.WikiLoginClient")
    def test_init_sets_attributes(self, mock_wlc, mock_login_bot):
        mock_wlc.return_value = mock_login_bot
        api = AllAPIS("ar", "wikipedia", "user", "pass")
        assert api.lang == "ar"
        assert api.family == "wikipedia"
        assert api.username == "user"
        assert api.password == "pass"
        assert api.login_bot == mock_login_bot

    @patch("src.core.client_wiki.all_apis.WikiLoginClient")
    def test_login2_called_with_correct_args(self, mock_wlc, mock_login_bot):
        mock_wlc.return_value = mock_login_bot
        AllAPIS("en", "wikisource", "bot", "pw")
        mock_wlc.assert_called_once_with(lang="en", family="wikisource", username="bot", password="pw")

    @patch("src.core.client_wiki.all_apis.super_page")
    @patch("src.core.client_wiki.all_apis.WikiLoginClient")
    def test_main_page_returns_main_page(self, mock_wlc, mock_super_page, mock_login_bot):
        mock_wlc.return_value = mock_login_bot
        api = AllAPIS("ar", "wikipedia", "user", "pass")
        result = api.MainPage("TestTitle")
        mock_super_page.MainPage.assert_called_once_with(mock_login_bot, "TestTitle", "ar", family="wikipedia")
        assert result == mock_super_page.MainPage.return_value

    @patch("src.core.client_wiki.all_apis.catdepth_new")
    @patch("src.core.client_wiki.all_apis.WikiLoginClient")
    def test_cat_depth_calls_subcatquery(self, mock_wlc, mock_catdepth, mock_login_bot):
        mock_wlc.return_value = mock_login_bot
        api = AllAPIS("ar", "wikipedia", "user", "pass")
        result = api.CatDepth("Category:Test", depth=2)
        mock_catdepth.subcatquery.assert_called_once_with(
            mock_login_bot, "Category:Test", sitecode="ar", family="wikipedia", depth=2
        )
        assert result == mock_catdepth.subcatquery.return_value
