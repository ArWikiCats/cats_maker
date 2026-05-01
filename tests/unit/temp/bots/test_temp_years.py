#!/usr/bin/python3
"""
Test file for make_years_template function
"""

import sys
from pathlib import Path

from src.temp.bots import make_years_template


def test_make_years_template_basic():
    result = make_years_template("تصنيف:2018 في أوقيانوسيا", "")

    assert result == "{{بلد|201|8|أوقيانوسيا}}"


def test_make_years_template_with_foundation_year():
    result = make_years_template("تصنيف:تأسيسات سنة 2018 في أوقيانوسيا", "تأسيسات ")

    assert result == "{{تأسيس بلد|201|8|أوقيانوسيا}}"


def test_make_years_template_by_country():
    result = make_years_template("تصنيف:تأسيسات سنة 2018 حسب البلد", "تأسيسات ")

    assert result == "{{تأسيس بلد|201|8|حسب البلد|في=}}"


def test_make_years_template_with_dissolution():
    result = make_years_template("تصنيف:انحلالات 2018 في أوقيانوسيا", "انحلالات ")

    assert result == "{{انحلال بلد|201|8|أوقيانوسيا}}"


def test_make_years_template_dissolution_by_country():
    result = make_years_template("تصنيف:انحلالات سنة 2018 حسب البلد", "انحلالات ")

    assert result == "{{انحلال بلد|201|8|حسب البلد|في=}}"


def test_make_years_template_dissolution_year():
    result = make_years_template("تصنيف:انحلالات سنة 2018", "انحلالات ")

    assert result == "{{انحلال سنة|201|8}}"


def test_make_years_template_foundation_year():
    result = make_years_template("تصنيف:تأسيسات سنة 2018", "تأسيسات ")

    assert result == "{{تأسيس سنة|201|8}}"


def test_make_years_template_by_country_only():
    result = make_years_template("تصنيف:2018 حسب البلد", "")

    assert result == "{{بلد|201|8|حسب البلد|في=}}"


def test_make_years_template_year_only():
    result = make_years_template("تصنيف:2018", "")

    assert result == "{{سنة|201|8}}"
