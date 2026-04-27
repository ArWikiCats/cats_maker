# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cats Maker New is a Python automation bot that creates Arabic Wikipedia categories from their English counterparts. It resolves Arabic translations via [ArWikiCats](https://github.com/MrIbrahem/ArWikiCats), creates category pages with proper templates/portals, and links them to Wikidata.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.in

# Run the bot
python run.py -encat:Science              # Single category
python run.py -quarry:357357              # From Quarry query
python run.py DEBUG -encat:Mathematics    # With debug logging

# Testing
pytest                                    # Run all tests (excludes network/skip2 by default)
pytest tests/mk_cats/test_mknew.py        # Specific file
pytest -m unit                            # Unit tests only
pytest -m integration                     # Integration tests only
pytest -m "not network"                   # Exclude network tests

# Linting/Formatting
black src/                                # Format code (120 char line length)
isort src/                                # Sort imports
ruff check src/                           # Lint code
```

## Architecture

Layered architecture from top to bottom:

```
run.py (CLI args) → config/settings.py (dataclass config) → mk_cats/mknew.py (business logic)
    → mk_cats/members_helper.py (member collection) → mk_cats/create_category_page.py, categorytext.py (page creation)
    → c18_new/ (data processing) → wiki_api/, wd_bots/, api_sql/ (external services)
```

**Data flow**: English category → `ar_make_lab()` (Arabic label via ArWikiCats) → collect members (SQL/API/SubSub) → filter redirects → check min_members threshold → generate category text → save to ar.wikipedia → update Wikidata sitelink

## Key Modules

-   `src/config/settings.py`: Centralized dataclass-based configuration. All settings accessed via `from src.config import settings`
-   `src/mk_cats/mknew.py`: Core functions - `create_categories_from_list()`, `ar_make_lab()`
-   `src/mk_cats/members_helper.py`: Member collection from SQL, API, and SubSub sources
-   `src/core/wd_bots/`: Wikidata API integration
-   `src/core/wiki_api/`: MediaWiki API calls

## Configuration

Settings are dataclasses in `src/config/settings.py`:

-   `WikipediaConfig`: language codes, user agent, timeout
-   `WikidataConfig`: endpoints, maxlag
-   `DatabaseConfig`: SQL connection settings
-   `CategoryConfig`: min_members (default: 10), stubs, we_try mode
-   `BotConfig`: ask confirmation, diff display

Runtime config via CLI args (processed in `settings._process_argv()`):

-   `-range:<n>`, `-depth:<n>`, `-minmembers:<n>`
-   `-nosql`, `DEBUG`, `testwikidata`, `ask`

## Code Style

-   Line length: 120 characters
-   Formatters: Black, isort (black profile), ruff
-   Target: Python 3.10+ (tested on 3.13)
-   Test framework: pytest with pytest-mock

## Testing Conventions

-   Tests in `tests/` mirror `src/` structure
-   Shared fixtures in `tests/conftest.py`
-   Mock all external API calls (Wikipedia, Wikidata, SQL)
-   Test markers: `unit`, `integration`, `network`, `slow`, `skip2`
-   Default pytest excludes `network` and `skip2` tests

## Important Patterns

```python
# Import main functions from mk_cats
from src.mk_cats import create_categories_from_list, ar_make_lab

# Access settings
from src.config import settings
settings.category.min_members  # minimum members threshold
settings.database.use_sql      # whether to use SQL queries

# Process categories with callback
create_categories_from_list(["Category:Science"], callback=my_callback)
```

## Special Considerations

-   Arabic text handling: ensure proper Unicode/RTL support
-   Wikipedia bot policies: respect rate limits, use bot accounts
-   Blacklists in `src/core/utils/skip_cats.py`: always check before processing categories
-   SQL database access is optional (Wikimedia Tool Labs)
