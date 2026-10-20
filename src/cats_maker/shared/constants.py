from __future__ import annotations

AR_CATEGORIES_TITLES_BLACKLIST = [
    "صفحات تحتوي رابط بمحتوى للمشتركين فقط",
    "صفحات بأخطاء في المراجع",
    "صفحات بمراجع لها معرف وثيقة رقمية ناقص",
    "صفحات بمراجع مكسورة",
    "صفحات بها أخطاء في المراجع",
    "صفحات تحتوي مراجع بوسائط زائدة",
    "صفحات تحتوي مراجع بوسائط غير مدعومة",
    "صفحات تحتوي مراجع بوسائط غير مسماه",
    "صفحات تحتوي مراجع بوسائط متجاهله",
    "صفحات تحتوي مراجع بوسائط متضاربة",
    "صفحات تحتوي مراجع تستخدم مصطلحات مترجمة دون الأصلية",
    "صفحات تحتوي مراجع تستخدم وصلات إنترويكي في العنوان",
    "صفحات تحتوي مراجع تستشهد بوصلات إنترويكي",
    "صفحات تحتوي مراجع ويب بتاريخ وصول وبدون رابط تشعبي",
    "صفحات تحتوي مراجع ويب بدون رابط تشعبي",
    "صفحات تحتوي مراجع ويب بدون عنوان",
    "صفحات تحتوي مراجع ويب برابط تشعبي فقير",
    "صفحات تحتوي مراجع ويب منسقة بدون رابط تشعبي",
    "صفحات تستخدم قالب معلومات شخص بحاجة لمراجعة",
    "صفحات تستخدم قالب:مراجع مع وسائط غير معروفة",
    "صفحات ذات مراجع DOI غير مكتملة",
    "صفحات برابط أرشيف خاطئ",
    "صفحات برابط تشعبي خاطئ",
    "صفحات تحتوي مراجع بالطريقة القديمة",
    "صفحات مع استشهادات فارغة",
    "صفحات تحتوي مراجع",
    "قالب أرشيف الإنترنت",
    "مقالة مع وصف قصير",
    "جميع المقالات التي في استشهاداتها وصلات عارية",
    "الإحداثيات في ويكي بيانات",
    "Articles with hAudio microformats",
    "مقالات تحتوي نصا ب",
    "صفحات بها مراجع ب",
    "صفحات بها عناوين ب",
    "صفحات بوصلات خارجية",
    "Pages using infobox",
    "Short description is",
    "Short description is different from Wikidata",
    "أخطاء الاستشهاد",
    "أخطاء CS1",
    "CS1:",
    "CS1 errors",
    "CS1 maint",
    "صيانة الاستشهاد",
    "صيانة CS1",
    "مقالات ذات روابط خارجية",
    "صفحات تستخدم خاصية P",
    "مقالات بحاجة لمصادر أكثر منذ",
    "مقالات سير شخصية بدون مصدر منذ",
    "سير شخصية غير موثقة منذ",
    "مقالات بحاجة لتحديد رقم صفحة المرجع منذ",
    "مقالات يتيمة منذ",
    "مقالات بحاجة لتدقيق خبير منذ",
    "مقالات بحاجة لمصادر أكثر منذ",
    "مقالات بدون مصدر منذ",
    "مقالات بها وصلات داخلية قليلة منذ",
    "مقالات ذات عبارات بحاجة لمصادر منذ",
    "مقالات ذات وصلات خارجية مكسورة منذ",
    "مقالات فيها ألفاظ تعظيم منذ",
    "مقالات فيها عبارات متقادمة منذ",
    "مقالات مختلف على صحتها منذ",
    "مقدمات مقالات بحاجة لتهذيب منذ",
    "مقالات ينقصها مصادر موثوقة منذ",
    "مقالات ينقصها استشهادات مضمنة منذ",
    "مقالات ويكيبيديا بمشاكل في الأسلوب منذ",
    "مقالات مطلوب توسيعها منذ",
    "مقالات مختلف على حياديتها منذ",
    "مقالات لا تحقق الملحوظية منذ",
    "مقالات فيها تعارض مصالح منذ",
    "مقالات غير متوازنة منذ",
    "مقالات طويلة منذ",
    "مقالات ربما تحتوي بحثا أصليا منذ",
    "مقالات بها وقت مبهم أو غير محدد منذ",
    "مقالات بها عبارات مبهمة منذ",
    "مقالات بها أقسام فارغة منذ",
    "مقالات بلهجة ترويجية منذ",
    "مقالات بحاجة للتوضيح منذ",
    "مقالات بحاجة للتحديث منذ",
    "مقالات بحاجة لسياق منذ",
    "مقالات بحاجة لتهذيب المصادر منذ",
    "مقالات بحاجة لتهذيب منذ",
    "مقالات بحاجة لتنظيف الوصلات الخارجية منذ",
    "مقالات بحاجة لإعادة الكتابة منذ",
    "قوائم غير مكتملة منذ",
    "قوالب مستغنى عنها منذ",
    "صور ملكية عامة منتجة من مستخدم منذ",
    "تصنيفات تهذيب منذ",
    "الاستشهاد بمصادر باللغة",
    "بذرة",
    "مقالات مع إتش كارد",
    "تصنيفات بذرة",
    "Templates generating hCards",
]

