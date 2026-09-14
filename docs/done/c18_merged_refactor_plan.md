# c18 — Merged Refactoring Plan (b18 + c18)

> **Status:** `src/core/b18` has been merged into `src/core/c18`.
> This plan supersedes `b18_new_refactor_plan.md` and `c18_new_refactor_plan.md`.
> _Synthesized 2026-04-27_

---

## 1. Executive Summary

The unified `src/core/c18` module now drives Arabic Wikipedia category generation, cross-wiki page linking (EN→AR, FR→AR), template handling, filtering/sorting, **and** the former `b18` responsibilities:

-   Resolving English/French category members into Arabic page titles (via SQL or API)
-   Validating Arabic/English category pairs before creation
-   Gathering page lists for new category population
-   Member listing & cache management

Technical debt inherited from both modules:

-   **Inconsistent naming** — `MakeLitApiWay`, `get_listenpageTitle`, `typee`, `lenth` typo (from b18); `categorized_page_generator`, `Dont_add_to_pages_def` (from c18)
-   **Massive string-cleaning duplication** — every file manually strips `Category:`, `تصنيف:`, `[[`, `]]`, and swaps `_` / ` `
-   **Mixed responsibilities** — SQL query strings, API fallback logic, and parameter sanitization live in the same file (`sql_cat.py`)
-   **Poor return types** — `MakeLitApiWay` returns `False` instead of `[]`; `get_ar_list_from_encat` returns a `dict` when callers expect a list; c18 functions return `False` vs `""` vs `None`
-   **Global mutable state** — `pages_in_arcat_toMake` in `cat_tools_enlist.py` (b18); mutable `tatone_ns` and `Skippe_Cat` (c18)
-   **Duplicated validation logic** — `check_category_status` and `check_arabic_category_status` in `sql_cat_checker.py` are mirror images
-   **Near-complete duplication** between `ar_from_en.py` and `ar_from_en2.py` (c18)
-   **`filter_cats_text`** — O(n²) list mutation, 140+ lines, high cyclomatic complexity (c18)
-   **Weak type hints** — most signatures are untyped or use bare `list` instead of `list[str]`

---

## 2. Non-Goals (Scope Guard)

These are explicitly out of scope to protect business logic stability:

-   Changing filtering or sorting **behavior** — output must be pixel-for-pixel identical
-   Rewriting external API wrappers (`find_lcn`, `load_main_api`, etc.)
-   Introducing new CLI arguments or UI changes
-   Switching databases or changing SQL schemas

---

## 3. Proposed Directory Structure

```
src/core/c18/
├── __init__.py                  # Export only the public interface; add __all__
├── constants.py                 # All magic strings, namespace IDs, template names (merged b18 + c18)
├── models.py                    # Lightweight dataclasses: WikiPage, Category, Sitelink, ValidationResult
├── core/
│   ├── __init__.py
│   ├── category_generator.py    # Merged cat_tools2 + ar_from_en2 logic
│   ├── cross_wiki_linker.py     # Refactored english_page_title.py
│   ├── category_filter.py       # Refactored filter_cat.py + predicates
│   ├── category_resolver.py     # MERGED from former b18: sql_cat.py + cat_tools_enlist2.py
│   ├── member_lister.py         # MERGED from former b18: cat_tools_enlist.py
│   └── category_validator.py    # MERGED from former b18: sql_cat_checker.py
├── tools/
│   ├── __init__.py
│   ├── sort.py                  # Refactored sort_bot.py
│   ├── template_query.py        # Refactored temp_bot.py
│   └── doc_handler.py           # Refactored text_to_temp_bot.py
├── io/
│   ├── __init__.py
│   ├── json_store.py            # File I/O only (was dontadd.py)
│   └── sql_queries.py           # Pure SQL query functions (merged b18 + c18 SQL strings)
└── utils/
    ├── __init__.py
    └── text.py                  # Shared helpers: clean_category_input, extract_wikidata_qid, normalize_category_title
```

**Migration shim pattern** — old files become thin re-exporters with a deprecation warning, kept for one release cycle before deletion:

