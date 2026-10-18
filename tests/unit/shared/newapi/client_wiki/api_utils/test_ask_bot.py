"""
Unit tests for src/app/core/client_wiki/api_utils/ask_bot.py module.
"""

from src.app.shared.newapi.client_wiki.api_utils import ask_bot
from src.app.shared.newapi.client_wiki.api_utils.ask_bot import AskBot


class TestASKBOT:
    def test_init(self):
        AskBot()
        assert ask_bot._save_or_ask == {}
