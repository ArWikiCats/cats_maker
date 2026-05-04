"""
Unit tests for src/core/client_wiki/api_utils/ask_bot.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.api_utils import ask_bot
from src.core.client_wiki.api_utils.ask_bot import AskBot, showDiff


class TestShowDiff:
    @patch("src.core.client_wiki.api_utils.ask_bot.pywikibot.showDiff")
    def test_show_diff_calls_pywikibot(self, mock_show_diff):
        showDiff("old line", "new line")
        mock_show_diff.assert_called_once_with("old line", "new line")

    @patch("src.core.client_wiki.api_utils.ask_bot.pywikibot.showDiff")
    def test_show_diff_no_changes(self, mock_show_diff):
        showDiff("same text", "same text")
        mock_show_diff.assert_called_once_with("same text", "same text")

    @patch("src.core.client_wiki.api_utils.ask_bot.pywikibot.showDiff")
    def test_show_diff_multiline(self, mock_show_diff):
        old = "line1\nline2\nline3"
        new = "line1\nmodified\nline3"
        showDiff(old, new)
        mock_show_diff.assert_called_once_with(old, new)

    @patch("src.core.client_wiki.api_utils.ask_bot.pywikibot.showDiff")
    def test_show_diff_plus_lines(self, mock_show_diff):
        """Verify showDiff delegates to pywikibot.showDiff with correct arguments."""
        old = "aaa"
        new = "bbb"
        showDiff(old, new)
        mock_show_diff.assert_called_once_with("aaa", "bbb")

    @patch("src.core.client_wiki.api_utils.ask_bot.sys")
    @patch("src.core.client_wiki.api_utils.ask_bot.pywikibot.showDiff")
    def test_show_diff_nodiff_in_argv_skips(self, mock_show_diff, mock_sys):
        """When 'nodiff' is in sys.argv, showDiff should not call pywikibot."""
        mock_sys.argv = ["script.py", "nodiff"]
        showDiff("aaa", "bbb")
        mock_show_diff.assert_not_called()


class TestASKBOT:
    def test_init(self):
        bot = AskBot()
        assert ask_bot._save_or_ask == {}

    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_returns_true_when_ask_false(self, mock_settings):
        mock_settings.bot.ask = False
        mock_settings.bot.no_diff = False
        bot = AskBot()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_returns_true_when_job_saved(self, mock_settings):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        bot = AskBot()
        ask_bot._save_or_ask["myjob"] = True
        assert bot.ask_put(job="myjob") is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_yes(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="n")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_no(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put() is False

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="a")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_all_saves_job(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put(job="testjob") is True
        assert ask_bot._save_or_ask["testjob"] is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_empty_input_accepts(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="Y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_uppercase_y(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="A")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_uppercase_a(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put(job="j") is True
        # "A" is accepted but only lowercase "a" sets _save_or_ask
        assert "j" not in ask_bot._save_or_ask

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="all")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_all_string(self, mock_settings, mock_input):
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put(job="j") is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="aaa")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    def test_ask_put_aaa_accepts(self, mock_settings, mock_input):
        """'aaa' is in the accepted list so should return True."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        assert bot.ask_put() is True

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.showDiff")
    def test_ask_put_with_text_and_newtext_calls_showdiff(self, mock_showdiff, mock_settings, mock_input):
        """When ask=True, no_diff=False, nodiff=False and text/newtext provided, showDiff is called."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(text="old text", newtext="new text")
        assert result is True
        mock_showdiff.assert_called_once_with("old text", "new text")

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.showDiff")
    def test_ask_put_nodiff_flag_skips_showdiff(self, mock_showdiff, mock_settings, mock_input):
        """When nodiff=True, showDiff should not be called even with text/newtext."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(nodiff=True, text="old", newtext="new")
        assert result is True
        mock_showdiff.assert_not_called()

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.showDiff")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_large_text_show_diff_true(self, mock_logger, mock_showdiff, mock_settings, mock_input):
        """When text > 70000 chars but show_diff=True, showDiff is still called."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        mock_settings.bot.show_diff = True
        bot = AskBot()
        large_text = "x" * 70001
        result = bot.ask_put(text=large_text, newtext="small")
        assert result is True
        mock_showdiff.assert_called_once_with(large_text, "small")

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.showDiff")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_large_text_show_diff_false(self, mock_logger, mock_showdiff, mock_settings, mock_input):
        """When text > 70000 chars and show_diff=False, showDiff is NOT called and error is logged."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        mock_settings.bot.show_diff = False
        bot = AskBot()
        large_text = "x" * 70001
        result = bot.ask_put(text=large_text, newtext="small")
        assert result is True
        mock_showdiff.assert_not_called()
        mock_logger.warning.assert_any_call("showDiff error..")

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_logs_summary(self, mock_logger, mock_settings, mock_input):
        """When summary is provided, it should be logged."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(summary="Fixed typo")
        assert result is True
        mock_logger.warning.assert_any_call("-Edit summary: Fixed typo")

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_logs_username(self, mock_logger, mock_settings, mock_input):
        """When username is provided, it should appear in the AskBot prompt."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(username="TestUser")
        assert result is True
        logged_messages = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("TestUser" in m for m in logged_messages)

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_no_summary_skips_summary_log(self, mock_logger, mock_settings, mock_input):
        """When summary is empty, the summary log line should not appear."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(summary="")
        assert result is True
        logged_messages = [str(c) for c in mock_logger.warning.call_args_list]
        assert not any("Edit summary" in m for m in logged_messages)

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_default_message(self, mock_logger, mock_settings, mock_input):
        """When message is empty, default message is used."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put()
        assert result is True
        logged_messages = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Do you want to accept these changes?" in m for m in logged_messages)

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_custom_message(self, mock_logger, mock_settings, mock_input):
        """When a custom message is provided, it is used instead of default."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = True
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(message="Save this?")
        assert result is True
        logged_messages = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Save this?" in m for m in logged_messages)

    @patch("src.core.client_wiki.api_utils.ask_bot.input", return_value="y")
    @patch("src.core.client_wiki.api_utils.ask_bot.settings")
    @patch("src.core.client_wiki.api_utils.ask_bot.logger")
    def test_ask_put_logs_difference_in_bytes(self, mock_logger, mock_settings, mock_input):
        """When text and newtext are provided, difference in bytes is logged."""
        mock_settings.bot.ask = True
        mock_settings.bot.no_diff = False
        mock_settings.bot.show_diff = False
        bot = AskBot()
        result = bot.ask_put(text="abc", newtext="abcde")
        assert result is True
        logged_messages = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("diference in bytes" in m and "2" in m for m in logged_messages)
