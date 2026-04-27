# GitHub Copilot Instructions for Cats Maker New

## Project Overview

Cats Maker New is a Python automation tool for creating Arabic Wikipedia categories from their English counterparts. The bot processes English Wikipedia categories and creates equivalent Arabic categories with proper translations, templates, portals, and Wikidata integration.

## Technology Stack

- **Language**: Python 3.10+ (currently targeting 3.13)
- **Key Dependencies**:
  - `wikitextparser>=0.55.7` - Wiki text parsing
  - `tqdm>=4.67.1` - Progress bars
  - `SPARQLWrapper>=2.0.0` - SPARQL queries
  - `pymysql` - MySQL database connections
  - `jsonlines` - JSONL file handling
  - `sqlite_utils` - SQLite utilities
  - `pytest` - Testing framework
  - `pytest-mock` - Test mocking

## Code Style and Formatting

### Formatters and Linters
- **Black**: Code formatter with line length of 120 characters
- **isort**: Import sorter with Black profile
- **ruff**: Linter targeting Python 3.13

### Style Guidelines
- Line length: 120 characters
- Use Black formatting style
- Follow isort for import organization (multi-line imports with trailing commas)
- Minimum Python version: 3.10 (currently tested with 3.13)

### Commands
```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
ruff check src/
```

## Testing

### Test Framework
- **Framework**: pytest
- **Total Tests**: ~1563 tests covering all modules
- **Test Markers**: `unit`, `integration`, `network`, `slow`, `fast`, `skip2`

### Running Tests
```bash
# Run all tests (excluding network and skip2)
pytest

# Run specific test file
pytest tests/mk_cats/test_mknew.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Test Guidelines
- Use pytest conventions with fixtures from `tests/conftest.py`
- Mock external API calls (Wikipedia API, Wikidata API, SQL databases)
- Keep tests focused and atomic
- Use descriptive test names following pattern: `test_<action>_<expected_result>`
- Test files follow pattern: `test*.py`, `*Test.py`, `Test*.py`

## Architecture

### Layered Architecture
```
Entry Point (run.py)
    ↓
Business Logic (mk_cats/mknew.py)
    ↓
Page Creation (mk_cats/create_category_page.py, categorytext.py)
    ↓
Data Processing (c18/)
    ↓
External Services (wiki_api/, wd_bots/, api_sql/)
    ↓
Utilities (helps/, utils/, temp/)
```

### Key Modules

1. **mk_cats/**: Main category creation logic
   - `mknew.py`: Core functions (`create_categories_from_list`, `ar_make_lab`)
   - `categorytext.py`: Text generation for category pages
   - `create_category_page.py`: Page creation logic

2. **c18/**: Category processing, link resolution, and category tools
   - `sql_cat.py`: SQL-based category queries
   - `cat_tools_enlist.py`: Category member listing
   - `bots/`: Bot tools (filter_cat, english_page_title)
   - `cats_tools/`: Category conversion tools (ar_from_en)
   - `tools_bots/`: Helper bots

3. **wd_bots/**: Wikidata integration
   - `wd_api_bot.py`: Wikidata API functions
   - `to_wd.py`: Log categories to Wikidata

4. **wiki_api/**: Wikipedia API calls
   - `himoBOT2.py`: General Wikipedia API functions

5. **temp/**: Template generation for centuries, decades, years

## Important Conventions

### Category Processing
- Always check blacklists before processing categories (`utils/skip_cats.py`)
- Use Wikidata and ArWikiCats for Arabic label resolution
- Validate category existence before creation
- Log all operations for debugging

### API Interactions
- Cache API responses when possible
- Handle rate limiting and network errors gracefully
- Use mock data in tests, never make real API calls in tests
- Disable pagers when using git commands: `git --no-pager`

### Error Handling
- Use try-except blocks for external API calls
- Log errors with appropriate context
- Return meaningful error messages
- Don't fail silently

### Configuration
- Command-line arguments handled via `sys.argv`
- Runtime configuration in settings  (e.g., `settings.range_limit = 5`)
- Debug mode enabled with `DEBUG` argument

## Build and Run

### Installation
```bash
pip install -r requirements.in
```

### Running the Application
```bash
# Process a single category
python run.py -encat:Science

# Process from Quarry query
python run.py -quarry:357357

# With debug logging
python run.py DEBUG -encat:Mathematics
```

### Command Line Arguments
- `encat:<name>`: Process a single English category
- `quarry:<id>`: Fetch categories from Quarry query
- `-depth:<n>`: Set recursion depth (default: 5)
- `-range:<n>`: Set range limit for processing
- `DEBUG`: Enable debug logging

## Common Patterns

### Arabic Label Resolution
```python
# ar_make_lab is re-exported from mk_cats/__init__.py
from src.mk_cats import ar_make_lab

# Get Arabic label for English category
ar_label = ar_make_lab("Category:Science")
```

### Category Processing
```python
# create_categories_from_list is re-exported from mk_cats/__init__.py
from src.mk_cats import create_categories_from_list

categories = ["Category:Science", "Category:Mathematics"]
create_categories_from_list(categories, callback=my_callback)
```

### Mocking in Tests
```python
def test_example(mocker):
    mocker.patch('src.module.function', return_value='expected')
    # Test code
```

## Special Considerations

### Wikipedia Integration
- Respect Wikipedia's rate limits and API usage policies
- Use bot accounts for automated edits
- Follow Wikipedia's bot approval process
- Never commit credentials to source code

### Arabic Text Handling
- Ensure proper Unicode handling for Arabic text
- Test RTL (right-to-left) text rendering when applicable
- Validate Arabic character encoding

### Database Access
- SQL database access is optional (Wikimedia Tool Labs)
- Use connection pooling for efficiency
- Always close database connections properly

## Files to Avoid Modifying

- `.git/`: Git internals
- `__pycache__/`: Python cache files
- `.pytest_cache/`: Pytest cache
- `.mypy_cache/`: MyPy cache
- `build/`, `dist/`: Build artifacts
- `.venv/`, `venv/`: Virtual environments

## Documentation

- **README.md**: User-facing documentation and usage guide
- **refactoring_plan.md**: Technical architecture and planned improvements
- **testing_plan.md**: Testing strategy and coverage goals

## When Making Changes

1. Understand the existing code structure before modifying
2. Follow the established patterns in similar modules
3. Add or update tests for new functionality
4. Run tests before committing: `pytest`
5. Format code: `black src/ && isort src/`
6. Lint code: `ruff check src/`
7. Update documentation if changing public APIs
8. Keep commits focused and atomic
