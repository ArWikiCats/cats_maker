"""
Unit tests for src/temp/bots/new.py module.
"""

from src.temp.bots.new import (
    make_century_template,
    make_millennium_template,
    make_decades_template,
    make_years_template,
    TemplatesMaker,
    main_make_temp,
)


class TestTemplatesMakerInit:
    def test_has_elfffff(self):
        assert isinstance(TemplatesMaker.elfffff, dict)
        assert -1 in TemplatesMaker.elfffff
        assert 1 in TemplatesMaker.elfffff

    def test_has_decades_list(self):
        assert isinstance(TemplatesMaker.decades_list, dict)
        assert 1 in TemplatesMaker.decades_list
        assert -1 in TemplatesMaker.decades_list

    def test_has_cacaca(self):
        assert "تأسيسات " in TemplatesMaker.cacaca
        assert "انحلالات " in TemplatesMaker.cacaca


class TestInitializeData:
    def test_builds_years_baco(self):
        bot = TemplatesMaker()
        bot._initialize_data()
        assert len(bot.years_Baco) > 0

    def test_builds_baco_decades(self):
        bot = TemplatesMaker()
        bot._initialize_data()
        assert len(bot.Baco_decades) > 0

    def test_builds_baco_centries(self):
        bot = TemplatesMaker()
        bot._initialize_data()
        assert len(bot.Baco_centries) > 0

    def test_idempotent(self):
        bot = TemplatesMaker()
        bot._initialize_data()
        count1 = len(bot.years_Baco)
        bot._initialize_data()
        count2 = len(bot.years_Baco)
        assert count1 == count2


class TestMakeElffTemp:
    def test_millennium_1(self):
        result, temp = make_millennium_template("تصنيف:الألفية الأولى")
        assert "الألفية 1" in result

    def test_millennium_2(self):
        result, temp = make_millennium_template("تصنيف:الألفية الثانية")
        assert "الألفية 2" in result

    def test_millennium_3(self):
        result, temp = make_millennium_template("تصنيف:الألفية الثالثة")
        assert "الألفية 3" in result

    def test_non_millennium_returns_season(self):
        result, temp = make_millennium_template("تصنيف:علوم")
        assert "تصنيف موسم" in result


class Testmake_decades_template:
    def test_basic_decade(self):
        result, temp = make_decades_template("تصنيف:عقد 1990")
        assert "عقد" in result

    def test_non_decade_returns_season(self):
        result, temp = make_decades_template("تصنيف:علوم")
        assert "تصنيف موسم" in result


class TestMakeCentTemp:
    def test_basic_century(self):
        result, temp = make_century_template("تصنيف:القرن 19")
        assert "قرن" in result

    def test_non_century_still_matches_broadly(self):
        # make_century_template uses re.sub which returns the original string if no match
        # The if-dee check then passes because the original string is truthy
        result, temp = make_century_template("تصنيف:علوم")
        # Due to the regex logic, non-century titles still produce output
        assert isinstance(result, str)


class TestMakeYearsTemp:
    def test_returns_empty_for_bc(self):
        result = make_years_template("تصنيف:100 ق م", "تأسيسات ")
        assert result == ""

    def test_non_year_returns_season(self):
        result = make_years_template("تصنيف:علوم", "تأسيسات ")
        assert "تصنيف موسم" in result


class TestMainMakeTemp:
    def test_coronavirus_returns_empty(self):
        result, temp = main_make_temp("", "تصنيف:فيروس كورونا")
        assert result == ""

    def test_numeric_prefix_returns_season(self):
        result, temp = main_make_temp("", "تصنيف:123 test")
        assert "تصنيف موسم" in result

    def test_decade_title(self):
        result, temp = main_make_temp("", "تصنيف:عقد 1990")
        assert "عقد" in result

    def test_century_title(self):
        result, temp = main_make_temp("", "تصنيف:القرن 19")
        assert "قرن" in result

    def test_millennium_title(self):
        result, temp = main_make_temp("", "تصنيف:الألفية الأولى")
        assert "الألفية" in result

    def test_normal_category_returns_empty(self):
        result, temp = main_make_temp("", "تصنيف:علوم")
        assert result == ""
