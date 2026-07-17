"""
Unit tests for src/core/client_wiki/pages/super_page.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.newapi.client_wiki.pages.super_page import (
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
    from src.core.newapi.api_client.client import WikiLoginClient

    mock = MagicMock(spec=WikiLoginClient)
    mock.client_request = MagicMock()
    return mock


@pytest.fixture
def page(mock_login_bot):
    with patch("src.core.newapi.client_wiki.pages.super_page.change_codes", {}):
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
        assert m.is_disambig is False
        assert m.can_be_edit is False
        assert m.Exists is False
        assert m.wikibase_item == ""

    def test_revisions_data_defaults(self):
        r = RevisionsData()
        assert r.revid == ""
        assert r.pageid == ""
        assert r.timestamp == ""

    def test_links_data_defaults(self):
        te = LinksData()
        assert te.back_links == []
        assert te.extlinks == []
        assert te.iwlinks == []

    def test_categories_data_defaults(self):
        c = CategoriesData()
        assert c.categories == {}
        assert c.hidden_categories == {}

    def test_template_data_defaults(self):
        t = TemplateData()
        assert t.templates == []
        assert t.templates_api == []
