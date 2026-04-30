"""
Unit tests for src/core/client_wiki/factory.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.factory import load_login_bot, load_main_api


@pytest.fixture(autouse=True)
def clear_lru_caches():
    """Clear LRU caches before each test."""
    load_main_api.cache_clear()
    load_login_bot.cache_clear()
    yield
    load_main_api.cache_clear()
    load_login_bot.cache_clear()


class TestLoadMainApi:
    @patch("src.core.client_wiki.factory.ALL_APIS")
    def test_creates_all_apis_instance(self, mock_all_apis):
        mock_instance = MagicMock()
        mock_all_apis.return_value = mock_instance
        with patch("src.core.client_wiki.factory.username", "testuser"), patch(
            "src.core.client_wiki.factory.password", "testpass"
        ):
            result = load_main_api("ar", "wikipedia")
        mock_all_apis.assert_called_once_with(lang="ar", family="wikipedia", username="testuser", password="testpass")
        assert result == mock_instance

    @patch("src.core.client_wiki.factory.ALL_APIS")
    def test_default_params(self, mock_all_apis):
        mock_all_apis.return_value = MagicMock()
        with patch("src.core.client_wiki.factory.username", "u"), patch(
            "src.core.client_wiki.factory.password", "p"
        ):
            load_main_api()
        mock_all_apis.assert_called_once_with(lang="ar", family="wikipedia", username="u", password="p")

    @patch("src.core.client_wiki.factory.ALL_APIS")
    def test_caches_result(self, mock_all_apis):
        mock_all_apis.return_value = MagicMock()
        with patch("src.core.client_wiki.factory.username", "u"), patch(
            "src.core.client_wiki.factory.password", "p"
        ):
            r1 = load_main_api("en", "wikipedia")
            r2 = load_main_api("en", "wikipedia")
        assert r1 is r2
        mock_all_apis.assert_called_once()


class TestLoadLoginBot:
    @patch("src.core.client_wiki.factory.load_main_api")
    def test_returns_login_bot(self, mock_load):
        mock_api = MagicMock()
        mock_load.return_value = mock_api
        result = load_login_bot("ar", "wikipedia")
        mock_load.assert_called_once_with(lang="ar", family="wikipedia")
        assert result == mock_api.login_bot