```python
# bots/filter_cat.py (legacy shim)
import warnings
warnings.warn("bots.filter_cat is deprecated; import from core.category_filter", DeprecationWarning)
from ..core.category_filter import filter_category_text as filter_cats_text  # noqa: F401
```

---

## 4. Quick Wins (Execute Before Any Phase)

Zero-risk changes that can be done in a single PR right now across the merged codebase:

-   [ ] Replace mutable `tatone_ns` list with `frozenset`
-   [ ] Replace mutable `Skippe_Cat` list with `tuple`
-   [ ] Replace `page_false_templates.remove("بذرة")` (import-time mutation) with conditional logic inside the function body
-   [ ] Remove `__pycache__` from version control and add to `.gitignore`
-   [ ] Add `__all__` to every `__init__.py` that lacks it
-   [ ] Rename all camelCase symbols in former b18 code to `snake_case`:
    -   `MakeLitApiWay` → `make_lit_api_way` (or merge into `resolve_via_api`)
    -   `get_listenpageTitle` → `get_listen_page_title`
-   [ ] Fix typos: `lenth` → `length`, `typee` → `item_type` or `member_type`, `sito_code` → `site_code`

---

## 5. Detailed Phases

### Phase 1 — Code Hygiene (Week 1)

**Target:** All files in the merged `c18`.

**Tasks:**

**5.1.1 Create unified `constants.py`**

Centralise everything that is currently scattered across the former b18 and c18 files:

```python
from enum import IntEnum

class Namespace(IntEnum):
    MAIN     = 0
    TEMPLATE = 10
    CATEGORY = 14
    PORTAL   = 100

# Prefixes
CAT_PREFIX_AR = "تصنيف:"
CAT_PREFIX_EN = "Category:"
CAT_PREFIX_FR = "Catégorie:"

# Blacklists (immutable)
SKIPPED_CATEGORIES: frozenset[str] = frozenset({...})   # was Skippe_Cat
FALSE_TEMPLATES:    frozenset[str] = frozenset({...})   # was page_false_templates
NO_TEMPLATES_AR:    frozenset[str] = frozenset({...})   # was NO_Templates_ar
SKIP_CATEGORIES:    frozenset[str] = frozenset({...})   # was temp_bot.SKIP_CATEGORIES

# Template replacement maps
TOSEARCH_AND_REPLACE: dict[str, str] = {...}            # was tosearch_and_replace
TO_SEARCH: list[str]                  = [...]           # was to_search
PRE_TEXT: str                         = "..."           # was pre_text
```

Sources to consolidate:

-   `tatone_ns` from `cat_tools2.py`
-   `Skippe_Cat`, `page_false_templates` from `filter_cat.py`
-   `NO_Templates_ar` / `NO_Templates_lower` from `sql_cat_checker.py`
-   `SKIP_CATEGORIES` from `temp_bot.py`
-   `tosearch_and_replace`, `to_search`, `pre_text` from `text_to_temp_bot.py`
-   `namespace_ids` from `ar_from_en2.py`

**5.1.2 Rename all symbols to snake_case (PEP 8)**

| Old name                     | New name                     | Source |
| ---------------------------- | ---------------------------- | ------ |
| `MakeLitApiWay`              | `make_lit_api_way`           | b18    |
| `get_listenpageTitle`        | `get_listen_page_title`      | b18    |
| `categorized_page_generator` | `generate_categorized_pages` | c18    |
| `Dont_add_to_pages_def`      | `get_dont_add_pages`         | c18    |
| `get_ar_list_from_en_list`   | `get_ar_list_from_en_list`   | c18    |
| `english_page_link_from_api` | `_resolve_page_link_via_api` | c18    |
| `filter_cats_text`           | `filter_category_text`       | c18    |

**5.1.3 Add type hints and normalize return types**

-   Add `list[str]`, `str | None`, `dict[str, Any]` to all public signatures.
-   Replace every `return False` where a list or string is expected with `return []` or `return None`.
-   Standardize `english_page_link` family and b18 resolver family to return `list[str]` or `str | None` consistently.

