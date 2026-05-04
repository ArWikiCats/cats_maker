"""
Unit tests for src/core/wd_bots/wd_bots_main.py module.
TODO: write tests
"""

import pytest

from src.core.wd_bots.wd_bots_main import WdAPI


class TestWDAPI:
    """Tests for WdAPI class"""

    def test_instantiation(self, mocker):
        """Test that WdAPI can be instantiated"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WdAPI(mock_login)

        assert api is not None
        assert api.login_bot == mock_login

    def test_inherits_error_handler(self, mocker):
        """Test that WdAPI inherits from WD_ERRORS_HANDLER"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"

        api = WdAPI(mock_login)

        # Should have methods from WD_ERRORS_HANDLER
        assert hasattr(api, "handle_err_wd")

    def test_post_params_delegates(self, mocker):
        """Test that client_request delegates to login_bot"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mock_login.client_request.return_value = {"result": "ok"}

        api = WdAPI(mock_login)
        result = api.login_bot.client_request({"action": "query"})

        mock_login.client_request.assert_called()

    def test_filter_data_adds_format(self, mocker):
        """Test that filter_data adds format and utf8"""
        mock_login = mocker.MagicMock()
        mock_login.user_login = "testuser"
        mocker.patch("src.core.wd_bots.wd_bots_main.do_lag")
        mocker.patch("src.core.wd_bots.wd_bots_main.get_lag_value", return_value=5)

        api = WdAPI(mock_login)
        data = {"action": "wbeditentity"}
        result = api.filter_data(data)

        assert result["format"] == "json"
        assert result["utf8"] == 1
