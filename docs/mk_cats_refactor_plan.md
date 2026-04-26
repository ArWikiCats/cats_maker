# mk_cats — Refactoring Plan

> Companion plan to `c18_new_master_refactoring_plan.md`.
> Applies the same principles — clean structure, phased execution, backward-compatible shims — to the `src/mk_cats` module.

---

## 1. Executive Summary

`src/mk_cats` drives Arabic Wikipedia category creation: given an English category, it resolves an Arabic label, collects members, creates the page, adds templates/portals/categories, then cross-links onto member pages. It works but carries technical debt:

| Issue                                                  | Location                         | Impact                                                     |
| ------------------------------------------------------ | -------------------------------- | ---------------------------------------------------------- |
| Typo in public API: `process_catagories` (missing `e`) | `mknew.py:337`, `__init__.py`    | Breaking rename needed                                     |
| Typo `lenth` → `length`                                | `mknew.py:337,379`               | Cosmetic but flagrant                                      |
| Typo `BBlcak` / `blcak_starts`                         | `utils/filter_en.py:9,17`        | Confusing naming                                           |
| Module-level mutable state leaks between runs          | `mknew.py:49-51`                 | State pollution across tests/calls                         |
| `make_ar` does everything (85 lines)                   | `mknew.py:249-334`               | Validates, checks WD, collects members, creates page, logs |
| `add_text_to_cat` does everything (65 lines)           | `create_category_page.py:63-129` | Adds cats, commons, portal, nav template in one function   |
| Inconsistent return types                              | Multiple                         | `False` vs `[]` vs `""` vs `None`                          |
| Hardcoded strings everywhere                           | All files                        | No `constants.py`                                          |
| `_get_page` caches page objects (LRU)                  | `add_bot.py:25-51`               | Dangerous for a live bot — stale page state                |
| Tests mutate module state directly                     | test_mknew.py                    | Fragile: `_done_d.clear()` before/after every test         |

**This plan reorganises the module in five sequential phases**, with the same shim pattern used in c18_new.

---

## 2. Non-Goals (Scope Guard)

-   No changes to filtering/sorting **behavior** — output must be identical
-   No changes to external API calls (`find_LCN`, `load_main_api`, `Get_Sitelinks_From_wikidata`, etc.)
-   No new CLI arguments or UI changes
-   No database schema changes

---

## 3. Proposed Directory Structure

```
src/mk_cats/
├── __init__.py                  # Public API; deprecation shims for renames
├── constants.py                 # All hardcoded strings, blacklists, config values
├── models.py                    # Dataclasses: CategoryResult (moved from create_category_page.py)
├── core/
│   ├── __init__.py
│   ├── category_pipeline.py     # create_categories_from_list, process_categories, make_ar
│   └── member_collector.py      # collect_category_members + helpers (from members_helper.py)
├── tools/
│   ├── __init__.py
│   ├── label_resolver.py        # ar_make_lab + resolve_arabic_category_label wrapper
│   ├── page_creator.py          # new_category, make_category, add_text_to_cat (from create_category_page.py)
│   ├── page_text.py             # generate_category_text, portal, commons (from categorytext.py)
│   └── page_updater.py          # add_to_final_list, add_to_page (from add_bot.py)
├── filters/
│   ├── __init__.py
│   ├── en_category.py           # filter_cat (was utils/filter_en.py)
│   └── en_template.py           # check_en_temps (was utils/check_en.py)
└── data/
    ├── __init__.py
    ├── portal_map.py             # portal_en_to_ar_lower (was utils/portal_list.py)
    └── category_mappings.py      # category_mapping, LocalLanguageLinks (was categorytext_data.py)
```

**Migration shim pattern** — old files become thin re-exporters with a deprecation warning:

```python
# src/mk_cats/mknew.py (legacy shim)
import warnings
warnings.warn("mk_cats.mknew is deprecated; use mk_cats.core.category_pipeline", DeprecationWarning, stacklevel=2)
from .core.category_pipeline import create_categories_from_list, process_categories, make_ar  # noqa: F401
from .tools.label_resolver import ar_make_lab  # noqa: F401
```

---

## 4. Quick Wins (Execute Before Any Phase)

-   [ ] Replace mutable `BBlcak` list with `tuple[str, ...]` — `filters/en_category.py`
-   [ ] Replace mutable `blcak_starts` list with `tuple[str, ...]` — `filters/en_category.py`
-   [ ] Replace `months` list created inside function with module-level `tuple` — `filters/en_category.py`
-   [ ] Remove `__pycache__` from version control and add to `.gitignore`
-   [ ] Add `__all__` to every `__init__.py` that lacks it

