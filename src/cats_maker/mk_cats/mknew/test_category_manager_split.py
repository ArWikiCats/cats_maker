"""Simple tests for the classes split out of CategoryManager.

Adjust the `PKG` import path below to the real package that contains mknew_state.py.
"""

from PKG import mknew_creator, mknew_processor, mknew_wikidata
from PKG.mknew_members import CategoryMembersAdder
from PKG.mknew_sources import EnglishCategorySource
from PKG.mknew_state import CategoryManagerStats

SITE_AR = {"family": "wikipedia", "code": "ar"}
SITE_EN = {"family": "wikipedia", "code": "en"}


class TestCategoryMembersAdder:
    """Tests for ``CategoryMembersAdder.add``."""

    def test_add_prefixes_title_and_calls_callback(self):
        calls = []
        done = []
        adder = CategoryMembersAdder(add_to_page_func=lambda page, title: calls.append((page, title)) or True)

        adder.add(["A", "B"], "Some_cat", callback=done.append)

        assert calls == [("A", "تصنيف:Some cat"), ("B", "تصنيف:Some cat")]
        assert done == ["تصنيف:Some cat", "تصنيف:Some cat"]

    def test_add_with_empty_list_does_nothing(self):
        calls = []
        adder = CategoryMembersAdder(add_to_page_func=lambda page, title: calls.append(page))

        adder.add([], "cat")

        assert calls == []

    def test_add_ignores_callback_errors(self):
        def bad_callback(title):
            raise ValueError("boom")

        adder = CategoryMembersAdder(add_to_page_func=lambda page, title: True)

        adder.add(["A"], "cat", callback=bad_callback)


class FakeLangLinksClient:
    def __init__(self, family):
        self.family = family

    def find_page_categories_informations(self, title, prop, site_code):
        return {"Cat:One": {"ar": "تصنيف:واحد"}, "Cat:Two": {}}


class TestEnglishCategorySource:
    """Tests for ``EnglishCategorySource``."""

    def test_normalize_title(self):
        assert EnglishCategorySource.normalize_title("[[Foo_bar]] ") == "Foo bar"

    def test_find_parent_categories_splits_by_arabic_link(self):
        source = EnglishCategorySource(SITE_EN, langlinks_client_cls=FakeLangLinksClient)

        en_cats, ar_cats = source.find_parent_categories("Foo")

        assert en_cats == ["Cat:Two"]
        assert ar_cats == ["تصنيف:واحد"]


class TestCategoryWikidataService:
    """Tests for ``CategoryWikidataService``."""

    def test_check_sitelink_found(self, monkeypatch):
        info = {"q": "Q1", "sitelinks": {"arwiki": "تصنيف:س"}}
        monkeypatch.setattr(mknew_wikidata, "get_sitelinks_from_wikidata", lambda lang, title: info)

        found, result = mknew_wikidata.CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Foo")

        assert found is True
        assert result == info

    def test_check_sitelink_missing(self, monkeypatch):
        monkeypatch.setattr(mknew_wikidata, "get_sitelinks_from_wikidata", lambda lang, title: None)

        found, result = mknew_wikidata.CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Foo")

        assert found is False
        assert result == {}

    def test_log_creation_uses_qid_when_known(self, monkeypatch):
        calls = []
        monkeypatch.setattr(mknew_wikidata, "log_to_wikidata_qid", lambda *a: calls.append(("qid", a)))
        monkeypatch.setattr(mknew_wikidata, "log_to_wikidata", lambda *a: calls.append(("title", a)))
        service = mknew_wikidata.CategoryWikidataService(SITE_AR, SITE_EN)

        service.log_creation("ar", "en", "Q1")
        service.log_creation("ar", "en", "")

        assert calls == [("qid", ("ar", "Q1")), ("title", ("ar", "en"))]


class TestCategoryCreatorMakeAr:
    """Tests for the early exits of ``CategoryCreator.make_ar``."""

    def _creator(self, stats):
        # Only the collaborators used by the early exits are real; the rest are never reached
        return mknew_creator.CategoryCreator(
            wiki_site_ar=SITE_AR,
            stats=stats,
            wikidata=None,
            english_source=EnglishCategorySource(SITE_EN),
            arabic_checker=None,
            members_adder=CategoryMembersAdder(add_to_page_func=lambda page, title: True),
            category_resolver=object(),
        )

    def test_empty_arabic_title_returns_empty_list(self):
        assert self._creator(CategoryManagerStats()).make_ar("Foo", "  ") == []

    def test_already_processed_title_returns_empty_list(self):
        stats = CategoryManagerStats()
        stats._scan_ar_title("تصنيف:س")

        assert self._creator(stats).make_ar("Foo", "تصنيف:س") == []


class FakeCreator:
    def __init__(self):
        self.calls = []

    def make_ar(self, cat, arlab, callback=None):
        self.calls.append((cat, arlab))
        return []


class TestCategoryBatchProcessor:
    """Tests for ``CategoryBatchProcessor``."""

    def test_one_cat_rejects_empty_title(self):
        processor = mknew_processor.CategoryBatchProcessor(CategoryManagerStats(), FakeCreator(), object())

        assert processor.one_cat(" ", 1, 1) is False

    def test_one_cat_skips_title_already_done(self):
        stats = CategoryManagerStats()
        stats.insert_done_d("Foo")
        processor = mknew_processor.CategoryBatchProcessor(stats, FakeCreator(), object())

        assert processor.one_cat("Foo", 1, 1) is False
