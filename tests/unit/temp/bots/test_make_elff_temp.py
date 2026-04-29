#!/usr/bin/python3
"""
Test file for Make_Elff_temp function
"""

import sys
from pathlib import Path

from src.temp.bots import Make_Elff_temp


def test_make_elff_temp_basic():
    result = Make_Elff_temp("تصنيف:الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{الألفية 3 في بلد|أوقيانوسيا}}"
    assert result[1] == "الألفية 3 في بلد"


def test_make_elff_temp_with_foundation():
    result = Make_Elff_temp("تصنيف:تأسيسات الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس بلد الألفية 3|أوقيانوسيا}}"
    assert result[1] == "تأسيس بلد الألفية 3"


def test_make_elff_temp_foundation_by_country():
    result = Make_Elff_temp("تصنيف:تأسيسات الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس بلد الألفية 3|حسب البلد|في=}}"
    assert result[1] == "تأسيس بلد الألفية 3"


def test_make_elff_temp_with_dissolution():
    result = Make_Elff_temp("تصنيف:انحلالات الألفية 3 في أوقيانوسيا")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال بلد الألفية 3|أوقيانوسيا}}"
    assert result[1] == "انحلال بلد الألفية 3"


def test_make_elff_temp_dissolution_by_country():
    result = Make_Elff_temp("تصنيف:انحلالات الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال بلد الألفية 3|حسب البلد|في=}}"
    assert result[1] == "انحلال بلد الألفية 3"


def test_make_elff_temp_dissolution_only():
    result = Make_Elff_temp("تصنيف:انحلالات الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{انحلال  الألفية 3}}"
    assert result[1] == "انحلال  الألفية 3"


def test_make_elff_temp_foundation_only():
    result = Make_Elff_temp("تصنيف:تأسيسات الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{تأسيس  الألفية 3}}"
    assert result[1] == "تأسيس  الألفية 3"


def test_make_elff_temp_by_country_only():
    result = Make_Elff_temp("تصنيف:الألفية 3 حسب البلد")

    assert isinstance(result, tuple)
    assert result[0] == "{{الألفية 3 في بلد|حسب البلد|في=}}"
    assert result[1] == "الألفية 3 في بلد"


def test_make_elff_temp_millennium_only():
    result = Make_Elff_temp("تصنيف:الألفية 3")

    assert isinstance(result, tuple)
    assert result[0] == "{{ الألفية 3}}"
    assert result[1] == " الألفية 3"