---

## 5. Detailed Phases

### Phase 1 — Code Hygiene

**Target:** All files in `mk_cats`.

**5.1.1 Create `constants.py`**

Centralise everything scattered across the module:

```python
from enum import IntEnum

class Namespace(IntEnum):
    MAIN = 0
    TEMPLATE = 10
    CATEGORY = 14
    PORTAL = 100

# Wiki site config
WIKI_SITE_AR = {"family": "wikipedia", "code": "ar"}
WIKI_SITE_EN = {"family": "wikipedia", "code": "en"}

# Category prefixes
CAT_PREFIX_AR = "تصنيف:"
CAT_PREFIX_EN = "Category:"
PORTAL_PREFIX_EN = "Portal:"

# Filter blacklists (immutable)
BLACKLIST_SUBSTRINGS: tuple[str, ...] = (     # was BBlcak
    "Disambiguation", "wikiproject", "sockpuppets",
    "without a source", "images for deletion",
)
BLACKLIST_PREFIXES: tuple[str, ...] = (        # was blcak_starts
    "Clean-up", "Cleanup", "Uncategorized", "Unreferenced",
    "Unverifiable", "Unverified", "Wikipedia", "Wikipedia articles",
    "Articles about", "Articles containing", "Articles covered",
    "Articles lacking", "Articles needing", "Articles prone",
    "Articles requiring", "Articles slanted", "Articles sourced",
    "Articles tagged", "Articles that", "Articles to", "Articles with",
    "use ", "User pages", "Userspace",
)
MONTH_NAMES: tuple[str, ...] = ("January", "February", ...)

# Label filters
BAD_WORDS: tuple[str, ...] = ("ذكور",)        # was bad_words in mknew.py

# Minimum members for category creation default
DEFAULT_MIN_MEMBERS: int = 5
DEFAULT_RANGE_LIMIT: int = 5
```

**Sources to consolidate:**

| Constant                           | Current location              |
| ---------------------------------- | ----------------------------- |
| `WIKI_SITE_AR`, `WIKI_SITE_EN`     | `mknew.py:54-55`              |
| `bad_words`                        | `mknew.py:59-61`              |
| `BBlcak`, `blcak_starts`, `months` | `utils/filter_en.py:9-72`     |
| `category_mapping`                 | `categorytext_data.py:3-21`   |
| `LocalLanguageLinks`               | `categorytext_data.py:23-246` |
| `New_Portal_List`                  | `utils/New_Portal_List.json`  |

**5.1.2 Rename all symbols to snake_case (PEP 8)**

| Old name                        | New name                  |
| ------------------------------- | ------------------------- |
| `process_catagories`            | `process_categories`      |
| `lenth` (parameter)             | `length`                  |
| `BBlcak`                        | `BLACKLIST_SUBSTRINGS`    |
| `blcak_starts`                  | `BLACKLIST_PREFIXES`      |
| `enca` (parameter)              | `en_title`                |
| `arlab` (parameter)             | `ar_label`                |
| `sugust` (parameter)            | `suggested_label`         |
| `labe` / `labb` (variable)      | `label`                   |
| `lilo` (variable)               | `portal_list`             |
| `litp` (variable)               | `portal_text`             |
| `Dont_add_to_pages_def`         | `get_dont_add_pages`      |
| `category_mapping`              | `CATEGORY_PORTAL_MAP`     |
| `LocalLanguageLinks`            | `LOCAL_LANGUAGE_LINKS`    |
| `New_Portal_List`               | `NEW_PORTAL_LIST`         |
| `portal_en_to_ar_lower`         | `PORTAL_EN_TO_AR`         |
| `MakeLitApiWay` (imported name) | keep as-is (external API) |

**5.1.3 Add type hints and normalize return types**

-   Add full type hints to all public functions
-   Replace every `return False` where a list or string is expected:
    -   `scan_ar_title` returns `bool` (correct)
    -   `check_if_artitle_exists` returns `bool` (correct)
    -   `make_ar` returns `list[str]` (currently returns `[]` consistently — good)
    -   `ar_make_lab` returns `str` (currently `""` on failure — good)
    -   `one_cat` returns `bool` (currently `False` — change to `False` → keep `bool`)
    -   `filter_cat` returns `bool` (currently `False`/`True` — correct)
    -   `check_en_temps` returns `bool` (correct)

