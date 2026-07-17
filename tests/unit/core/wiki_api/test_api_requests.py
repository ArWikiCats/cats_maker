"""
Unit tests for src/core/wiki_api/api_requests.py module.
"""

from unittest.mock import MagicMock, patch

from src.core.wiki_api.api_requests import _load_session, submitAPI


class TestLoadSession:
    def test_returns_session(self):
        session = _load_session()
        assert session is not None

    def test_is_cached(self):
        s1 = _load_session()
        s2 = _load_session()
        assert s1 is s2


class TestSubmitAPI:
    @patch("src.core.wiki_api.api_requests._load_session")
    @patch("src.core.wiki_api.api_requests.settings")
    def test_basic_query(self, mock_settings, mock_load_session):
        mock_settings.wikipedia.user_agent = "test"
        mock_settings.wikipedia.default_timeout = 30
        mock_session = MagicMock()
        mock_load_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = {"query": {}}
        mock_session.post.return_value = mock_response

        result = submitAPI({"action": "query"}, "en", "wikipedia")
        assert "query" in result

    @patch("src.core.wiki_api.api_requests._load_session")
    @patch("src.core.wiki_api.api_requests.settings")
    def test_strips_wiki_suffix(self, mock_settings, mock_load_session):
        mock_settings.wikipedia.user_agent = "test"
        mock_settings.wikipedia.default_timeout = 30
        mock_session = MagicMock()
        mock_load_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        submitAPI({"action": "query"}, "enwiki", "wikipedia")
        call_args = mock_session.post.call_args
        assert "en.wikipedia.org" in call_args[0][0]

    @patch("src.core.wiki_api.api_requests._load_session")
    @patch("src.core.wiki_api.api_requests.settings")
    def test_joins_titles_list(self, mock_settings, mock_load_session):
        mock_settings.wikipedia.user_agent = "test"
        mock_settings.wikipedia.default_timeout = 30
        mock_session = MagicMock()
        mock_load_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        submitAPI({"action": "query", "titles": ["A", "B"]}, "en", "wikipedia")
        call_data = mock_session.post.call_args[1]["data"]
        assert call_data["titles"] == "A|B"

    @patch("src.core.wiki_api.api_requests._load_session")
    @patch("src.core.wiki_api.api_requests.settings")
    def test_commons_maps_to_wikimedia(self, mock_settings, mock_load_session):
        mock_settings.wikipedia.user_agent = "test"
        mock_settings.wikipedia.default_timeout = 30
        mock_session = MagicMock()
        mock_load_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        submitAPI({"action": "query"}, "en", "commons")
        call_args = mock_session.post.call_args
        assert "wikimedia.org" in call_args[0][0]

    @patch("src.core.wiki_api.api_requests._load_session")
    @patch("src.core.wiki_api.api_requests.settings")
    def test_timeout_returns_empty(self, mock_settings, mock_load_session):
        import requests as req_lib

        mock_settings.wikipedia.user_agent = "test"
        mock_settings.wikipedia.default_timeout = 30
        mock_session = MagicMock()
        mock_load_session.return_value = mock_session
        mock_session.post.side_effect = req_lib.exceptions.ReadTimeout()

        result = submitAPI({"action": "query"}, "en", "wikipedia")
        assert result == {}