**Success criteria:** `ruff check src/core/c18` and `mypy src/core/c18 --ignore-missing-imports` pass with zero errors.

---

### Phase 2 — Deduplication (Week 2)

**Target:** Remove the two largest sources of duplication.

**5.2.1 Merge `ar_from_en.py` + `ar_from_en2.py` → `core/category_generator.py`**

The two files differ only in wiki source (`en` vs `fr`) and minor variable names. Merge into a single parameterised module:

```python
def fetch_category_members(
    title: str,
    wiki: str = "en",
    namespaces: list[int] | None = None,
) -> list[str]:
    """Fetch category members from any source wiki."""
    ...

def translate_titles_to_ar(
    titles: list[str],
    source_wiki: str = "en",
    batch_size: int = 50,
) -> list[str]:
    """Batch-translate page titles from source_wiki to Arabic via langlinks."""
    ...
```

Also merge `get_ar_list_from_en_list` and `get_ar_list_title_from_en_list` into `translate_titles_to_ar`. Extract `clean_category_input` into `utils/text.py`.

Delete `ar_from_en2.py`. Leave `ar_from_en.py` as a shim for one release.

**5.2.2 Merge former b18 resolution logic → `core/category_resolver.py` + `io/`**

`sql_cat.py` (SQL-centric) and `cat_tools_enlist2.py` (API-centric) both resolve EN→AR category members. Unify under `core/category_resolver.py`:

```python
class CategoryResolver:
    def __init__(self, backend: str = "auto") -> None: ...

    def resolve_members(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]: ...
    def list_ar_pages_in_cat(self, ar_title: str) -> list[str]: ...
    def list_en_pages_with_ar_links(self, en_title: str, wiki: str = "en") -> list[str]: ...
    def diff_missing_ar_pages(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]: ...
```

-   Move `get_ar_list`, `get_ar_list_from_en`, `do_sql`, `make_ar_list_newcat2` into this module.
-   Move `get_ar_list_from_encat`, `MakeLitApiWay` into the same resolver as API-based methods.
-   **Standardize return types** — always return `list[str]`, never `False` or `{}`.
-   Remove the `us_sql` boolean flag from public APIs; let the resolver decide based on availability.

Move all raw SQL strings into `io/sql_queries.py`. Keep API fallback wrappers in `io/api_fallback.py`.

**5.2.3 Merge `templatequery` + `templatequerymulti` → `tools/template_query.py`**

Make `templatequery` a thin wrapper instead of a near-duplicate:

```python
def get_templates(
    titles: str | list[str],
    sitecode: str = "ar",
) -> dict[str, list[str]] | list[str] | None:
    """Single entry point. Pass a string for one title, list for batch."""
    if isinstance(titles, str):
        result = _query_multi(titles, sitecode)
        if not result:
            return None
        return result.get(titles, {}).get("templates")
    return _query_multi("|".join(titles), sitecode)

class TemplateCache:
    """Encapsulates the module-level defaultdict. Key: f'{sitecode}:{title}'."""
    ...
```

**Success criteria:** Code volume in `c18` drops by 15–20% with no functional difference. Verify with an integration run on a real category (e.g., `Science`) before and after.

---

### Phase 3 — Complexity Reduction (Week 3)

**Target:** The three highest-complexity functions, plus former b18 validators.

**5.3.1 Refactor `filter_cats_text` → `core/category_filter.py`**

Current issues: 140-line function, O(n²) list removal during iteration, mutable global lists, high cyclomatic complexity.

Extract each rule into a standalone predicate:

```python
def is_template_category(cat: str, ns: int) -> bool: ...
def is_deleted_category(cat: str, deleted: set[str]) -> bool: ...
def has_false_template(cat: str, false_templates: frozenset[str]) -> bool: ...
def is_already_in_text(cat: str, text: str) -> bool: ...
def is_blacklisted(cat: str) -> bool: ...
```

Replace in-place mutation with building a new list (changes O(n²) to O(n)):