**5.1.4 Encapsulate module-level state**

Replace raw module lists with a state class:

```python
# core/category_pipeline.py
@dataclass
class ProcessingState:
    done_titles: list[str] = field(default_factory=list)
    new_cat_attempts: dict[str, int] = field(default_factory=dict)
    already_created: list[str] = field(default_factory=list)

    def is_done(self, title: str) -> bool:
        return title in self.done_titles

    def mark_done(self, title: str) -> None:
        self.done_titles.append(title)

    def clear(self) -> None:
        self.done_titles.clear()
        self.new_cat_attempts.clear()
        self.already_created.clear()

# Thread-safe version uses threading.local if needed
_state = ProcessingState()

def get_state() -> ProcessingState:
    return _state

def clear_state() -> None:
    _state.clear()
```

**Success criteria:** All module-level variables (`_done_d`, `_new_cat_done`, `_already_created`) are encapsulated. `ruff check` and `mypy` pass on `src/mk_cats`.

---

### Phase 2 — Structural Split

**Target:** Decompose the two largest files.

**5.2.1 Split `mknew.py` (421 lines)**

Current responsibilities (all in one file):

1. `create_categories_from_list` — entry point, iterates list
2. `one_cat` — single-category orchestrator
3. `process_catagories` — recursive subcategory processor
4. `make_ar` — the big one: validate → WD check → members → create → log
5. `ar_make_lab` — Arabic label resolution
6. Helper functions: `scan_ar_title`, `check_if_artitle_exists`, `_normalize_en_page_title`, `_get_site_identifiers`, `_check_wikidata_sitelink`, `_extract_parent_categories`, `_finalize_category_creation`, `clear_processing_state`, `get_processing_state`

**Split plan:**

| New file                    | Functions moved                                                                                                                                                                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `core/category_pipeline.py` | `create_categories_from_list`, `one_cat`, `process_categories`, `make_ar`, `_normalize_en_page_title`, `_get_site_identifiers`, `_check_wikidata_sitelink`, `_extract_parent_categories`, `_finalize_category_creation`, `ProcessingState`, `get_state`, `clear_state` |
| `tools/label_resolver.py`   | `ar_make_lab`, `scan_ar_title`, `check_if_artitle_exists`, plus `resolve_arabic_category_label` wrapper                                                                                                                                                                |

**5.2.2 Split `create_category_page.py` (207 lines)**

| New file                | Functions moved                                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `tools/page_creator.py` | `new_category`, `make_category`, `add_text_to_cat`, `page_put`, `create_Page`, `CategoryResult`                                       |
| `tools/page_text.py`    | Functions from `categorytext.py`: `generate_category_text`, `generate_portal_content`, `fetch_commons_category`, `get_page_link_data` |

**5.2.3 Rename and move remaining files**

| Old file                     | New file                         | Notes                                                                   |
| ---------------------------- | -------------------------------- | ----------------------------------------------------------------------- |
| `members_helper.py`          | `core/member_collector.py`       | `collect_category_members` + helpers — already well factored            |
| `add_bot.py`                 | `tools/page_updater.py`          | `add_to_final_list`, `add_to_page`, `_get_page`, `add_text_to_articles` |
| `categorytext.py`            | Merged into `tools/page_text.py` | See 5.2.2                                                               |
| `categorytext_data.py`       | `data/category_mappings.py`      | Pure data                                                               |
| `utils/portal_list.py`       | `data/portal_map.py`             | JSON loading + dict building                                            |
| `utils/filter_en.py`         | `filters/en_category.py`         | `filter_cat`                                                            |
| `utils/check_en.py`          | `filters/en_template.py`         | `check_en_temps`                                                        |
| `utils/New_Portal_List.json` | `data/New_Portal_List.json`      | Kept as JSON asset                                                      |

**Success criteria:** All old paths importable via deprecation shims. All new paths work. Code volume stays same (pure restructuring).

---

### Phase 3 — Complexity Reduction

**5.3.1 Simplify `make_ar`**

Current flow (85 lines in one function): validation → scan → normalize → exists check → WD check → parent cats → members → min-members check → create page → finalize

Extract clear steps:

