# c18_new — Master Refactoring Plan

> Synthesized from two prior plans. Combines Plan A's clean directory structure and concrete API
> sketches with Plan B's phased process discipline, quick-wins, and risk mitigations.

---

## 1. Executive Summary

The `src/c18_new` module drives Arabic Wikipedia category generation, cross-wiki page linking
(EN→AR, FR→AR), template handling, and filtering/sorting. It works, but carries visible
technical debt:

-   Near-complete duplication between `ar_from_en.py` and `ar_from_en2.py`
-   Tight coupling between I/O, SQL, caching, and business logic
-   Magic numbers and hardcoded strings scattered across 7+ files
-   `filter_cats_text` — O(n²) list mutation, 140+ lines, high cyclomatic complexity
-   Inconsistent return types (`False` vs `""` vs `list` vs `None`)
-   camelCase function names, typos, no type hints

This plan reorganises the module in five sequential phases, with backward-compatible shims
so nothing breaks between releases.

---

## 2. Non-Goals (Scope Guard)

These are explicitly out of scope to protect business logic stability:

-   Changing filtering or sorting **behavior** — output must be pixel-for-pixel identical
-   Rewriting external API wrappers (`find_LCN`, `load_main_api`, etc.)
-   Introducing new CLI arguments or UI changes
-   Switching databases or changing SQL schemas

---

## 3. Proposed Directory Structure

```
src/c18_new/
├── __init__.py                  # Export only the public interface; add __all__
├── constants.py                 # All magic strings, namespace IDs, template names
├── models.py                    # Lightweight dataclasses: WikiPage, Category, Sitelink
├── core/
│   ├── __init__.py
│   ├── category_generator.py    # Merged cat_tools2 + ar_from_en2 logic
│   ├── cross_wiki_linker.py     # Refactored english_page_title.py
│   └── category_filter.py       # Refactored filter_cat.py + predicates
├── tools/
│   ├── __init__.py
│   ├── sort.py                  # Refactored sort_bot.py
│   ├── template_query.py        # Refactored temp_bot.py
│   └── doc_handler.py           # Refactored text_to_temp_bot.py
├── io/
│   ├── __init__.py
│   ├── json_store.py            # File I/O only (was dontadd.py)
│   └── sql_queries.py           # SQL queries only (was dontadd.py)
└── utils/
    ├── __init__.py
    └── text.py                  # Shared helpers: clean_category_input, extract_wikidata_qid
```

**Migration shim pattern** — old files become thin re-exporters with a deprecation warning,
kept for one release cycle before deletion:

```python
# bots/filter_cat.py (legacy shim)
import warnings
warnings.warn("bots.filter_cat is deprecated; import from core.category_filter", DeprecationWarning)
from ..core.category_filter import filter_category_text as filter_cats_text  # noqa: F401
```

---

## 4. Quick Wins (Execute Before Any Phase)

These are zero-risk and can be done in a single PR right now:

-   [ ] Replace mutable `tatone_ns` list with `frozenset`
-   [ ] Replace mutable `Skippe_Cat` list with `tuple`
-   [ ] Replace `page_false_templates.remove("بذرة")` (import-time mutation) with conditional
        logic inside the function body
-   [ ] Remove `__pycache__` from version control and add to `.gitignore`
-   [ ] Add `__all__` to every `__init__.py` that lacks it

---

## 5. Detailed Phases

### Phase 1 — Code Hygiene (Week 1)

**Target:** All files in `c18_new`.

**Tasks:**

**5.1.1 Create `constants.py`**

Centralise everything that is currently scattered across 7 files:

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

# Blacklists (immutable)
SKIPPED_CATEGORIES: frozenset[str] = frozenset({...})   # was Skippe_Cat
FALSE_TEMPLATES:    frozenset[str] = frozenset({...})   # was page_false_templates
SKIP_CATEGORIES:    frozenset[str] = frozenset({...})   # was temp_bot.SKIP_CATEGORIES

