# Migrating from `api_sql` to `api_sql_new`

This guide maps the public API of `src/core/api_sql` to the new refactored `src/core/api_sql_new` package.

## High-level differences

| Aspect                  | `api_sql`                                         | `api_sql_new`                                                                             |
| ----------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Architecture**        | Flat module with free functions                   | Layered: `ConfigLoader` → `DatabaseManager` → `CategoryRepository` → `CategoryComparator` |
| **DB connection**       | `make_sql_connect_silent` (function-per-call)     | `DatabaseManager` singleton with context-manager connections and connection pooling       |
| **Production guard**    | `GET_SQL()` must be checked by caller             | Checked automatically inside `DatabaseManager.get_connection` and `CategoryComparator`    |
| **Error handling**      | Returns `[]` on any error / silently skips in dev | Raises typed exceptions (`DatabaseConnectionError`, `QueryExecutionError`)                |
| **Namespace prefixing** | `add_nstext_to_title(title, ns, lang)`            | `CategoryRepository._add_namespace_prefix` (internal helper)                              |

---

## Function-by-function replacement

### 1. `get_exclusive_category_titles(en_category, ar_category)`

**Old usage**

```python
from core.api_sql import get_exclusive_category_titles

result = get_exclusive_category_titles("Some_category", "تصنيف:اسم_التصنيف")
```

**New usage**

```python
from core.api_sql_new import CategoryComparator

comparator = CategoryComparator()
result = comparator.get_exclusive_category_titles("Some_category", "تصنيف:اسم_التصنيف")
```

| Detail           | Old                          | New                                                     |
| ---------------- | ---------------------------- | ------------------------------------------------------- |
| Returns          | `list[str]`                  | `List[str]`                                             |
| Production guard | Caller checks `GET_SQL()`    | Handled internally; returns `[]` when not in production |
| Normalisation    | Done in `sql_bot.py` helpers | Done by `CategoryComparator.normalize_category_title`   |

---

### 2. `GET_SQL()`

**Old usage**

```python
from core.api_sql import GET_SQL

if GET_SQL():
    ...
```

**New usage**

```python
from core.api_sql_new.config import ConfigLoader

config = ConfigLoader()
if config.is_production():
    ...
```

> **Note:** `api_sql_new` already guards DB access inside `DatabaseManager.get_connection` and `CategoryComparator`, so in most cases you no longer need to check the environment flag manually.

---

### 3. `sql_new(query, wiki="", values=())`

**Old usage**

```python
from core.api_sql import sql_new

rows = sql_new("SELECT * FROM page WHERE page_title = %s", wiki="enwiki", values=("Title",))
```

**New usage**

```python
from core.api_sql_new.db_pool import db_manager

rows = db_manager.execute_query(wiki="enwiki", query="SELECT * FROM page WHERE page_title = %s", params=("Title",))
```

| Detail                  | Old                        | New                                            |
| ----------------------- | -------------------------- | ---------------------------------------------- |
| Entry point             | `sql_new(...)`             | `db_manager.execute_query(...)`                |
| Query param name        | `query`                    | `query`                                        |
| Values param name       | `values`                   | `params`                                       |
| Return type             | `list[dict]`               | `list[dict]`                                   |
| Production guard        | Returns `[]` when not prod | Raises `DatabaseConnectionError` when not prod |
| SELECT-only enforcement | No                         | `execute_query` rejects non-SELECT statements  |
| Bytes decoding          | Manual (if needed)         | Automatic (`bytes` → `utf-8` `str`)            |

---

### 4. `sql_new_title_ns(query, wiki="", t1="page_title", t2="page_namespace", values=())`

There is **no direct drop-in replacement** in `api_sql_new`. You can replicate it by chaining `execute_query` with namespace prefixing:

**Old usage**

```python
from core.api_sql import sql_new_title_ns

titles = sql_new_title_ns(
    "SELECT page_title, page_namespace FROM page ...",
    wiki="ar",
    t1="page_title",
    t2="page_namespace",
    values=("My_Category",),
)
```

**New usage**

```python
from core.api_sql_new.db_pool import db_manager
from core.api_sql_new.repository import CategoryRepository
from core.api_sql_new.constants import NS_TEXT_AR, NS_TEXT_EN

rows = db_manager.execute_query(
    wiki="ar",
    query="SELECT page_title, page_namespace FROM page ...",
    params=("My_Category",),
)

# use the internal helper (simplest if you are inside the same package boundary)
titles = [
    CategoryRepository._add_namespace_prefix(row["page_title"], row["page_namespace"], lang="ar")
    for row in rows
]
```

