#!/usr/bin/python3
"""
Test file for make_decades_template function
"""

import sys
from pathlib import Path

from src.temp.bots import make_decades_template


def test_makedecades_temp_basic():
    result = make_decades_template("تصنيف:عقد 2010 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{تصنيف عقد|قرن=21|عقد=2010|بلد=أوقيانوسيا}}"
    assert result[1] == "تصنيف عقد"


def test_makedecades_temp_with_foundation():
    result = make_decades_template("تصنيف:تأسيسات عقد 2010 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس عقد|قرن=21|عقد=2010|بلد=أوقيانوسيا}}"
    assert result[1] == "تأسيس عقد"


def test_makedecades_temp_foundation_by_country():
    result = make_decades_template("تصنيف:تأسيسات عقد 2010 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس عقد|قرن=21|عقد=2010|حسب=حسب البلد}}"
    assert result[1] == "تأسيس عقد"


def test_makedecades_temp_with_dissolution():
    result = make_decades_template("تصنيف:انحلالات عقد 2010 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال عقد|قرن=21|عقد=2010|بلد=أوقيانوسيا}}"
    assert result[1] == "انحلال عقد"


def test_makedecades_temp_dissolution_by_country():
    result = make_decades_template("تصنيف:انحلالات عقد 2010 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال عقد|قرن=21|عقد=2010|حسب=حسب البلد}}"
    assert result[1] == "انحلال عقد"


def test_makedecades_temp_dissolution_only():
    result = make_decades_template("تصنيف:انحلالات عقد 2010")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال عقد|قرن=21|عقد=2010}}"
    assert result[1] == "انحلال عقد"


def test_makedecades_temp_foundation_only():
    result = make_decades_template("تصنيف:تأسيسات عقد 2010")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس عقد|قرن=21|عقد=2010}}"
    assert result[1] == "تأسيس عقد"


def test_makedecades_temp_by_country_only():
    result = make_decades_template("تصنيف:عقد 2010 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{تصنيف عقد|قرن=21|عقد=2010|حسب=حسب البلد}}"
    assert result[1] == "تصنيف عقد"


def test_makedecades_temp_decade_only():
    result = make_decades_template("تصنيف:عقد 2010")

    assert isinstance(result, tuple)
    assert result[0] == "{{تصنيف عقد|قرن=21|عقد=2010}}"
    assert result[1] == "تصنيف عقد"
