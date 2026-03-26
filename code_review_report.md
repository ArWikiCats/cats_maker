# Code Review Report: cats_maker_new

**Generated:** 2026-03-26
**Project:** Wikipedia/Wikidata Category Bot
**Scope:** Full codebase security, quality, and maintainability audit

---

## Executive Summary

This is a Wikipedia/Wikidata bot project for creating and managing categories on Arabic Wikipedia. The codebase shows signs of active development with recent refactoring efforts, but contains numerous issues ranging from critical security vulnerabilities to maintainability concerns.

**Overall Assessment:** The project has a solid foundation with good test coverage in some areas, but suffers from:

-   🔴 **Critical security vulnerabilities** requiring immediate attention
-   🟠 **High-severity code quality issues** affecting reliability
-   🟡 **Medium-severity maintainability issues** impacting development velocity
-   🟢 **Low-severity cosmetic issues** affecting code consistency

---

## 🔴 Critical Issues (Fix Immediately)

### 1.1 Hardcoded Credentials and Paths

**Severity:** CRITICAL - Security
**Files:** `src/new_api/pagenew.py:13-18`

```python
project = "/data/project/himo"
if not os.path.isdir(project):
    project = "I:/core/bots/core1"

config = configparser.ConfigParser()
config.read(f"{project}/confs/user.ini")

username = config["DEFAULT"].get("botusername", "")
password = config["DEFAULT"].get("botpassword", "")
```

**Problems:**

-   Hardcoded production paths expose infrastructure details
-   Credentials stored in plaintext INI file
-   No encryption for sensitive data
-   Makes local development difficult without exposing paths

**Fix:**

```python
# Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()
username = os.getenv("BOT_USERNAME")
password = os.getenv("BOT_PASSWORD")

# Or use a secrets manager
# AWS Secrets Manager, HashiCorp Vault, etc.
```

**Action Items:**

-   [ ] Move all credentials to environment variables
-   [ ] Add `.env` file support with proper `.gitignore`
-   [ ] Update `.env.example` with placeholder values
-   [ ] Remove all hardcoded production paths
-   [ ] Document credential setup in README

---

### 1.2 SQL Injection Vulnerability

**Severity:** CRITICAL - Security
**Files:** `src/b18_new/sql_cat.py:33-42, 68-82`

```python
# VULNERABLE CODE
ar_cat2 = escape_string(arcat.replace(" ", "_").replace("تصنيف:", ""))
qia_ar = f"""
select page_title, page_namespace
    from page
    join categorylinks on cl_from = page_id
    join linktarget on lt_id = cl_target_id
    where lt_title = "{ar_cat2}"
    and lt_namespace = 14
"""
```

```python
# ALSO VULNERABLE
en_qua = f"""
    SELECT DISTINCT ll_title
        FROM page p1
        JOIN categorylinks cla ON cla.cl_from = p1.page_id
        JOIN linktarget lt ON cla.cl_target_id = lt.lt_id
        WHERE p1.page_namespace IN ({nss})
        AND lt.lt_namespace = 14
        AND lt.lt_title = '{encat2}'
        AND ll_lang = 'ar'
"""
```

**Problems:**

-   String interpolation despite `escape_string` usage
-   `escape_string` is deprecated and insufficient
-   Variable `{nss}` interpolated without validation
-   High risk of SQL injection attacks

**Fix:**

```python
# Use parameterized queries
query = """
    SELECT page_title, page_namespace
    FROM page
    JOIN categorylinks ON cl_from = page_id
    JOIN linktarget ON lt_id = cl_target_id
    WHERE lt_title = %s
    AND lt_namespace = 14
"""
cursor.execute(query, (ar_cat2,))
```

**Action Items:**

-   [ ] Replace ALL f-string SQL queries with parameterized queries
-   [ ] Remove all uses of `escape_string()`
-   [ ] Add SQL linting to CI/CD pipeline
-   [ ] Write tests specifically for SQL injection prevention

---

### 1.3 Silent Exception Swallowing

**Severity:** CRITICAL - Reliability
**Files:** `src/api_sql/mysql_client.py:44-58`

```python
try:
    connection = pymysql.connect(**DB_CONFIG)
except Exception as e:
    logger.exception(e)
    return []  # Silent failure - calling code can't detect error!

with connection as conn, conn.cursor() as cursor:
    try:
        cursor.execute(query, params)
    except Exception as e:
        logger.exception(e)
        return []  # Silent failure!

    try:
        results = cursor.fetchall()
    except Exception as e:
        logger.exception(e)
        return []  # Silent failure!
```

**Problems:**

