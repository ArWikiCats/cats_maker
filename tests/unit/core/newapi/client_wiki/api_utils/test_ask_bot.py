"""
Unit tests for src/core/client_wiki/api_utils/ask_bot.py module.
"""

from unittest.mock import patch

from src.core.newapi.client_wiki.api_utils import ask_bot
from src.core.newapi.client_wiki.api_utils.ask_bot import AskBot


class TestASKBOT:
    def test_init(self):
        bot = AskBot()
        assert ask_bot._save_or_ask == {}
