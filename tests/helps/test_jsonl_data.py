"""
Tests for src/helps/jsonl_data.py

اختبارات لملف jsonl_data.py - حفظ وتحميل بيانات JSONL

This module tests:
- save() - Save data to JSONL file
- dump_data() - Decorator to save function inputs/outputs
- SAVE_ENABLE - Global save enable flag
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestSaveFunction:
    """Tests for save function."""

    def test_save_creates_directory_if_not_exists(self, tmp_path, mocker):
        """Test that save creates parent directory if it doesn't exist."""
        from src.core.helps.jsonl_data import save

        new_dir = tmp_path / "new_dir"
        file_path = new_dir / "test.jsonl"

        # Mock jsonlines to avoid actual file operations
        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        save(file_path, {"key": "value"})

        # Directory should be created
        assert new_dir.exists()

    def test_save_converts_dict_to_list(self, tmp_path, mocker):
        """Test that save converts dict to list internally."""
        from src.core.helps.jsonl_data import save

        file_path = tmp_path / "test.jsonl"

        # Create the file first
        file_path.touch()

        # Mock jsonlines.open
        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        save(file_path, {"key": "value"})

        # Writer should be called with a list
        mock_writer.write.assert_called()

    def test_save_appends_to_existing_file(self, tmp_path, mocker):
        """Test that save appends to existing file."""
        from src.core.helps.jsonl_data import save

        file_path = tmp_path / "test.jsonl"
        file_path.touch()  # Create empty file

        # Mock jsonlines.open to track mode
        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mock_open = mocker.patch("jsonlines.open", return_value=mock_open_context)

        save(file_path, [{"key": "value"}])

        # Should open in append mode
        mock_open.assert_called_with(file_path, mode="a")

    def test_save_handles_path_as_string(self, tmp_path, mocker):
        """Test that save handles path as string."""
        from src.core.helps.jsonl_data import save

        file_path = str(tmp_path / "test.jsonl")

        # Mock jsonlines
        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        # Should not raise exception
        save(file_path, {"key": "value"})

    def test_save_handles_list_data(self, tmp_path, mocker):
        """Test that save handles list data correctly."""
        from src.core.helps.jsonl_data import save

        file_path = tmp_path / "test.jsonl"
        file_path.touch()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        save(file_path, [{"item1": 1}, {"item2": 2}])

        mock_writer.write.assert_called()


