"""
Unit tests for src/app/mk_cats/categorytext_data.py module.
"""

from src.app.mk_cats.categorytext_data import LocalLanguageLinks, category_mapping


class TestCategoryMapping:
    def test_is_dict(self):
        assert isinstance(category_mapping, dict)

    def test_has_olympics_mapping(self):
        assert "الألعاب الأولمبية" in category_mapping
        assert category_mapping["الألعاب الأولمبية"] == "ألعاب أولمبية"

    def test_has_covid_mapping(self):
        assert "كوفيد-19" in category_mapping

    def test_has_religion_mapping(self):
        assert " الدين" in category_mapping
        assert category_mapping[" الدين"] == "الأديان"

    def test_has_cinema_mapping(self):
        assert "أفلام" in category_mapping
        assert category_mapping["أفلام"] == "سينما"

    def test_has_transport_mapping(self):
        assert "النقل" in category_mapping
        assert category_mapping["النقل"] == "نقل"


class TestLocalLanguageLinks:
    def test_is_set(self):
        assert isinstance(LocalLanguageLinks, set)

    def test_contains_countries(self):
        assert "فلسطين" in LocalLanguageLinks
        assert "اليمن" in LocalLanguageLinks
        assert "سوريا" in LocalLanguageLinks
        assert "المغرب" in LocalLanguageLinks

    def test_contains_sciences(self):
        assert "الكيمياء" in LocalLanguageLinks

    def test_contains_sports(self):
        assert "كرة القدم" in LocalLanguageLinks
        assert "كرة السلة" in LocalLanguageLinks

    def test_contains_culture(self):
        assert "سينما" in LocalLanguageLinks
        assert "أنمي ومانغا" in LocalLanguageLinks

    def test_size_is_reasonable(self):
        assert len(LocalLanguageLinks) > 100
