"""
Unit tests for src/core/client_wiki/api_utils/ask_bot.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.api_utils.ask_bot import ASK_BOT, showDiff


class TestShowDiff:
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_show_diff_logs_lines(self, mock_logger):
        showDiff("old line", "new line")
        assert mock_logger.warning.called

    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_show_diff_no_changes(self, mock_logger):
        showDiff("same text", "same text")
        # No diff lines for identical text
        mock_logger.warning.assert_not_called()

    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_show_diff_multiline(self, mock_logger):
        old = "line1\nline2\nline3"
        new = "line1\nmodified\nline3"
        showDiff(old, new)
        assert mock_logger.warning.called


class TestASKBOT:
    def test_init(self):
        bot = ASK_BOT()
        assert bot._save_or_ask == {}

    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_returns_true_when_ask_false(self, mock_settings):
        mock_settings.bot.ask = False
        mock_settings.bot.no_diff = False
        bot = ASK_BOT()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_returns_true_when_job_saved(self, mock_settings):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        bot = ASK_BOT()
        bot._save_or_ask["myjob"] = True
        assert bot.ask_put(job="myjob") is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_yes(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="n")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_no(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put() is False

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="a")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_all_saves_job(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put(job="testjob") is True
        assert bot._save_or_ask["testjob"] is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_empty_input_accepts(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="Y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_uppercase_y(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="A")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_uppercase_a(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put(job="j") is True
        # "A" is accepted but only lowercase "a" sets _save_or_ask
        assert "j" not in bot._save_or_ask

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="all")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_all_string(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = ASK_BOT()
        assert bot.ask_put(job="j") is True