class TestDumpDataDecorator:
    """Tests for dump_data decorator."""

    def test_dump_data_returns_function_result(self, mocker):
        """Test that dump_data decorator returns the function result."""
        from src.core.helps.jsonl_data import dump_data

        @dump_data()
        def test_func(x, y):
            return x + y

        result = test_func(1, 2)

        assert result == 3

    def test_dump_data_preserves_function_name(self):
        """Test that dump_data preserves the function name."""
        from src.core.helps.jsonl_data import dump_data

        @dump_data()
        def my_function():
            return True

        assert my_function.__name__ == "my_function"

    def test_dump_data_disabled_by_default(self, mocker):
        """Test that dump_data is disabled by default (SAVE_ENABLE=False)."""
        from src.core.helps import jsonl_data

        # Ensure SAVE_ENABLE is False
        original_save_enable = jsonl_data.SAVE_ENABLE
        jsonl_data.SAVE_ENABLE = False

        mock_jsonlines = mocker.patch("jsonlines.open")

        @jsonl_data.dump_data()
        def test_func():
            return "result"

        test_func()

        # Should not open jsonlines when disabled
        mock_jsonlines.assert_not_called()

        # Restore
        jsonl_data.SAVE_ENABLE = original_save_enable

    def test_dump_data_enabled_with_parameter(self, mocker, tmp_path):
        """Test that dump_data can be enabled with parameter."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True)
        def test_func():
            return "result"

        test_func()

        # Should open jsonlines when enabled
        mock_writer.write.assert_called()

        # Cleanup
        jsonl_data.already_saved.clear()

    def test_dump_data_does_not_save_empty_output(self, mocker):
        """Test that dump_data does not save when output is empty."""
        from src.core.helps import jsonl_data

        mock_jsonlines = mocker.patch("jsonlines.open")

        @jsonl_data.dump_data(enable=True)
        def test_func():
            return None

        test_func()

        # Should not save empty output
        mock_jsonlines.assert_not_called()

    def test_dump_data_does_not_save_empty_list_output(self, mocker):
        """Test that dump_data does not save when output is empty list."""
        from src.core.helps import jsonl_data

        mock_jsonlines = mocker.patch("jsonlines.open")

        @jsonl_data.dump_data(enable=True)
        def test_func():
            return []

        test_func()

        # Should not save empty list output
        mock_jsonlines.assert_not_called()

    def test_dump_data_saves_specific_input_keys(self, mocker):
        """Test that dump_data saves only specified input keys."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True, input_keys=["x"])
        def test_func(x, y, z):
            return x + y + z

        test_func(1, 2, 3)

        # Check what was written
        call_args = mock_writer.write.call_args[0][0]
        assert "x" in call_args
        assert "y" not in call_args
        assert "z" not in call_args

        # Cleanup
        jsonl_data.already_saved.clear()

    def test_dump_data_prevents_duplicate_saves(self, mocker):
        """Test that dump_data prevents duplicate saves."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True)
        def test_func(x):
            return x * 2

        # Call twice with same input
        test_func(5)
        test_func(5)

        # Should only save once
        assert mock_writer.write.call_count == 1

        # Cleanup
        jsonl_data.already_saved.clear()

    def test_dump_data_saves_different_inputs_separately(self, mocker):
        """Test that dump_data saves different inputs separately."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True)
        def test_func(x):
            return x * 2

        # Call with different inputs
        test_func(5)
        test_func(10)

        # Should save both
        assert mock_writer.write.call_count == 2

        # Cleanup
        jsonl_data.already_saved.clear()

    def test_dump_data_compare_with_output(self, mocker):
        """Test that dump_data respects compare_with_output parameter."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True, compare_with_output="x")
        def test_func(x):
            return x  # Output equals input

        test_func(5)

        # Should not save when output equals compared input
        mock_writer.write.assert_not_called()

        # Cleanup
        jsonl_data.already_saved.clear()

    def test_dump_data_handles_non_serializable_data(self, mocker):
        """Test that dump_data handles non-serializable data."""
        from src.core.helps import jsonl_data

        # Clear already_saved
        jsonl_data.already_saved.clear()

        mock_writer = MagicMock()
        mock_open_context = MagicMock()
        mock_open_context.__enter__ = MagicMock(return_value=mock_writer)
        mock_open_context.__exit__ = MagicMock(return_value=False)
        mocker.patch("jsonlines.open", return_value=mock_open_context)

        @jsonl_data.dump_data(enable=True)
        def test_func(obj):
            return str(obj)

        # Call with non-serializable object
        test_func(object())

        # Should still work (uses string representation for key)
        mock_writer.write.assert_called()

        # Cleanup
        jsonl_data.already_saved.clear()


class TestAlreadySavedDict:
    """Tests for already_saved dictionary."""

    def test_already_saved_is_dict(self):
        """Test that already_saved is a dictionary."""
        from src.core.helps.jsonl_data import already_saved

        assert isinstance(already_saved, dict)

    def test_already_saved_can_be_cleared(self):
        """Test that already_saved can be cleared."""
        from src.core.helps.jsonl_data import already_saved

        already_saved["test_key"] = True
        already_saved.clear()

        assert len(already_saved) == 0


class TestSaveEnableFlag:
    """Tests for SAVE_ENABLE flag."""

    def test_save_enable_is_boolean(self):
        """Test that SAVE_ENABLE is a boolean."""
        from src.core.helps.jsonl_data import SAVE_ENABLE

        assert isinstance(SAVE_ENABLE, bool)

    def test_save_enable_default_is_false(self):
        """Test that SAVE_ENABLE default is False."""
        from src.core.helps.jsonl_data import SAVE_ENABLE

        # The last assignment in the file sets it to False
        assert SAVE_ENABLE is False
