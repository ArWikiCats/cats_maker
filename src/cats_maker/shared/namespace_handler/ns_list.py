"""
en mapping:
https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces%7Cnamespacealiases&formatversion=2

ar mapping:
https://ar.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces%7Cnamespacealiases&formatversion=2
"""

from __future__ import annotations

from .mapping import Namespace

# Mapping of namespace ID (int) to Namespace object (with aliases)
AR_NAMESPACES_DATA: list[Namespace] = [
    Namespace(
        id=-2,
        name="ميديا",
        canonical_name="Media",
        aliases=[],
        has_talk_ns=False,
    ),
    Namespace(
        id=-1,
        name="خاص",
        canonical_name="Special",
        aliases=[],
        has_talk_ns=False,
    ),
    Namespace(
        id=0,
        name="",
        canonical_name="",
        aliases=[],
    ),
    Namespace(
        id=1,
        name="نقاش",
        canonical_name="Talk",
        aliases=[],
    ),
    Namespace(
        id=2,
        name="مستخدم",
        canonical_name="User",
        aliases=[],
    ),
    Namespace(
        id=3,
        name="نقاش المستخدم",
        canonical_name="User talk",
        aliases=[],
    ),
    Namespace(
        id=4,
        name="ويكيبيديا",
        canonical_name="Project",
        aliases=[],
    ),
    Namespace(
        id=5,
        name="نقاش ويكيبيديا",
        canonical_name="Project talk",
        aliases=[],
    ),
    Namespace(
        id=6,
        name="ملف",
        canonical_name="File",
        aliases=[],
    ),
    Namespace(
        id=7,
        name="نقاش الملف",
        canonical_name="File talk",
        aliases=[],
    ),
    Namespace(
        id=8,
        name="ميدياويكي",
        canonical_name="MediaWiki",
        aliases=[],
    ),
    Namespace(
        id=9,
        name="نقاش ميدياويكي",
        canonical_name="MediaWiki talk",
        aliases=[],
    ),
    Namespace(
        id=10,
        name="قالب",
        canonical_name="Template",
        aliases=[],
    ),
    Namespace(
        id=11,
        name="نقاش القالب",
        canonical_name="Template talk",
        aliases=[],
    ),
    Namespace(
        id=12,
        name="مساعدة",
        canonical_name="Help",
        aliases=[],
    ),
    Namespace(
        id=13,
        name="نقاش المساعدة",
        canonical_name="Help talk",
        aliases=[],
    ),
    Namespace(
        id=14,
        name="تصنيف",
        canonical_name="Category",
        aliases=[],
    ),
    Namespace(
        id=15,
        name="نقاش التصنيف",
        canonical_name="Category talk",
        aliases=[],
    ),
    Namespace(
        id=100,
        name="بوابة",
        canonical_name="بوابة",
        aliases=[],
    ),
    Namespace(
        id=101,
        name="نقاش البوابة",
        canonical_name="نقاش البوابة",
        aliases=[],
    ),
    Namespace(
        id=710,
        name="نص زمني",
        canonical_name="TimedText",
        aliases=[],
    ),
    Namespace(
        id=711,
        name="نقاش النص الزمني",
        canonical_name="TimedText talk",
        aliases=[],
    ),
    Namespace(
        id=828,
        name="وحدة",
        canonical_name="Module",
        aliases=[],
    ),
    Namespace(
        id=829,
        name="نقاش الوحدة",
        canonical_name="Module talk",
        aliases=[],
    ),
    Namespace(
        id=1728,
        name="فعالية",
        canonical_name="Event",
        aliases=[],
    ),
    Namespace(
        id=1729,
        name="نقاش فعالية",
        canonical_name="Event talk",
        aliases=[],
    ),
    Namespace(
        id=2600,
        name="موضوع",
        canonical_name="Topic",
        aliases=[],
        has_talk_ns=False,
    ),
]

