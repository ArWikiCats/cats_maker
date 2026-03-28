# Code Review Fix Plan & Checklist

**Created:** 2026-03-26
**Source:** `code_review_report.md`
**Total Issues:** 45+ across 86 Python files

---

## How to Use This Document

-   Work through issues **top-to-bottom** (Critical → Low priority)
-   Check off items as you complete them
-   Each issue includes: **files to change**, **steps to fix**, and **verification criteria**
-   Run tests after each section to prevent regressions

---

## Phase 1: 🔴 Critical Issues (Week 1–2)

### 1.1 Hardcoded Credentials and Paths

**Files:** `src/new_api/pagenew.py:13-18`
**Estimated Effort:** 2–3 hours

#### Steps

1. **Create environment variable infrastructure**

    - [ ] Install `python-dotenv` — add it to `requirements.txt`
    - [ ] Create a `.env.example` file with placeholder values:
        ```
        WIKIPEDIA_BOT_USERNAME=your_bot_username
        WIKIPEDIA_BOT_PASSWORD=your_bot_password
        PROJECT_PATH=/data/project/himo
        ```
    - [ ] Add `.env` to `.gitignore` (verify it's not already tracked)

2. **Refactor credential loading in `src/new_api/pagenew.py`**

    - [ ] Remove hardcoded paths (`/data/project/himo`, `I:/core/bots/core1`)
    - [ ] Remove `configparser` credential reading
    - [ ] Replace with:

        ```python
        import os
        from dotenv import load_dotenv

        load_dotenv()
        username = os.getenv("WIKIPEDIA_BOT_USERNAME", "")
        password = os.getenv("WIKIPEDIA_BOT_PASSWORD", "")
        ```

3. **Scan for other hardcoded paths**

    - [ ] Search entire codebase for `I:/core/bots` and `/data/project/himo`
    - [ ] Replace all occurrences with environment variables or config settings
    - [ ] Check `run.py:12-17` — remove `sys.path.append("D:/categories_bot/make2_new")`
    - [ ] Check `src/mk_cats/mknew.py:29-33` — remove `D:/categories_bot/make2_new/ArWikiCats`

4. **Update documentation**
    - [ ] Add credential setup instructions to `README.md`

#### Verification

-   [ ] App starts without hardcoded paths
-   [ ] Credentials load from `.env` file
-   [ ] No plaintext credentials in any committed file

---

### 1.2 SQL Injection Vulnerability

**Files:** `src/b18_new/sql_cat.py:33-42, 54-82`
**Estimated Effort:** 3–4 hours

#### Steps

1. **Audit all SQL queries**

    - [ ] Search for f-string SQL queries: `grep -rn 'f"""' src/ --include="*.py"`
    - [ ] Search for `escape_string` usage: `grep -rn 'escape_string' src/`
    - [ ] List every file and line number with string-interpolated SQL

2. **Fix `src/b18_new/sql_cat.py`**

    - [ ] Convert `get_ar_list_from_en()` query (line 68-82) to parameterized:
        ```python
        query = """
            SELECT DISTINCT ll_title
            FROM page p1
            JOIN categorylinks cla ON cla.cl_from = p1.page_id
            JOIN linktarget lt ON cla.cl_target_id = lt.lt_id
            WHERE p1.page_namespace IN (%s)
            AND lt.lt_namespace = 14
            AND lt.lt_title = %s
            AND ll_lang = 'ar'
        """
        cursor.execute(query, (nss, encat2))
        ```
    - [ ] Convert the `lt_title = "{ar_cat2}"` query (line 33-42) to parameterized
    - [ ] Remove all `escape_string()` calls

3. **Fix all other files with SQL interpolation**

    - [ ] Fix every file found in the audit (Step 1)
    - [ ] Ensure `cursor.execute(query, params)` pattern is used everywhere

4. **Validate `nss` (namespace) parameter**
    - [ ] Add validation to ensure `nss` is a valid integer or comma-separated integers
    - [ ] Never interpolate `nss` directly into SQL

#### Verification

-   [ ] Zero f-string SQL queries remain in codebase
-   [ ] Zero `escape_string` calls remain
-   [ ] All queries pass with parameterized values
-   [ ] Existing tests still pass

---

### 1.3 Silent Exception Swallowing

**Files:** `src/api_sql/mysql_client.py:44-58`
**Estimated Effort:** 3–4 hours

#### Steps

1. **Create custom exception classes**

    - [ ] Create `src/exceptions.py` (or add to existing):

        ```python
        class DatabaseError(Exception):
            """Base exception for database errors."""
            pass

        class DatabaseConnectionError(DatabaseError):
            """Raised when database connection fails."""
            pass

        class QueryExecutionError(DatabaseError):
            """Raised when a query fails to execute."""
            pass
        ```

2. **Refactor `src/api_sql/mysql_client.py`**

    - [ ] Replace `return []` in connection `except` block → `raise DatabaseConnectionError(...)`
    - [ ] Replace `return []` in `cursor.execute` `except` block → `raise QueryExecutionError(...)`
    - [ ] Replace `return []` in `cursor.fetchall` `except` block → `raise QueryExecutionError(...)`
    - [ ] Catch specific `pymysql.Error` instead of broad `Exception`

3. **Update all calling code**

    - [ ] Search for all callers of the refactored functions
    - [ ] Add `try/except DatabaseError` where appropriate
    - [ ] Decide on fallback behavior for each call site (retry, user message, etc.)

4. **Write tests**
    - [ ] Test that `DatabaseConnectionError` is raised on connection failure
    - [ ] Test that `QueryExecutionError` is raised on bad queries
    - [ ] Test that callers handle exceptions correctly

#### Verification

-   [ ] No silent `return []` on errors
-   [ ] Callers explicitly handle database exceptions
-   [ ] Error scenarios produce clear log messages

---

### 1.4 Inconsistent Return Values

**Files:** `src/mk_cats/create_category_page.py:103-119`
**Estimated Effort:** 4–5 hours

#### Steps

1. **Define result types**

    - [ ] Create a `CategoryResult` NamedTuple or dataclass:

        ```python
        from typing import Optional, NamedTuple

        class CategoryResult(NamedTuple):
            success: bool
            page_title: Optional[str]
            error_message: Optional[str]
        ```

2. **Refactor `make_category()` in `src/mk_cats/create_category_page.py`**

    - [ ] Change all `return False` → `return CategoryResult(False, None, "reason")`
    - [ ] Change success return → `return CategoryResult(True, new_cat, None)`
    - [ ] Remove `is not False` checks — use `.success` attribute instead

3. **Update all callers of `make_category()`**

    - [ ] Search: `grep -rn 'make_category' src/`
    - [ ] Update each call site to use `result.success` instead of `result is not False`

4. **Audit other functions with mixed return types**
    - [ ] Search for functions returning both `False` and other types
    - [ ] Apply the same pattern (result type or exceptions)

#### Verification

-   [ ] `make_category()` always returns `CategoryResult`
-   [ ] No `is False` / `is not False` checks remain for this function
-   [ ] All tests pass with new return types

---

## Phase 2: 🟠 High Severity Issues (Month 1)

### 2.1 Global Mutable State

**Files:** `src/mk_cats/mknew.py:35-38`, `src/b18_new/cat_tools.py:28`
**Estimated Effort:** 4–6 hours

#### Steps

1. **Identify all global mutable variables**

    - [ ] Search for module-level lists and dicts: `DONE_D`, `NewCat_Done`, `Already_Created`
    - [ ] Document where each is read and written

2. **Create a `CategoryProcessor` class**

    - [ ] Move `DONE_D`, `NewCat_Done`, `Already_Created` to instance attributes
    - [ ] Move related functions to methods on the class
    - [ ] Use dependency injection to pass the processor where needed

3. **Move constants to config**

    - [ ] Move `wiki_site_ar`, `wiki_site_en` to `src/config/settings.py`
    - [ ] Make them immutable (frozen dataclass or module-level constants)

4. **Update tests**
    - [ ] Ensure tests create fresh instances (no shared state)
    - [ ] Verify test isolation — running tests in any order produces same results

#### Verification

-   [ ] No mutable global variables remain in refactored modules
-   [ ] Tests pass in any order
-   [ ] No `global` keyword usage for state variables

---

### 2.2 Missing Type Hints

**Files:** Throughout codebase, especially `src/mk_cats/mknew.py:230-235`
**Estimated Effort:** 6–8 hours (incremental)

#### Steps

1. **Set up type checking tooling**

    - [ ] Install `mypy` — add to `requirements-dev.txt`
    - [ ] Create `mypy.ini` or add `[mypy]` section to `setup.cfg`
    - [ ] Run `mypy src/` to get a baseline of errors

2. **Add type hints to critical modules first**

    - [ ] `src/api_sql/mysql_client.py`
    - [ ] `src/mk_cats/create_category_page.py`
    - [ ] `src/b18_new/sql_cat.py`
    - [ ] `src/new_api/super/bot.py`
    - [ ] `src/mk_cats/mknew.py` — uncomment and fix `# -> list:` on `make_ar()`

3. **Fix commented-out type annotations**

    - [ ] Search: `grep -rn '# ->' src/ --include="*.py"`
    - [ ] Uncomment and correct all found annotations

4. **Add to remaining public APIs**
    - [ ] Prioritize public-facing functions
    - [ ] Include `Args`, `Returns` in docstrings alongside type hints

#### Verification

-   [ ] `mypy src/` runs with zero errors on critical modules
-   [ ] No commented-out type annotations remain

---

### 2.3 Inconsistent Error Handling

**Files:** `src/new_api/super/bot.py:133-145`
**Estimated Effort:** 3–4 hours

#### Steps

1. **Create API exception hierarchy**

    - [ ] Add to `src/exceptions.py`:
        ```python
        class ApiError(Exception): pass
        class NetworkError(ApiError): pass
        class AuthenticationError(ApiError): pass
        class ServerError(ApiError): pass
        ```

2. **Refactor `src/new_api/super/bot.py`**

    - [ ] Replace `return ""` on error → `raise AuthenticationError(...)`
    - [ ] Distinguish network vs. auth vs. server errors
    - [ ] Catch specific exceptions (`requests.RequestException`, etc.)

3. **Update all callers**
    - [ ] Search for all call sites that check for empty string returns
    - [ ] Replace with `try/except ApiError` blocks

#### Verification

-   [ ] No sentinel value returns (`""`, `None`, `False`) for error cases
-   [ ] Clear exception types for each failure mode

---

### 2.4 Magic Numbers

**Files:** `src/logging_config.py:21-32`, `src/config/settings.py:251`, `src/mk_cats/categorytext.py:10`
**Estimated Effort:** 2–3 hours

#### Steps

1. **Extract to named constants**

    - [ ] Create `src/constants.py` or add to relevant files:

        ```python
        class AnsiColor:
            RED = 91
            GREEN = 92
            YELLOW = 93
            # ... (with comments: ANSI escape code color values)

        # MediaWiki namespace IDs
        NAMESPACE_PORTAL = 100
        NAMESPACE_CATEGORY = 14

        # Processing limits
        DEFAULT_RANGE_LIMIT = 5  # Max categories per batch
        ```

2. **Replace all magic numbers**

    - [ ] `src/logging_config.py` — use `AnsiColor.*`
    - [ ] `src/config/settings.py:251` — use `DEFAULT_RANGE_LIMIT`
    - [ ] `src/mk_cats/categorytext.py:10` — use `NAMESPACE_PORTAL`
    - [ ] Search for other numeric literals: `grep -rn 'ns.*=.*[0-9]' src/`

3. **Add comments where constants are defined**
    - [ ] Explain _why_ each value was chosen

#### Verification

-   [ ] No unexplained numeric literals in business logic
-   [ ] All constants have descriptive names and comments

---

### 2.5 Circular Import Risk

**Files:** `src/__init__.py`
**Estimated Effort:** 2–3 hours

#### Steps

1. **Map import dependencies**

    - [ ] Draw/list the import graph from `src/__init__.py`
    - [ ] Identify circular chains

2. **Refactor `src/__init__.py`**

    - [ ] Remove unnecessary re-exports
    - [ ] Use lazy imports where circular deps exist:
        ```python
        def get_create_categories():
            from .mk_cats import create_categories_from_list
            return create_categories_from_list
        ```
    - [ ] Or restructure modules to break cycles

3. **Remove legacy aliases**
    - [ ] Remove `ToMakeNewCat2222 = create_categories_from_list` (after updating callers)

#### Verification

-   [ ] `python -c "import src"` works without import errors
-   [ ] No circular import warnings

---

## Phase 3: 🟡 Medium Severity Issues (Months 2–3)

### 3.1 Inconsistent Naming Conventions

**Files:** `src/mk_cats/mknew.py:273-275`
**Estimated Effort:** 2–3 hours

#### Steps

-   [ ] Rename `process_catagories` → `process_categories`
-   [ ] Rename `lenth` parameter → `length`
-   [ ] Rename `arlab` → `arabic_label` (or similar descriptive name)
-   [ ] Search for other typos: `grep -rn 'catagori\|lenth\|respons\b' src/`
-   [ ] Update all callers of renamed functions
-   [ ] Establish naming convention in a `CONTRIBUTING.md`

#### Verification

-   [ ] No typos in function or parameter names
-   [ ] All tests pass after renames

---

### 3.2 Missing Docstrings

**Files:** Multiple — `src/mk_cats/add_bot.py:56`, `src/wiki_api/check_redirects.py:10`
**Estimated Effort:** 4–6 hours (incremental)

#### Steps

-   [ ] Add docstrings to all public functions in critical modules:
    -   [ ] `src/mk_cats/add_bot.py` — `add_to_page()`
    -   [ ] `src/wiki_api/check_redirects.py` — enhance `load_non_redirects()` docstring
    -   [ ] `src/b18_new/sql_cat.py` — all exported functions
    -   [ ] `src/api_sql/mysql_client.py` — all exported functions
-   [ ] Use Google-style or NumPy-style docstrings consistently:

    ```python
    def func(arg: str) -> bool:
        """Short summary.

        Args:
            arg: Description of argument.

        Returns:
            True if successful, False otherwise.

        Raises:
            ValueError: If arg is empty.
        """
    ```

-   [ ] Configure docstring linting (e.g., `pydocstyle`)

#### Verification

-   [ ] All public functions have docstrings with Args/Returns/Raises

---

### 3.3 Inefficient Database Queries

**Files:** `src/b18_new/sql_cat.py:54-71`
**Estimated Effort:** 3–4 hours

#### Steps

-   [ ] Add `LIMIT` clauses to all unbounded `SELECT` queries
-   [ ] Make limit configurable via settings (e.g., `DEFAULT_QUERY_LIMIT = 10000`)
-   [ ] Implement query result caching for frequently-called queries
-   [ ] Add logging to track slow queries (log queries taking >1s)
-   [ ] Review database indexes for frequently-queried columns

#### Verification

-   [ ] No unbounded `SELECT` queries remain
-   [ ] Performance improvement measured for high-frequency queries

---

### 3.4 LRU Cache Without Size Limits

**Files:** Multiple — `src/wd_bots/get_bots.py:55`
**Estimated Effort:** 2–3 hours

#### Steps

-   [ ] Audit all `@lru_cache` usages: `grep -rn 'lru_cache' src/`
-   [ ] Ensure every `@lru_cache` has a justified `maxsize`
-   [ ] Add comments documenting why each `maxsize` was chosen
-   [ ] Add cache-clearing in test fixtures:
    ```python
    @pytest.fixture(autouse=True)
    def clear_caches():
        Get_Sitelinks_From_wikidata.cache_clear()
        yield
    ```
-   [ ] Consider adding cache hit/miss monitoring

#### Verification

-   [ ] No unbounded `@lru_cache()` (without maxsize)
-   [ ] All cache sizes documented
-   [ ] Tests don't leak state through caches

---

### 3.5 Unused Imports and Code

**Files:** `run.py:12-17`, `src/mk_cats/mknew.py:29-33`
**Estimated Effort:** 1–2 hours

#### Steps

-   [ ] Remove `sys.path.append("D:/categories_bot/make2_new")` from `run.py`
-   [ ] Remove `arwikicats_path = Path("D:/categories_bot/make2_new/ArWikiCats")` from `mknew.py`
-   [ ] Run a linter to find unused imports: `pip install autoflake && autoflake --check -r src/`
-   [ ] Remove all unused imports
-   [ ] Document necessary external dependencies in `README.md`

#### Verification

-   [ ] No hardcoded development paths remain
-   [ ] No unused imports flagged by linter

---

### 3.6 Test Coverage Gaps

**Files:** Multiple modules with no tests
**Estimated Effort:** 8–12 hours (incremental)

#### Steps

-   [ ] Measure current coverage: `pytest --cov=src --cov-report=term-missing`
-   [ ] Write tests for untested critical modules:
    -   [ ] `src/api_sql/mysql_client.py` — connection, query, error handling
    -   [ ] `src/new_api/super/super_page.py` — `MainPage` class
    -   [ ] `src/mk_cats/add_bot.py` — `add_to_page()`
    -   [ ] `src/wiki_api/api_requests.py` — request/response handling
    -   [ ] `src/c18_new/dontadd.py` — all functions
-   [ ] Include error scenario tests and edge cases
-   [ ] Target **80% coverage** for critical modules

#### Verification

-   [ ] Coverage report shows ≥80% on critical modules
-   [ ] Error scenarios are tested

---

## Phase 4: 🟢 Low Severity Issues (When Possible)

### 4.1 Inconsistent Logging Levels

**Files:** `src/mk_cats/mknew.py:266-268`, `src/mk_cats/create_category_page.py:120`
**Estimated Effort:** 1–2 hours

#### Steps

-   [ ] Audit all `logger.*` calls for correct levels:
    -   `debug` — detailed diagnostic info
    -   `info` — normal operations (e.g., "New category created")
    -   `warning` — unexpected but recoverable
    -   `error` — failures
-   [ ] Fix `logger.warning(f"<<lightgreen>> New_Cat: {new_cat}")` → `logger.info(...)`
-   [ ] Remove inline color tags (`<<red>>`, `<<lightgreen>>`) — let the formatter handle it
-   [ ] Document logging conventions in `CONTRIBUTING.md`

#### Verification

-   [ ] No `warning` used for success messages
-   [ ] No `debug` used for error messages

---

### 4.2 Commented-Out Code

**Files:** `src/new_api/super/super_login.py:17-19`, `src/new_api/super/super_page.py:234-235`
**Estimated Effort:** 1 hour

#### Steps

-   [ ] Search for large blocks of commented code: `grep -rn '^\s*#.*=' src/ --include="*.py"`
-   [ ] Remove all commented-out code blocks (they're in version control history)
-   [ ] Keep only meaningful comments that explain _why_
-   [ ] Add "no commented-out code" to code review checklist

#### Verification

-   [ ] No blocks of commented-out executable code remain

---

### 4.3 Inconsistent String Formatting

**Files:** Multiple
**Estimated Effort:** 2–3 hours

#### Steps

-   [ ] Search for old-style formatting: `grep -rn '% ["\x27]' src/ --include="*.py"`
-   [ ] Search for `.format()` calls: `grep -rn '\.format(' src/ --include="*.py"`
-   [ ] Convert all to f-strings where possible
-   [ ] Add linting rule to enforce f-strings for new code

#### Verification

-   [ ] No `%` or `.format()` string formatting in new/modified code

---

### 4.4 Missing Input Validation

**Files:** `src/config/settings.py:283-288`
**Estimated Effort:** 2–3 hours

#### Steps

-   [ ] Add validation in `_process_argv()`:

    ```python
    VALID_ARGS = {"limit", "lang", "cat", ...}

    def _process_argv(self):
        for arg in sys.argv[1:]:
            arg_name, _, value = arg.partition(":")
            if arg_name not in VALID_ARGS:
                raise ValueError(f"Unknown argument: {arg_name}")
            # Add type-specific validation
    ```

-   [ ] Add type checking for all configuration values
-   [ ] Document expected argument formats and ranges
-   [ ] Write tests for invalid inputs

#### Verification

-   [ ] Invalid arguments raise clear errors
-   [ ] All config values are validated before use

---

## Progress Tracker

| Phase | Section                   | Status         | Completed Date |
| ----- | ------------------------- | -------------- | -------------- |
| 🔴 1  | 1.1 Hardcoded Credentials | ⬜ Not Started |                |
| 🔴 1  | 1.2 SQL Injection         | ⬜ Not Started |                |
| 🔴 1  | 1.3 Silent Exceptions     | ⬜ Not Started |                |
| 🔴 1  | 1.4 Inconsistent Returns  | ⬜ Not Started |                |
| 🟠 2  | 2.1 Global Mutable State  | ⬜ Not Started |                |
| 🟠 2  | 2.2 Missing Type Hints    | ⬜ Not Started |                |
| 🟠 2  | 2.3 Error Handling        | ⬜ Not Started |                |
| 🟠 2  | 2.4 Magic Numbers         | ⬜ Not Started |                |
| 🟠 2  | 2.5 Circular Imports      | ⬜ Not Started |                |
| 🟡 3  | 3.1 Naming Conventions    | ⬜ Not Started |                |
| 🟡 3  | 3.2 Missing Docstrings    | ⬜ Not Started |                |
| 🟡 3  | 3.3 Inefficient Queries   | ⬜ Not Started |                |
| 🟡 3  | 3.4 LRU Cache Limits      | ⬜ Not Started |                |
| 🟡 3  | 3.5 Unused Imports/Code   | ⬜ Not Started |                |
| 🟡 3  | 3.6 Test Coverage         | ⬜ Not Started |                |
| 🟢 4  | 4.1 Logging Levels        | ⬜ Not Started |                |
| 🟢 4  | 4.2 Commented-Out Code    | ⬜ Not Started |                |
| 🟢 4  | 4.3 String Formatting     | ⬜ Not Started |                |
| 🟢 4  | 4.4 Input Validation      | ⬜ Not Started |                |

---

## Quick Reference: Commands to Run

```bash
# Find all SQL injection risks
grep -rn 'f"""' src/ --include="*.py"
grep -rn "f'''" src/ --include="*.py"
grep -rn 'escape_string' src/ --include="*.py"

# Find all hardcoded paths
grep -rn 'D:/' src/ --include="*.py"
grep -rn 'I:/' src/ --include="*.py"
grep -rn '/data/project/' src/ --include="*.py"

# Find unused imports
pip install autoflake
autoflake --check -r src/

# Measure test coverage
pytest --cov=src --cov-report=term-missing

# Type checking
pip install mypy
mypy src/

# Find magic numbers
grep -rn '= [0-9]\+' src/ --include="*.py"

# Find commented-out code
grep -rn '^\s*# .*=' src/ --include="*.py" | head -50
```

---

_Plan derived from `code_review_report.md` — 2026-03-26_