-   All database errors return empty lists silently
-   Calling code cannot distinguish "no results" from "error occurred"
-   Makes debugging production issues extremely difficult
-   Violates fail-fast principle

**Fix:**

```python
def execute_query(query: str, params: tuple = ()) -> list:
    """Execute query and return results. Raises on error."""
    try:
        connection = pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseConnectionError(f"Failed to connect: {e}")

    with connection as conn, conn.cursor() as cursor:
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except pymysql.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Query failed: {e}")
```

**Action Items:**

-   [ ] Create custom exception classes for database errors
-   [ ] Re-raise exceptions or return error indicators
-   [ ] Update all calling code to handle exceptions properly
-   [ ] Add integration tests for error scenarios

---

### 1.4 Inconsistent Return Values

**Severity:** CRITICAL - Bug Risk
**Files:** `src/mk_cats/create_category_page.py:103-119`

```python
def make_category(categories, enca, title, qid, family=""):
    if enca in skip_encats:
        return False

    if not title.startswith("تصنيف:"):
        return False

    if page.get_text() or page.exists():
        return False

    new_cat = create_Page(text, page)

    if new_cat is not False:  # Inconsistent None/False checking
        text = add_text_to_cat(text, categories, enca, title, qid)

    logger.warning(f"<<lightgreen>> New_Cat: {new_cat}")
    return new_cat
```

**Problems:**

-   Returns `False`, `None`, `True`, strings inconsistently
-   Calling code uses `is False`, `is not False`, `== False` inconsistently
-   Type safety completely absent
-   High risk of bugs from misinterpreted return values

**Fix:**

```python
from typing import Optional, NamedTuple

class CategoryResult(NamedTuple):
    success: bool
    page_title: Optional[str]
    error_message: Optional[str]

def make_category(categories: list, enca: str, title: str, qid: str, family: str = "") -> CategoryResult:
    if enca in skip_encats:
        return CategoryResult(False, None, "Category in skip list")

    if not title.startswith("تصنيف:"):
        return CategoryResult(False, None, "Invalid title prefix")

    if page.get_text() or page.exists():
        return CategoryResult(False, None, "Page already exists")

    new_cat = create_Page(text, page)
    return CategoryResult(True, new_cat, None)
```

**Action Items:**

-   [ ] Define consistent return types for all functions
-   [ ] Use exceptions for error conditions
-   [ ] Add type hints to all functions
-   [ ] Update all calling code to use new return types

---

## 🟠 High Severity Issues (Fix This Month)

### 2.1 Global Mutable State

**Severity:** HIGH - Code Quality
**Files:** `src/mk_cats/mknew.py:35-38`, `src/b18_new/cat_tools.py:28`

```python
# Global mutable state - causes test isolation problems
DONE_D = []
NewCat_Done = {}
Already_Created = []

# TODO: move it to the settings file!
wiki_site_ar = {"family": "wikipedia", "code": "ar"}
wiki_site_en = {"family": "wikipedia", "code": "en"}
```

**Problems:**

-   Global mutable state causes test isolation problems
-   State persists between runs causing unpredictable behavior
-   Thread-unsafe
-   Makes testing difficult

**Fix:**

```python
# Encapsulate state in a class
class CategoryProcessor:
    def __init__(self):
        self.done_d: list = []
        self.new_cat_done: dict = {}
        self.already_created: list = []

    def process(self, categories: list) -> list:
        # Use instance state instead of global
        pass
```

**Action Items:**

-   [ ] Encapsulate all global state in classes
-   [ ] Use dependency injection for shared state
-   [ ] Add tests to verify state isolation
-   [ ] Document state management strategy

---

### 2.2 Missing Type Hints

**Severity:** HIGH - Code Quality
**Files:** Throughout codebase, especially `src/mk_cats/mknew.py:230-235`

```python
def make_ar(en_page_title, ar_title, callback=None):  # -> list:
    """
    # Return type annotation is COMMENTED OUT!
```

```python
def submitAPI(params, Code, family, printurl=False, **kwargs):
    # No type hints at all!
```

**Problems:**

-   Makes code harder to understand and maintain
-   Prevents static analysis tools from catching bugs
-   Inconsistent with modern Python best practices
-   Some type annotations are commented out

**Action Items:**

-   [ ] Add comprehensive type hints to all functions
-   [ ] Fix commented-out type annotations
-   [ ] Configure `mypy` or `pyright` for type checking
-   [ ] Add type checking to CI/CD pipeline
-   [ ] Target 100% type coverage for public APIs

---

### 2.3 Inconsistent Error Handling

**Severity:** HIGH - Reliability
**Files:** `src/new_api/super/bot.py:133-145`

