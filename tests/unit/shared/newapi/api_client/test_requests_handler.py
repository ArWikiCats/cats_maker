"""
Unit tests for src/core/api_client/requests_handler.py - RequestsHandler and related methods.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.shared.newapi.api_client.client import WikiLoginClient
from src.shared.newapi.api_client.exceptions import MaxlagError
from src.shared.newapi.api_client.requests_handler import RequestsHandler


def _make_client(lang="en", family="wikipedia", username="MyBot", password="pass"):
    """Create a WikiLoginClient with all external dependencies mocked."""
    with (
        patch("src.shared.newapi.api_client.client.mwclient.Site") as mock_site,
        patch("src.shared.newapi.api_client.cookies_client.get_cookie_path") as mock_path,
    ):
        mock_path.return_value = MagicMock()
        site_instance = mock_site.return_value
        site_instance.api.return_value = {"query": {"userinfo": {"id": 1}}}
        site_instance.connection = MagicMock()
        site_instance.api_url = "http://example.com/api"
        site_instance.get_token = MagicMock(return_value="test_token")

        client = WikiLoginClient(lang=lang, family=family, username=username, password=password)
        return client, site_instance


class TestNonJsonResponse:
    """Tests for non-JSON response handling."""

    def test_non_json_content_type_returns_empty_dict(self):
        client, site = _make_client()
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.headers = {"Content-Type": "text/html"}
        response.json = MagicMock(side_effect=ValueError("not json"))
        site.connection.request.return_value = response

        result = client.client_request_retry({"action": "query"}, method="get")
        assert result == {}


class TestJsonParsingError:
    """Tests for JSON parsing error handling."""

    def test_json_parse_failure_returns_empty_dict(self):
        client, site = _make_client()
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.headers = {"Content-Type": "application/json"}
        response.json = MagicMock(side_effect=ValueError("invalid json"))
        site.connection.request.return_value = response

        result = client.client_request_retry({"action": "query"}, method="get")
        assert result == {}


class TestMaxlagHandling:
    """Tests for maxlag error handling."""

    def test_maxlag_error_retries_and_succeeds(self):
        client, site = _make_client()
        maxlag_response = MagicMock()
        maxlag_response.raise_for_status = MagicMock()
        maxlag_response.headers = {"Content-Type": "application/json", "X-RateLimit-RetryAfter": "2"}
        maxlag_response.json.return_value = {"error": {"code": "maxlag", "info": "Lag"}}

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.headers = {"Content-Type": "application/json"}
        success_response.json.return_value = {"query": {"pages": {"1": {"title": "Test"}}}}

        site.connection.request.side_effect = [maxlag_response, success_response]

        with patch("src.shared.newapi.api_client.requests_handler.time.sleep") as mock_sleep:
            result = client.client_request_retry({"action": "query"}, method="get")
            assert "query" in result

    def test_maxlag_exhausted_retries_raises_maxlag_error(self):
        client, site = _make_client()
        maxlag_response = MagicMock()
        maxlag_response.raise_for_status = MagicMock()
        maxlag_response.headers = {"Content-Type": "application/json"}
        maxlag_response.json.return_value = {"error": {"code": "maxlag", "info": "Lag"}}
        site.connection.request.return_value = maxlag_response

        with patch("src.shared.newapi.api_client.requests_handler.time.sleep"):
            with pytest.raises(MaxlagError):
                client.client_request_retry({"action": "query"}, method="get")


class TestCSRFErrorHandling:
    """Tests for CSRF token error handling."""

    def test_csrf_error_refreshes_token_and_retries(self):
        client, site = _make_client()

        csrf_error_response = MagicMock()
        csrf_error_response.raise_for_status = MagicMock()
        csrf_error_response.headers = {"Content-Type": "application/json"}
        csrf_error_response.json.return_value = {"error": {"code": "badtoken", "info": "Invalid token"}}

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.headers = {"Content-Type": "application/json"}
        success_response.json.return_value = {"query": {"pages": {"1": {"title": "Test"}}}}

        site.connection.request.side_effect = [csrf_error_response, success_response]
        site_instance = site  # store reference

        result = client.client_request_retry({"action": "query", "token": "bad"}, method="get")
        assert "query" in result


class TestAssertNamedUserFailed:
    """Tests for assertnameduserfailed recovery."""

    def test_assertnameduserfailed_recovery_succeeds(self):
        client, site = _make_client()

        assert_failed_response = MagicMock()
        assert_failed_response.raise_for_status = MagicMock()
        assert_failed_response.headers = {"Content-Type": "application/json"}
        assert_failed_response.json.return_value = {
            "error": {"code": "assertnameduserfailed", "info": "Session expired"}
        }

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.headers = {"Content-Type": "application/json"}
        success_response.json.return_value = {"query": {"pages": {"1": {"title": "Test"}}}}

        site.connection.request.side_effect = [assert_failed_response, success_response]
        site.login = MagicMock()

        result = client.client_request_retry({"action": "query"}, method="get")
        assert "query" in result


class TestLoginForced:
    """Tests for login method with force=True."""

    @patch.object(WikiLoginClient, "_do_login")
    def test_login_force_calls_do_login_when_not_logged_in(self, mock_do_login):
        client, site = _make_client()
        site.logged_in = False

        client.login(force=True)

        mock_do_login.assert_called_once()


class TestHandleMaxlag:
    """Tests for _handle_maxlag method."""

    def test_handle_maxlag_with_retry_after_header(self):
        client, _ = _make_client()
        response = MagicMock()
        response.headers = {"Retry-After": "3"}

        with patch("src.shared.newapi.api_client.requests_handler.time.sleep") as mock_sleep:
            client.requests_handler._handle_maxlag(response, 1)
            mock_sleep.assert_called_with(3.0)

    def test_handle_maxlag_with_invalid_retry_after_uses_backoff(self):
        client, _ = _make_client()
        response = MagicMock()
        response.headers = {"Retry-After": "not_a_number"}

        with patch("src.shared.newapi.api_client.requests_handler.time.sleep") as mock_sleep:
            client.requests_handler._handle_maxlag(response, 1)
            mock_sleep.assert_called_with(2.0)  # 1 * 2^1

    def test_handle_maxlag_no_retry_after_uses_backoff(self):
        client, _ = _make_client()
        response = MagicMock()
        response.headers = {}

        with patch("src.shared.newapi.api_client.requests_handler.time.sleep") as mock_sleep:

            client.requests_handler._handle_maxlag(response, 2)
            mock_sleep.assert_called_with(4.0)  # 1 * 2^2


class TestInjectToken:
    """Tests for _inject_token static method."""

    def test_inject_token_into_data(self):

        data, params = RequestsHandler._inject_token("new_token", {"token": "old"}, {})
        assert data["token"] == "new_token"

    def test_inject_token_into_params(self):

        data, params = RequestsHandler._inject_token("new_token", {}, {"token": "old"})
        assert params["token"] == "new_token"

    def test_inject_token_no_existing_token(self):

        data, params = RequestsHandler._inject_token("new_token", {}, {})
        assert data == {}
        assert params == {}