# Template replacement maps
TOSEARCH_AND_REPLACE: dict[str, str] = {...}            # was tosearch_and_replace
TO_SEARCH: list[str]                  = [...]           # was to_search
PRE_TEXT: str                         = "..."           # was pre_text
```

Sources to consolidate:

-   `tatone_ns` from `cat_tools2.py`
-   `Skippe_Cat`, `page_false_templates` from `filter_cat.py`
-   `SKIP_CATEGORIES` from `temp_bot.py`
-   `tosearch_and_replace`, `to_search`, `pre_text` from `text_to_temp_bot.py`
-   `namespace_ids` from `ar_from_en2.py`

**5.1.2 Rename all symbols to snake_case (PEP 8)**

| Old name                     | New name                     |
| ---------------------------- | ---------------------------- |
| `Categorized_Page_Generator` | `generate_categorized_pages` |
| `Dont_add_to_pages_def`      | `get_dont_add_pages`         |
| `Get_ar_list_from_en_list`   | `get_ar_list_from_en_list`   |
| `english_page_link_from_api` | `_resolve_page_link_via_api` |
| `filter_cats_text`           | `filter_category_text`       |

Fix typos: `Skippe_Cat` → `skipped_categories`, `lenth` → `length`, `sito_code` → `site_code`.

**5.1.3 Add type hints and normalize return types**

-   Add `list[str]`, `str | None`, `dict[str, Any]` to all public signatures.
-   Replace every `return False` where a list or string is expected with `return []` or `return None`.
-   Standardize `english_page_link` family to return `str | None` consistently.

**Success criteria:** `ruff check src/c18_new` and `mypy src/c18_new --ignore-missing-imports`
pass with zero errors.

---

### Phase 2 — Deduplication (Week 2)

**Target:** Remove the two largest sources of duplication.

**5.2.1 Merge `ar_from_en.py` + `ar_from_en2.py` → `core/category_generator.py`**

The two files differ only in wiki source (`en` vs `fr`) and minor variable names. Merge into
a single parameterised module:

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

Also merge `Get_ar_list_from_en_list` and `get_ar_list_title_from_en_list` into
`translate_titles_to_ar`. Extract `clean_category_input` into `utils/text.py`.

Delete `ar_from_en2.py`. Leave `ar_from_en.py` as a shim for one release.

**5.2.2 Merge `templatequery` + `templatequerymulti` → `tools/template_query.py`**

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

**Success criteria:** Code volume in `c18_new` drops by 15–20% with no functional difference.
Verify with an integration run on a real category (e.g., `Science`) before and after.

---

### Phase 3 — Complexity Reduction (Week 3)

**Target:** The three highest-complexity functions.

**5.3.1 Refactor `filter_cats_text` → `core/category_filter.py`**

Current issues: 140-line function, O(n²) list removal during iteration, mutable global
lists, high cyclomatic complexity.

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

Move `pre_text` into a separate `.txt` asset or clearly named constant. Use
`wikitextparser` consistently instead of mixing it with `str.find`.

**Success criteria:** `radon cc src/c18_new -s` shows the top 3 functions have dropped from
grade C/D to grade A/B (cyclomatic complexity ≤ 10).

---

### Phase 4 — Structural Reorganization (Week 4)

Move code into the new directory layout from Section 3. Use the shim pattern for all
moved modules. Order of moves (lowest risk first):

| Step | Move                                                             | Risk   |
| ---- | ---------------------------------------------------------------- | ------ |
| 4.1  | `constants.py` + `utils/text.py` (already done in Phase 1)       | None   |
| 4.2  | `dontadd.py` → `io/json_store.py` + `io/sql_queries.py`          | Low    |
| 4.3  | `cat_tools2.py` + `ar_from_en.py` → `core/category_generator.py` | Medium |
| 4.4  | `english_page_title.py` → `core/cross_wiki_linker.py`            | Medium |
| 4.5  | `filter_cat.py` → `core/category_filter.py`                      | Medium |
| 4.6  | `temp_bot.py` → `tools/template_query.py`                        | Low    |
| 4.7  | `sort_bot.py` → `tools/sort.py`                                  | Low    |
| 4.8  | `text_to_temp_bot.py` → `tools/doc_handler.py`                   | Medium |
| 4.9  | Add `models.py` and wire into all modules                        | Low    |

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

Replace broad `except Exception` with specific exceptions (`PermissionError`,
`json.JSONDecodeError`, `sqlite3.Error`). Use `pathlib` consistently.

**`models.py` detail:**

```python
from dataclasses import dataclass, field

