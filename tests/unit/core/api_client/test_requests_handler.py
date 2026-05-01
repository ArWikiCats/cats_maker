"""
Unit tests for src/core/api_client/requests_handler.py module.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.core.api_client.exceptions import CSRFError, MaxlagError
from src.core.api_client.requests_handler import _replace_token, wrap_session


class TestReplaceToken:
    def test_replaces_token_in_params(self):
        kwargs = {"params": {"token": "old", "action": "edit"}}
        result = _replace_token(kwargs, "new_token")
        assert result["params"]["token"] == "new_token"
        assert result["params"]["action"] == "edit"

    def test_replaces_token_in_data(self):
        kwargs = {"data": {"token": "old", "action": "edit"}}
        result = _replace_token(kwargs, "new_token")
        assert result["data"]["token"] == "new_token"

    def test_does_not_mutate_original(self):
        original = {"params": {"token": "old"}}
        _replace_token(original, "new")
        assert original["params"]["token"] == "old"

    def test_no_token_key(self):
        kwargs = {"params": {"action": "query"}}
        result = _replace_token(kwargs, "new")
        assert result["params"]["action"] == "query"

    def test_prefers_params_over_data(self):
        kwargs = {"params": {"token": "p_token"}, "data": {"token": "d_token"}}
        result = _replace_token(kwargs, "new")
        assert result["params"]["token"] == "new"
        assert result["data"]["token"] == "d_token"


class TestWrapSession:
    def test_wraps_session(self):
        session = MagicMock(spec=requests.Session)
        site = MagicMock()
        wrap_session(session, site)
        assert hasattr(session, "_original_request")

    def test_does_not_double_wrap(self):
        session = MagicMock(spec=requests.Session)
        session._original_request = MagicMock()
        site = MagicMock()
        wrap_session(session, site)
        # Should not overwrite _original_request


class TestWrappedRequest:
    def test_passes_through_normal_response(self):
        session = MagicMock(spec=requests.Session)
        site = MagicMock()
        response = MagicMock()
        response.headers = {"Content-Type": "text/html"}
        session.request.return_value = response

        wrap_session(session, site)
        result = session.request("GET", "http://example.com")
        assert result == response

    def test_raises_csrf_error_after_max_retries(self):
        session = MagicMock(spec=requests.Session)
        site = MagicMock()
        response = MagicMock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"error": {"code": "badtoken"}}
        session.request.return_value = response

        site.get_token.return_value = "new_token"

        wrap_session(session, site)
        with pytest.raises(CSRFError):
            session.request("POST", "http://example.com")

    @patch("src.core.api_client.requests_handler.time.sleep")
    def test_raises_maxlag_error_after_max_retries(self, mock_sleep):
        session = MagicMock(spec=requests.Session)
        site = MagicMock()
        response = MagicMock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"error": {"code": "maxlag"}}
        session.request.return_value = response

        wrap_session(session, site)
        with pytest.raises(MaxlagError):
            session.request("POST", "http://example.com")
