"""
Unit tests for src/core/client_wiki/pages/super_page.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.pages.super_page import (
    CategoriesData,
    Content,
    LinksData,
    MainPage,
    Meta,
    RevisionsData,
    TemplateData,
    find_edit_error,
)


@pytest.fixture
def mock_login_bot():
    return MagicMock()


@pytest.fixture
def page(mock_login_bot):
    with patch("src.core.client_wiki.pages.super_page.change_codes", {}):
        return MainPage(mock_login_bot, "TestPage", "ar", family="wikipedia")


class TestDataclasses:
    def test_content_defaults(self):
        c = Content()
        assert c.text_html == ""
        assert c.summary == ""
        assert c.words == 0
        assert c.length == 0

    def test_meta_defaults(self):
        m = Meta()
        assert m.is_Disambig is False
        assert m.can_be_edit is False
        assert m.Exists == ""
        assert m.wikibase_item == ""

    def test_revisions_data_defaults(self):
        r = RevisionsData()
        assert r.revid == ""
        assert r.pageid == ""
        assert r.timestamp == ""

    def test_links_data_defaults(self):
        l = LinksData()
        assert l.back_links == []
        assert l.extlinks == []
        assert l.iwlinks == []

    def test_categories_data_defaults(self):
        c = CategoriesData()
        assert c.categories == {}
        assert c.hidden_categories == {}

    def test_template_data_defaults(self):
        t = TemplateData()
        assert t.templates == {}
        assert t.templates_API == {}


class TestFindEditError:
    def test_returns_true_when_phrase_removed(self):
        old = "text #تحويل [[Page]] more"
        new = "text more"
        assert find_edit_error(old, new) is True

    def test_returns_false_when_phrase_preserved(self):
        old = "text #تحويل [[Page]] more"
        new = "text #تحويل [[Page]] more"
        assert find_edit_error(old, new) is False

    def test_returns_false_when_no_phrase(self):
        old = "normal text"
        new = "different text"
        assert find_edit_error(old, new) is False


class TestMainPageInit:
    def test_sets_attributes(self, mock_login_bot):
        with patch("src.core.client_wiki.pages.super_page.change_codes", {"nb": "no"}):
            page = MainPage(mock_login_bot, "MyPage", "nb", family="wikisource")
        assert page.title == "MyPage"
        assert page.lang == "no"
        assert page.family == "wikisource"
        assert page.login_bot == mock_login_bot

    def test_default_family(self, mock_login_bot):
        with patch("src.core.client_wiki.pages.super_page.change_codes", {}):
            page = MainPage(mock_login_bot, "Page", "ar")
        assert page.family == "wikipedia"

    def test_endpoint(self, page):
        assert page.endpoint == "https://ar.wikipedia.org/w/api.php"

    def test_ns_false_by_default(self, page):
        assert page.ns is False

    def test_empty_text_by_default(self, page):
        assert page.text == ""
        assert page.newtext == ""


class TestIsDisambiguation:
    def test_arabic_disambig(self, page):
        page.title = "صفحة (توضيح)"
        assert page.isDisambiguation() is True

    def test_english_disambig(self, page):
        page.title = "Page (disambiguation)"
        assert page.isDisambiguation() is True

    def test_not_disambig(self, page):
        page.title = "Normal Page"
        assert page.isDisambiguation() is False


class TestFalseEdit:
    def test_returns_false_for_non_main_ns(self, page):
        page.ns = 14
        assert page.false_edit() is False

    def test_returns_false_for_ns_false(self, page):
        page.ns = False
        assert page.false_edit() is False

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_returns_false_when_no_fa_enabled(self, mock_settings, page):
        page.ns = 0
        mock_settings.bot.no_fa = True
        assert page.false_edit() is False

    @patch("src.core.client_wiki.pages.super_page.logger")
    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_detects_90_percent_removal(self, mock_settings, mock_logger, page):
        page.ns = 0
        mock_settings.bot.no_fa = False
        page.text = "a" * 1000
        page.newtext = "a" * 50
        assert page.false_edit() is True

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_normal_edit_returns_false(self, mock_settings, page):
        page.ns = 0
        mock_settings.bot.no_fa = False
        page.text = "old content here"
        page.newtext = "new content here"
        assert page.false_edit() is False


class TestExists:
    def test_returns_true_when_exists(self, page):
        page.meta.Exists = True
        assert page.exists() is True

    @patch.object(MainPage, "get_text", return_value="")
    def test_fetches_text_when_not_loaded(self, mock_get_text, page):
        page.meta.Exists = False
        page.exists()
        mock_get_text.assert_called_once()


class TestNamespace:
    def test_returns_ns_when_set(self, page):
        page.ns = 14
        assert page.namespace() == 14

    @patch.object(MainPage, "get_text", return_value="")
    def test_fetches_text_when_ns_false(self, mock_get_text, page):
        page.ns = False
        page.namespace()
        mock_get_text.assert_called_once()


class TestGetTimestamp:
    def test_returns_cached_timestamp(self, page):
        page.revisions_data.timestamp = "2024-01-01T00:00:00Z"
        assert page.get_timestamp() == "2024-01-01T00:00:00Z"

    @patch.object(MainPage, "get_text", return_value="")
    def test_fetches_when_empty(self, mock_get_text, page):
        page.revisions_data.timestamp = ""
        page.get_timestamp()
        mock_get_text.assert_called_once()


class TestGetQid:
    def test_returns_cached_qid(self, page):
        page.meta.wikibase_item = "Q123"
        assert page.get_qid() == "Q123"

    @patch.object(MainPage, "get_text", return_value="")
    def test_fetches_when_empty(self, mock_get_text, page):
        page.meta.wikibase_item = ""
        page.get_qid()
        mock_get_text.assert_called_once()


class TestCanEdit:
    def test_non_wikipedia_returns_true(self, page):
        page.family = "wikisource"
        assert page.can_edit() is True

    @patch("src.core.client_wiki.pages.super_page.bot_May_Edit", return_value=True)
    @patch.object(MainPage, "get_text", return_value="text")
    def test_wikipedia_delegates_to_bot_may_edit(self, mock_get_text, mock_bot_edit, page):
        page.family = "wikipedia"
        result = page.can_edit(script="cat", delay=5)
        mock_bot_edit.assert_called_once()
        assert result is True


class TestGetText:
    def test_fetches_and_sets_attributes(self, page):
        page.login_bot.client_request.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "ns": 0,
                        "pageid": 123,
                        "pageprops": {"wikibase_item": "Q456"},
                        "revisions": [
                            {
                                "slots": {"main": {"*": "Page content"}},
                                "user": "TestUser",
                                "revid": 789,
                                "timestamp": "2024-01-01T00:00:00Z",
                                "parentid": 100,
                            }
                        ],
                    }
                }
            }
        }
        result = page.get_text()
        assert result == "Page content"
        assert page.ns == 0
        assert page.meta.Exists is True
        assert page.meta.wikibase_item == "Q456"
        assert page.user == "TestUser"

    def test_missing_page(self, page):
        page.login_bot.client_request.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "ns": 0,
                        "missing": "",
                    }
                }
            }
        }
        page.get_text()
        assert page.meta.Exists is False


class TestGetRedirectTarget:
    def test_returns_target(self, page):
        page.login_bot.client_request.return_value = {
            "query": {"redirects": [{"from": "Yemen", "to": "اليمن"}]}
        }
        assert page.get_redirect_target() == "اليمن"

    def test_no_redirect(self, page):
        page.login_bot.client_request.return_value = {"query": {"pages": {}}}
        assert page.get_redirect_target() == ""


class TestGetUserinfo:
    def test_fetches_userinfo(self, page):
        page.user = "TestUser"
        page.meta.userinfo = {}
        page.login_bot.client_request.return_value = {
            "query": {"users": [{"id": 1, "name": "TestUser", "groups": ["user"]}]}
        }
        result = page.get_userinfo()
        assert result["name"] == "TestUser"

    def test_cached_userinfo(self, page):
        page.meta.userinfo = {"id": 1, "name": "Cached"}
        result = page.get_userinfo()
        assert result["name"] == "Cached"
        page.login_bot.client_request.assert_not_called()


class TestSave:
    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_save_success(self, mock_settings, page):
        mock_settings.bot.ask = False
        mock_settings.bot.no_fa = False
        page.ns = 14
        page.login_bot.client_request.return_value = {
            "edit": {
                "result": "Success",
                "pageid": 123,
                "newrevid": 456,
                "newtimestamp": "2024-01-01T00:00:00Z",
            }
        }
        result = page.save(newtext="new text", summary="test edit")
        assert result is True
        assert page.text == "new text"

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_save_failure(self, mock_settings, page):
        mock_settings.bot.ask = False
        mock_settings.bot.no_fa = False
        page.ns = 14
        page.login_bot.client_request.return_value = {
            "error": {"code": "protectedpage", "info": "Protected"}
        }
        result = page.save(newtext="new text")
        assert result is False

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_save_empty_response(self, mock_settings, page):
        mock_settings.bot.ask = False
        mock_settings.bot.no_fa = False
        page.ns = 14
        page.login_bot.client_request.return_value = None
        result = page.save(newtext="new text")
        assert result is False


class TestCreate:
    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_create_success(self, mock_settings, page):
        mock_settings.bot.ask = False
        page.login_bot.client_request.return_value = {
            "edit": {
                "result": "Success",
                "pageid": 999,
                "newrevid": 1000,
                "newtimestamp": "2024-01-01T00:00:00Z",
            }
        }
        result = page.Create(text="content", summary="create")
        assert result is True

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_create_failure(self, mock_settings, page):
        mock_settings.bot.ask = False
        page.login_bot.client_request.return_value = {
            "error": {"code": "articleexists", "info": "Already exists"}
        }
        result = page.Create(text="content")
        assert result == "articleexists"

    @patch("src.core.client_wiki.pages.super_page.settings")
    def test_create_empty_response(self, mock_settings, page):
        mock_settings.bot.ask = False
        page.login_bot.client_request.return_value = None
        result = page.Create(text="content")
        assert result is False


class TestPostContinue:
    def test_single_page(self, page):
        params = {"action": "query", "prop": "links"}
        page.login_bot.client_request.return_value = {
            "query": {"links": [{"title": "Link1"}]}
        }
        result = page.post_continue(params, "query")
        assert len(result) == 1

    def test_with_continuation(self, page):
        params = {"action": "query", "prop": "links"}
        page.login_bot.client_request.side_effect = [
            {"continue": {"continue": "x"}, "query": {"links": [{"title": "L1"}]}},
            {"query": {"links": [{"title": "L2"}]}},
        ]
        result = page.post_continue(params, "query")
        assert len(result) == 2

    def test_empty_response_breaks(self, page):
        params = {"action": "query"}
        page.login_bot.client_request.return_value = None
        result = page.post_continue(params, "query")
        assert result == []


class TestGetInfos:
    def test_sets_metadata(self, page):
        page.login_bot.client_request.return_value = {
            "query": {
                "pages": [
                    {
                        "ns": 0,
                        "pageid": 123,
                        "length": 500,
                        "lastrevid": 456,
                        "touched": "2024-01-01T00:00:00Z",
                        "categories": [
                            {"ns": 14, "title": "تصنيف:A", "sortkey": "a", "hidden": False},
                            {"ns": 14, "title": "تصنيف:B", "sortkey": "b", "hidden": True},
                        ],
                        "langlinks": [{"lang": "en", "title": "Test"}],
                        "templates": [{"ns": 10, "title": "قالب:T"}],
                        "linkshere": [{"pageid": 999, "ns": 0, "title": "Other"}],
                        "iwlinks": [{"prefix": "d", "title": "Q123"}],
                    }
                ]
            }
        }
        page.get_infos()
        assert page.ns == 0
        assert page.revisions_data.pageid == 123
        assert page.content.length == 500
        assert page.meta.info["done"] is True
        assert "تصنيف:A" in page.categories_data.categories
        assert "تصنيف:B" in page.categories_data.hidden_categories
        assert page.langlinks == {"en": "Test"}
        assert page.template_data.templates_API == ["قالب:T"]


class TestGetExtlinks:
    def test_returns_sorted_links(self, page):
        page.login_bot.client_request.return_value = {
            "query": {
                "pages": [
                    {
                        "extlinks": [
                            {"url": "https://b.com"},
                            {"url": "https://a.com"},
                        ]
                    }
                ]
            }
        }
        result = page.get_extlinks()
        assert result == ["https://a.com", "https://b.com"]


class TestIsRedirect:
    def test_true_when_redirect(self, page):
        page.meta.is_redirect = True
        assert page.isRedirect() is True


class TestGetCategories:
    def test_returns_categories(self, page):
        page.meta.info["done"] = True
        page.categories_data.categories = {"تصنيف:A": {}}
        result = page.get_categories()
        assert "تصنيف:A" in result

    def test_with_hidden(self, page):
        page.meta.info["done"] = True
        page.categories_data.all_categories_with_hidden = {"تصنيف:A": {}, "تصنيف:B": {}}
        result = page.get_categories(with_hidden=True)
        assert len(result) == 2


class TestGetLanglinks:
    def test_returns_langlinks(self, page):
        page.meta.info["done"] = True
        page.langlinks = {"en": "Test"}
        assert page.get_langlinks() == {"en": "Test"}


class TestGetCreateData:
    def test_returns_cached_data(self, page):
        page.meta.create_data = {"timestamp": "2024-01-01T00:00:00Z", "user": "test"}
        result = page.get_create_data()
        assert result["timestamp"] == "2024-01-01T00:00:00Z"
