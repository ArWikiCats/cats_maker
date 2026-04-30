"""
Unit tests for src/core/client_wiki/api_utils/handel_errors.py module.
"""

import pytest

from src.core.client_wiki.api_utils.handel_errors import HandleErrors


@pytest.fixture
def handler():
    return HandleErrors()


class TestHandleErrors:
    def test_abusefilter_bot_delay_returns_false(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات"},
        }
        assert handler.handle_err(error) is False

    def test_abusefilter_bot_delay_variant_1(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 3 من 3"},
        }
        assert handler.handle_err(error) is False

    def test_abusefilter_bot_delay_variant_2(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 1 من 3"},
        }
        assert handler.handle_err(error) is False

    def test_abusefilter_bot_delay_variant_3(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {"description": "تأخير البوتات 3 ساعات- 2 من 3"},
        }
        assert handler.handle_err(error) is False

    def test_abusefilter_other_description_returns_description(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {"description": "Some other filter"},
        }
        assert handler.handle_err(error) == "Some other filter"

    def test_abusefilter_non_dict_abusefilter(self, handler):
        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": "string_value",
        }
        result = handler.handle_err(error)
        assert result == ""

    def test_no_such_entity_returns_false(self, handler):
        error = {"code": "no-such-entity"}
        assert handler.handle_err(error) is False

    def test_protectedpage_returns_false(self, handler):
        error = {"code": "protectedpage"}
        assert handler.handle_err(error) is False

    def test_articleexists_returns_string(self, handler):
        error = {"code": "articleexists"}
        assert handler.handle_err(error) == "articleexists"

    def test_maxlag_returns_false(self, handler):
        error = {"code": "maxlag"}
        assert handler.handle_err(error) is False

    def test_unknown_error_returns_dict_with_do_error(self, handler):
        error = {"code": "unknown", "info": "Something went wrong"}
        result = handler.handle_err(error, do_error=True)
        assert result == error

    def test_unknown_error_returns_dict_without_do_error(self, handler):
        error = {"code": "unknown", "info": "Something went wrong"}
        result = handler.handle_err(error, do_error=False)
        assert result == error

    def test_params_cleared_on_error(self, handler):
        error = {"code": "unknown", "info": "test"}
        params = {"data": {"key": "val"}, "text": {"key": "val"}}
        handler.handle_err(error, params=params)
        assert params["data"] == {}
        assert params["text"] == {}

    def test_no_code_defaults_to_empty_string(self, handler):
        error = {"info": "no code"}
        result = handler.handle_err(error)
        assert result == error
