"""
Tests for handel_errors.py

This module tests error handling functions.
"""

import pytest

from src.core.client_wiki.api_utils.handel_errors import HandleErrors


class TestHandleErrors:
    """Tests for HandleErrors class"""

    def test_handles_abusefilter_disallowed_bot_delay(self):
        """Test handling of bot delay abuse filter"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {
                "id": "169",
                "description": "تأخير البوتات 3 ساعات",
                "actions": ["disallow"],
            },
        }

        result = handler.handle_err(error)
        assert result is False

    def test_handles_abusefilter_disallowed_bot_delay_1_of_3(self):
        """Test handling of bot delay abuse filter 1 of 3"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {
                "description": "تأخير البوتات 3 ساعات- 1 من 3",
            },
        }

        result = handler.handle_err(error)
        assert result is False

    def test_handles_abusefilter_disallowed_bot_delay_2_of_3(self):
        """Test handling of bot delay abuse filter 2 of 3"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {
                "description": "تأخير البوتات 3 ساعات- 2 من 3",
            },
        }

        result = handler.handle_err(error)
        assert result is False

    def test_handles_abusefilter_disallowed_bot_delay_3_of_3(self):
        """Test handling of bot delay abuse filter 3 of 3"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {
                "description": "تأخير البوتات 3 ساعات- 3 من 3",
            },
        }

        result = handler.handle_err(error)
        assert result is False

    def test_handles_abusefilter_disallowed_other_description(self):
        """Test handling of other abuse filter descriptions"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {
                "description": "some other filter",
            },
        }

        result = handler.handle_err(error)
        assert result == "some other filter"

    def test_handles_abusefilter_with_empty_dict(self):
        """Test handling of empty abusefilter dict"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": {},
        }

        result = handler.handle_err(error)
        assert result == ""

    def test_handles_abusefilter_not_a_dict(self):
        """Test handling of non-dict abusefilter"""
        handler = HandleErrors()

        error = {
            "code": "abusefilter-disallowed",
            "abusefilter": "not a dict",
        }

        result = handler.handle_err(error)
        assert result == ""

    def test_handles_no_such_entity(self):
        """Test handling of no-such-entity error"""
        handler = HandleErrors()

        error = {"code": "no-such-entity"}

        result = handler.handle_err(error)
        assert result is False

    def test_handles_protectedpage(self):
        """Test handling of protectedpage error"""
        handler = HandleErrors()

        error = {"code": "protectedpage"}

        result = handler.handle_err(error)
        assert result is False

    def test_handles_articleexists(self):
        """Test handling of articleexists error"""
        handler = HandleErrors()

        error = {"code": "articleexists"}

        result = handler.handle_err(error)
        assert result == "articleexists"

    def test_handles_maxlag(self):
        """Test handling of maxlag error"""
        handler = HandleErrors()

        error = {"code": "maxlag"}

        result = handler.handle_err(error)
        assert result is False

    def test_logs_error_when_do_error_true(self, mocker):
        """Test that error is logged when do_error is True"""
        handler = HandleErrors()
        mock_logger = mocker.patch("src.core.client_wiki.api_utils.handel_errors.logger")

        error = {"code": "unknown", "info": "Some error info"}
        result = handler.handle_err(error, function="test_func", params={"key": "value"}, do_error=True)

        mock_logger.error.assert_called_once()
        assert result == error

    def test_does_not_log_when_do_error_false(self, mocker):
        """Test that error is not logged when do_error is False"""
        handler = HandleErrors()
        mock_logger = mocker.patch("src.core.client_wiki.api_utils.handel_errors.logger")

        error = {"code": "unknown", "info": "Some error info"}
        result = handler.handle_err(error, do_error=False)

        mock_logger.error.assert_not_called()
        assert result == error

    def test_clears_data_and_text_when_params_provided(self, mocker):
        """Test that data and text are cleared in params when do_error is True"""
        handler = HandleErrors()
        mocker.patch("src.core.client_wiki.api_utils.handel_errors.logger")

        params = {"data": {"key": "value"}, "text": {"key": "value"}}
        error = {"code": "unknown"}
        handler.handle_err(error, params=params, do_error=True)

        assert params["data"] == {}
        assert params["text"] == {}
