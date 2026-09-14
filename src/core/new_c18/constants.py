#!/usr/bin/python3
"""Centralised constants for the module."""

from enum import IntEnum


class Namespace(IntEnum):
    """Wikipedia namespace IDs."""

    MAIN = 0
    TEMPLATE = 10
    CATEGORY = 14
    PORTAL = 100


# Category prefixes
CAT_PREFIX_AR = "تصنيف:"
CAT_PREFIX_EN = "Category:"
CAT_PREFIX_FR = "Catégorie:"

# Blacklists (immutable)
SKIPPED_CATEGORIES: frozenset[str] = frozenset(
    {
        "تصنيف:مقالات ويكيبيديا تضمن نصوصا من الطبعة العشرين لكتاب تشريح جرايز (1918)",
        "تصنيف:Webarchive template wayback links",
        "تصنيف:Templates generating hCalendars",
        "تصنيف:Templates generating hCards and Geo",
        "تصنيف:قوالب معلومات مباني",
        "تصنيف:قوالب بحقول إحداثيات",
        "تصنيف:قوالب لغة-س",
        "تصنيف:قوالب معلومات",
        "تصنيف:قوالب تستند على وحدات لوا",
        "تصنيف:قوالب تستخدم بيانات من ويكي بيانات",
        "تصنيف:قوالب تستخدم قالب بيانات القالب",
        "تصنيف:صفحات توضيح",
    }
)

FALSE_TEMPLATES: frozenset[str] = frozenset(
    {
        "شطب",
        "مقالات متعلقة",
        "بذرة",
        "ويكي بيانات",
        "تستند على",
    }
)

NO_TEMPLATES_AR: frozenset[str] = frozenset(
    {
        "تصنيف ويكيبيديا",
        "تحويل تصنيف",
        "تصنيف تتبع",
        "تصنيف تهذيب شهري",
        "تصنيف مخفي",
        "تصنيف بذرة",
        "تصنيف حاوية",
    }
)

SKIP_CATEGORIES: frozenset[str] = frozenset(
    {
        "تصنيف:أشخاص على قيد الحياة",
        "تصنيف:أشخاص أحياء",
    }
)

# Template replacement markers
TOSEARCH_AND_REPLACE: list[str] = [
    "{{توثيق شريط}}",
    "{{Navbox documentation}}",
]

TO_SEARCH: list[str] = [
    "{{#استدعاء:شريط|شريط",
]

PRE_TEXT: str = """{{صفحة توثيق فرعية}}

=== استعمال ===
{{نسخ:توثيق/مسبق/1|0}}
<!-- إن أردت توليد تلقائي لنموذج قالب فارغ لوسائط هذا القالب بإطار <pre></pre> قم بتحويل الرقم 0 إلى 1
{{نسخ:توثيق/مسبق/1| 0 }}
-->

=== مثال ===
{{توصيف
| <nowiki>
<!-- هنا المثال -->
</nowiki>
| <!-- هنا المثال -->
}}

== بيانات القالب==
{{رأس بيانات القالب}}
<div style="max-height:350px; width:100%; overflow:auto; padding:3px; border:solid 1px;">
<templatedata>
{
 "params": {},
 "format": "block"
}
</templatedata>
</div>

<includeonly>{{ملعب أخر||
<!-- [[تصنيف:قوالب ويكيبيديا]] -->

"""

# Default namespace lists for category member fetching
DEFAULT_MEMBER_NAMESPACES: frozenset[int] = frozenset({0, 14, 100})
STUB_MEMBER_NAMESPACES: frozenset[int] = frozenset({14})

# Collation mapping for Arabic sort
ARABIC_ALPHABET = " 0123456789آاأإبتثجحخدذرزسشصضطظعغفقكلمنهوي"

# Regex patterns for cross-wiki linker
QID_PATTERNS: list[str] = [
    r"Q\d+",
    r"wikidata\.org/wiki/(Q\d+)",
]

SKIP_ENCATS = [
    "Category:Invasions of Israel",
]

GLOBAL_FALSE_ENTEMPS = [
    "Hidden category",
    "Maintenance category",  # تصنيف صيانة
    "Wikipedia category",  # تصنيف ويكيبيديا
    "Sockpuppet",  #
    "Empty category",  # تصنيف فارغ
    "Possibly empty category",  # تصنيف فارغ
    "Tracking category",  # تصنيف تتبع
    "WPSS-cat",  # تصنيف مخفي
    "Monthly clean-up category",  # تصنيف مخفي
    "Category class",  # تصنيف مخفي
    "Hiddencat",  # تصنيف مخفي
    "Backlog subcategories",  #
    "Category redirect",
    "Stub Category",  # تصنيف بذرة
    # 'container category',      #تصنيف حاوية
]

NO_Templates_lower = [x.lower() for x in GLOBAL_FALSE_ENTEMPS]