---

### 5. `add_nstext_to_title(title, ns, lang="ar")`

**Old usage**

```python
from core.api_sql import add_nstext_to_title

full_title = add_nstext_to_title("Science", "14", "en")   # → "Category:Science"
```

**New usage**

`api_sql_new` does not expose a public free function for this, but the logic is trivial to re-use from the constants module:

```python
from core.api_sql_new.constants import NS_TEXT_AR, NS_TEXT_EN

def add_nstext_to_title(title: str, ns: str | int, lang: str = "ar") -> str:
    ns_key = str(ns)
    if not title or ns_key == "0":
        return title
    table = NS_TEXT_AR if lang == "ar" else NS_TEXT_EN
    prefix = table.get(ns_key)
    return f"{prefix}:{title}" if prefix else title
```

> If you need this helper in many places, consider adding it to a shared `utils.py` inside your own module.

---

## Consumers that still import from `api_sql`

The following files still reference the old package and should be migrated:

| File                                   | Imports to replace                         |
| -------------------------------------- | ------------------------------------------ |
| `src/core/b18_new/cat_tools_enlist.py` | `GET_SQL`, `get_exclusive_category_titles` |
| `src/core/b18_new/sql_cat.py`          | `GET_SQL`, `sql_new`, `sql_new_title_ns`   |
| `src/core/c18_new/dontadd.py`          | `GET_SQL`, `sql_new_title_ns`              |

### Migration example for `cat_tools_enlist.py`

```python
# Before
from ..api_sql import GET_SQL, get_exclusive_category_titles

if GET_SQL() and settings.database.use_sql:
    fapages = get_exclusive_category_titles(cat2, "") or []

# After
from ..api_sql_new import CategoryComparator

comparator = CategoryComparator()
if settings.database.use_sql:
    fapages = comparator.get_exclusive_category_titles(cat2, "") or []
```

### Migration example for `sql_cat.py`

```python
# Before
from ..api_sql import GET_SQL, sql_new, sql_new_title_ns

if us_sql is True and GET_SQL():
    ar_list = sql_new_title_ns(qia_ar, wiki="arwiki", t1="page_title", t2="page_namespace", values=(ar_cat2,))

# After
from ..api_sql_new.db_pool import db_manager
from ..api_sql_new.repository import CategoryRepository

if us_sql is True:
    rows = db_manager.execute_query(wiki="arwiki", query=qia_ar, params=(ar_cat2,))
    ar_list = [
        CategoryRepository._add_namespace_prefix(r["page_title"], r["page_namespace"], lang="ar")
        for r in rows
    ]
```

### Migration example for `dontadd.py`

```python
# Before
from ..api_sql import GET_SQL, sql_new_title_ns

if GET_SQL():
    cats = sql_new_title_ns(queries, wiki="ar", t1="page_title", t2="page_namespace")

# After
from ..api_sql_new.db_pool import db_manager
from ..api_sql_new.repository import CategoryRepository

try:
    rows = db_manager.execute_query(wiki="ar", query=queries)
    cats = [
        CategoryRepository._add_namespace_prefix(r["page_title"], r["page_namespace"], lang="ar")
        for r in rows
    ]
except Exception:
    cats = []
```

---

## Summary mapping table

| Old (`api_sql`)                 | New (`api_sql_new`)                                                             | Notes                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `get_exclusive_category_titles` | `CategoryComparator().get_exclusive_category_titles(...)`                       | Instantiated service object                                              |
| `GET_SQL`                       | `ConfigLoader().is_production()`                                                | Usually no longer needed explicitly                                      |
| `sql_new`                       | `db_manager.execute_query(...)`                                                 | `values` → `params`; raises on error                                     |
| `sql_new_title_ns`              | `db_manager.execute_query(...) + CategoryRepository._add_namespace_prefix(...)` | No single function; compose the two steps                                |
| `add_nstext_to_title`           | Re-implement with `NS_TEXT_AR` / `NS_TEXT_EN`                                   | Or extract `CategoryRepository._add_namespace_prefix` into a public util |

---

## Next steps

1. **Update imports** in the three consumer files listed above.
2. **Add a public `add_nstext_to_title` helper** (optional) if you want a true drop-in replacement without duplicating the 10-line logic.
3. **Update tests** in `tests/api_sql/` to import from `api_sql_new` where appropriate.
4. **Remove the old `api_sql` package** once all callers are migrated and tests pass.
