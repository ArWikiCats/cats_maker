"""
Unit tests for src/core/new_api/auth.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.new_api.auth import AuthProvider


class TestAuthProviderInit:
    def test_sets_attributes(self):
        auth = AuthProvider("ar", "wikipedia")
        assert auth.lang == "ar"
        assert auth.family == "wikipedia"
        assert auth.endpoint == "https://ar.wikipedia.org/w/api.php"
        assert auth.username is None
        assert auth.password is None

    def test_with_session(self):
        session = MagicMock()
        auth = AuthProvider("en", "wikisource", session=session)
        assert auth.session is session


class TestAddUserTables:
    def test_sets_credentials_for_matching_family(self):
        auth = AuthProvider("ar", "wikipedia")
        table = {"username": "bot", "password": "pass"}
        auth.add_User_tables("wikipedia", table)
        assert auth.username == "bot"
        assert auth.password == "pass"

    def test_ignores_non_matching_family(self):
        auth = AuthProvider("en", "wikisource")
        table = {"username": "bot", "password": "pass"}
        auth.add_User_tables("wikipedia", table)
        assert auth.username is None

    def test_empty_family_ignored(self):
        auth = AuthProvider("ar", "wikipedia")
        table = {"username": "bot", "password": "pass"}
        auth.add_User_tables("", table)
        assert auth.username is None


class TestGetLogintoken:
    def test_returns_token(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"query": {"tokens": {"logintoken": "abc123"}}}
        auth.session.request.return_value = mock_response
        assert auth.get_logintoken() == "abc123"

    def test_returns_empty_on_error(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        auth.session.request.side_effect = Exception("network error")
        assert auth.get_logintoken() == ""


class TestGetLoginResult:
    def test_returns_false_when_no_password(self):
        auth = AuthProvider("ar", "wikipedia")
        assert auth.get_login_result("token", "user", "") is False

    def test_returns_true_on_success(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"login": {"result": "Success"}}
        auth.session.request.return_value = mock_response
        with patch.object(auth, "loged_in", return_value=True):
            assert auth.get_login_result("token", "user", "pass") is True

    def test_returns_false_on_failure(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"login": {"result": "Failed", "reason": "Wrong password"}}
        auth.session.request.return_value = mock_response
        assert auth.get_login_result("token", "user", "pass") is False


class TestMakeNewR3Token:
    def test_returns_token(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"query": {"tokens": {"csrftoken": "csrf123"}}}
        auth.session.request.return_value = mock_response
        assert auth._make_new_r3_token() == "csrf123"

    def test_returns_empty_on_error(self):
        auth = AuthProvider("ar", "wikipedia")
        auth.session = MagicMock()
        auth.session.request.side_effect = Exception("error")
        assert auth._make_new_r3_token() == ""
