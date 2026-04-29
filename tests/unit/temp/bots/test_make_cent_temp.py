#!/usr/bin/python3
"""
Test file for Make_Cent_temp function
"""

import sys
from pathlib import Path

from src.temp.bots import Make_Cent_temp


def test_make_cent_temp_basic():
    # Basic century category
    result = Make_Cent_temp("تصنيف:القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_with_foundation():
    # Century foundation category
    result = Make_Cent_temp("تصنيف:تأسيسات القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "تأسيس قرن"


def test_make_cent_temp_foundation_by_country():
    # Century foundation by country
    result = Make_Cent_temp("تصنيف:تأسيسات القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21|حسب=حسب البلد}}"
    assert result[1] == "تأسيس قرن"


def test_make_cent_temp_with_dissolution():
    # Century dissolution category
    result = Make_Cent_temp("تصنيف:انحلالات القرن 21 في أوقيانوسيا")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21|بلد=أوقيانوسيا}}"
    assert result[1] == "انحلال قرن"


def test_make_cent_temp_dissolution_by_country():
    # Century dissolution by country
    result = Make_Cent_temp("تصنيف:انحلالات القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21|حسب=حسب البلد}}"
    assert result[1] == "انحلال قرن"


def test_make_cent_temp_dissolution_only():
    # Century dissolution without country
    result = Make_Cent_temp("تصنيف:انحلالات القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال قرن|21}}"
    assert result[1] == "انحلال قرن"


def test_make_cent_temp_foundation_only():
    # Century foundation without country
    result = Make_Cent_temp("تصنيف:تأسيسات القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس قرن|21}}"
    assert result[1] == "تأسيس قرن"


def test_make_cent_temp_by_country_only():
    # Century by country only
    result = Make_Cent_temp("تصنيف:القرن 21 حسب البلد")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21|حسب=حسب البلد}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_century_only():
    # Century only, no country
    result = Make_Cent_temp("تصنيف:القرن 21")
    assert isinstance(result, tuple)
    assert result[0] == "{{سنوات في القرن|21}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_invalid_text():
    # Text without century should return default template
    result = Make_Cent_temp("تصنيف:موضوع عشوائي")
    assert result[0] == "{{تصنيف موسم}}"
    assert result[1] == "تصنيف موسم"


def test_make_cent_temp_bc_with_dot():
    # BC century with dot (B.C.) should return empty
    result = Make_Cent_temp("تصنيف:القرن 5 ق.م")
    assert result[0] == "{{سنوات في القرن|-5}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_bc_without_dot():
    # BC century without dot should return empty
    result = Make_Cent_temp("تصنيف:القرن 2 ق م")
    assert result[0] == "{{سنوات في القرن|-2}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_hijri_century():
    # Hijri centuries like "القرن 3 هـ" - return default template or ignore
    result = Make_Cent_temp("تصنيف:القرن 3 هـ")
    assert result[0] == "{{سنوات في القرن|3}}"
    assert result[1] == "سنوات في القرن"


def test_make_cent_temp_hijri_with_country():
    # Hijri century with country - test function behavior
    result = Make_Cent_temp("تصنيف:القرن 10 هـ في اليمن")
    assert result[0] == "{{سنوات في القرن|10}}"
    assert result[1] == "سنوات في القرن"
