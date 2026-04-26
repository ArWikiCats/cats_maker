# Refactoring Plan for `src/b18_new`

> **Scope:** This plan targets the `src/b18_new` directory, which handles Arabic category member resolution, SQL/API category translation, and category validation.

---

## 1. Executive Summary

The `b18_new` module is responsible for:

-   Resolving English/French category members into Arabic page titles (via SQL or API)
-   Validating Arabic/English category pairs before creation
-   Gathering page lists for new category population

While functional, the module suffers from:

-   **Inconsistent naming** (`MakeLitApiWay`, `get_listenpageTitle`, `typee`, `lenth` typo)
-   **Massive string-cleaning duplication** — every file manually strips `Category:`, `تصنيف:`, `[[`, `]]`, and swaps `_` / ` `
-   **Mixed responsibilities** — SQL query strings, API fallback logic, and parameter sanitization live in the same file (`sql_cat.py`)
-   **Poor return types** — `MakeLitApiWay` returns `False` instead of `[]`; `get_ar_list_from_encat` returns a `dict` when callers expect a list
-   **Global mutable state** — `pages_in_arcat_toMake` in `cat_tools_enlist.py`
-   **Tight coupling to global config** — `settings.query.ns_no_10`, `settings.category.stubs`, `settings.database.use_sql`
-   **Duplicated validation logic** — `check_category_status` and `check_arabic_category_status` in `sql_cat_checker.py` are mirror images
-   **Weak type hints** — most signatures are untyped or use bare `list` instead of `list[str]`

---

## 2. Proposed Directory Structure

```
src/b18_new/
├── __init__.py
├── constants.py              # Hardcoded template blacklists, namespace IDs
├── models.py                 # Small dataclasses: CategoryRef, PageRef, ValidationResult
├── core/
│   ├── __init__.py
│   ├── category_resolver.py  # Merged logic from sql_cat.py + cat_tools_enlist2.py
│   ├── member_lister.py      # Refactored cat_tools_enlist.py
│   └── category_validator.py # Refactored sql_cat_checker.py
├── io/
│   ├── __init__.py
│   ├── sql_queries.py        # Pure SQL query functions (no API fallback)
│   └── api_fallback.py       # API wrappers used when SQL is disabled
└── utils/
    ├── __init__.py
    └── text.py               # Shared category-title normalization
```

---

## 3. Refactoring Tasks

### 3.1 Centralize Constants (`constants.py`)

**Why:** Template blacklists, namespace IDs, and category prefixes are scattered or hardcoded.

**Action:**

-   Move `NO_Templates_ar` from `sql_cat_checker.py`
-   Move `NO_Templates_lower` logic (currently built from `global_False_entemps` at import time) into a factory function
-   Define canonical prefix constants:
    ```python
    AR_CATEGORY_PREFIX = "تصنيف:"
    EN_CATEGORY_PREFIX = "Category:"
    FR_CATEGORY_PREFIX = "Catégorie:"
    ```
-   Add a `Namespace` enum:
    ```python
    from enum import IntEnum
    class Namespace(IntEnum):
        MAIN = 0
        TEMPLATE = 10
        CATEGORY = 14
    ```

---

### 3.2 Extract Shared Text Normalization (`utils/text.py`)

**Why:** Every module repeats the same prefix stripping and underscore replacement.

**Action:**

-   Create a single `normalize_category_title(title: str, lang: str = "en") -> str` function.
-   It should handle all prefixes (`Category:`, `category:`, `Catégorie:`, `تصنيف:`), brackets (`[[`, `]]`), and whitespace/underscore normalization.
-   Replace every inline `.replace("Category:", "")` chain with a call to this helper.

**API sketch:**

```python
def normalize_category_title(title: str | None, lang: str = "en") -> str:
    ...

def clean_wiki_brackets(title: str) -> str:
    ...
```

---

### 3.3 Merge Category Resolution Logic (`core/category_resolver.py`)

**Why:** `sql_cat.py` (SQL-centric) and `cat_tools_enlist2.py` (API-centric) both resolve EN→AR category members. They should live under a unified resolver.

**Action:**

-   Create `core/category_resolver.py` with a `CategoryResolver` class.
-   The class accepts a `backend: str = "auto"` (`"sql"`, `"api"`, or `"auto"`).
-   Move `get_ar_list`, `get_ar_list_from_en`, `do_sql`, `make_ar_list_newcat2` into this module.
-   Move `get_ar_list_from_encat`, `MakeLitApiWay` into the same resolver as API-based methods.
-   **Standardize return types** — always return `list[str]`, never `False` or `{}`.
-   Remove the `us_sql` boolean flag from public APIs; let the resolver decide based on availability.

**API sketch:**

```python
class CategoryResolver:
    def __init__(self, backend: str = "auto") -> None: ...

    def resolve_members(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]: ...
    def list_ar_pages_in_cat(self, ar_title: str) -> list[str]: ...
    def list_en_pages_with_ar_links(self, en_title: str, wiki: str = "en") -> list[str]: ...
    def diff_missing_ar_pages(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]: ...
```

---

### 3.4 Refactor Category Validator (`core/category_validator.py`)

**Why:** `sql_cat_checker.py` has two nearly identical functions (`check_category_status`, `check_arabic_category_status`) with inverted logic.

**Action:**

-   Merge both into a single `CategoryValidator` class or a set of pure functions.
-   Extract a generic `_check_page_status(site: str, title: str, expected_langlink: str | None)` helper.
-   Convert template blacklisting into a predicate:
    ```python
    def is_blacklisted_template(template: str, lang: str = "ar") -> bool: ...
    ```
