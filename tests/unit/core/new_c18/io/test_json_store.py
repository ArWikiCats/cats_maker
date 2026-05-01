"""
Unit tests for src/core/new_c18/io/json_store.py module.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.new_c18.io.json_store import JsonStore, _load_json, _save_json


class TestLoadJson:
    def test_loads_list(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps(["a", "b"]), encoding="utf-8")
        result = _load_json(path)
        assert result == ["a", "b"]

    def test_loads_dict(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"key": "val"}), encoding="utf-8")
        result = _load_json(path, empty_data="dict")
        assert result == {"key": "val"}

    def test_creates_missing_file_as_list(self, tmp_path):
        path = tmp_path / "missing.json"
        result = _load_json(path)
        assert result == []

    def test_creates_missing_file_as_dict(self, tmp_path):
        path = tmp_path / "missing.json"
        result = _load_json(path, empty_data="dict")
        assert result == {}

    def test_handles_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        result = _load_json(path)
        assert result == []


class TestSaveJson:
    def test_saves_list(self, tmp_path):
        path = tmp_path / "test.json"
        _save_json(["a", "b"], path)
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == ["a", "b"]

    def test_saves_dict(self, tmp_path):
        path = tmp_path / "test.json"
        _save_json({"key": "val"}, path)
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == {"key": "val"}


class TestJsonStore:
    def test_load(self, tmp_path):
        path = tmp_path / "store.json"
        path.write_text(json.dumps([1, 2]), encoding="utf-8")
        store = JsonStore(path)
        assert store.load() == [1, 2]

    def test_save(self, tmp_path):
        path = tmp_path / "store.json"
        store = JsonStore(path)
        store.save([3, 4])
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == [3, 4]

    def test_is_stale_true_for_missing(self, tmp_path):
        path = tmp_path / "missing.json"
        store = JsonStore(path)
        assert store.is_stale() is True

    def test_is_stale_true_for_old_file(self, tmp_path):
        path = tmp_path / "old.json"
        path.write_text("[]", encoding="utf-8")
        old_time = datetime.now() - timedelta(days=2)
        os.utime(path, (old_time.timestamp(), old_time.timestamp()))
        store = JsonStore(path)
        assert store.is_stale(days=1) is True

    def test_is_stale_false_for_fresh_file(self, tmp_path):
        path = tmp_path / "fresh.json"
        path.write_text("[]", encoding="utf-8")
        store = JsonStore(path)
        assert store.is_stale(days=1) is False


class TestLoadJsonEdgeCases:
    def test_creates_parent_directory(self, tmp_path):
        """Test that _load_json creates parent directory for missing file."""
        path = tmp_path / "subdir" / "test.json"
        assert not path.parent.exists()
        result = _load_json(path)
        assert path.parent.exists()
        assert result == []

    def test_permission_error_on_read(self, tmp_path):
        """Test that PermissionError during read is caught."""
        path = tmp_path / "test.json"
        path.write_text("[]", encoding="utf-8")
        with patch("builtins.open", side_effect=PermissionError("denied")):
            result = _load_json(path)
        # Should return empty data since the read failed
        assert result == []


class TestSaveJsonEdgeCases:
    def test_permission_error_retry_path(self, tmp_path):
        """Test that PermissionError triggers retry path."""
        path = tmp_path / "test.json"
        call_count = 0
        original_open = open

        def mock_open(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PermissionError("denied")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            _save_json(["data"], path)
        # The retry should have succeeded
        assert call_count >= 2

    def test_oserror_on_write(self, tmp_path):
        """Test that OSError during write is caught."""
        path = tmp_path / "test.json"
        with patch("builtins.open", side_effect=OSError("disk full")):
            _save_json(["data"], path)  # Should not raise