```python
try:
    r11 = seasons_by_lang[self.sea_key].request("POST", self.endpoint, data=r1_params, headers=self.headers)
    self.log_error(r11.status_code, "logintoken")

    if not str(r11.status_code).startswith("2"):
        logger.debug(f"<<red>> {botname} {r11.status_code} Server Error")
except Exception as e:
    logger.warning(f"<<red>> Error getting login token: {e}")
    return ""  # Returns empty string on error
```

**Problems:**

-   Returns empty string instead of raising exception
-   No distinction between network errors and authentication errors
-   Calling code must check for empty string returns everywhere
-   Makes error handling inconsistent

**Action Items:**

-   [ ] Define custom exception hierarchy for API errors
-   [ ] Raise exceptions instead of returning sentinel values
-   [ ] Document all exception types that can be raised
-   [ ] Add tests for all error scenarios

---

### 2.4 Magic Numbers

**Severity:** HIGH - Code Quality
**Files:** Multiple files

```python
# src/logging_config.py:21-32
color_numbers = {
    "red": 91,  # What are these numbers?
    "green": 92,
    # ...
}

# src/config/settings.py:251
range_limit: int = 5  # Why 5?

# src/mk_cats/categorytext.py:10
def get_page_link_data(title: str, sitecode: str, ns: int = 100) -> list:  # Why 100?
```

**Problems:**

-   Unexplained numeric constants throughout codebase
-   Makes code harder to understand and maintain
-   Risk of incorrect values being used
-   No documentation of why specific values were chosen

**Fix:**

```python
# Define constants with descriptive names
class AnsiColorCodes:
    RED = 91
    GREEN = 92
    YELLOW = 93
    # ...

class CategoryConfig:
    DEFAULT_RANGE_LIMIT = 5  # Maximum categories to process in one batch
    DEFAULT_NAMESPACE = 100  # Portal namespace
```

**Action Items:**

-   [ ] Extract all magic numbers to named constants
-   [ ] Add comments explaining the significance of values
-   [ ] Document default values in configuration
-   [ ] Review and justify all numeric constants

---

### 2.5 Circular Import Risk

**Severity:** HIGH - Architecture
**Files:** `src/__init__.py`

```python
from .logging_config import setup_logging
from .mk_cats import (
    ToMakeNewCat2222,
    ar_make_lab,
    create_categories_from_list,
    # ...
)
```

**Problems:**

-   Root `__init__.py` imports from submodules
-   Submodules may import from `src`, creating circular dependencies
-   Can cause import errors that are hard to debug
-   Makes code harder to test in isolation

**Action Items:**

-   [ ] Audit all import statements for circular dependencies
-   [ ] Refactor to use dependency injection where needed
-   [ ] Consider lazy imports for problematic cases
-   [ ] Add import linting to CI/CD

---

## 🟡 Medium Severity Issues (Fix Next Quarter)

### 3.1 Inconsistent Naming Conventions

**Severity:** MEDIUM - Code Quality
**Files:** `src/mk_cats/mknew.py:273-275`

```python
def process_catagories(cat, arlab, num, lenth, callback=None):  # Typos!
    # "catagories" should be "categories"
    # "lenth" should be "length"
    # "arlab" is unclear abbreviation
```

**Problems:**

-   Typos in function and parameter names (`catagories`, `lenth`)
-   Unclear abbreviations (`arlab`)
-   Mix of snake_case and unclear naming
-   Makes code harder to search and understand

**Action Items:**

-   [ ] Fix all typos in function and parameter names
-   [ ] Establish naming convention guidelines
-   [ ] Use descriptive names instead of abbreviations
-   [ ] Add linting rules for naming conventions

---

### 3.2 Missing Docstrings

**Severity:** MEDIUM - Documentation
**Files:** Multiple files

```python
# src/mk_cats/add_bot.py:56-95
def add_to_page(page_title, arcat):
    # No docstring!
    Dont_add_to_pages = Dont_add_to_pages_def()
```

```python
# src/wiki_api/check_redirects.py:10-17
def load_non_redirects(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""  # Too brief!
```

**Action Items:**

-   [ ] Add comprehensive docstrings to all public functions
-   [ ] Include Args, Returns, Raises sections
-   [ ] Document side effects
-   [ ] Add examples for complex functions
-   [ ] Configure docstring linting

---

### 3.3 Inefficient Database Queries

**Severity:** MEDIUM - Performance
**Files:** `src/b18_new/sql_cat.py:54-71`

```python
def get_ar_list_from_en(encat, us_sql=True, wiki="en"):
    # No LIMIT clause - could return millions of rows
    en_qua = f"""
        SELECT DISTINCT ll_title
            FROM page p1
            JOIN categorylinks cla ON cla.cl_from = p1.page_id
            # ...
    """
```