EN_NAMESPACES_DATA: list[Namespace] = [
    Namespace(
        id=-2,
        name="Media",
        canonical_name="Media",
        aliases=[],
        has_talk_ns=False,
    ),
    Namespace(
        id=-1,
        name="Special",
        canonical_name="Special",
        aliases=[],
        has_talk_ns=False,
    ),
    Namespace(
        id=0,
        name="",
        aliases=[],
    ),
    Namespace(
        id=1,
        name="Talk",
        canonical_name="Talk",
        aliases=[],
    ),
    Namespace(
        id=2,
        name="User",
        canonical_name="User",
        aliases=[],
    ),
    Namespace(
        id=3,
        name="User talk",
        canonical_name="User talk",
        aliases=[],
    ),
    Namespace(
        id=4,
        name="Wikipedia",
        canonical_name="Project",
        aliases=[],
    ),
    Namespace(
        id=5,
        name="Wikipedia talk",
        canonical_name="Project talk",
        aliases=[],
    ),
    Namespace(
        id=6,
        name="File",
        canonical_name="File",
        aliases=[],
    ),
    Namespace(
        id=7,
        name="File talk",
        canonical_name="File talk",
        aliases=[],
    ),
    Namespace(
        id=8,
        name="MediaWiki",
        canonical_name="MediaWiki",
        aliases=[],
    ),
    Namespace(
        id=9,
        name="MediaWiki talk",
        canonical_name="MediaWiki talk",
        aliases=[],
    ),
    Namespace(
        id=10,
        name="Template",
        canonical_name="Template",
        aliases=[],
    ),
    Namespace(
        id=11,
        name="Template talk",
        canonical_name="Template talk",
        aliases=[],
    ),
    Namespace(
        id=12,
        name="Help",
        canonical_name="Help",
        aliases=[],
    ),
    Namespace(
        id=13,
        name="Help talk",
        canonical_name="Help talk",
        aliases=[],
    ),
    Namespace(
        id=14,
        name="Category",
        canonical_name="Category",
        aliases=[],
    ),
    Namespace(
        id=15,
        name="Category talk",
        canonical_name="Category talk",
        aliases=[],
    ),
    Namespace(
        id=100,
        name="Portal",
        canonical_name="Portal",
        aliases=[],
    ),
    Namespace(
        id=101,
        name="Portal talk",
        canonical_name="Portal talk",
        aliases=[],
    ),
    Namespace(
        id=118,
        name="Draft",
        canonical_name="Draft",
        aliases=[],
    ),
    Namespace(
        id=119,
        name="Draft talk",
        canonical_name="Draft talk",
        aliases=[],
    ),
    Namespace(
        id=126,
        name="MOS",
        canonical_name="MOS",
        aliases=[],
    ),
    Namespace(
        id=127,
        name="MOS talk",
        canonical_name="MOS talk",
        aliases=[],
    ),
    Namespace(
        id=710,
        name="TimedText",
        canonical_name="TimedText",
        aliases=[],
    ),
    Namespace(
        id=711,
        name="TimedText talk",
        canonical_name="TimedText talk",
        aliases=[],
    ),
    Namespace(
        id=828,
        name="Module",
        canonical_name="Module",
        aliases=[],
    ),
    Namespace(
        id=829,
        name="Module talk",
        canonical_name="Module talk",
        aliases=[],
    ),
    Namespace(
        id=1728,
        name="Event",
        canonical_name="Event",
        aliases=[],
    ),
    Namespace(
        id=1729,
        name="Event talk",
        canonical_name="Event talk",
        aliases=[],
    ),
]

AR_NAMESPACES: dict[int, str] = {x.id: x.name for x in AR_NAMESPACES_DATA}

EN_NAMESPACES: dict[int, str] = {x.id: x.name for x in EN_NAMESPACES_DATA}

LANGCODE_TO_NAMESPACES = {
    "ar": AR_NAMESPACES_DATA,
    "en": EN_NAMESPACES_DATA,
}

__all__ = [
    "LANGCODE_TO_NAMESPACES",
    "AR_NAMESPACES_DATA",
    "EN_NAMESPACES_DATA",
    "AR_NAMESPACES",
    "EN_NAMESPACES",
]
