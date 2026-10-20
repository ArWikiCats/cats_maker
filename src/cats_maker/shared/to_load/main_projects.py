#!/usr/bin/python3
"""

بوت تقييمات الصفحات

"""

from __future__ import annotations

import logging
import re
from typing import Any

from .loader import FilesBaseWorker

logger = logging.getLogger(__name__)

main_projse = [
    "اللغة العربية",
    "أسماك",
    "أعلام",
    "أغنية الجليد والنار",
    "أفغانستان",
    "ألعاب أولمبية",
    "ألعاب الفيديو",
    "أنتاركتيكا",
    "أوروبا",
    "إسرائيل",
    "إنترنت",
    "إيران",
    "إيطاليا",
    "الأردن",
    "الأنمي والمانغا",
    "الإسلام",
    "البحرين",
    "الجزائر",
    "الدولة العثمانية",
    "السعودية",
    "السودان",
    "الصين",
    "العراق",
    "القوائم",
    "القوقاز",
    "الكويت",
    "المرأة",
    "المسيحية",
    "المغرب",
    "الهند",
    "الوطن العربي",
    "الولايات المتحدة",
    "اليمن",
    "برمجيات",
    "بيئة",
    "تاريخ",
    "تربية وتعليم",
    "تركيا",
    "تشريح",
    "تقنية",
    "تلفاز",
    "تونس",
    "ثدييات",
    "جغرافيا",
    "رئيسيات",
    "ركوب الدراجات",
    "روسيا",
    "رياضة",
    "رياضيات",
    "زواحف وبرمائيات",
    "سوريا",
    "سياسة",
    "سينما",
    "صيدلة",
    "طب بيطري",
    "طب",
    "طيور",
    "علم الأحياء القديمة",
    "علم الأحياء",
    "حوسبة",
    "علوم",
    "عمارة",
    "فلسطين",
    "فلسفة",
    "فلك",
    "فيزياء",
    "قروش",
    "قطر",
    "كرة السلة",
    "كرة القدم",
    "كرة المضرب",
    "كندا",
    "كيمياء",
    "لبنان",
    "مأكولات ومشروبات",
    "مصر",
    "موسيقى",
    "نقل",
]

default_data = dict.fromkeys(main_projse, True)

# ==========================
# FilesBaseWorker
# ==========================


class MainProjectsWorker(FilesBaseWorker):
    def __init__(self) -> None:
        file: str = "main_proj.json"
        self.title = "ويكيبيديا:مشاريع ويكي/التقييم الآلي"
        super().__init__(file, self.title, default_data)

    def load_data_from_text(self, text: str) -> dict:
        if not text:
            return {}

        RE = re.compile(r"\[\[ويكيبيديا\:مشروع ويكي .*?\]\]", flags=re.IGNORECASE).findall(text)

        if not RE:
            return {}

        data = {}

        for linke in RE:
            tit = linke.replace("[[ويكيبيديا:مشروع ويكي ", "")
            tit = tit.split("|")[0].replace("[[", "").replace("]]", "").strip()

            if tit in main_projse:
                data[tit] = True

        return data

    def load_new_data(self) -> dict[str, Any]:

        logger.info(f"Loading: {self.title}")

        text = self.load_text()

        data = self.load_data_from_text(text)

        return data


_local_data: list = []


def main_projects_loader() -> list[Any]:
    global _local_data

    worker = MainProjectsWorker()

    data = worker.run()

    _local_data = list(data.keys())

    return _local_data


__all__ = [
    "MainProjectsWorker",
    "main_projects_loader",
]
