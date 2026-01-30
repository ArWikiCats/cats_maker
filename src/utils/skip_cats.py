""" """

from ..config import settings

# ---
skip_encats = [
    "Category:Invasions of Israel",
]

global_False_entemps = [
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
# ---
if settings.category.stubs:
    global_False_entemps.remove("Hiddencat")
    global_False_entemps.remove("WPSS-cat")
    global_False_entemps.remove("Stub Category")


NO_Templates_lower = [x.lower() for x in global_False_entemps]
