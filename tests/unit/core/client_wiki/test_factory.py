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


class TestLoadLoginBot:
    @patch("src.core.client_wiki.factory.load_main_api")
    def test_returns_login_bot(self, mock_load):
        mock_api = MagicMock()
        mock_load.return_value = mock_api
        result = load_login_bot("ar", "wikipedia")
        mock_load.assert_called_once_with(lang="ar", family="wikipedia")
        assert result == mock_api.login_bot