```python
def make_ar(en_title: str, ar_title: str, callback=None) -> list[str]:
    result = _validate_inputs(en_title, ar_title)
    if result is not None:
        return result

    en_title = _normalize_en_page_title(en_title)

    if not _check_arabic_not_exists(ar_title):
        return []

    ar_site_wiki, en_site_lang = _get_site_identifiers()
    has_ar_sitelink, ar_info = _check_wikidata_sitelink(en_site_lang, en_title, ar_site_wiki)
    if has_ar_sitelink:
        return []

    qid = ar_info.get("q", "")
    en_cats_of_new_cat, cats_of_new_cat = _extract_parent_categories(en_title)

    mark_created(ar_title)

    members = _gather_members(ar_title, en_title)
    if not members:
        return []

    page_result = _create_category_page(en_title, ar_title, cats_of_new_cat, qid)
    if not page_result.success:
        add_labels(qid, ar_title, "ar")
        return en_cats_of_new_cat

    return _finalize_creation(ar_title, en_title, qid, members, en_cats_of_new_cat, callback)
```

**5.3.2 Simplify `add_text_to_cat`**

Replace the sequential `if save:` chain with a loop over operations:

```python
_OPERATIONS: list[Callable] = [
    _add_parent_categories,
    _add_commons_template,
    _add_portal_template,
    _add_nav_template,
]

def add_text_to_cat(text, categories, en_title, title, qid, family=""):
    if family != "wikipedia" and family:
        return text
    new_text = text
    for operation in _OPERATIONS:
        new_text = operation(new_text, categories, en_title, title, qid)
    return new_text
```

**5.3.3 Fix `_get_page` LRU cache**

Replace `functools.lru_cache` with a simple instance check or remove caching entirely — a live bot should always fetch fresh page state:

```python
def _get_page(page_title: str):
    """No caching — always fetch fresh page state for a bot."""
    api = load_main_api("ar")
    page = api.MainPage(page_title)
    if not page.exists() or page.isRedirect() or page.isDisambiguation():
        return False
    if not page.get_text():
        return False
    if not page.can_edit(script="cat"):
        return False
    return page
```

**Success criteria:** `make_ar` ≤ 40 lines (down from 85). `add_text_to_cat` ≤ 25 lines (down from 65). Each extracted function has a single clear responsibility.

---

### Phase 4 — Structural Reorganization

Move code into the new directory layout from Section 3. Order:

| Step | Move                                                                      | Risk   |
| ---- | ------------------------------------------------------------------------- | ------ |
| 4.1  | `constants.py` + `models.py` (new files)                                  | None   |
| 4.2  | `data/` — `portal_map.py`, `category_mappings.py`, `New_Portal_List.json` | None   |
| 4.3  | `filters/` — `en_category.py`, `en_template.py`                           | Low    |
| 4.4  | `core/member_collector.py` (from `members_helper.py`)                     | Low    |
| 4.5  | `tools/label_resolver.py` (from `mknew.py` functions)                     | Low    |
| 4.6  | `tools/page_text.py` (from `categorytext.py`)                             | Low    |
| 4.7  | `tools/page_creator.py` (from `create_category_page.py`)                  | Medium |
| 4.8  | `tools/page_updater.py` (from `add_bot.py`)                               | Medium |
| 4.9  | `core/category_pipeline.py` (from `mknew.py` functions)                   | Medium |
| 4.10 | Add deprecation shims for all old file paths                              | Low    |

**`models.py` detail:**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CategoryResult:
    success: bool
    page_title: Optional[str] = None
    error_message: Optional[str] = None
