# Cross-Cutting Suggestions

> Derived from reviewing all 7 refactoring plans in `docs/`. Addresses overlaps, deduplication opportunities, and architectural gaps between modules.

---

## 1. Shared Namespace Constants (Merge: api_sql + new_api)

**Source plans:** `api_sql_refactor_plan.md` (5.1.1), `new_api_refactor_plan.md` (5.1.4)

`api_sql/constants.py` **created** — namespace dicts (`NS_TEXT_AR`, `NS_TEXT_EN`, `WIKI_ALIASES`, `SUFFIXED_WIKIS`) now live there and are imported by `service.py`. `new_api/catdepth_new.py:17-39` still has a separate hardcoded `ns_list` dict that should eventually import from `api_sql/constants.py`.

**Suggestion:** Consolidate namespace constants into a single shared location:

-   Option A: Move to `src/core/constants.py` imported by both `api_sql` and `new_api`
-   Option B: `new_api/constants.py` imports from `api_sql/constants.py`
-   The `new_api` plan explicitly says: _"Use the same constants from api_sql/constants.py if possible (deduplicate with api_sql)"_

---

## 2. Shared Text/Category Normalization (Merge: c18 + mk_cats)

**Source plans:** `c18_merged_refactor_plan.md` (5.3.2), `mk_cats_refactor_plan.md` (5.1.1)

Each module repeatedly strips `Category:`/`تصنيف:` prefixes, `[[`, `]]`, and normalizes underscores/spaces.

**Current duplication:**

-   Former `b18` (now in `c18`) proposed `utils/text.py` with `normalize_category_title()`
-   `c18` proposes `utils/text.py` with `clean_category_input()` and `extract_wikidata_qid()`
-   `mk_cats` has `_normalize_en_page_title()` inline in `mknew.py`

**Suggestion:** Create a single `src/core/utils/text.py` with:

-   `normalize_category_title(title, lang) -> str`
-   `clean_wiki_brackets(title) -> str`
-   `extract_wikidata_qid(text) -> str | None`
-   Imported by all three modules instead of each defining its own.

---

## 3. wiki_api + new_api Layering (Merge or Unify)

**Source plans:** `wiki_api_refactor_plan.md`, `new_api_refactor_plan.md`

`new_api` is described as _"object-oriented MediaWiki API abstraction layer (wrapper around wiki_api)"_. Both plans propose `transport.py`, `client.py`, `models.py`, `cache.py` — significant overlap in architecture.

**Suggestion:** After both are individually refactored, consider whether the `client.py` + `transport.py` in `wiki_api` and the `client.py` + `transport.py` in `new_api` should be unified. The `wiki_api` transport layer could be the single source of truth, with `new_api` providing only the OOP wrapper (`MainPage`, `Login`, `CategoryDepth`).

---

## 4. Shared SQL Query Functions (Merge: c18 + api_sql)

**Source plans:** `c18_merged_refactor_plan.md` (5.2.2 / 5.6), `api_sql_refactor_plan.md`

-   `c18/sql_cat.py` embeds raw SQL strings for category member queries
-   `c18/dontadd.py` embeds SQL for fetching "don't add" pages
-   `api_sql/queries.py` will hold `fetch_arcat_titles`, `fetch_encat_titles`, etc.

**Suggestion:** Move all SQL query strings from `c18` into `api_sql/queries.py` (or a shared `src/core/db/queries.py`). Business logic modules should not embed raw SQL.

---

## 5. Remove Dead Code Across All Modules

**Source plans:** All 7 plans

Consolidated dead-code removal checklist:

| Dead code                                             | Module                                           | Plan                            |
| ----------------------------------------------------- | ------------------------------------------------ | ------------------------------- |
| `decode_bytes` function                               | `api_sql/sql_bot.py`                             | api_sql (Quick Wins) — **DONE** |
| `printurl` param, `url`/`url2` variables              | `wiki_api/api_requests.py`                       | wiki_api (Phase 1)              |
| `WikiApiCache` stub (never instantiated)              | `wiki_api/LCN_new.py`                            | wiki_api (Phase 2)              |
| `numb` variable (assigned twice, used once)           | `wiki_api/himoBOT2.py`                           | wiki_api (Phase 4)              |
| `do_lag()` `while GG is True` loop (always exits)     | `wd_bots/lag_bot.py`                             | wd_bots (Phase 1)               |
| `make_sleep_def()` `or` chain (always short-circuits) | `wd_bots/lag_bot.py`                             | wd_bots (Phase 1)               |
| Empty `__init__` methods                              | `new_api/ask_bot.py`, `new_api/handel_errors.py` | new_api (Quick Wins)            |
| Commented-out debug code blocks                       | `new_api/super_page.py`, `new_api/botEdit.py`    | new_api (Quick Wins)            |
| Unused `import copy`                                  | `new_api/super_page.py`                          | new_api (Quick Wins)            |