-   Remove the import-time mutation of `NO_Templates_ar` based on `settings.category.stubs`; make it a runtime parameter.
-   **Standardize return type** to a `ValidationResult` dataclass instead of bare `bool`:
    ```python
    @dataclass
    class ValidationResult:
        valid: bool
        reason: str | None = None
    ```

---

### 3.5 Refactor Member Lister (`core/member_lister.py`)

**Why:** `cat_tools_enlist.py` mixes SQL fallback logic, validation calls, and a global cache dict.

**Action:**

-   Replace the module-level `pages_in_arcat_toMake: dict` with an explicit `MemberCache` dataclass or pass it as a parameter.
-   Rename `get_listenpageTitle` → `get_listen_page_title` (or `resolve_listen_pages`) and `extract_fan_page_titles` → `extract_fan_page_titles`.
-   Move the orchestration logic (SQL → API → cache) into a thin `MemberLister` class.
-   Remove the direct dependency on `settings.database.use_sql` by delegating to `CategoryResolver`.

---

### 3.6 Refactor SQL Query Layer (`io/sql_queries.py`)

**Why:** `sql_cat.py` embeds raw SQL strings and manually builds namespace lists with f-strings.

**Action:**

-   Move all SQL query strings into `io/sql_queries.py`.
-   Replace the `nss` f-string construction with a proper parameterized `IN (...)` helper or a clean tuple builder.
-   Ensure every query uses parameterized `values` tuples; no string concatenation.
-   Keep API fallback logic out of this file — it should be pure SQL.

---

### 3.7 Refactor API Fallback Layer (`io/api_fallback.py`)

**Why:** API calls are scattered across `sql_cat.py` (inside `get_ar_list`) and `cat_tools_enlist2.py`.

**Action:**

-   Move `Categorized_Page_Generator`, `sub_cats_query`, `find_LCN`, `get_arpage_inside_encat` wrappers into `io/api_fallback.py`.
-   Provide thin, typed wrappers around the wiki API so `core/` modules do not import from `..wiki_api` directly.

---

### 3.8 Add Data Models (`models.py`)

**Why:** The code passes raw strings and dicts between layers, making mocking and type-checking hard.

**Action:**

```python
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
class ValidationResult:
    valid: bool
    reason: str | None = None
```

Update `CategoryResolver` and `CategoryValidator` to accept and return these types where appropriate.

---

### 3.9 Add Unit Tests

Create a `tests/b18_new/` suite covering:

-   `normalize_category_title` edge cases (duplicate prefixes, mixed `[[`, `_`, spaces)
-   `CategoryResolver.diff_missing_ar_pages` with mocked SQL and API backends
-   `CategoryValidator` rule matrix (redirect, missing, mismatched langlink, blacklisted template)
-   `MemberLister` cache behavior and deduplication
-   `ValidationResult` serialization

Use `pytest` and `unittest.mock` to patch SQL and API calls.

---

### 3.10 Code Style & Tooling

-   **Rename all camelCase functions** to `snake_case` (PEP 8):
    -   `MakeLitApiWay` → `make_lit_api_way` (or merge into `resolve_via_api`)
    -   `get_listenpageTitle` → `get_listen_page_title`
-   **Fix typos:** `lenth` → `length`, `typee` → `item_type` or `member_type`
-   **Add `__all__`** to each module to define public APIs.
-   **Run `ruff`** (or `flake8` + `black`) for formatting and linting.

---

## 4. Migration Order (Recommended)

| Phase | Task                                                                              | Risk   |
| ----- | --------------------------------------------------------------------------------- | ------ |
| 1     | Extract `constants.py` + `utils/text.py`                                          | Low    |
| 2     | Refactor `sql_cat_checker.py` → `core/category_validator.py`                      | Medium |
| 3     | Refactor `cat_tools_enlist.py` → `core/member_lister.py`                          | Medium |
| 4     | Merge `sql_cat.py` + `cat_tools_enlist2.py` → `core/category_resolver.py` + `io/` | High   |
| 5     | Add `models.py` and wire into all modules                                         | Low    |
| 6     | Update `__init__.py` re-exports with `DeprecationWarning` shims                   | Low    |
| 7     | Write tests + run linter                                                          | Low    |

---

## 5. Risks & Mitigations

| Risk                                             | Impact | Mitigation                                                                                 |
| ------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------ |
| Breaking imports in `mk_cats`                    | High   | Keep legacy re-export files for one full release cycle with `DeprecationWarning`.          |
| Changing return type from `False` to `[]`        | Medium | Update `members_helper.py` and tests; `if not result:` already works for both.             |
| SQL query regressions from namespace refactoring | Low    | Add integration test that executes queries against a read-only replica or mocked cursor.   |
| Losing `pages_in_arcat_toMake` cache behavior    | Low    | Explicitly pass cache dict into `MemberLister` so callers (like `mk_cats`) retain control. |

---

## 6. Acceptance Criteria

-   [ ] No camelCase function names remain in `b18_new`.
-   [ ] All category-title normalization uses `utils/text.py` — no inline `.replace(...)` chains.
-   [ ] `MakeLitApiWay` and `get_ar_list_from_encat` return `list[str]` consistently (never `False` or `{}`).
-   [ ] `sql_cat_checker.py` duplication is eliminated; a single generic checker handles both EN and AR pages.
-   [ ] `pages_in_arcat_toMake` is no longer a module-level mutable dict.
-   [ ] All hardcoded template names and namespace IDs are imported from `constants.py`.
-   [ ] `py.test tests/b18_new/` passes with >80% coverage.
-   [ ] `ruff check src/b18_new` reports zero errors.

---

_Plan created on 2026-04-26_