```python
def filter_category_text(
    cats: list[str],
    ns: int,
    text: str,
    *,
    deleted: set[str] | None = None,
) -> list[str]:
    """Pure function — returns a new list, never mutates input."""
    if deleted is None:
        deleted = set(get_dont_add_pages())
    false_temps = FALSE_TEMPLATES
    templates_map = get_templates(cats, "ar") or {}

    return [
        cat for cat in cats
        if not _should_exclude(cat, ns, text, deleted, false_temps, templates_map)
    ]
```

**5.3.2 Break down `english_page_title.py` → `core/cross_wiki_linker.py`**

Split the 80-line `english_page_link_from_api` into:

```python
def resolve_via_wikidata(text: str) -> str | None: ...
def resolve_via_api(link: str, source: str, target: str) -> str | None: ...
def get_page_link(link: str, ...) -> str | None:   # thin orchestrator
    return resolve_via_wikidata(link) or resolve_via_api(link, ...)
```

Extract all regex patterns into named constants at the top of the file:

```python
QID_PATTERNS = [
    re.compile(r"Q\d+"),
    re.compile(r"wikidata\.org/wiki/(Q\d+)"),
]
```

Move `extract_wikidata_qid` into `utils/text.py`.

**5.3.3 Replace sorting algorithm in `tools/sort.py`**

Replace the character-substitution trick with a named key function:

```python
_ARABIC_COLLATION = str.maketrans({
    'آ': '02', 'ا': '03', 'أ': '04',  # ... full mapping
})

def arabic_sort_key(text: str) -> str:
    """
    Custom collation key for Arabic Wikipedia category sorting.
    Maps Arabic characters to digit sequences that sort in the desired
    alphabetical order. Upgrade to pyicu if available.
    """
    return text.translate(_ARABIC_COLLATION)

def sort_categories(categories: list[str]) -> list[str]:
    return sorted(categories, key=arabic_sort_key)
```

**5.3.4 Clean up `text_to_temp_bot.py` → `tools/doc_handler.py`**

Replace the long `elif` chain in `add_direct` with a dispatch map:

```python
INSERTION_MARKERS = [
    ("{{توثيق",        _insert_before_tag),
    ("{{توثيق شريط}}", _insert_before_tag),
    # ...
]

def add_direct(text: str, content: str) -> str:
    for marker, handler in INSERTION_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            return handler(text, content, idx)
    return text + content
```

Move `pre_text` into a separate `.txt` asset or clearly named constant. Use `wikitextparser` consistently instead of mixing it with `str.find`.

**5.3.5 Refactor former b18 validator → `core/category_validator.py`**

`sql_cat_checker.py` has two nearly identical functions (`check_category_status`, `check_arabic_category_status`) with inverted logic.

-   Merge both into a single `CategoryValidator` class or a set of pure functions.
-   Extract a generic `_check_page_status(site: str, title: str, expected_langlink: str | None)` helper.
-   Convert template blacklisting into a predicate:
    ```python
    def is_blacklisted_template(template: str, lang: str = "ar") -> bool: ...
    ```
-   **Standardize return type** to a `ValidationResult` dataclass instead of bare `bool`:
    ```python
    @dataclass
    class ValidationResult:
        valid: bool
        reason: str | None = None
    ```

**5.3.6 Refactor former b18 member lister → `core/member_lister.py`**

`cat_tools_enlist.py` mixes SQL fallback logic, validation calls, and a global cache dict.

-   Replace the module-level `pages_in_arcat_toMake: dict` with an explicit `MemberCache` dataclass or pass it as a parameter.
-   Rename `get_listenpageTitle` → `get_listen_page_title` (or `resolve_listen_pages`) and `extract_fan_page_titles` → `extract_fan_page_titles`.
-   Move the orchestration logic (SQL → API → cache) into a thin `MemberLister` class.
-   Remove the direct dependency on `settings.database.use_sql` by delegating to `CategoryResolver`.

**Success criteria:** `radon cc src/core/c18 -s` shows the top 5 functions have dropped from grade C/D to grade A/B (cyclomatic complexity ≤ 10).

---

### Phase 4 — Structural Reorganization (Week 4)

