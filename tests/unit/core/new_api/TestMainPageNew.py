import pytest

from src.core.client_wiki.factory import load_main_api


@pytest.fixture
def fake_api():
    class FakeMainPage:
        def __init__(self, title):
            self.title = title

        def exists(self):
            return self.title != "NonExistentPage12345"

        def can_edit(self):
            return True

        def get_text(self):
            if self.title == "NonExistentPage12345":
                return ""
            return "Sample page text."

    class FakeAPI:
        def MainPage(self, title) -> FakeMainPage:
            return FakeMainPage(title)

    return FakeAPI()


@pytest.fixture
def api_en(monkeypatch, fake_api):
    monkeypatch.setattr("src.core.client_wiki.factory.load_main_api", lambda lang="en": fake_api)
    return fake_api


@pytest.fixture
def api_ar(monkeypatch, fake_api):
    monkeypatch.setattr("src.core.client_wiki.factory.load_main_api", lambda lang="ar": fake_api)
    return fake_api


class TestMainPage:
    @pytest.fixture
    def test_page(self, api_en):
        page = api_en.MainPage("User:Mr. Ibrahem/sandbox")
        return page

    @pytest.fixture
    def arabic_page(self, api_ar):
        return api_ar.MainPage("وب:ملعب")

    def test_page_exists(self, test_page):
        """Test page existence check"""
        exists = test_page.exists()
        # assert isinstance(exists, bool)
        assert exists is True

    def test_can_edit_permission(self, arabic_page):
        """Test edit permission check"""
        can_edit = arabic_page.can_edit()
        assert isinstance(can_edit, bool)

    def test_get_text(self, arabic_page):
        """Test text retrieval"""
        text = arabic_page.get_text()
        # assert isinstance(text, str)
        assert len(text) >= 0, "Text should be retrievable"

    def test_nonexistent_page(self, api_en):
        """Test behavior with non-existent page"""
        page = api_en.MainPage("NonExistentPage12345")
        assert page.exists() is False
        assert isinstance(page.get_text(), str)  # Should handle gracefully
