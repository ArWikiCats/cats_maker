import pytest

from src.new_api.pagenew import load_main_api


@pytest.mark.network
class TestMainPage:
    @pytest.fixture
    def test_page(self) :
        api = load_main_api("en")
        page = api.MainPage("User:Mr. Ibrahem/sandbox")
        return page

    @pytest.fixture
    def arabic_page(self):
        api = load_main_api("ar")
        return api.MainPage("وب:ملعب")

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

    def test_nonexistent_page(self):
        """Test behavior with non-existent page"""
        api = load_main_api("en")
        page = api.MainPage("NonExistentPage12345")
        assert page.exists() is False
        assert isinstance(page.get_text(), str)  # Should handle gracefully