```

**Success criteria:** All imports from old paths still work (with deprecation warnings). All new imports use clean paths. Integration test on a real category passes.

---

### Phase 5 — Testing & Validation

**5.5.1 Update existing tests**

Tests need updating to match the refactored structure:

-   Replace `from src.mk_cats.mknew import process_catagories` → `from src.mk_cats.core.category_pipeline import process_categories`
-   Remove module-level state manipulation (`_done_d.clear()` etc.) — use `clear_state()` instead
-   Fix assertions to use new function names

**5.5.2 Add missing unit tests**

| Function                   | Test cases                                                               |
| -------------------------- | ------------------------------------------------------------------------ |
| `filter_cat`               | Month regex patterns, case-insensitive prefix matching, caching behavior |
| `scan_ar_title`            | Already created, max retries exceeded (currently missing), new title     |
| `check_if_artitle_exists`  | Page exists, page doesn't exist, API error                               |
| `normalize_en_page_title`  | `[[brackets]]`, underscores, already clean                               |
| `_check_wikidata_sitelink` | Sitelink exists, no sitelink, no arwiki key, empty response              |
| `ProcessingState`          | Mark done, is done, clear, duplicate tracking                            |

**5.5.3 Integration tests**

Run the full pipeline before/after each phase:

```bash
python run.py -encat:Science 2>&1 | tee before_phase_N.txt
# ... apply changes ...
python run.py -encat:Science 2>&1 | tee after_phase_N.txt
diff before_phase_N.txt after_phase_N.txt   # must be empty
```

**Success criteria:** All existing tests pass with updated imports. `pytest tests/mk_cats/ --cov=src/mk_cats --cov-report=term-missing` shows ≥ 80% coverage.

---

## 6. Public API Changes

| Current public symbol                  | New canonical location                                       | Shim kept?        |
| -------------------------------------- | ------------------------------------------------------------ | ----------------- |
| `mk_cats.process_catagories`           | `mk_cats.core.category_pipeline.process_categories`          | Yes, 1 release    |
| `mk_cats.create_categories_from_list`  | `mk_cats.core.category_pipeline.create_categories_from_list` | Yes, 1 release    |
| `mk_cats.ar_make_lab`                  | `mk_cats.tools.label_resolver.ar_make_lab`                   | Yes, 1 release    |
| `mk_cats.make_category`                | `mk_cats.tools.page_creator.make_category`                   | Yes, 1 release    |
| `mk_cats.mknew.scan_ar_title`          | Not exported publicly — internal                             | No shim needed    |
| `mk_cats.mknew.clear_processing_state` | `category_pipeline.clear_state`                              | Via mknew.py shim |

---

## 7. Acceptance Criteria

-   [ ] `process_catagories` renamed to `process_categories`; old name works via deprecation shim
-   [ ] `lenth` → `length`, `BBlcak` → `BLACKLIST_SUBSTRINGS`, `blcak_starts` → `BLACKLIST_PREFIXES`
-   [ ] All hardcoded strings moved to `constants.py`
-   [ ] Module-level mutable state (`_done_d`, `_new_cat_done`, `_already_created`) encapsulated in `ProcessingState`
-   [ ] `_get_page` no longer uses `lru_cache`
-   [ ] `make_ar` broken into < 50 lines with extracted helper functions
-   [ ] `add_text_to_cat` uses an operation dispatch list
-   [ ] All old file paths remain importable with `DeprecationWarning`
-   [ ] `ruff check src/mk_cats` reports zero errors
-   [ ] `mypy src/mk_cats --ignore-missing-imports` passes
-   [ ] `pytest tests/mk_cats/` passes with ≥ 80% coverage
-   [ ] Integration diff on `Science` category is empty before → after

---

## 8. Risks & Mitigations

| Risk                                                        | Impact | Mitigation                                              |
| ----------------------------------------------------------- | ------ | ------------------------------------------------------- |
| Breaking imports in `src/__init__.py` or downstream callers | High   | Deprecation shims for one full release cycle            |
| `process_catagories` rename missed somewhere                | High   | grep for `catagor` across entire codebase               |
| Module state encapsulation changes test behavior            | Medium | Keep `clear_state()` as public API; update test cleanup |
| Behavior change from function extraction                    | Medium | Integration diff test before/after each phase           |
| JSON portal data path changes                               | Low    | Use `importlib.resources` or `__file__`-relative paths  |

---

## 9. Current vs. Target Structure

```
Current:                              Target:
src/mk_cats/                          src/mk_cats/
├── __init__.py                       ├── __init__.py          (shim)
├── mknew.py (421 lines)              ├── constants.py         (new)
├── members_helper.py                 ├── models.py            (new)
├── categorytext.py                   ├── core/
├── categorytext_data.py              │   ├── __init__.py
├── create_category_page.py           │   ├── category_pipeline.py
├── add_bot.py                        │   └── member_collector.py
├── utils/                            ├── tools/
│   ├── __init__.py                   │   ├── __init__.py
│   ├── filter_en.py                  │   ├── label_resolver.py
│   ├── check_en.py                   │   ├── page_creator.py
│   ├── portal_list.py                │   ├── page_text.py
│   └── New_Portal_List.json          │   └── page_updater.py
                                      ├── filters/
                                      │   ├── __init__.py
                                      │   ├── en_category.py
                                      │   └── en_template.py
                                      └── data/
                                          ├── __init__.py
                                          ├── portal_map.py
                                          ├── category_mappings.py
                                          └── New_Portal_List.json
```

---

_Plan created 2026-04-26. Follows the same methodology as `c18_new_master_refactoring_plan.md`._
