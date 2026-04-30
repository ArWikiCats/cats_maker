"""
Unit tests for src/core/client_wiki/api_utils/botEdit.py module.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.api_utils.botEdit import (
    BOT_USERNAME,
    STOP_EDIT_TEMPLATES,
    Bot_Cache,
    _created_cache,
    bot_May_Edit,
    bot_May_Edit_do,
    check_create_time,
    check_last_edit_time,
    extract_templates_and_params,
)


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear module-level caches before each test."""
    Bot_Cache.clear()
    _created_cache.clear()
    yield
    Bot_Cache.clear()
    _created_cache.clear()


class TestExtractTemplatesAndParams:
    def test_simple_template(self):
        result = extract_templates_and_params("{{TemplateName}}")
        assert len(result) == 1
        assert result[0]["namestrip"] == "TemplateName"
        assert result[0]["name"] == "قالب:TemplateName"

    def test_template_with_params(self):
        result = extract_templates_and_params("{{TemplateName|key=value}}")
        assert len(result) == 1
        assert result[0]["params"]["key"] == "value"

    def test_no_templates(self):
        result = extract_templates_and_params("Just plain text")
        assert result == []

    def test_multiple_templates(self):
        result = extract_templates_and_params("{{A}} text {{B}}")
        assert len(result) == 2
        names = [t["namestrip"] for t in result]
        assert "A" in names
        assert "B" in names

    def test_nobots_template(self):
        result = extract_templates_and_params("{{nobots}}")
        assert len(result) == 1
        assert result[0]["namestrip"].lower() == "nobots"

    def test_bots_template_with_allow(self):
        result = extract_templates_and_params("{{bots|allow=all}}")
        assert len(result) == 1
        assert result[0]["params"]["allow"] == "all"


class TestBotMayEditDo:
    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_force_edit_returns_true(self, mock_settings):
        mock_settings.bot.force_edit = True
        assert bot_May_Edit_do(text="any", title_page="Page") is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_empty_text_returns_true(self, mock_settings):
        mock_settings.bot.force_edit = False
        assert bot_May_Edit_do(text="", title_page="Page") is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_stop_template(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{تحرر}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_nobots(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{nobots}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_nobots_allow_bot(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = f"{{{{nobots|{BOT_USERNAME}}}}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_bots_allow_all(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{bots|allow=all}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_bots_deny_all(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{bots|deny=all}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_bots_deny_bot(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = f"{{{{bots|deny={BOT_USERNAME}}}}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_cached_result_returned(self, mock_settings):
        mock_settings.bot.force_edit = False
        Bot_Cache["all"] = {"CachedPage": True}
        assert bot_May_Edit_do(text="anything", title_page="CachedPage") is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_empty_botjob_defaults_to_all(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{تحرر}}"
        assert bot_May_Edit_do(text=text, title_page="Page", botjob="") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_custom_botjob_with_matching_template(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{لا للتعريب}}"
        assert bot_May_Edit_do(text=text, title_page="Page", botjob="تعريب") is False

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_text_with_no_restrictions(self, mock_settings):
        mock_settings.bot.force_edit = False
        text = "{{SomeAllowedTemplate|param=value}}"
        assert bot_May_Edit_do(text=text, title_page="Page") is True


class TestCheckCreateTime:
    def test_non_arabic_lang_returns_true(self):
        page = MagicMock()
        page.namespace.return_value = 0
        page.lang = "en"
        assert check_create_time(page, "Page") is True

    def test_non_main_namespace_returns_true(self):
        page = MagicMock()
        page.namespace.return_value = 14
        page.lang = "ar"
        assert check_create_time(page, "Page") is True

    def test_recent_creation_returns_false(self):
        page = MagicMock()
        page.namespace.return_value = 0
        page.lang = "ar"
        now = datetime.datetime.now(datetime.timezone.utc)
        page.get_create_data.return_value = {
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user": "test",
        }
        assert check_create_time(page, "Page") is False

    def test_old_creation_returns_true(self):
        page = MagicMock()
        page.namespace.return_value = 0
        page.lang = "ar"
        old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
        page.get_create_data.return_value = {
            "timestamp": old.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user": "test",
        }
        assert check_create_time(page, "Page") is True

    def test_no_timestamp_returns_true(self):
        page = MagicMock()
        page.namespace.return_value = 0
        page.lang = "ar"
        page.get_create_data.return_value = {}
        assert check_create_time(page, "Page") is True

    def test_cached_result(self):
        _created_cache["CachedPage"] = True
        page = MagicMock()
        assert check_create_time(page, "CachedPage") is True


class TestCheckLastEditTime:
    def test_bot_editor_returns_true(self):
        page = MagicMock()
        page.get_userinfo.return_value = {"groups": ["bot", "user"]}
        assert check_last_edit_time(page, "Page", delay=30) is True

    def test_recent_edit_returns_false(self):
        page = MagicMock()
        page.get_userinfo.return_value = {"groups": ["user"]}
        now = datetime.datetime.now(datetime.timezone.utc)
        page.get_timestamp.return_value = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert check_last_edit_time(page, "Page", delay=30) is False

    def test_old_edit_returns_true(self):
        page = MagicMock()
        page.get_userinfo.return_value = {"groups": ["user"]}
        old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=60)
        page.get_timestamp.return_value = old.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert check_last_edit_time(page, "Page", delay=30) is True

    def test_no_timestamp_returns_true(self):
        page = MagicMock()
        page.get_userinfo.return_value = {"groups": ["user"]}
        page.get_timestamp.return_value = ""
        assert check_last_edit_time(page, "Page", delay=30) is True


class TestBotMayEdit:
    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_no_page_returns_check_result(self, mock_settings):
        mock_settings.bot.force_edit = True
        assert bot_May_Edit(text="text", title_page="Page") is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_with_page_non_wikipedia_returns_true(self, mock_settings):
        mock_settings.bot.force_edit = False
        page = MagicMock()
        page.namespace.return_value = 14
        page.lang = "ar"
        assert bot_May_Edit(text="text", title_page="Page", page=page) is True

    @patch("src.core.client_wiki.api_utils.botEdit.settings")
    def test_with_page_and_delay_skipped_for_non_ar(self, mock_settings):
        mock_settings.bot.force_edit = False
        page = MagicMock()
        page.namespace.return_value = 0
        page.lang = "en"
        assert bot_May_Edit(text="text", title_page="Page", page=page, delay=10) is True


class TestConstants:
    def test_stop_edit_templates_has_all_key(self):
        assert "all" in STOP_EDIT_TEMPLATES

    def test_bot_username(self):
        assert BOT_USERNAME == "Mr.Ibrahembot"
