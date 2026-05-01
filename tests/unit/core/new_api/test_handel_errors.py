"""
Unit tests for src/core/client_wiki/api_utils/handel_errors.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.api_utils.handel_errors import HandleErrors


class TestHandleErr:
    """Tests for HandleErrors.handle_err method."""

    def setup_method(self):
        self.handler = HandleErrors()

    def test_abusefilter_disallowed_returns_false_for_known_description(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات", "actions": ["disallow"]},
        }
        result = self.handler.handle_err(error)
        assert result is False

    def test_abusefilter_disallowed_returns_false_for_variant1(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 3 من 3", "actions": ["disallow"]},
        }
        result = self.handler.handle_err(error)
        assert result is False

    def test_abusefilter_disallowed_returns_false_for_variant2(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 1 من 3", "actions": ["disallow"]},
        }
        result = self.handler.handle_err(error)
        assert result is False

    def test_abusefilter_disallowed_returns_false_for_variant3(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 2 من 3", "actions": ["disallow"]},
        }
        result = self.handler.handle_err(error)
        assert result is False

    def test_abusefilter_disallowed_returns_description_for_unknown(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": {"description": "Some other filter", "actions": ["disallow"]},
        }
        result = self.handler.handle_err(error)
        assert result == "Some other filter"

    def test_abusefilter_disallowed_with_string_abusefilter(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
            "abusefilter": "not a dict",
        }
        result = self.handler.handle_err(error)
        assert result == ""

    def test_abusefilter_disallowed_with_missing_abusefilter(self):
        error = {
            "code": "abusefilter-disallowed",
            "info": "blocked",
        }
        result = self.handler.handle_err(error)
        assert result == ""

    def test_no_such_entity_returns_false(self):
        error = {"code": "no-such-entity", "info": "Entity not found"}
        result = self.handler.handle_err(error)
        assert result is False

    def test_protectedpage_returns_false(self):
        error = {"code": "protectedpage", "info": "Page is protected"}
        result = self.handler.handle_err(error)
        assert result is False

    def test_articleexists_returns_articleexists(self):
        error = {"code": "articleexists", "info": "Article already exists"}
        result = self.handler.handle_err(error)
        assert result == "articleexists"

    def test_maxlag_returns_false(self):
        error = {"code": "maxlag", "info": "Too much lag"}
        result = self.handler.handle_err(error)
        assert result is False

    def test_unknown_error_returns_error_dict_with_do_error_true(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        result = self.handler.handle_err(error, do_error=True)
        assert result == error

    def test_unknown_error_with_params_clears_data_and_text(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        params = {"action": "edit", "data": "some_data", "text": "some_text"}
        result = self.handler.handle_err(error, params=params, do_error=True)
        assert params["data"] == {}
        assert params["text"] == {}
        assert result == error

    def test_unknown_error_returns_error_dict_with_do_error_false(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        result = self.handler.handle_err(error, do_error=False)
        assert result == error

    def test_do_error_false_does_not_modify_params(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        params = {"action": "edit", "data": "keep", "text": "keep"}
        result = self.handler.handle_err(error, params=params, do_error=False)
        assert params["data"] == "keep"
        assert params["text"] == "keep"

    def test_with_function_name(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        result = self.handler.handle_err(error, function="test_func", do_error=True)
        assert result == error

    def test_params_none_with_do_error(self):
        error = {"code": "unknown-error", "info": "Something went wrong"}
        result = self.handler.handle_err(error, params=None, do_error=True)
        assert result == error

    def test_empty_error_code(self):
        error = {"code": "", "info": "No code"}
        result = self.handler.handle_err(error)
        assert result == error

    def test_missing_code_key(self):
        error = {"info": "No code key"}
        result = self.handler.handle_err(error)
        assert result == error

    def test_missing_info_key(self):
        error = {"code": "some-code"}
        result = self.handler.handle_err(error)
        assert result == error