---

## 6. Module-Level Global State Elimination

**Source plans:** All 7 plans

Every module has module-level mutable state that must become instance-scoped:

| Global                                         | Module                        | Plan               |
| ---------------------------------------------- | ----------------------------- | ------------------ |
| `Save_or_Ask` dict                             | `new_api/ask_bot.py`          | new_api (Phase 2)  |
| `Bot_Cache`, `Created_Cache`                   | `new_api/botEdit.py`          | new_api (Phase 2)  |
| `users_by_lang`, `logins_count`                | `new_api/bot.py`              | new_api (Phase 2)  |
| `ar_lag`, `urls_prints`                        | `new_api/super_login.py`      | new_api (Phase 2)  |
| `FFa_lag`, `newsleep`, `Find_Lag`              | `wd_bots/lag_bot.py`          | wd_bots (Phase 1)  |
| `LC_bot = WikiApiHandler()`                    | `wiki_api/LCN_new.py`         | wiki_api (Phase 3) |
| `API_n_CALLS`                                  | `wiki_api/sub_cats_bot.py`    | wiki_api (Phase 5) |
| `pages_in_arcat_toMake` dict                   | `c18/cat_tools_enlist.py` | c18_merged (5.3.6) |
| `_done_d`, `_new_cat_done`, `_already_created` | `mk_cats/mknew.py`            | mk_cats (5.1.4)    |

---

## 7. Standardize Error Handling Patterns

**Source plans:** `wd_bots_refactor_plan.md` (Phase 2), `wiki_api_refactor_plan.md` (Phase 1), `new_api_refactor_plan.md` (Phase 5)

Multiple error-handling approaches across modules:

-   `wd_bots`: Dual error classification (`WD_API.handle_err_wd` + `out_json.outbot_json_bot`)
-   `wiki_api`: Silent `except Exception` swallows errors
-   `new_api`: Recursive retry in `post_params`

**Suggestion:** Standardize on a common error classification pattern (e.g., `ErrorType` enum + structured error dataclass) across `wd_bots`, `wiki_api`, and `new_api`.

---

## 8. Consistent file rename pattern across all modules

| Plan     | Old name           | New name                                 | Pattern                     |
| -------- | ------------------ | ---------------------------------------- | --------------------------- |
| api_sql  | `db_pool.py`       | `client.py`                              | Lower-layer file renamed    |
| api_sql  | `service.py`       | `gateway.py` + `constants.py`            | Split                       |
| api_sql  | `sql_bot.py`       | `queries.py`                             | Business query file renamed |
| new_api  | `bot.py`           | `transport.py` + `auth.py` + `client.py` | Split into 3                |
| new_api  | `handel_errors.py` | `handle_errors.py`                       | Spelling fix                |
| new_api  | `pagenew.py`       | `factory.py`                             | Factory pattern             |
| wd_bots  | `wd_api_bot.py`    | `queries.py`                             | Query file renamed          |
| wd_bots  | `to_wd.py`         | `operations.py`                          | Operations file renamed     |
| wd_bots  | `lag_bot.py` →     | `lag.py`                                 | Simplify name               |
| wd_bots  | `out_json.py` →    | `errors.py` (merged)                     | Merge + rename              |
| wiki_api | `api_requests.py`  | `transport.py`                           | Transport layer rename      |

---

## 9. Proposed Common Directory Structure

All plans propose a similar subdirectory structure for their modules:

```
module/
├── __init__.py       # Public API re-exports
├── constants.py      # Magic strings, enums, config
├── models.py         # Dataclasses
├── core/             # Business logic
├── tools/            # Reusable tools
├── io/               # I/O layer (SQL, API, files)
└── utils/            # Shared utilities
```

**Suggestion:** Where possible, share `utils/` and `constants.py` across modules rather than each having its own copy.

---

## 10. Planned Order of Execution Across Modules

See `roadmap.md` for the suggested cross-module execution order based on dependency chains.

---

_Generated 2026-04-26 from analysis of all 7 refactoring plans._