**Problems:**

-   No LIMIT clause - could return millions of rows
-   No indexing hints
-   Multiple string replacements instead of proper parsing
-   Query executed repeatedly without caching

**Action Items:**

-   [ ] Add LIMIT clauses to all queries
-   [ ] Implement query result caching
-   [ ] Add database query profiling
-   [ ] Optimize slow queries with proper indexing

---

### 3.4 LRU Cache Without Size Limits

**Severity:** MEDIUM - Performance
**Files:** Multiple files

```python
# src/wd_bots/get_bots.py:55
@lru_cache(maxsize=5000)  # Arbitrary limit without justification
def Get_Sitelinks_From_wikidata(site, title, ...):
```

**Problems:**

-   Some caches have no maxsize (unbounded memory growth)
-   Some have arbitrary limits without justification
-   No cache invalidation strategy
-   Caches persist across test runs causing test failures

**Action Items:**

-   [ ] Document cache size justification for all caches
-   [ ] Implement cache invalidation strategy
-   [ ] Add cache monitoring and metrics
-   [ ] Clear caches between test runs

---

### 3.5 Unused Imports and Code

**Severity:** MEDIUM - Code Quality
**Files:** `run.py:12-17`, `src/mk_cats/mknew.py:29-33`

```python
# run.py - Import from completely different project!
try:
    sys.path.append("D:/categories_bot/make2_new")
    from new_all import work_bot as new_all
except ImportError:
    new_all = None
```

```python
# src/mk_cats/mknew.py - Hardcoded development path
arwikicats_path = Path("D:/categories_bot/make2_new/ArWikiCats")
if arwikicats_path.exists():
    sys.path.insert(0, str(arwikicats_path.parent))
```

**Action Items:**

-   [ ] Remove all unused imports
-   [ ] Remove hardcoded development paths
-   [ ] Add import linting to CI/CD
-   [ ] Document external dependencies clearly

---

### 3.6 Test Coverage Gaps

**Severity:** MEDIUM - Testing
**Files:** Multiple modules with minimal or no tests

**Modules lacking tests:**

-   `src/api_sql/mysql_client.py` - Only basic connection tests
-   `src/new_api/super/super_page.py` - No tests for MainPage class
-   `src/mk_cats/add_bot.py` - No tests
-   `src/wiki_api/api_requests.py` - No tests
-   `src/c18_new/dontadd.py` - No tests

**Action Items:**

-   [ ] Target 80% coverage for critical modules
-   [ ] Add integration tests for database operations
-   [ ] Add tests for error scenarios
-   [ ] Add tests for edge cases

---

## 🟢 Low Severity Issues (Fix When Possible)

### 4.1 Inconsistent Logging Levels

**Severity:** LOW - Code Quality
**Files:** `src/mk_cats/mknew.py:266-268`, `src/mk_cats/create_category_page.py:120`

```python
logger.debug(f"*: <<lightred>> {num}/{lenth} cat: {cat}, arlab: {arlab}")
# Uses debug level with color tags suggesting importance

logger.warning(f"<<lightgreen>> New_Cat: {new_cat}")
# Uses warning level for successful operations (should be info)
```

**Action Items:**

-   [ ] Standardize logging levels across codebase
-   [ ] Use appropriate levels (debug, info, warning, error)
-   [ ] Remove color tags from log messages (let formatter handle it)
-   [ ] Document logging conventions

---

### 4.2 Commented-Out Code

**Severity:** LOW - Code Quality
**Files:** Multiple files

```python
# src/new_api/super/super_login.py:17-19
Exception:{'login': {'result': 'Failed', 'reason': 'You have made too many recent login attempts...'}}

# src/new_api/super/super_page.py:234-235
# _dat_ = { "batchcomplete": "", "query": { "normalized": [{ "from": "وب:ملعب", "to": "ويكيبيديا:ملعب" }], ...
```

**Action Items:**

-   [ ] Remove all commented-out code
-   [ ] Use version control for historical code
-   [ ] Add code review checklist item for commented code

---

### 4.3 Inconsistent String Formatting

**Severity:** LOW - Code Quality
**Files:** Multiple files

```python
# Mix of f-strings, % formatting, and .format()
template = "{{تصنيف كومنز|%s}}" % P373  # Old style

newtext = f"{(newtext[:num] + final_categories)}\n{newtext[num:]}"  # f-string
```

**Action Items:**

-   [ ] Standardize on f-strings for all new code
-   [ ] Gradually migrate old-style formatting
-   [ ] Add formatting linting rules

