"""
Tests for src/core/c18_new/cat_tools2.py

This module tests category tools functions.
"""

import pytest

from src.core.cats_helpers.cat_tools2 import tatone_ns


class TestTatoneNs:
    """Tests for tatone_ns list"""

    def test_is_list(self):
        """Test that tatone_ns is a list"""
        assert isinstance(tatone_ns, list)

    def test_contains_main_namespace(self):
        """Test that tatone_ns contains main namespace (0)"""
        assert 0 in tatone_ns

    def test_contains_category_namespace(self):
        """Test that tatone_ns contains category namespace (14)"""
        assert 14 in tatone_ns

    def test_contains_template_namespace(self):
        """Test that tatone_ns contains template namespace (10)"""
        assert 10 in tatone_ns

    def test_contains_portal_namespace(self):
        """Test that tatone_ns contains portal namespace (100)"""
        assert 100 in tatone_ns

    def test_all_valid_namespaces(self):
        """Test that all namespace values are valid integers"""
        for ns in tatone_ns:
            assert isinstance(ns, int)
            assert ns >= 0