Move all code into the new directory layout from Section 3. Use the shim pattern for all moved modules. Order of moves (lowest risk first):

| Step | Move                                                                        | Risk   |
| ---- | --------------------------------------------------------------------------- | ------ |
| 4.1  | `constants.py` + `utils/text.py` (already done in Phase 1)                  | None   |
| 4.2  | `dontadd.py` → `io/json_store.py` + `io/sql_queries.py`                     | Low    |
| 4.3  | `cat_tools2.py` + `ar_from_en.py` → `core/category_generator.py`            | Medium |
| 4.4  | `english_page_title.py` → `core/cross_wiki_linker.py`                       | Medium |
| 4.5  | `filter_cat.py` → `core/category_filter.py`                                 | Medium |
| 4.6  | `temp_bot.py` → `tools/template_query.py`                                   | Low    |
| 4.7  | `sort_bot.py` → `tools/sort.py`                                             | Low    |
| 4.8  | `text_to_temp_bot.py` → `tools/doc_handler.py`                              | Medium |
| 4.9  | `sql_cat.py` + `cat_tools_enlist2.py` → `core/category_resolver.py` + `io/` | High   |
| 4.10 | `cat_tools_enlist.py` → `core/member_lister.py`                             | Medium |
| 4.11 | `sql_cat_checker.py` → `core/category_validator.py`                         | Medium |
| 4.12 | Add `models.py` and wire into all modules                                   | Low    |

**`io/` split detail** — `dontadd.py` currently mixes four concerns:

```python
# io/json_store.py
class JsonStore:
    def __init__(self, path: Path): ...
    def load(self) -> dict: ...
    def save(self, data: dict) -> None: ...
    def is_stale(self, days: int = 1) -> bool: ...

# io/sql_queries.py
def fetch_dont_add_pages() -> list[str]:
    """Pure SQL — no file logic, no caching."""
    ...
```

Replace broad `except Exception` with specific exceptions (`PermissionError`, `json.JSONDecodeError`, `sqlite3.Error`). Use `pathlib` consistently.

**`models.py` detail:**

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class CategoryRef:
    title: str          # normalized, no prefix
    lang: str           # "ar", "en", "fr"

@dataclass
class PageRef:
    title: str
    namespace: int
    langlinks: dict[str, str]

@dataclass
class WikiPage:
    title: str
    namespace: int
    langlinks: dict[str, str] = field(default_factory=dict)

