"""
Unit tests for src/cats_maker/core_cat/new_c18/utils/text.py module.
"""

from src.cats_maker.core_cat.new_c18.utils.text import (
    clean_category_input,
    extract_wikidata_qid,
    normalize_category_title,
)


class TestCleanCategoryInput:
    def test_strips_arabic_prefix(self):
        assert clean_category_input("تصنيف:علوم", lang="ar") == "علوم"

    def test_strips_english_prefix(self):
        assert clean_category_input("Category:Science", lang="en") == "Science"

    def test_strips_french_prefix(self):
        assert clean_category_input("Catégorie:Sciences", lang="fr") == "Sciences"

    def test_strips_brackets(self):
        assert clean_category_input("[[تصنيف:علوم]]", lang="ar") == "علوم"

    def test_replaces_underscores(self):
        assert clean_category_input("Computer_science", lang="en") == "Computer science"

    def test_strips_whitespace(self):
        assert clean_category_input("  تصنيف:علوم  ", lang="ar") == "علوم"

    def test_unknown_lang_no_prefix(self):
        assert clean_category_input("Test", lang="de") == "Test"


class TestNormalizeCategoryTitle:
    def test_arabic_prefix(self):
        assert normalize_category_title("تصنيف:علوم", lang="ar") == "علوم"

    def test_double_arabic_prefix(self):
        assert normalize_category_title("تصنيف:تصنيف:علوم", lang="ar") == "علوم"

    def test_english_prefix(self):
        assert normalize_category_title("Category:Science", lang="en") == "Science"

    def test_double_english_prefix(self):
        assert normalize_category_title("Category:Category:Science", lang="en") == "Science"

    def test_french_prefix(self):
        assert normalize_category_title("Catégorie:Sciences", lang="fr") == "Sciences"

    def test_brackets(self):
        assert normalize_category_title("[[تصنيف:علوم]]", lang="ar") == "علوم"

    def test_underscores(self):
        assert normalize_category_title("Computer_science", lang="en") == "Computer science"


class TestExtractWikidataQid:
    def test_extracts_qid_from_wikidata_template(self):
        text = "{{قيمة ويكي بيانات/قالب تحقق|Q12345}}"
        assert extract_wikidata_qid(text) == "Q12345"

    def test_extracts_qid_with_id_parameter(self):
        text = "{{قيمة ويكي بيانات/قالب تحقق|id=Q67890}}"
        assert extract_wikidata_qid(text) == "Q67890"

    def test_extracts_qid_from_cycling_race_template(self):
        text = "{{سباق الدراجات/صندوق معلومات|Q11111}}"
        assert extract_wikidata_qid(text) == "Q11111"

    def test_extracts_qid_from_english_cycling_template(self):
        text = "{{Cycling race/infobox|Q22222}}"
        assert extract_wikidata_qid(text) == "Q22222"

    def test_returns_none_when_no_qid(self):
        assert extract_wikidata_qid("plain text") is None

    def test_returns_none_for_empty_text(self):
        assert extract_wikidata_qid("") is None

    def test_handles_multiple_templates(self):
        text = "{{قيمة ويكي بيانات/قالب تحقق|Q111}}{{قيمة ويكي بيانات/قالب تحقق|Q222}}"
        assert extract_wikidata_qid(text) == "Q111"
