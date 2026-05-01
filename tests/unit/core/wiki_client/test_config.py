"""
Unit tests for src/core/wiki_client/config.py module.
"""

from src.core.api_client.config import BACKOFF_BASE, COOKIES_DIR, MAX_RETRIES, MAXLAG_HEADER


class TestConfig:
    def test_max_retries(self):
        assert MAX_RETRIES == 5

    def test_backoff_base(self):
        assert BACKOFF_BASE == 1

    def test_maxlag_header(self):
        assert MAXLAG_HEADER == "Retry-After"

    def test_cookies_dir(self):
        assert COOKIES_DIR == "cookies"
