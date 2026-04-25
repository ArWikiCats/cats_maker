"""
Tests for src/wd_bots/wd_newapi_bot.py

This module tests the WD_API class.
"""

import pytest

from src.wd_bots.wd_bots_main import WD_API


class TestWDAPI:
    """Tests for WD_API class"""

    def test_instantiation(self, mocker):
        """Test that WD_API can be instantiated"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WD_API(mock_login)

        assert api is not None
        assert api.login_bot == mock_login

    def test_inherits_wd_functions(self, mocker):
        """Test that WD_API inherits from WD_Functions"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WD_API(mock_login)

        # Should have methods from WD_Functions
        assert hasattr(api, "format_labels_descriptions")

    def test_inherits_error_handler(self, mocker):
        """Test that WD_API inherits from WD_ERRORS_HANDLER"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WD_API(mock_login)

        # Should have methods from WD_ERRORS_HANDLER
        assert hasattr(api, "handle_err_wd")

    def test_get_rest_result_delegates(self, mocker):
        """Test that get_rest_result delegates to login_bot"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_login.get_rest_result.return_value = {"test": "data"}

        api = WD_API(mock_login)
        result = api.get_rest_result("https://example.com")

        mock_login.get_rest_result.assert_called_with("https://example.com")
        assert result == {"test": "data"}

    def test_post_params_delegates(self, mocker):
        """Test that post_params delegates to login_bot"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_login.post_params.return_value = {"result": "ok"}

        api = WD_API(mock_login)
        result = api.post_params({"action": "query"})

        mock_login.post_params.assert_called()

    def test_post_continue_delegates(self, mocker):
        """Test that post_continue delegates to login_bot"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_login.post_continue.return_value = {"pages": []}

        api = WD_API(mock_login)
        result = api.post_continue({"action": "query"}, "query")

        mock_login.post_continue.assert_called()

    def test_filter_data_adds_format(self, mocker):
        """Test that filter_data adds format and utf8"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mocker.patch("src.wd_bots.wd_newapi_bot.lag_bot.do_lag")
        mocker.patch("src.wd_bots.wd_newapi_bot.lag_bot.FFa_lag", {1: 5})

        api = WD_API(mock_login)
        data = {"action": "wbeditentity"}
        result = api.filter_data(data, "", "")

        assert result["format"] == "json"
        assert result["utf8"] == 1

    def test_lag_work_calls_find_lag(self, mocker):
        """Test that lag_work calls find_lag"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_find_lag = mocker.patch("src.wd_bots.wd_newapi_bot.lag_bot.find_lag")

        api = WD_API(mock_login)
        api.lag_work({"lag": 10})

        mock_find_lag.assert_called_with({"lag": 10})
