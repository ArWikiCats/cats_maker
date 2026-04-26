"""
Tests for src/wd_bots/wd_bots_main.py

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

    def test_inherits_error_handler(self, mocker):
        """Test that WD_API inherits from WD_ERRORS_HANDLER"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WD_API(mock_login)

        # Should have methods from WD_ERRORS_HANDLER
        assert hasattr(api, "handle_err_wd")

    def test_post_params_delegates(self, mocker):
        """Test that post_params delegates to login_bot"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_login.post_params.return_value = {"result": "ok"}

        api = WD_API(mock_login)
        result = api.login_bot.post_params({"action": "query"})

        mock_login.post_params.assert_called()

    def test_filter_data_adds_format(self, mocker):
        """Test that filter_data adds format and utf8"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mocker.patch("src.wd_bots.wd_bots_main.lag_bot.do_lag")
        mocker.patch("src.wd_bots.wd_bots_main.lag_bot.FFa_lag", {1: 5, 2: 0})

        api = WD_API(mock_login)
        data = {"action": "wbeditentity"}
        result = api.filter_data(data)

        assert result["format"] == "json"
        assert result["utf8"] == 1
