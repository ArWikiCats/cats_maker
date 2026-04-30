#!/usr/bin/python3
"""
Test file for make_century_template function
"""

import sys
from pathlib import Path

from src.temp.bots import make_century_template


def test_make_century_template_basic():
    # Basic century category
    result = make_century_template("تصنيف:القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_with_foundation():
    # Century foundation category
    result = make_century_template("تصنيف:تأسيسات القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "تأسيس قرن"


def test_make_century_template_foundation_by_country():
    # Century foundation by country
    result = make_century_template("تصنيف:تأسيسات القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21|حسب=حسب البلد}}"
    assert result[1] == "تأسيس قرن"


def test_make_century_template_with_dissolution():
    # Century dissolution category
    result = make_century_template("تصنيف:انحلالات القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "انحلال قرن"


def test_make_century_template_dissolution_by_country():
    # Century dissolution by country
    result = make_century_template("تصنيف:انحلالات القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21|حسب=حسب البلد}}"
    assert result[1] == "انحلال قرن"


def test_make_century_template_dissolution_only():
    # Century dissolution without country
    result = make_century_template("تصنيف:انحلالات القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21}}"
    assert result[1] == "انحلال قرن"


def test_make_century_template_foundation_only():
    # Century foundation without country
    result = make_century_template("تصنيف:تأسيسات القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21}}"
    assert result[1] == "تأسيس قرن"


def test_make_century_template_by_country_only():
    # Century by country only
    result = make_century_template("تصنيف:القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21|حسب=حسب البلد}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_century_only():
    # Century only, no country
    result = make_century_template("تصنيف:القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_invalid_text():
    # Text without century should return default template
    result = make_century_template("تصنيف:موضوع عشوائي")
    assert result[0] == "{{تصنيف موسم}}"
    assert result[1] == "تصنيف موسم"


def test_make_century_template_bc_with_dot():
    # BC century with dot (B.C.) should return empty
    result = make_century_template("تصنيف:القرن 5 ق.م")
    assert result[0] == "{{سنوات في القرن|-5}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_bc_without_dot():
    # BC century without dot should return empty
    result = make_century_template("تصنيف:القرن 2 ق م")
    assert result[0] == "{{سنوات في القرن|-2}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_hijri_century():
    # Hijri centuries like "القرن 3 هـ" - return default template or ignore
    result = make_century_template("تصنيف:القرن 3 هـ")
    assert result[0] == "{{سنوات في القرن|3}}"
    assert result[1] == "سنوات في القرن"


def test_make_century_template_hijri_with_country():
    # Hijri century with country - test function behavior
    result = make_century_template("تصنيف:القرن 10 هـ في اليمن")
    assert result[0] == "{{سنوات في القرن|10}}"
    assert result[1] == "سنوات في القرن"
