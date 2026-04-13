# Cats Maker - Arabic Wikipedia Category Creator

A Python automation tool for creating Arabic Wikipedia categories from their English counterparts. This bot processes English Wikipedia categories and creates equivalent Arabic categories with proper translations, templates, portals, and Wikidata integration.

## Table of Contents

-   [Overview](#overview)
-   [Features](#features)
-   [Architecture](#architecture)
-   [Installation](#installation)
-   [Usage](#usage)
-   [Configuration](#configuration)
-   [Project Structure](#project-structure)
-   [Testing](#testing)
-   [Contributing](#contributing)
-   [Related Documentation](#related-documentation)

## Overview

Cats Maker New is a sophisticated Wikipedia bot designed to automate the creation of Arabic Wikipedia categories based on their English counterparts. The tool:

1. Takes a list of English Wikipedia category names
2. Resolves Arabic translations using [ArWikiCats](https://github.com/MrIbrahem/ArWikiCats)
3. Creates the Arabic category pages with proper structure
4. Adds appropriate templates and portal links
5. Links the new categories to Wikidata
6. Adds the new categories to relevant pages

The project uses a centralized dataclass-based configuration system and supports both command-line and programmatic usage. This is particularly useful for expanding the Arabic Wikipedia's category structure to match the more comprehensive English Wikipedia.

## Features

### Core Functionality

-   **Category Translation**: Automatically resolves Arabic category labels from English categories using Wikidata sitelinks and the [ArWikiCats](https://github.com/MrIbrahem/ArWikiCats) library
-   **Category Creation**: Creates new Arabic Wikipedia category pages with proper formatting
-   **Template Generation**: Generates navigation templates for categories (centuries, decades, years, millennia)
-   **Portal Integration**: Automatically adds relevant portal links to categories based on topic detection
-   **Wikidata Integration**: Creates and updates Wikidata sitelinks for newly created categories

### Data Sources

-   **Wikidata API**: Retrieves sitelinks, labels, descriptions, and properties
-   **Wikipedia API**: Queries page information, categories, and langlinks
-   **SQL Database**: Supports Wikimedia Tool Labs SQL databases for efficient queries
-   **Quarry Integration**: Fetches category lists from Quarry queries

### Processing Features

-   **Batch Processing**: Processes multiple categories in a single run
-   **Recursive Processing**: Discovers and processes subcategories
-   **Duplicate Detection**: Tracks processed categories to avoid duplicates
-   **Error Handling**: Robust error handling with logging
-   **Caching**: In-memory caching for API responses
-   **Redirect Filtering**: Automatically filters redirect pages from member lists
-   **Minimum Members Threshold**: Configurable minimum member count before creating categories

## Architecture

The project follows a layered architecture with centralized configuration:

```
┌─────────────────────────────────────────┐
│         Entry Point Layer               │
│         run.py                          │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Configuration Layer                │
│      config/settings.py                 │
│      - WikipediaConfig, WikidataConfig  │
│      - DatabaseConfig, CategoryConfig   │
│      - BotConfig, DebugConfig           │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Business Logic Layer               │
│      mk_cats/mknew.py                   │
│      - create_categories_from_list()    │
│      - one_cat(), process_catagories()  │
│      - make_ar(), ar_make_lab()         │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Member Collection Layer            │
│      mk_cats/members_helper.py          │
│      - collect_category_members()       │
│      - gather_members_from_sql/api      │
│      - merge/filter/deduplicate         │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Page Creation Layer                │
│      mk_cats/create_category_page.py    │
│      mk_cats/categorytext.py            │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Data Processing Layer              │
│      b18_new/, c18_new/                 │
│      - Category processing              │
│      - Link resolution                  │
│      - Member list management           │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      External Services Layer            │
│      - wiki_api/ (MediaWiki API)        │
│      - wd_bots/ (Wikidata API)          │
│      - api_sql/ (Database)              │
└─────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Utilities Layer                    │
│      helps/, utils/, temp/              │
└─────────────────────────────────────────┘
```

### Data Flow

```
English Category Name
    ↓
[ar_make_lab] → Arabic Label (from ArWikiCats)
    ↓
[get_ar_list_from_en] → List of Arabic article titles
    ↓
[find_LCN, Get_Sitelinks] → Language links, Qid
    ↓
[find_Page_Cat_without_hidden] → Parent categories (English)
    ↓
[collect_category_members] → Member pages (SQL, API, SubSub sources)
    ↓
[merge_member_lists] → Deduplicated member list
    ↓
[remove_redirects] → Filtered member list (no redirects)
    ↓
[min_members check] → Ensure minimum member threshold
    ↓
[generate_category_text] → Category page text (with templates)
    ↓
[page.save] → Save to ar.wikipedia
    ↓
[Log_to_wikidata] → Update Wikidata sitelink
```

## Installation

### Prerequisites

-   Python 3.10 or higher
-   pip (Python package manager)
-   Access to Wikipedia API (for actual operations)
-   (Optional) Access to Wikimedia Tool Labs for SQL queries

### Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/MrIbrahem/cats_maker_new.git
    cd cats_maker_new
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.in
    ```

3. **Install optional dependencies (for full functionality):**
    ```bash
    # For Arabic category label resolution
    pip install ArWikiCats
    ```

### Dependencies

-   `wikitextparser>=0.55.7` - Wiki text parsing
-   `tqdm>=4.67.1` - Progress bars
-   `SPARQLWrapper>=2.0.0` - SPARQL queries
-   `pymysql` - MySQL database connections
-   `jsonlines` - JSONL file handling
-   `sqlite_utils` - SQLite utilities
-   `pytest` - Testing framework
-   `pytest-mock` - Test mocking

## Usage

### Basic Usage

```bash
# Process a single category
python run.py -encat:Science

# Process categories from a Quarry query
python run.py -quarry:357357

# Process with debug logging
python run.py DEBUG -encat:Mathematics
```

### Command Line Arguments

#### Category Processing

| Argument          | Description                                              | Example           |
| ----------------- | -------------------------------------------------------- | ----------------- |
| `encat:<name>`    | Process a single English category                        | `encat:Science`   |
| `quarry:<id>`     | Fetch categories from Quarry query                       | `quarry:357357`   |
| `-range:<n>`      | Set range limit for processing (default: 5)              | `-range:10`       |
| `-We_Try`         | Enable retry mode for failed categories                  | `-We_Try`         |
| `-nowetry`        | Disable retry mode                                       | `-nowetry`        |
| `-minmembers:<n>` | Minimum members required to create category (default: 5) | `-minmembers:3`   |
| `-stubs`          | Process stub categories                                  | `-stubs`          |
| `-dontMakeNewCat` | Disable new category creation                            | `-dontMakeNewCat` |
| `-uselabels`      | Use Wikidata labels for category names                   | `-uselabels`      |

#### Debug and Logging

| Argument            | Description                               | Example       |
| ------------------- | ----------------------------------------- | ------------- |
| `DEBUG` or `-debug` | Enable debug logging                      | `DEBUG`       |
| `printurl`          | Print API URLs for debugging              | `printurl`    |
| `printdata`         | Print API data for debugging              | `printdata`   |
| `printtext`         | Print text output for debugging           | `printtext`   |
| `printresult`       | Print results for debugging               | `printresult` |
| `raise`             | Raise exceptions instead of handling them | `raise`       |

#### Database and SQL

| Argument | Description                | Example  |
| -------- | -------------------------- | -------- |
| `-nosql` | Disable SQL database usage | `-nosql` |
| `usesql` | Enable SQL database usage  | `usesql` |

#### Wikidata

| Argument       | Description                          | Example        |
| -------------- | ------------------------------------ | -------------- |
| `testwikidata` | Use Wikidata test environment        | `testwikidata` |
| `maxlag2`      | Set Wikidata maxlag to 1             | `maxlag2`      |
| `descqs`       | Use QuickStatements for descriptions | `descqs`       |

#### Bot Behavior

| Argument  | Description                                  | Example   |
| --------- | -------------------------------------------- | --------- |
| `ask`     | Ask for confirmation before making changes   | `ask`     |
| `nodiff`  | Don't show diff when asking for confirmation | `nodiff`  |
| `diff`    | Force show diff when asking for confirmation | `diff`    |
| `nofa`    | Disable false edit detection                 | `nofa`    |
| `botedit` | Force bot edit (bypass nobots check)         | `botedit` |
| `nologin` | Disable login assertion                      | `nologin` |

#### Site Configuration

| Argument          | Description                                | Example             |
| ----------------- | ------------------------------------------ | ------------------- |
| `-commons`        | Use Commons instead of Wikipedia           | `-commons`          |
| `-family:<name>`  | Custom wiki family (wikiquote, wikisource) | `-family:wikiquote` |
| `-uselang:<code>` | Custom language code for source site       | `-uselang:de`       |
| `-slang:<code>`   | Secondary language for fallback            | `-slang:fr`         |

#### Query Parameters

| Argument      | Description                                     | Example       |
| ------------- | ----------------------------------------------- | ------------- |
| `-offset:<n>` | Starting offset for queries                     | `-offset:100` |
| `depth:<n>`   | Depth limit for category traversal (default: 0) | `depth:3`     |
| `-to:<n>`     | Upper limit for results                         | `-to:500`     |
| `nons10`      | Exclude namespace 10 from results               | `nons10`      |
| `ns:14`       | Only include namespace 14 in results            | `ns:14`       |

### Programmatic Usage

```python
from src.mk_cats import create_categories_from_list

# Process a list of categories
categories = [
    "Category:Science",
    "Category:Mathematics",
    "Category:Physics"
]

# Optional callback for processing results
def my_callback(title, **kwargs):
    print(f"Processed: {title}")

create_categories_from_list(categories, callback=my_callback)
```

### Individual Functions

```python
from src.mk_cats import ar_make_lab, process_catagories

# Get Arabic label for an English category
ar_label = ar_make_lab("Category:Science")
print(f"Arabic label: {ar_label}")

# Process a single category with its subcategories
process_catagories("Category:Science", ar_label, num=1, lenth=1)
```

## Configuration

Configuration is managed through the `src/config/settings.py` module, which provides dataclass-based settings that can be configured via environment variables or command-line arguments. All settings are centralized and type-safe.

### Settings Classes

The configuration system uses the following dataclasses:

-   **WikipediaConfig**: Wikipedia API settings (language codes, user agent, timeout)
-   **WikidataConfig**: Wikidata API settings (endpoints, timeout, maxlag)
-   **DatabaseConfig**: Database connection settings (host, port, use_sql)
-   **DebugConfig**: Debug and logging options (print_url, print_data, raise_errors)
-   **BotConfig**: Bot behavior settings (ask, no_diff, force_edit)
-   **CategoryConfig**: Category processing settings (stubs, min_members, we_try)
-   **QueryConfig**: Query parameters (offset, depth, to_limit)
-   **SiteConfig**: Alternative site settings (use_commons, custom_family)

### Usage

```python
from src.config import settings

# Access Wikipedia configuration
print(settings.wikipedia.ar_code)  # 'ar'
print(settings.wikipedia.user_agent)  # 'Himo bot/1.0...'

# Access Wikidata configuration
print(settings.wikidata.endpoint)  # 'https://www.wikidata.org/w/api.php'
print(settings.wikidata.maxlag)  # 5

# Access Database configuration
print(settings.database.use_sql)  # True

# Access Category configuration
print(settings.category.min_members)  # 5
print(settings.category.we_try)  # True

# Access Bot configuration
print(settings.bot.ask)  # False

# Access computed site properties
print(settings.EEn_site.code)  # 'en'
print(settings.AAr_site.family)  # 'wikipedia'

# Access global settings
print(settings.range_limit)  # 5
print(settings.debug)  # False
```

### Environment Variables

#### Wikipedia Configuration

| Variable               | Description                                | Default                                                                |
| ---------------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `WIKIPEDIA_AR_CODE`    | Arabic Wikipedia language code             | `ar`                                                                   |
| `WIKIPEDIA_EN_CODE`    | English Wikipedia language code            | `en`                                                                   |
| `WIKIPEDIA_AR_FAMILY`  | Arabic Wikipedia family                    | `wikipedia`                                                            |
| `WIKIPEDIA_EN_FAMILY`  | English Wikipedia family                   | `wikipedia`                                                            |
| `WIKIPEDIA_USER_AGENT` | User agent string for API requests         | `Himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)` |
| `WIKIPEDIA_TIMEOUT`    | Default timeout for API requests (seconds) | `10`                                                                   |

#### Wikidata Configuration

| Variable                   | Description                                     | Default                              |
| -------------------------- | ----------------------------------------------- | ------------------------------------ |
| `WIKIDATA_ENDPOINT`        | Wikidata API endpoint URL                       | `https://www.wikidata.org/w/api.php` |
| `WIKIDATA_SPARQL_ENDPOINT` | SPARQL query endpoint URL                       | `https://query.wikidata.org/sparql`  |
| `WIKIDATA_TIMEOUT`         | Default timeout for Wikidata requests (seconds) | `30`                                 |
| `WIKIDATA_MAXLAG`          | Maximum lag for Wikidata API requests           | `5`                                  |

#### Database Configuration

| Variable           | Description                             | Default |
| ------------------ | --------------------------------------- | ------- |
| `DATABASE_HOST`    | Database host (optional)                | `None`  |
| `DATABASE_PORT`    | Database port                           | `3306`  |
| `DATABASE_USE_SQL` | Whether to use SQL database for queries | `True`  |

#### Category Configuration

| Variable      | Description                                   | Default |
| ------------- | --------------------------------------------- | ------- |
| `MIN_MEMBERS` | Minimum members required to create a category | `5`     |

#### Global Settings

| Variable      | Description                                          | Default |
| ------------- | ---------------------------------------------------- | ------- |
| `RANGE_LIMIT` | Maximum number of iterations for category processing | `5`     |
| `DEBUG`       | Enable debug mode                                    | `False` |
| `LOG_LEVEL`   | Logging level (DEBUG, INFO, WARNING, ERROR)          | `INFO`  |

### Blacklists

The project maintains several blacklists to skip certain categories:

-   **English category blacklist**: Categories to skip entirely
-   **Template blacklist**: Templates to exclude from processing
-   **Name blacklist**: Specific names to avoid

## Project Structure

```
cats_maker_new/
├── run.py                    # Main entry point
├── requirements.in           # Python dependencies
├── pyproject.toml           # Project configuration (Black, isort, ruff)
├── pytest.ini               # Pytest configuration
├── refactoring_plan.md      # Technical refactoring documentation
├── testing_plan.md          # Testing strategy documentation
│
├── src/                     # Source code
│   ├── config/             # Configuration management
│   │   ├── __init__.py     # Exports settings
│   │   └── settings.py     # Centralized dataclass-based settings
│   │
│   ├── mk_cats/            # Main category creation logic
│   │   ├── __init__.py     # Module exports
│   │   ├── mknew.py        # Core functions (create_categories_from_list)
│   │   ├── categorytext.py # Text generation for category pages
│   │   ├── create_category_page.py  # Page creation logic
│   │   ├── members_helper.py # Category member collection/processing
│   │   ├── add_bot.py      # Add categories to pages
│   │   └── utils/          # Utility functions (filter_en, check_en, portal_list)
│   │
│   ├── b18_new/            # Category processing and links
│   │   ├── LCN_new.py      # Language link discovery
│   │   ├── cat_tools.py    # Category utilities (SubSub)
│   │   ├── sql_cat.py      # SQL-based category queries
│   │   └── sql_cat_checker.py # SQL category validation
│   │
│   ├── c18_new/            # Additional category tools
│   │   ├── bots/           # Bot utilities (filter_cat, english_page_title)
│   │   ├── cats_tools/     # Category conversion tools (ar_from_en)
│   │   └── tools_bots/     # Helper bots
│   │
│   ├── wd_bots/            # Wikidata integration
│   │   ├── wd_api_bot.py   # Wikidata API functions
│   │   ├── to_wd.py        # Log to Wikidata
│   │   ├── get_bots.py     # Data retrieval
│   │   ├── qs_bot.py       # QuickStatements integration
│   │   └── utils/          # Utilities (lag_bot, handle_wd_errors)
│   │
│   ├── wiki_api/           # Wikipedia API calls
│   │   ├── himoBOT2.py     # General Wikipedia functions
│   │   ├── wd_sparql.py    # SPARQL queries
│   │   ├── api_requests.py # HTTP request handling
│   │   └── check_redirects.py # Redirect page filtering
│   │
│   ├── api_sql/            # Database operations
│   │   ├── wiki_sql.py     # Wiki SQL queries
│   │   └── mysql_client/   # MySQL connection handling
│   │
│   ├── new_api/            # Page API abstraction
│   │   ├── page.py         # MainPage class
│   │   └── super/          # API utilities (login, cookies, params)
│   │
│   ├── helps/              # Helper utilities
│   │   ├── log.py          # Logging wrapper
│   │   └── printe_helper.py # Print formatting
│   │
│   ├── temp/               # Template generation
│   │   └── *_temp.py       # Century, decade, year templates
│   │
│   └── utils/              # General utilities
│       └── skip_cats.py    # Category blacklists
│
├── tests/                  # Test suite
│   ├── conftest.py        # Shared test fixtures
│   ├── config/            # Configuration tests
│   ├── mk_cats/           # mk_cats tests
│   ├── b18_new/           # b18_new tests
│   ├── c18_new/           # c18_new tests
│   ├── wd_bots/           # wd_bots tests
│   ├── wiki_api/          # wiki_api tests
│   ├── api_sql/           # api_sql tests
│   ├── integration/       # Integration tests
│   └── temp/              # Template tests
│
└── .github/
    ├── workflows/
    │   └── pytest.yaml    # CI/CD configuration
    └── copilot-instructions.md  # Copilot coding agent instructions
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/mk_cats/test_mknew.py

# Run with coverage report
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude network-dependent tests
pytest -m "not network"
```

### Test Structure

The test suite covers:

-   **Unit Tests**: Individual function testing with mocked dependencies
-   **Integration Tests**: End-to-end workflow testing
-   **Fixture Tests**: Reusable test data and mock configurations

### Test Coverage

Current test coverage includes approximately **880+ tests** covering:

| Module      | Description                    | Status |
| ----------- | ------------------------------ | ------ |
| api_sql     | Database query functions       | ✅     |
| b18_new     | Category processing and links  | ✅     |
| c18_new     | Category tools and conversions | ✅     |
| config      | Settings and configuration     | ✅     |
| helps       | Logging and utilities          | ✅     |
| mk_cats     | Core category creation         | ✅     |
| utils       | Skip lists and blacklists      | ✅     |
| wd_bots     | Wikidata integration           | ✅     |
| wiki_api    | Wikipedia API calls            | ✅     |
| temp        | Template generation            | ✅     |
| integration | End-to-end tests               | ✅     |

### Test Markers

The test suite uses the following pytest markers:

-   `unit`: Unit tests (fast, isolated)
-   `integration`: Integration tests (may require mocking)
-   `network`: Tests requiring network access (skipped by default in CI)
-   `slow`: Slow-running tests
-   `skip2`: Tests to skip temporarily

### Writing Tests

Tests follow pytest conventions with comprehensive fixtures:

```python
import pytest
from src.mk_cats.mknew import ar_make_lab

class TestArMakeLab:
    """Tests for ar_make_lab function"""

    def test_returns_label_for_valid_category(self, mocker):
        """Test that valid categories return Arabic labels"""
        mocker.patch('src.mk_cats.mknew.filter_en.filter_cat', return_value=True)
        mocker.patch('src.mk_cats.mknew.resolve_arabic_category_label',
                     return_value='علوم')

        result = ar_make_lab("Category:Science")
        assert result == "علوم"

    def test_returns_empty_for_filtered_category(self, mocker):
        """Test that filtered categories return empty string"""
        mocker.patch('src.mk_cats.mknew.filter_en.filter_cat', return_value=False)

        result = ar_make_lab("Category:Stubs")
        assert result == ""
```

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install development dependencies: `pip install -r requirements.in`
4. Make your changes
5. Run tests: `pytest`
6. Run linters: `ruff check src/`
7. Submit a pull request

### Code Style

This project uses:

-   **Black** for code formatting (line length: 120)
-   **isort** for import sorting
-   **ruff** for linting

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
ruff check src/
```

### Commit Guidelines

-   Write clear, descriptive commit messages
-   Reference issues when applicable
-   Keep commits focused and atomic

## Related Documentation

-   **[refactoring_plan.md](refactoring_plan.md)**: Detailed technical documentation about the codebase architecture, execution flow, and planned improvements
-   **[testing_plan.md](testing_plan.md)**: Comprehensive testing strategy, test coverage goals, and test examples
-   **[Wikidata API](https://www.wikidata.org/wiki/Wikidata:Data_access)**: Wikidata data access documentation
-   **[MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page)**: Wikipedia API reference

## License

This project is open source. See repository for license details.

## Acknowledgments

-   Arabic Wikipedia community
-   Wikidata project
-   [ArWikiCats](https://github.com/MrIbrahem/ArWikiCats) project
