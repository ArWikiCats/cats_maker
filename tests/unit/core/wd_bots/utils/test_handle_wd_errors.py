"""
This module tests Wikidata error handling functions.
"""

from unittest.mock import MagicMock

import pytest

from src.core.wd_bots.wd_bots_main import WD_API


@pytest.fixture
def mock_wd_api():
    """Create a WD_API instance for testing"""
    _mock = MagicMock()
    _mock.user_login = "test"
    return WD_API(_mock)


class TestWDErrorsHandler:
    """Tests for WD_API class"""

    def test_handle_abusefilter_error(self, mock_wd_api):
        """Test handling of abusefilter-disallowed error"""
        error = {"code": "abusefilter-disallowed", "abusefilter": {"description": "Test filter"}}

        result = mock_wd_api.handle_err_wd(error)

        assert result == "Test filter"

    def test_handle_bot_delay_filter(self, mock_wd_api):
        """Test handling of bot delay filter"""

        error = {"code": "abusefilter-disallowed", "abusefilter": {"description": "تأخير البوتات 3 ساعات"}}

        result = mock_wd_api.handle_err_wd(error)

        assert result is False

    def test_handle_no_such_entity_error(self, mock_wd_api):
        """Test handling of no-such-entity error"""

        error = {"code": "no-such-entity"}

        result = mock_wd_api.handle_err_wd(error)

        assert result is False

    def test_handle_protectedpage_error(self, mock_wd_api):
        """Test handling of protectedpage error"""

        error = {"code": "protectedpage"}

        result = mock_wd_api.handle_err_wd(error)

        assert result is False

    def test_handle_articleexists_error(self, mock_wd_api):
        """Test handling of articleexists error"""

        error = {"code": "articleexists"}

        result = mock_wd_api.handle_err_wd(error)

        assert result == "articleexists"

    def test_handle_maxlag_error(self, mock_wd_api):
        """Test handling of maxlag error"""

        error = {"code": "maxlag"}

        result = mock_wd_api.handle_err_wd(error)

        assert result is False

    def test_handle_unknown_error(self, mock_wd_api):
        """Test handling of unknown error"""

        error = {"code": "unknown_error", "info": "Unknown error occurred"}
        params = {"data": {"test": "data"}}

        result = mock_wd_api.handle_err_wd(error, params=params)

        # Should clear data in params
        assert params["data"] == {}

    def test_extracts_error_code(self, mock_wd_api):
        """Test that error code is extracted"""

        error = {"code": "test_code", "info": "Test info"}
        params = {"data": {"test": "data"}}

        # Should not raise error - params must be provided
        mock_wd_api.handle_err_wd(error, function="test_func", params=params)

    def test_extracts_error_info(self, mock_wd_api):
        """Test that error info is extracted"""

        error = {"code": "unknown", "info": "Test error info"}
        params = {"data": {}}

        mock_wd_api.handle_err_wd(error, params=params)

        # Should process without error