@dataclass
class WikiPage:
    title: str
    namespace: int
    langlinks: dict[str, str] = field(default_factory=dict)

@dataclass
class Category:
    title: str
    templates: list[str] = field(default_factory=list)
```

**Success criteria:** All imports from old paths still work (with deprecation warnings).
All new imports use the clean paths. Integration test on a real category passes.

---

### Phase 5 — Testing & Validation (Week 5)

**Unit tests** — one test file per new module, in `tests/c18_new/`:

| Function               | Test cases                                                          |
| ---------------------- | ------------------------------------------------------------------- |
| `clean_category_input` | Prefix stripping, empty string, no-op                               |
| `filter_category_text` | Each predicate: template cat, deleted, blacklisted, already-in-text |
| `arabic_sort_key`      | Known character ordering, ties, mixed scripts                       |
| `extract_wikidata_qid` | Valid QID, bare Q-number, no match → None                           |
| `add_direct`           | Each insertion marker, no-marker fallback                           |
| `JsonStore.is_stale`   | Fresh file, 2-day-old file                                          |

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

**CI/CD:** `pytest tests/c18_new/ --cov=src/c18_new --cov-report=term-missing` must
show ≥ 80% coverage in GitHub Actions.

---

## 6. Risks & Mitigations

| Risk                                                  | Impact | Mitigation                                                                |
| ----------------------------------------------------- | ------ | ------------------------------------------------------------------------- |
| Breaking imports in `mk_cats` or `b18_new`            | High   | Deprecation shims for one full release cycle                              |
| Filtering behavior change due to predicate reordering | High   | Integration diff test on real category before/after each phase            |
| Performance regression from new-list building         | Low    | Benchmark; new-list is almost always faster than repeated `list.remove()` |
| Losing logging context when splitting large functions | Low    | Keep `logger.info/debug` in top-level orchestrators, not in predicates    |
| Cache invalidation bugs in `TemplateCache`            | Medium | Unit-test cache key scheme and TTL boundary explicitly                    |

---

## 7. Acceptance Criteria

-   [ ] No camelCase function names remain anywhere in `c18_new`
-   [ ] `ar_from_en2.py` deleted; its logic lives in `core/category_generator.py`
-   [ ] All hardcoded namespace IDs, template names, and category strings imported from `constants.py`
-   [ ] `filter_category_text` is a pure function — never mutates its input
-   [ ] `english_page_link` family returns `str | None` consistently — no `False`, no `""`
-   [ ] `dontadd.py` split into `io/json_store.py` and `io/sql_queries.py`
-   [ ] `pytest tests/c18_new/` passes with ≥ 80% coverage
-   [ ] `ruff check src/c18_new` reports zero errors
-   [ ] `radon cc src/c18_new -s` shows no function above grade B (complexity ≤ 10)
-   [ ] Integration diff on `Science` category is empty before → after

---

## 8. What Each Plan Contributed

| Element                                                        | Source            |
| -------------------------------------------------------------- | ----------------- |
| Clean directory structure (`core/`, `tools/`, `io/`, `utils/`) | Plan A            |
| Concrete API function signatures                               | Plan A            |
| `Namespace` IntEnum                                            | Plan A            |
| Phased timeline with explicit success criteria                 | Plan B            |
| Non-goals / scope guard                                        | Plan B            |
| Quick-wins checklist                                           | Plan B            |
| Risk/mitigation table                                          | Plan B            |
| Integration diff test strategy                                 | Plan B            |
| Performance benchmark requirement                              | Plan B            |
| Deprecation shim migration pattern                             | Plan B (extended) |

---

_Plan synthesized 2026-04-26_
