# Arabic Wikipedia Category Creation Tool

`cats_maker` is a Python tool designed to automate and simplify the creation and management of categories on Arabic Wikipedia using `wikitextparser` and the MediaWiki API.

## Project Overview

- **Package Name:** `cats_maker`
- **Python Version:** `>= 3.10`
- **Build Backend:** `hatchling`
- **Primary Dependencies:** `requests`, `wikitextparser`

---

## Installation

### Production Installation

Install the package directly from the Git repository:

```bash
pip install git+https://github.com/ArWikiCats/cats_maker.git -U
```

### Local Development Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/ArWikiCats/cats_maker.git
    cd cats_maker
    ```

2. **Install in editable mode with development dependencies:**
    ```bash
    pip install -e ".[dev]"
    ```

---

## Usage

Here is a basic example of how to import and use `cats_maker` in your Python scripts:

```python
import cats_maker

# Example usage (adjust according to your module exports)
print(f"cats_maker version: {cats_maker.__version__}")
```

---

## Development & Tooling

This project uses modern Python code quality tools configured in `pyproject.toml`.

### Running Tests

Run unit tests using `pytest`:

```bash
pytest
```

### Code Formatting and Linting

- **Ruff (Linter & Formatter):**

    ```bash
    ruff check .
    ruff format .
    ```

- **Black:**

    ```bash
    black .
    ```

- **Isort (Import Ordering):**

    ```bash
    isort .
    ```

- **Type Checking (Pyright / MyPy):**
    ```bash
    pyright
    mypy src
    ```
