#!/usr/bin/python3
"""
Test file for Make_years_temp function
"""

import sys
from pathlib import Path

from src.temp.bots import Make_years_temp


def test_make_years_temp_basic():
    result = Make_years_temp("تصنيف:2018 في أوقيانوسيا", "")

    assert result == "{{بلد|201|8|أوقيانوسيا}}"


def test_make_years_temp_with_foundation_year():
    result = Make_years_temp("تصنيف:تأسيسات سنة 2018 في أوقيانوسيا", "تأسيسات ")

    assert result == "{{تأسيس بلد|201|8|أوقيانوسيا}}"


def test_make_years_temp_by_country():
    result = Make_years_temp("تصنيف:تأسيسات سنة 2018 حسب البلد", "تأسيسات ")

    assert result == "{{تأسيس بلد|201|8|حسب البلد|في=}}"


def test_make_years_temp_with_dissolution():
    result = Make_years_temp("تصنيف:انحلالات 2018 في أوقيانوسيا", "انحلالات ")

    assert result == "{{انحلال بلد|201|8|أوقيانوسيا}}"


def test_make_years_temp_dissolution_by_country():
    result = Make_years_temp("تصنيف:انحلالات سنة 2018 حسب البلد", "انحلالات ")

    assert result == "{{انحلال بلد|201|8|حسب البلد|في=}}"


def test_make_years_temp_dissolution_year():
    result = Make_years_temp("تصنيف:انحلالات سنة 2018", "انحلالات ")

    assert result == "{{انحلال سنة|201|8}}"


def test_make_years_temp_foundation_year():
    result = Make_years_temp("تصنيف:تأسيسات سنة 2018", "تأسيسات ")

    assert result == "{{تأسيس سنة|201|8}}"


def test_make_years_temp_by_country_only():
    result = Make_years_temp("تصنيف:2018 حسب البلد", "")

    assert result == "{{بلد|201|8|حسب البلد|في=}}"


def test_make_years_temp_year_only():
    result = Make_years_temp("تصنيف:2018", "")

    assert result == "{{سنة|201|8}}"