# Categories that should always be skipped
AR_CATEGORIES_SHOULD_SKIPPED = [
    "مقالات ويكيبيدية تضمن نصوصا من الطبعة العشرين لكتاب تشريح جرايز (1918)",
    "Webarchive template wayback links",
    "Templates generating hCalendars",
    "Templates generating hCards and Geo",
    "قوالب معلومات مباني",
    "قوالب بحقول إحداثيات",
    "قوالب لغة-س",
    "قوالب معلومات",
    "قوالب تستند على وحدات لوا",
    "قوالب تستخدم بيانات من ويكي بيانات",
    "قوالب تستخدم قالب بيانات القالب",
    "صفحات توضيح",
    "أشخاص على قيد الحياة",
    "أشخاص أحياء",
]

# Living people categories (used for filtering)
AR_CATEGORIES_SHOULD_SKIPPED_WITH_NS = [f"تصنيف:{x}" for x in AR_CATEGORIES_SHOULD_SKIPPED]


LIVING_PEOPLE_CATEGORIES = [
    "أشخاص على قيد الحياة",
    "أشخاص أحياء",
]

# False templates found on pages
AR_PAGE_FALSE_TEMPLATES = [
    "شطب",
    "مقالات متعلقة",
    "بذرة",
    "ويكي بيانات",
    "تستند على",
]

# Name blacklist (English category titles that should be ignored)
EN_CATEGORIES_TITLES_BLACKLIST = [
    "Current events",  # حدث جاري
    "Articles with",
    "Tracking",
    "articles",
    "Surnames",
    "Loanword",
    "Words and phrases",
    "Given names",
    "Human names",
    "stubs",  # بذرة
    "Nicknames",
]

# Namespace blacklist (only these namespaces are allowed)
ALLOWED_NAMESPACES = [0, 10, 14]

# Documentation / template related
TOSEARCH_AND_REPLACE = [
    "{{توثيق شريط}}",
    "{{Navbox documentation}}",
]

TO_SEARCH = [
    "{{#استدعاء:شريط|شريط",
]

EN_FALSE_TEMPLATES = [
    "Stub Category",  # تصنيف بذرة
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
    # 'container category',      #تصنيف حاوية
]
EN_FALSE_TEMPLATES_WITH_NS = [f"Template:{x}" for x in EN_FALSE_TEMPLATES]


# Templates that should be ignored on Arabic side
AR_FALSE_TEMPLATES = [
    "تصنيف ويكيبيديا",
    "تحويل تصنيف",
    "تصنيف تتبع",
    "تصنيف تهذيب شهري",
    "تصنيف مخفي",
    "تصنيف بذرة",
    "تصنيف حاوية",
    "delete",
    "حذف",
]

AR_FALSE_TEMPLATES_WITH_NS = [f"قالب:{x}" for x in AR_FALSE_TEMPLATES]

__all__ = [
    "ALLOWED_NAMESPACES",
    "AR_CATEGORIES_TITLES_BLACKLIST",
    "AR_FALSE_TEMPLATES",
    "AR_FALSE_TEMPLATES_WITH_NS",
    "AR_PAGE_FALSE_TEMPLATES",
    "AR_CATEGORIES_SHOULD_SKIPPED_WITH_NS",
    "AR_CATEGORIES_SHOULD_SKIPPED",
    "EN_FALSE_TEMPLATES",
    "EN_FALSE_TEMPLATES_WITH_NS",
    "EN_CATEGORIES_TITLES_BLACKLIST",
    "TO_SEARCH",
    "TOSEARCH_AND_REPLACE",
    "LIVING_PEOPLE_CATEGORIES",
]
