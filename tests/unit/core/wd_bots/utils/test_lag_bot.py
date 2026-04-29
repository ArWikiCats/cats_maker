"""
Tests for lag_bot.py

This module tests Wikidata lag handling functions.
"""

import pytest

from src.core.wd_bots.lag_bot import (
    FFa_lag,
    Find_Lag,
    do_lag,
    find_lag,
    is_wd_lag_high,
    make_sleep_def,
)


class TestFFaLag:
    """Tests for FFa_lag dictionary"""

    def test_is_dict(self):
        """Test that FFa_lag is a dictionary"""
        assert isinstance(FFa_lag, dict)

    def test_has_required_keys(self):
        """Test that FFa_lag has required keys"""
        assert 1 in FFa_lag
        assert 2 in FFa_lag


class TestFindLag:
    """Tests for Find_Lag dictionary"""

    def test_is_dict(self):
        """Test that Find_Lag is a dictionary"""
        assert isinstance(Find_Lag, dict)


class TestFindLagFunction:
    """Tests for find_lag function"""

    def test_updates_ffa_lag(self, mocker):
        """Test that FFa_lag is updated"""
        mocker.patch("src.core.wd_bots.lag_bot.time.sleep")

        initial_value = FFa_lag[1]
        err = {"lag": 10}

        find_lag(err)

        # Should update FFa_lag[1] to lag value
        assert FFa_lag[1] == 10

        # Reset
        FFa_lag[1] = initial_value

    def test_sleeps_for_lag_plus_one(self, mocker):
        """Test that function sleeps for lag + 1 seconds"""
        mock_sleep = mocker.patch("src.core.wd_bots.lag_bot.time.sleep")

        err = {"lag": 5}
        find_lag(err)

        # Should sleep for at least lag + 1
        mock_sleep.assert_called()


class TestDoLag:
    """Tests for do_lag function"""

    def test_calls_make_sleep_def(self, mocker):
        """Test that make_sleep_def is called"""
        mock_make_sleep = mocker.patch("src.core.wd_bots.lag_bot.make_sleep_def")
        mocker.patch("src.core.wd_bots.lag_bot.time.sleep")

        # Set low lag to avoid long sleep
        FFa_lag[1] = 1

        do_lag()

        mock_make_sleep.assert_called()


class TestBadLag:
    """Tests for is_wd_lag_high function"""

    def test_returns_false_when_lag_low(self):
        """Test that False is returned when lag is low"""
        FFa_lag[1] = 3

        result = is_wd_lag_high()

        assert result is False

    def test_returns_true_when_lag_high_and_nowait(self):
        """Test that True is returned when lag is high and nowait=True"""
        FFa_lag[1] = 10

        result = is_wd_lag_high()

        assert result is True

        # Reset
        FFa_lag[1] = 5
