"""
Unit tests for src/temp/bots/load_data.py module.
"""

from src.temp.bots.load_data import (
    Baco,
    Baco_centries,
    Baco_decades,
    cacaca,
    decades_list,
    elfffff,
    years_baco,
)


class TestModuleData:
    def test_years_baco_is_dict(self):
        assert isinstance(years_baco, dict)

    def test_baco_decades_is_dict(self):
        assert isinstance(Baco_decades, dict)

    def test_baco_centries_is_dict(self):
        assert isinstance(Baco_centries, dict)

    def test_baco_is_dict(self):
        assert isinstance(Baco, dict)

    def test_elfffff_structure(self):
        assert isinstance(elfffff, dict)
        assert -1 in elfffff
        assert 1 in elfffff
        assert elfffff[1] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_decades_list_structure(self):
        assert isinstance(decades_list, dict)
        assert 1 in decades_list
        assert -1 in decades_list
        assert "0" in decades_list[1]
        assert "-90" in decades_list[-1]

    def test_cacaca_structure(self):
        assert isinstance(cacaca, dict)
        assert "تأسيسات " in cacaca
        assert cacaca["تأسيسات "] == "تأسيس "

    def test_years_baco_has_entries(self):
        assert len(years_baco) > 0

    def test_baco_decades_has_entries(self):
        assert len(Baco_decades) > 0

    def test_baco_centries_has_entries(self):
        assert len(Baco_centries) > 0

    def test_baco_has_entries(self):
        assert len(Baco) > 0

    def test_year_2000_in_years_baco(self):
        assert "2000" in years_baco

    def test_decade_1990_in_baco_decades(self):
        assert "1990" in Baco_decades
