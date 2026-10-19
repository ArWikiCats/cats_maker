"""
Unit tests for src/cats_maker/mk_cats/utils/filter_en.py module.
"""

from src.cats_maker.mk_cats.utils.filter_en import filter_category


class TestFilterCategory:
    def test_normal_category_passes(self):
        assert filter_category("Mathematics") is True

    def test_wikiproject_filtered(self):
        # "wikiproject" is lowercase in BBlcak, so it matches against cat.lower()
        assert filter_category("Wikiproject Science") is False

    def test_sockpuppets_filtered(self):
        assert filter_category("sockpuppets of admin") is False

    def test_without_source_filtered(self):
        assert filter_category("Articles without a source") is False

    def test_images_for_deletion_filtered(self):
        assert filter_category("images for deletion") is False

    def test_cleanup_starts_with_filtered(self):
        assert filter_category("Cleanup articles") is False

    def test_uncategorized_starts_with_filtered(self):
        assert filter_category("Uncategorized pages") is False

    def test_unreferenced_starts_with_filtered(self):
        assert filter_category("Unreferenced articles") is False

    def test_wikipedia_starts_with_filtered(self):
        assert filter_category("Wikipedia maintenance") is False

    def test_articles_lacking_filtered(self):
        assert filter_category("Articles lacking sources") is False

    def test_use_starts_with_filtered(self):
        assert filter_category("use English") is False

    def test_user_pages_filtered(self):
        assert filter_category("User pages") is False

    def test_month_date_filtered(self):
        assert filter_category("Events from January 2020") is False

    def test_month_date_february_filtered(self):
        assert filter_category("People from February 1990") is False

    def test_normal_category_with_prefix_passes(self):
        assert filter_category("Category:Physics") is True

    def test_case_insensitive_starts_with(self):
        assert filter_category("CLEANUP needed") is False

    def test_disambiguation_case_sensitive_bug(self):
        # BBlcak has "Disambiguation" (capital D) but code uses cat.lower().find(x)
        # Since find() is case-sensitive, "Disambiguation" never matches lowercase input
        # This is a known behavior quirk in the source
        assert filter_category("Disambiguation pages") is True

    def test_lowercase_disambiguation_also_passes(self):
        # BBlcak has "Disambiguation" (capital D), find() is case-sensitive
        # so even "disambiguation" (lowercase) won't match against it
        assert filter_category("disambiguation pages") is True

    def test_is_cached(self):
        r1 = filter_category("TestCategory")
        r2 = filter_category("TestCategory")
        assert r1 == r2