@dataclass
class Category:
    title: str
    templates: list[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    valid: bool
    reason: str | None = None
```

**Success criteria:** All imports from old paths still work (with deprecation warnings). All new imports use the clean paths. Integration test on a real category passes.

---

### Phase 5 — Testing & Validation (Week 5)

**Unit tests** — one test file per new module, in `tests/c18/`:

| Function                                 | Test cases                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------- |
| `clean_category_input`                   | Prefix stripping, empty string, no-op                                     |
| `filter_category_text`                   | Each predicate: template cat, deleted, blacklisted, already-in-text       |
| `arabic_sort_key`                        | Known character ordering, ties, mixed scripts                             |
| `extract_wikidata_qid`                   | Valid QID, bare Q-number, no match → None                                 |
| `add_direct`                             | Each insertion marker, no-marker fallback                                 |
| `JsonStore.is_stale`                     | Fresh file, 2-day-old file                                                |
| `normalize_category_title`               | Duplicate prefixes, mixed `[[`, `_`, spaces (from former b18)             |
| `CategoryResolver.diff_missing_ar_pages` | Mocked SQL and API backends (from former b18)                             |
| `CategoryValidator`                      | Rule matrix: redirect, missing, mismatched langlink, blacklisted template |
| `MemberLister`                           | Cache behavior and deduplication (from former b18)                        |

**Integration tests** — run the full pipeline before and after each phase:

```bash
python run.py -encat:Science 2>&1 | tee before_phase_N.txt
# ... apply changes ...
python run.py -encat:Science 2>&1 | tee after_phase_N.txt
diff before_phase_N.txt after_phase_N.txt   # must be empty
```

**Performance benchmark** — `filter_category_text` on a 1,000-item list:

```python
import timeit
timeit.timeit(lambda: filter_category_text(big_list, ns=14, text=""), number=100)
```

Expected: ≥ 30% speedup from O(n²) → O(n).

**Test migration note:** Existing tests in `tests/b18_new/` should be moved into `tests/c18/` (or merged into the relevant `test_*.py` files) as part of this phase.

**CI/CD:** `pytest tests/c18/ --cov=src/core/c18 --cov-report=term-missing` must show ≥ 80% coverage in GitHub Actions.

---

## 6. Risks & Mitigations

| Risk                                                  | Impact | Mitigation                                                                              |
| ----------------------------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| Breaking imports in `mk_cats` or downstream consumers | High   | Deprecation shims for one full release cycle                                            |
| Filtering behavior change due to predicate reordering | High   | Integration diff test on real category before/after each phase                          |
| Performance regression from new-list building         | Low    | Benchmark; new-list is almost always faster than repeated `list.remove()`               |
| Losing logging context when splitting large functions | Low    | Keep `logger.info/debug` in top-level orchestrators, not in predicates                  |
| Cache invalidation bugs in `TemplateCache`            | Medium | Unit-test cache key scheme and TTL boundary explicitly                                  |
| SQL query regressions from namespace refactoring      | Low    | Add integration test that executes queries against a read-only replica or mocked cursor |
| Losing `pages_in_arcat_toMake` cache behavior         | Low    | Explicitly pass cache dict into `MemberLister` so callers retain control                |

---

## 7. Acceptance Criteria

-   [ ] No camelCase function names remain anywhere in `c18`
-   [ ] `ar_from_en2.py` deleted; its logic lives in `core/category_generator.py`
-   [ ] All hardcoded namespace IDs, template names, and category strings imported from `constants.py`
-   [ ] `filter_category_text` is a pure function — never mutates its input
-   [ ] `english_page_link` family returns `str | None` consistently — no `False`, no `""`
-   [ ] `dontadd.py` split into `io/json_store.py` and `io/sql_queries.py`
-   [ ] `CategoryResolver` and `CategoryValidator` return typed results consistently — no `False`, no `{}`
-   [ ] `pages_in_arcat_toMake` is no longer a module-level mutable dict
-   [ ] All category-title normalization uses `utils/text.py` — no inline `.replace(...)` chains
-   [ ] `sql_cat_checker.py` duplication is eliminated; a single generic checker handles both EN and AR pages
-   [ ] `pytest tests/c18/` passes with ≥ 80% coverage
-   [ ] `ruff check src/core/c18` reports zero errors
-   [ ] `radon cc src/core/c18 -s` shows no function above grade B (complexity ≤ 10)
-   [ ] Integration diff on `Science` category is empty before → after

---

## 8. What Each Original Plan Contributed

| Element                                                          | Source            |
| ---------------------------------------------------------------- | ----------------- |
| Clean directory structure (`core/`, `tools/`, `io/`, `utils/`)   | c18 plan (Plan A) |
| Concrete API function signatures                                 | c18 plan (Plan A) |
| `Namespace` IntEnum                                              | c18 plan (Plan A) |
| Phased timeline with explicit success criteria                   | c18 plan (Plan B) |
| Non-goals / scope guard                                          | c18 plan (Plan B) |
| Quick-wins checklist                                             | c18 plan (Plan B) |
| Risk/mitigation table                                            | c18 plan (Plan B) |
| Integration diff test strategy                                   | c18 plan (Plan B) |
| Performance benchmark requirement                                | c18 plan (Plan B) |
| Deprecation shim migration pattern                               | c18 plan (Plan B) |
| `CategoryResolver`, `MemberLister`, `CategoryValidator` design   | b18 plan          |
| `ValidationResult` dataclass                                     | b18 plan          |
| SQL/API return-type standardization (`list[str]`, never `False`) | b18 plan          |
| `normalize_category_title()` helper spec                         | b18 plan          |

---

_Plan merged 2026-04-27. Replaces `b18_new_refactor_plan.md` and `c18_new_refactor_plan.md`._
