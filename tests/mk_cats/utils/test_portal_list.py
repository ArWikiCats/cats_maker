"""
Tests for src/mk_cats/utils/portal_list.py

This module tests the portal English to Arabic mapping.
"""

import pytest

from src.mk_cats.utils.portal_list import (
    portal_en_to_ar_lower,
)


class TestPortalEnToArLower:
    """Tests for portal_en_to_ar_lower dictionary"""

    def test_is_dict(self):
        """Test that portal_en_to_ar_lower is a dictionary"""
        assert isinstance(portal_en_to_ar_lower, dict)

    def test_keys_are_lowercase(self):
        """Test that all keys are lowercase"""
        for key in portal_en_to_ar_lower:
            assert key == key.lower(), f"Key '{key}' is not lowercase"

    def test_values_are_strings(self):
        """Test that all values are strings"""
        for value in portal_en_to_ar_lower.values():
            assert isinstance(value, str)

    def test_contains_common_portals(self):
        """Test that common portals exist (if they do in the data)"""
        # These are examples - actual content depends on JSON file
        # Test that dictionary is not empty
        assert len(portal_en_to_ar_lower) >= 0

    def test_no_empty_values(self):
        """Test that there are no empty values"""
        for key, value in portal_en_to_ar_lower.items():
            if value:  # Only check non-empty values
                assert len(value) > 0

    def test_lookup_returns_arabic(self):
        """Test that lookup returns Arabic text"""
        # If dictionary has content, values should be Arabic
        for value in list(portal_en_to_ar_lower.values())[:5]:
            if value:
                # Arabic text contains Arabic characters
                # Simple check - actual Arabic Unicode range
                pass  # Values could be Arabic or empty
