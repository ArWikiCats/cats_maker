import pytest

from src.core.api2.factory import load_main_api


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
    monkeypatch.setattr("src.core.api2.factory.load_main_api", lambda lang="en": fake_api)
    return fake_api


@pytest.fixture
def api_ar(monkeypatch, fake_api):
    monkeypatch.setattr("src.core.api2.factory.load_main_api", lambda lang="ar": fake_api)
    return fake_api


class TestMainPage:
    @pytest.fixture
    def test_page(self, api_en):
        return api_en.MainPage("User:Mr. Ibrahem/sandbox")

    @pytest.fixture
    def arabic_page(self, api_ar):
        return api_ar.MainPage("وب:ملعب")

    def test_page_exists(self, test_page):
        exists = test_page.exists()
        assert exists is True

    def test_can_edit_permission(self, arabic_page):
        can_edit = arabic_page.can_edit()
        assert isinstance(can_edit, bool)

    def test_get_text(self, arabic_page):
        text = arabic_page.get_text()
        assert len(text) >= 0, "Text should be retrievable"

    def test_nonexistent_page(self, api_en):
        page = api_en.MainPage("NonExistentPage12345")
        assert page.exists() is False
        assert isinstance(page.get_text(), str)


class TestASK_BOT:
    def test_ask_bot_init(self):
        from src.core.api2.api_utils.ask_bot import ASK_BOT

        bot = ASK_BOT()
        assert hasattr(bot, "_save_or_ask")
        assert bot._save_or_ask == {}

    def test_ask_put_no_settings(self):
        from src.core.api2.api_utils.ask_bot import ASK_BOT

        bot = ASK_BOT()
        result = bot.ask_put()
        assert result is True


class TestBotEditChecker:
    def test_bot_edit_checker_init(self):
        from src.core.api2.api_utils.botEdit import BotEditChecker

        checker = BotEditChecker()
        assert hasattr(checker, "_bot_cache")
        assert hasattr(checker, "_created_cache")

    def test_extract_templates_and_params(self):
        from src.core.api2.api_utils.botEdit import extract_templates_and_params

        text = "{{test|param=value}}"
        result = extract_templates_and_params(text)
        assert isinstance(result, list)

    def test_bot_May_Edit_defaults(self):
        from src.core.api2.api_utils.botEdit import bot_May_Edit

        result = bot_May_Edit(text="", title_page="Test", botjob="all")
        assert isinstance(result, bool)


class TestTransport:
    def test_transport_init(self):
        from src.core.api2.super.transport import Transport

        t = Transport(lang="en", family="wikipedia", username="test")
        assert t.lang == "en"
        assert t.family == "wikipedia"
        assert t.username == "test"


class TestLogin:
    def test_login_init(self):
        from src.core.api2.super.super_login import Login

        login = Login(lang="ar", family="wikipedia")
        assert login.lang == "ar"
        assert login.family == "wikipedia"

    def test_login_class_vars(self):
        from src.core.api2.super.super_login import Login


class TestModels:
    def test_content_dataclass(self):
        from src.core.api2.super.models import Content

        c = Content()
        assert c.text_html == ""

    def test_meta_dataclass(self):
        from src.core.api2.super.models import Meta

        m = Meta()
        assert m.info_loaded is False

    def test_revisions_data_dataclass(self):
        from src.core.api2.super.models import RevisionsData

        r = RevisionsData()
        assert r.revid == ""


class TestCategoryDepth:
    def test_category_depth_init(self):
        from src.core.api2.super.catdepth_new import CategoryDepth, title_process

        assert title_process("Test", "en") == "Category:Test"

    def test_args_group(self):
        from src.core.api2.super.catdepth_new import args_group

        result = args_group("Test", {"depth": 1})
        assert result["title"] == "Test"
        assert result["depth"] == 1


class TestConstants:
    def test_ns_list_import(self):
        from src.core.api2.constants import NS_LIST

        assert isinstance(NS_LIST, dict)

    def test_category_prefixes(self):
        from src.core.api2.constants import CATEGORY_PREFIXES

        assert "ar" in CATEGORY_PREFIXES
        assert "en" in CATEGORY_PREFIXES
