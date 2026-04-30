#!/usr/bin/python3
"""
Test file for make_millennium_template function
"""

import sys
from pathlib import Path

from src.temp.bots import make_millennium_template


def test_make_millennium_template_basic():
    result = make_millennium_template("تصنيف:الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{الألفية 3 في بلد|أوقيانوسيا}}"
    assert result[1] == "الألفية 3 في بلد"


def test_make_millennium_template_with_foundation():
    result = make_millennium_template("تصنيف:تأسيسات الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس بلد الألفية 3|أوقيانوسيا}}"
    assert result[1] == "تأسيس بلد الألفية 3"


def test_make_millennium_template_foundation_by_country():
    result = make_millennium_template("تصنيف:تأسيسات الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس بلد الألفية 3|حسب البلد|في=}}"
    assert result[1] == "تأسيس بلد الألفية 3"


def test_make_millennium_template_with_dissolution():
    result = make_millennium_template("تصنيف:انحلالات الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال بلد الألفية 3|أوقيانوسيا}}"
    assert result[1] == "انحلال بلد الألفية 3"


def test_make_millennium_template_dissolution_by_country():
    result = make_millennium_template("تصنيف:انحلالات الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال بلد الألفية 3|حسب البلد|في=}}"
    assert result[1] == "انحلال بلد الألفية 3"


def test_make_millennium_template_dissolution_only():
    result = make_millennium_template("تصنيف:انحلالات الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال  الألفية 3}}"
    assert result[1] == "انحلال  الألفية 3"


def test_make_millennium_template_foundation_only():
    result = make_millennium_template("تصنيف:تأسيسات الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس  الألفية 3}}"
    assert result[1] == "تأسيس  الألفية 3"


def test_make_millennium_template_by_country_only():
    result = make_millennium_template("تصنيف:الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{الألفية 3 في بلد|حسب البلد|في=}}"
    assert result[1] == "الألفية 3 في بلد"


def test_make_millennium_template_millennium_only():
    result = make_millennium_template("تصنيف:الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{ الألفية 3}}"
    assert result[1] == " الألفية 3"
