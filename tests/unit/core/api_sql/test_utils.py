"""Unit tests for src/core/api_sql/utils.py module."""

import pytest

from src.core.api_sql.utils import add_namespace_prefix


class TestAddNamespacePrefix:
    """Tests for the add_namespace_prefix utility function."""

    # --- Namespace 0 (main/article) ---

    def test_ns_0_returns_title_unchanged(self):
        assert add_namespace_prefix("Test", "0", "ar") == "Test"

    def test_ns_0_int_returns_title_unchanged(self):
        assert add_namespace_prefix("Test", 0, "en") == "Test"

    # --- Empty / falsy title ---

    def test_empty_title_returns_empty(self):
        assert add_namespace_prefix("", "14", "ar") == ""

    # --- Arabic namespaces ---

    @pytest.mark.parametrize(
        "ns, prefix",
        [
            ("1", "نقاش"),
            ("2", "مستخدم"),
            ("4", "ويكيبيديا"),
            ("6", "ملف"),
            ("10", "قالب"),
            ("14", "تصنيف"),
            ("100", "بوابة"),
            ("828", "وحدة"),
            ("2600", "موضوع"),
        ],
    )
    def test_ar_namespaces(self, ns, prefix):
        assert add_namespace_prefix("عنوان", ns, "ar") == f"{prefix}:عنوان"

    # --- English namespaces ---

    @pytest.mark.parametrize(
        "ns, prefix",
        [
            ("1", "Talk"),
            ("2", "User"),
            ("4", "Project"),
            ("6", "File"),
            ("10", "Template"),
            ("14", "Category"),
            ("100", "Portal"),
            ("828", "Module"),
        ],
    )
    def test_en_namespaces(self, ns, prefix):
        assert add_namespace_prefix("Title", ns, "en") == f"{prefix}:Title"

    # --- Invalid namespace ---

    def test_unknown_namespace_returns_title(self):
        assert add_namespace_prefix("Foo", "999", "ar") == "Foo"

    def test_unknown_namespace_en(self):
        assert add_namespace_prefix("Foo", "999", "en") == "Foo"

    # --- Default language ---

    def test_default_lang_is_arabic(self):
        assert add_namespace_prefix("علوم", "14") == "تصنيف:علوم"

    # --- Integer namespace input ---

    def test_int_namespace_input(self):
        assert add_namespace_prefix("Science", 14, "en") == "Category:Science"
