"""
Unit tests for src/core/utils/functions_timer.py module.
"""

from unittest.mock import patch

from src.core.utils.functions_timer import function_timer


class TestFunctionTimer:
    def test_preserves_function_name(self):
        @function_timer
        def my_func():
            return 42

        assert my_func.__name__ == "my_func"

    def test_preserves_return_value(self):
        @function_timer
        def my_func():
            return 42

        assert my_func() == 42

    def test_preserves_docstring(self):
        @function_timer
        def my_func():
            """My docstring."""

        assert my_func.__doc__ == "My docstring."

    def test_passes_args_and_kwargs(self):
        @function_timer
        def add(a, b, c=0):
            return a + b + c

        assert add(1, 2, c=3) == 6

    @patch("src.core.utils.functions_timer.logger")
    def test_logs_timing(self, mock_logger):
        @function_timer
        def my_func():
            return 1

        my_func()
        mock_logger.debug.assert_called_once()
        msg = mock_logger.debug.call_args[0][0]
        assert "my_func finished in" in msg
        assert "s" in msg