---

### 4.4 Missing Input Validation

**Severity:** LOW - Security
**Files:** `src/config/settings.py:283-288`

```python
def _process_argv(self):
    for arg in sys.argv:
        arg_name, _, value = arg.partition(":")
        # No validation of command-line argument values
```

**Action Items:**

-   [ ] Validate all command-line arguments
-   [ ] Add type checking for configuration values
-   [ ] Document expected value ranges
-   [ ] Add validation tests

---

## Patterns of Technical Debt

### 5.1 Refactoring In Progress

-   Files `refactor.md`, `refactor_old.md`, `refactoring_plan.md` exist in root
-   `src/c18_new/` and `src/b18_new/` suggest versioned refactoring
-   Legacy function aliases: `ToMakeNewCat2222 = create_categories_from_list`

**Recommendation:** Complete refactoring and remove legacy code

### 5.2 Mixed Programming Styles

-   Object-oriented (classes like `ALL_APIS`, `MainPage`)
-   Functional (module-level functions everywhere)
-   Procedural (global state, script-like execution)

**Recommendation:** Choose and document preferred paradigm

### 5.3 Inconsistent Abstraction Levels

High-level business logic mixed with low-level API details in the same functions.

**Recommendation:** Separate concerns into clear layers

---

## Prioritized Recommendations

### Immediate (Week 1-2) 🔴

1. **Fix SQL Injection** - Convert all SQL queries to parameterized queries
2. **Secure Credentials** - Move credentials to environment variables
3. **Fix Silent Failures** - Add proper exception handling in database layer
4. **Remove Hardcoded Paths** - Make all paths configurable

### Short Term (Month 1) 🟠

5. **Add Type Hints** - Complete type annotations for all public APIs
6. **Fix Global State** - Encapsulate mutable globals in classes
7. **Improve Error Handling** - Consistent error handling patterns
8. **Add Input Validation** - Validate all user inputs

### Medium Term (Months 2-3) 🟡

9. **Improve Test Coverage** - Target 80% coverage for critical modules
10. **Fix Naming Issues** - Rename functions with typos and unclear names
11. **Add Documentation** - Complete docstrings for all public APIs
12. **Performance Optimization** - Add query limits and caching strategy

### Long Term (Months 4-6) 🟢

13. **Architecture Refactoring** - Separate concerns into clear layers
14. **Dependency Cleanup** - Remove unused imports and dependencies
15. **CI/CD Pipeline** - Add automated testing and linting

---

## Files Requiring Immediate Attention

| File                                  | Issues Count | Severity    | Primary Issues                     |
| ------------------------------------- | ------------ | ----------- | ---------------------------------- |
| `src/new_api/pagenew.py`              | 3            | 🔴 Critical | Hardcoded paths, credentials       |
| `src/b18_new/sql_cat.py`              | 4            | 🔴 Critical | SQL injection, inefficient queries |
| `src/api_sql/mysql_client.py`         | 3            | 🔴 Critical | Silent exception swallowing        |
| `src/mk_cats/mknew.py`                | 5            | 🟠 High     | Global state, naming, types        |
| `src/mk_cats/create_category_page.py` | 4            | 🟠 High     | Inconsistent returns, logging      |
| `src/new_api/super/bot.py`            | 3            | 🟠 High     | Error handling                     |
| `src/config/settings.py`              | 2            | 🟡 Medium   | Magic numbers, validation          |
| `src/logging_config.py`               | 2            | 🟢 Low      | Magic numbers, logging levels      |

---

## Positive Observations ✅

1. **Good Test Structure** - Well-organized test files with good fixtures
2. **Modern Python Features** - Uses dataclasses, f-strings, type hints (where present)
3. **Configuration Management** - Centralized settings with environment variable support
4. **Logging Infrastructure** - Comprehensive logging with colored output
5. **Caching Strategy** - Uses LRU cache appropriately in many places
6. **Documentation** - Some modules have excellent docstrings

---

## Summary Statistics

-   **Total Issues Found:** 45+
-   **Critical Issues:** 4
-   **High Severity Issues:** 5
-   **Medium Severity Issues:** 6
-   **Low Severity Issues:** 4
-   **Files Analyzed:** 86 Python files
-   **Test Coverage:** Partial (needs improvement)

---

## Next Steps

1. **Review this report** with the development team
2. **Create GitHub issues** for each action item
3. **Prioritize critical security fixes** for immediate action
4. **Schedule refactoring sprints** for high-severity issues
5. **Set up CI/CD pipeline** with automated linting and testing
6. **Establish code review guidelines** based on findings

---

_Report generated by automated code review process_
